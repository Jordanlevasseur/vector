"""Portable snapshot repository: streaming catalogues and deduplicated blocks.

No general archive extraction, executable extension loading or external services.
Only known logical database/object names can be restored. Completion is published
last. Recovery restarts staged work using immutable blocks, never existing data.
"""
from contextlib import contextmanager
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import sys
import tempfile
import time
from uuid import uuid4
import zlib

from vector_core.database import APPLICATION_ID,MIGRATIONS
from vector_core.maintenance import sync,file_hash
from vector_core.storage import BLOCK,DIGEST,capacity,safe_path,input_file,atomic_json,object_path,object_chunks
from vector_core.portable_crypto import load_key,require_crypto,object_name,seal,unseal

ID=re.compile(r'[0-9a-f]{32}\Z')
FORMAT='VECTOR-PORTABLE-1'
CATALOGUE='''
CREATE TABLE meta(key TEXT PRIMARY KEY,value TEXT NOT NULL);
CREATE TABLE files(name TEXT PRIMARY KEY,bytes INTEGER NOT NULL,sha256 TEXT NOT NULL);
CREATE TABLE blocks(file_name TEXT NOT NULL REFERENCES files(name),ordinal INTEGER NOT NULL,
 digest TEXT NOT NULL,raw_bytes INTEGER NOT NULL,stored_bytes INTEGER NOT NULL,codec TEXT NOT NULL,
 PRIMARY KEY(file_name,ordinal));
'''


def unique(pairs):
    result={}
    for key,value in pairs:
        if key in result:raise ValueError('Duplicate manifest key.')
        result[key]=value
    return result


def read_json(path):
    with input_file(path) as stream:data=stream.read(65537)
    if len(data)>65536:raise ValueError('Descriptor exceeds bounded metadata size.')
    return json.loads(data,object_pairs_hook=unique,parse_constant=lambda x:(_ for _ in ()).throw(ValueError(x)))


def _schema(db):
    return [tuple(row) for row in db.execute("SELECT type,name,tbl_name,sql FROM sqlite_schema ORDER BY type,name")]


def validate_database(db,data_root=None,deadline=None):
    db.enable_load_extension(False)
    db.execute('PRAGMA trusted_schema=OFF')
    db.setlimit(sqlite3.SQLITE_LIMIT_LENGTH,32*1024*1024)
    identity=db.execute('PRAGMA application_id').fetchone()[0]
    version=db.execute('PRAGMA user_version').fetchone()[0]
    if identity!=APPLICATION_ID or type(version) is not int or not 1<=version<=len(MIGRATIONS):
        raise ValueError('Incompatible database identity/schema version.')
    expected=sqlite3.connect(':memory:')
    try:
        for script in MIGRATIONS[:version]:expected.executescript(script)
        if _schema(db)!=_schema(expected):raise ValueError('Unknown/modified database schema; persistence or code compatibility is not established.')
    finally:expected.close()
    from vector_core.memory import verify_connection
    integrity=verify_connection(db,data_root,deadline)
    if not integrity['passed']:raise ValueError('Database/original integrity failed: '+str(integrity['errors'][:3]))
    if version>=5:
        for contract,version in db.execute('SELECT name,version FROM persistence_contracts'):
            if version!=1:raise ValueError('Unsupported persistence contract version: '+contract)
        from vector_core.persistence import validate_model
        for contract,record_key,payload in db.execute('SELECT contract,record_key,payload FROM persistent_records'):
            decoded=json.loads(payload,object_pairs_hook=unique,parse_constant=lambda value:(_ for _ in ()).throw(ValueError(value)))
            if contract=='models':validate_model(db,decoded)
            from vector_core.projects import validate_record
            validate_record(db,contract,record_key,decoded)
            if contract=='preferences':
                from vector_core.persistence import validate_preference
                validate_preference(record_key,decoded)
            if contract=='preferences' and record_key=='__vector_runtime__':
                if (not isinstance(decoded,dict) or set(decoded)!={'max_source_bytes'}
                    or type(decoded['max_source_bytes']) is not int or not 1024<=decoded['max_source_bytes']<=16*1024*1024):
                    raise ValueError('Unsupported persistent runtime preferences.')
        missing=db.execute('SELECT name FROM external_dependencies LIMIT 1').fetchone()
        if missing:raise ValueError('Required external asset prevents self-contained restoration: '+missing[0])
    return integrity


def inventory(memory,deadline=None):
    """No arbitrary home-directory sweep and no silently omitted unknown files."""
    root=memory.config.data_dir
    validate_database(memory.db,memory.config.data_dir,deadline)
    allowed={'.vector-data','vector.sqlite3','vector.sqlite3-wal','vector.sqlite3-shm','vector.sqlite3-journal',
             'operations.log','operations.log.1','operations.log.2','objects','staging','backups','portable_work','.writer.lock','.location.json'}
    for entry in root.iterdir():
        directories={'objects','staging','backups','portable_work'}
        if (entry.is_symlink() or entry.name not in allowed
            or (entry.name in directories and not entry.is_dir())
            or (entry.name not in directories and not entry.is_file())):
            raise ValueError('Unregistered persistent state: '+entry.name)
    transfers=root/'portable_work'
    if transfers.exists():
        for repository in transfers.iterdir():
            if not repository.is_dir() or repository.is_symlink() or not ID.fullmatch(repository.name):raise ValueError('Unknown private transfer state.')
            for job in repository.iterdir():
                if not job.is_dir() or job.is_symlink() or not ID.fullmatch(job.name):raise ValueError('Unknown private transfer state.')
                for item in job.iterdir():
                    known=item.name in ('transfer.json','database.sqlite3','database.sqlite3-journal','database.sqlite3-wal','database.sqlite3-shm','catalogue.sqlite3','catalogue.sqlite3-journal','catalogue.gcm')
                    transient=re.fullmatch(r'[0-9a-f]{32}\.(part|block|cipher)',item.name) or re.fullmatch(r'transfer\.json\.[0-9a-f]{32}\.new',item.name)
                    if item.is_symlink() or not item.is_file() or not (known or transient):raise ValueError('Unknown private transfer file.')
    staging=root/'staging'
    if staging.exists() and any(staging.iterdir()):raise ValueError('Pending object transfer: run storage-recover before complete export.')
    for row in memory.db.execute('SELECT digest,raw_bytes,stored_bytes,codec FROM managed_objects'):
        for _ in object_chunks(root,row,deadline):pass
    objects=root/'objects'
    if objects.exists():
        for prefix in objects.iterdir():
            if prefix.is_symlink() or not prefix.is_dir() or not re.fullmatch('[0-9a-f]{2}',prefix.name):
                raise ValueError('Unknown managed storage path.')
            for item in prefix.iterdir():
                digest=prefix.name+item.name
                if item.is_symlink() or not DIGEST.fullmatch(digest) or not item.is_file():raise ValueError('Unsafe managed object path.')
                if memory.db.execute('SELECT 1 FROM managed_objects WHERE digest=?',(digest,)).fetchone() is None:
                    raise ValueError('Unregistered object; storage recovery required.')
    backups=root/'backups'
    if backups.exists():
        if backups.is_symlink():raise ValueError('Unsafe backup path.')
        for folder in backups.iterdir():
            if folder.is_symlink() or not ID.fullmatch(folder.name) or not folder.is_dir():raise ValueError('Unclassified local recovery file.')
            for entry in folder.iterdir():
                if entry.is_symlink() or not entry.is_file() or entry.name not in ('archive.sqlite3','manifest.json'):raise ValueError('Unclassified local recovery file.')
    return {'authoritative':'SQLite snapshot plus every registered managed object',
            'excluded':['SQLite transient WAL/SHM represented by consistent snapshot','rotating technical logs; authoritative audit is in database',
                        'recognized same-disk recovery replicas; no recursive backup inclusion'],
            'platform_dependencies':['Linux seccomp/libseccomp','Python >=3.12','SQLite with FTS5',
                                     'compatible VECTOR application/schema','cryptography if AES-GCM selected']}


def _connect(path,readonly=False):
    from urllib.parse import quote
    db=sqlite3.connect('file:'+quote(str(path),safe='/')+'?mode=ro&immutable=1',uri=True) if readonly else sqlite3.connect(path)
    db.execute('PRAGMA trusted_schema=OFF');db.enable_load_extension(False)
    return db


def _repository(directory,key,create=False):
    root=safe_path(directory)
    if create and (not root.exists() or (root.is_dir() and not any(root.iterdir()))):
        from vector_core.config import Config
        Config.load(data_dir=str(root))
        root.mkdir(parents=True,mode=0o700,exist_ok=True)
        root.chmod(0o700)
        descriptor={'format':FORMAT,'id':uuid4().hex,'salt':os.urandom(32).hex(),
                    'cipher':'AES-256-GCM' if key else 'none','block_bytes':BLOCK}
        atomic_json(root/'repository.json',descriptor)
        for name in ('objects','snapshots','pending'):(root/name).mkdir(mode=0o700)
        sync(root);sync(root.parent)
    descriptor=read_json(root/'repository.json')
    if (not isinstance(descriptor,dict) or set(descriptor)!={'format','id','salt','cipher','block_bytes'}
        or descriptor['format']!=FORMAT or not isinstance(descriptor['id'],str) or not ID.fullmatch(descriptor['id'])
        or not isinstance(descriptor['salt'],str) or not DIGEST.fullmatch(descriptor['salt']) or descriptor['block_bytes']!=BLOCK
        or descriptor['cipher'] not in ('none','AES-256-GCM')):raise ValueError('Incompatible repository descriptor.')
    if (descriptor['cipher']=='AES-256-GCM')!=(key is not None):raise ValueError('Recovery key required exactly for encrypted repositories.')
    if key:require_crypto()
    names=set()
    for item in root.iterdir():
        if item.name not in ('repository.json','objects','snapshots','pending','latest.json') or item.is_symlink():
            raise ValueError('Unclassified archive repository state.')
        names.add(item.name)
    if not {'repository.json','objects','snapshots','pending'}<=names:raise ValueError('Incomplete repository layout.')
    for name in ('objects','snapshots','pending'):
        if safe_path(root/name).is_symlink() or not (root/name).is_dir():raise ValueError('Unsafe repository path.')
    return root,descriptor


def _block_path(root,digest,key,descriptor):
    if not isinstance(digest,str) or not DIGEST.fullmatch(digest):raise ValueError('Invalid archive block digest.')
    name=object_name(digest,key,descriptor)
    path=root/'objects'/name[:2]/name[2:]
    return safe_path(path)


def _decode_block(root,row,key,descriptor,work):
    digest,size,stored,codec=row
    if (not isinstance(digest,str) or not DIGEST.fullmatch(digest) or type(size) is not int or not 0<size<=BLOCK
        or type(stored) is not int or not 0<stored<=BLOCK+65536 or codec not in ('raw','zlib')):
        raise ValueError('Malformed block descriptor / expansion bound.')
    path=_block_path(root,digest,key,descriptor)
    if path.stat().st_size!=stored:raise ValueError('Archive block size mismatch.')
    if key:
        decoded=work/(uuid4().hex+'.block')
        unseal(path,decoded,key,descriptor,'object:'+digest)
        try:
            with input_file(decoded) as stream:encoded=stream.read(BLOCK+65537)
        finally:decoded.unlink(missing_ok=True)
    else:
        with input_file(path) as stream:encoded=stream.read(BLOCK+65537)
    if codec=='zlib':
        decoder=zlib.decompressobj();data=decoder.decompress(encoded,size+1)
        if not decoder.eof or decoder.unused_data or decoder.unconsumed_tail:raise ValueError('Compressed archive block bomb/truncation.')
    else:data=encoded
    if len(data)!=size or hashlib.sha256(data).hexdigest()!=digest:raise ValueError('Archive block checksum mismatch.')
    return data


def _publish_file(source,target):
    """Atomic no-replace publication across filesystems; encrypted input stays encrypted."""
    temporary=target.parent/(uuid4().hex+'.part')
    try:
        with input_file(source) as original,temporary.open('xb') as output:
            temporary.chmod(0o600)
            capacity(target.parent,os.fstat(original.fileno()).st_size)
            shutil.copyfileobj(original,output,BLOCK)
            output.flush();os.fsync(output.fileno())
        os.link(temporary,target)
        sync(target.parent)
    finally:
        temporary.unlink(missing_ok=True)
        sync(target.parent)


def _store_block(root,data,key,descriptor,work):
    digest=hashlib.sha256(data).hexdigest();path=_block_path(root,digest,key,descriptor)
    encoded=zlib.compress(data,1);codec='zlib'
    expected=len(encoded)+(33 if key else 0)
    row=(digest,len(data),expected,codec)
    if path.exists():
        # Existing content is never blindly trusted or overwritten.
        row=(digest,len(data),path.stat().st_size,'zlib')
        _decode_block(root,row,key,descriptor,work)
        return row,False
    capacity(root,expected)
    path.parent.mkdir(mode=0o700,exist_ok=True)
    temporary=work/(uuid4().hex+'.part')
    with temporary.open('xb') as output:output.write(encoded);output.flush();os.fsync(output.fileno())
    encrypted=None
    if key:
        encrypted=work/(uuid4().hex+'.cipher')
        seal(temporary,encrypted,key,descriptor,'object:'+digest)
    try:
        _publish_file(encrypted or temporary,path)
    except FileExistsError:_decode_block(root,row,key,descriptor,work)
    path.chmod(0o600);sync(path.parent);sync(root/'objects')
    temporary.unlink()
    if encrypted:encrypted.unlink()
    return row,True


def export_vector(memory,directory,*,key_file=None,resume=None,deadline_seconds=900,fault=None):
    end=time.monotonic()+deadline_seconds
    key=load_key(key_file) if key_file else None
    destination=safe_path(directory)
    protected=(memory.config.data_dir,Path('/home/mint/VECTOR/helix'),Path(__file__).resolve().parents[2])
    if any(destination.is_relative_to(p) or p.is_relative_to(destination) for p in protected):
        raise ValueError('Portable repository must be independent of data/application/HELIX.')
    if key_file and (safe_path(key_file).is_relative_to(destination) or safe_path(key_file).is_relative_to(memory.config.data_dir)):
        raise ValueError('Keep the recovery key outside data and export repositories.')
    inventory_report=inventory(memory,end)
    root,descriptor=_repository(destination,key,create=True)
    identifier=resume or uuid4().hex
    if not ID.fullmatch(identifier):raise ValueError('Invalid transfer ID.')
    work=safe_path(memory.config.data_dir/'portable_work'/descriptor['id']/identifier)
    public_work=safe_path(root/'pending'/identifier)
    public_work.mkdir(mode=0o700,exist_ok=True)
    snapshot=work/'database.sqlite3'
    state=work/'transfer.json'
    published=root/'snapshots'/(identifier+('.gcm' if key else '.sqlite3'))
    if resume:
        info=read_json(state)
        if info.get('source')==str(memory.config.data_dir) and info.get('stage') in ('snapshot-ready','published') and published.exists():
            # A crash may occur after the durable publish and before updating the head.
            with open_catalogue(root,identifier,key_file) as (_,_,catalog,_,_,_):
                archived_hash=catalog.execute("SELECT sha256 FROM files WHERE name='database'").fetchone()[0]
                if archived_hash!=info.get('database_sha256'):raise ValueError('Published snapshot does not match transfer receipt.')
            verified=verify_export(root,snapshot=identifier,key_file=key_file,deadline_seconds=deadline_seconds)
            _finish_export(memory,root,work,public_work,identifier,archived_hash)
            return {'complete':True,'snapshot_id':identifier,'transfer_id':identifier,'recovered_publication':True,'verification':verified}
        if info.get('source')!=str(memory.config.data_dir) or info.get('stage')!='snapshot-ready':
            raise ValueError('Snapshot was not completed; retain evidence and start a new export.')
        if file_hash(snapshot)!=info['database_sha256']:raise ValueError('Staged snapshot corrupted; no resume.')
    else:
        work.mkdir(parents=True,mode=0o700)
        atomic_json(state,{'source':str(memory.config.data_dir),'stage':'snapshot-starting'})
        pages=memory.db.execute('PRAGMA page_count').fetchone()[0];page_size=memory.db.execute('PRAGMA page_size').fetchone()[0]
        capacity(work,pages*page_size)
        copy=_connect(snapshot)
        try:
            def progress(status,remaining,total):
                if time.monotonic()>end:raise TimeoutError('Snapshot deadline reached; start a new export.')
            memory.db.backup(copy,pages=128,progress=progress)
        finally:copy.close()
        snapshot.chmod(0o600);sync(snapshot)
        atomic_json(state,{'source':str(memory.config.data_dir),'stage':'snapshot-ready','database_sha256':file_hash(snapshot)})
    catalogue=work/'catalogue.sqlite3'
    if catalogue.exists():catalogue.unlink()  # Only own staged, never a published catalogue.
    catalog=_connect(catalogue);frozen=_connect(snapshot,True)
    new=reused=total=0
    try:
        validate_database(frozen,memory.config.data_dir,end)
        catalog.executescript(CATALOGUE)
        metadata={'format':FORMAT,'repository_id':descriptor['id'],'snapshot_id':identifier,'schema':frozen.execute('PRAGMA user_version').fetchone()[0],
                  'settings':{'max_source_bytes':memory.config.max_source_bytes},'inventory':inventory_report,'complete':False,
                  'python_min':[3,12],'platform':'linux'}
        for name,value in metadata.items():catalog.execute('INSERT INTO meta VALUES (?,?)',(name,json.dumps(value,sort_keys=True)))
        def include(name,path):
            nonlocal new,reused,total
            hasher=hashlib.sha256();size=0;index=0
            catalog.execute('INSERT INTO files VALUES (?,?,?)',(name,0,'pending'))
            with input_file(path) as stream:
                before=os.fstat(stream.fileno())
                while data:=stream.read(BLOCK):
                    if time.monotonic()>end:raise TimeoutError('Export deadline reached; staged transfer can be resumed.')
                    hasher.update(data);size+=len(data)
                    row,created=_store_block(root,data,key,descriptor,work)
                    catalog.execute('INSERT INTO blocks VALUES (?,?,?,?,?,?)',(name,index,*row))
                    index+=1;new+=created;reused+=not created
                    if fault:fault('block-written')
                after=os.fstat(stream.fileno())
                if (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):raise ValueError('Persistent asset changed during export.')
            catalog.execute('UPDATE files SET bytes=?,sha256=? WHERE name=?',(size,hasher.hexdigest(),name));total+=size
        include('database',snapshot)
        for row in frozen.execute('SELECT digest,raw_bytes,stored_bytes,codec FROM managed_objects ORDER BY digest'):
            for _ in object_chunks(memory.config.data_dir,row,end):pass
            include('object:'+row[0],object_path(memory.config.data_dir,row[0]))
        catalog.execute("UPDATE meta SET value='true' WHERE key='complete'");catalog.commit()
    finally:catalog.close();frozen.close()
    sync(catalogue)
    published=root/'snapshots'/(identifier+('.gcm' if key else '.sqlite3'))
    if published.exists():raise FileExistsError('Published snapshot is never replaced.')
    encoded=work/'catalogue.gcm'
    if key:
        if encoded.exists():encoded.unlink()
        seal(catalogue,encoded,key,descriptor,'catalogue:'+identifier)
    if fault:fault('before-publish')
    _publish_file(encoded if key else catalogue,published)
    if fault:fault('after-publish')
    _finish_export(memory,root,work,public_work,identifier,file_hash(snapshot))
    return {'complete':True,'repository':str(root),'snapshot_id':identifier,'file_bytes':total,
            'new_blocks':new,'reused_blocks':reused,'encrypted':bool(key),'transfer_id':identifier,
            'verification':'Created and block-checked; run verify-export for actual restore qualification.'}


def _finish_export(memory,root,work,public_work,identifier,database_hash):
    # The head is updated only after durable publication. Repeating finalization is safe.
    atomic_json(work/'transfer.json',{'source':str(memory.config.data_dir),'stage':'published',
                                    'snapshot':identifier,'database_sha256':database_hash})
    atomic_json(public_work/'transfer.json',{'stage':'published','snapshot':identifier})
    atomic_json(root/'latest.json',{'snapshot':identifier})
    for name in ('database.sqlite3','catalogue.sqlite3','catalogue.gcm'):
        (work/name).unlink(missing_ok=True)
    sync(work)


@contextmanager
def open_catalogue(directory,snapshot=None,key_file=None):
    key=load_key(key_file) if key_file else None
    root,descriptor=_repository(directory,key)
    if snapshot is None:
        latest=read_json(root/'latest.json')
        if not isinstance(latest,dict) or set(latest)!={'snapshot'}:raise ValueError('Invalid repository head.')
        snapshot=latest['snapshot']
    if not isinstance(snapshot,str) or not ID.fullmatch(snapshot):raise ValueError('Invalid snapshot identifier.')
    source=safe_path(root/'snapshots'/(snapshot+('.gcm' if key else '.sqlite3')))
    with tempfile.TemporaryDirectory(prefix='vector_catalogue_') as folder:
        work=Path(folder)
        if key:
            capacity(work,source.stat().st_size)
            decoded=work/'authenticated.sqlite3'
            unseal(source,decoded,key,descriptor,'catalogue:'+snapshot)
            source=decoded
        with input_file(source):pass
        if key is None:
            frozen=work/'frozen-catalogue.sqlite3'
            with input_file(source) as original,frozen.open('xb') as output:
                before=os.fstat(original.fileno());capacity(work,before.st_size)
                shutil.copyfileobj(original,output,BLOCK)
                after=os.fstat(original.fileno())
                if (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):raise ValueError('Catalogue changed while importing.')
            source=frozen
        db=_connect(source,True)
        try:
            db.setlimit(sqlite3.SQLITE_LIMIT_LENGTH,65536)
            db.setlimit(sqlite3.SQLITE_LIMIT_SQL_LENGTH,65536)
            expected=sqlite3.connect(':memory:');expected.executescript(CATALOGUE)
            try:
                if _schema(db)!=_schema(expected):raise ValueError('Unsafe or incompatible portable catalogue schema.')
            finally:expected.close()
            if db.execute('PRAGMA integrity_check').fetchone()[0]!='ok' or db.execute('PRAGMA foreign_key_check').fetchone():
                raise ValueError('Catalogue integrity/reference failure.')
            meta={}
            allowed={'format','repository_id','snapshot_id','schema','settings','inventory','complete','python_min','platform'}
            for name,value in db.execute('SELECT key,value FROM meta'):
                if name not in allowed:raise ValueError('Unknown manifest field.')
                meta[name]=json.loads(value,object_pairs_hook=unique)
            if set(meta)!=allowed or meta['complete'] is not True or meta['format']!=FORMAT:
                raise ValueError('Incomplete or incompatible portable manifest.')
            if (meta['repository_id']!=descriptor['id'] or meta['snapshot_id']!=snapshot or meta['platform']!='linux'
                or sys.platform!='linux' or meta['python_min']!=[3,12] or sys.version_info<(3,12)
                or type(meta['schema']) is not int or not 1<=meta['schema']<=len(MIGRATIONS)):
                raise ValueError('Platform, repository or application/schema compatibility failure.')
            inventory_meta=meta['inventory']
            if (not isinstance(inventory_meta,dict) or set(inventory_meta)!={'authoritative','excluded','platform_dependencies'}
                or not isinstance(inventory_meta['authoritative'],str)
                or not all(isinstance(inventory_meta[field],list) and all(isinstance(item,str) for item in inventory_meta[field])
                           for field in ('excluded','platform_dependencies'))):
                raise ValueError('Malformed persistence inventory metadata.')
            settings=meta['settings']
            if not isinstance(settings,dict) or set(settings)!={'max_source_bytes'} or type(settings['max_source_bytes']) is not int or not 1024<=settings['max_source_bytes']<=16*1024*1024:
                raise ValueError('Unsupported portable settings.')
            has_database=False
            for name,size,digest in db.execute('SELECT name,bytes,sha256 FROM files'):
                if name=='database':has_database=True
                elif not isinstance(name,str) or not name.startswith('object:') or not DIGEST.fullmatch(name[7:]):
                    raise ValueError('Unsafe archive logical path.')
                if type(size) is not int or size<0 or not isinstance(digest,str) or not DIGEST.fullmatch(digest):raise ValueError('Invalid archive file descriptor.')
            if not has_database:raise ValueError('Required application database missing.')
            yield root,descriptor,db,meta,key,work
        finally:db.close()


def restore_vector(config,directory,*,snapshot=None,key_file=None,resume=False,deadline_seconds=900,fault=None):
    """Restore to quarantined new data; resume replaces only labelled partial work."""
    root=config.data_dir
    if any(p.is_symlink() for p in (root,*root.parents)):raise ValueError('Unsafe restore destination.')
    from vector_core.config import Config
    Config.load(data_dir=str(root))
    marker=root/'.restore-incomplete'
    with open_catalogue(directory,snapshot,key_file) as (archive,descriptor,db,meta,key,work):
        identity={'format':1,'repository_id':descriptor['id'],'snapshot_id':meta['snapshot_id']}
        if root.exists():
            if not resume or not marker.exists() or read_json(marker)!=identity:
                raise FileExistsError('Existing installation preserved. Resume only the matching labelled incomplete restore.')
            expected={'.vector-data','.restore-incomplete','vector.sqlite3','vector.sqlite3.restore-part','objects'}
            if any(p.name not in expected or p.is_symlink() for p in root.iterdir()):
                raise ValueError('Unclassified data in incomplete restore; nothing overwritten.')
        else:
            config.initialize()
            atomic_json(marker,identity)
        required=db.execute('SELECT coalesce(sum(bytes),0) FROM files').fetchone()[0]
        capacity(root,required)  # Conservative before resuming; never spends the reserve.
        end=time.monotonic()+deadline_seconds
        count=0
        for name,size,digest in db.execute('SELECT name,bytes,sha256 FROM files ORDER BY name'):
            target=root/'vector.sqlite3' if name=='database' else object_path(root,name[7:])
            target.parent.mkdir(parents=True,mode=0o700,exist_ok=True)
            if target.exists() and target.is_file() and target.stat().st_size==size and file_hash(target)==digest:
                count+=1;continue
            temporary=target.with_name(target.name+'.restore-part')
            if temporary.exists():
                if temporary.is_symlink():raise ValueError('Unsafe incomplete restore part.')
                temporary.unlink()  # Labelled unactivated copy only.
            hasher=hashlib.sha256();length=0;ordinal=0
            with temporary.open('xb') as output:
                temporary.chmod(0o600)
                for index,block_digest,raw,stored,codec in db.execute(
                    'SELECT ordinal,digest,raw_bytes,stored_bytes,codec FROM blocks WHERE file_name=? ORDER BY ordinal',(name,)):
                    if type(index) is not int or type(raw) is not int or raw<=0 or index!=ordinal or length+raw>size:raise ValueError('Archive block sequence/size mismatch.')
                    if time.monotonic()>end:raise TimeoutError('Restore deadline reached; matching restore can be resumed.')
                    data=_decode_block(archive,(block_digest,raw,stored,codec),key,descriptor,work)
                    capacity(root,len(data));output.write(data);hasher.update(data);length+=len(data);ordinal+=1
                    if fault:fault('restore-block')
                output.flush();os.fsync(output.fileno())
            if length!=size or hasher.hexdigest()!=digest:raise ValueError('Restored file checksum failure; destination remains quarantined.')
            os.replace(temporary,target);sync(target.parent)
            if name!='database':sync(target.parent.parent)
            count+=1
        restored=_connect(root/'vector.sqlite3',True)
        try:
            integrity=validate_database(restored,root,end)
            if restored.execute('PRAGMA user_version').fetchone()[0]!=meta['schema']:raise ValueError('Snapshot schema metadata mismatch.')
            expected_count=1
            if meta['schema']>=5:
                for row in restored.execute('SELECT digest,raw_bytes,stored_bytes,codec FROM managed_objects'):
                    if db.execute('SELECT 1 FROM files WHERE name=?',('object:'+row[0],)).fetchone() is None:
                        raise ValueError('Required managed asset omitted from archive.')
                    for _ in object_chunks(root,row,end):pass
                    expected_count+=1
            if expected_count!=db.execute('SELECT count(*) FROM files').fetchone()[0]:raise ValueError('Unregistered extra archive asset.')
        finally:restored.close()
        # Persist settings without embedding the old computer's physical data path.
        from vector_core.memory import Memory
        # Preference state is authoritative inside the snapshot. No arbitrary imported path is followed.
        marker.unlink();sync(root)
        return {'restored':True,'activated':True,'directory':str(root),'snapshot_id':meta['snapshot_id'],
                'files':count,'integrity':integrity,'settings':meta['settings'],
                'extensions_executed':False,'platform_dependencies':meta['inventory']['platform_dependencies']}


def verify_export(directory,*,snapshot=None,key_file=None,deadline_seconds=900):
    """Actual independent restoration, not merely hash checks on creation."""
    from vector_core.config import Config
    started=time.monotonic()
    with tempfile.TemporaryDirectory(prefix='vector_verify_') as folder:
        config=Config.load(data_dir=str(Path(folder)/'restored'))
        result=restore_vector(config,directory,snapshot=snapshot,key_file=key_file,deadline_seconds=deadline_seconds)
        return {'verified':True,'actual_restoration':True,'snapshot_id':result['snapshot_id'],
                'files':result['files'],'integrity':result['integrity'],'seconds':time.monotonic()-started}
