"""Capacity policy and streamed managed content, independent of model execution."""
from contextlib import contextmanager
from vector_core.coordination import write_operation

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import time
from uuid import uuid4
import zlib

from vector_core.maintenance import sync

BLOCK=1024*1024
DIGEST=re.compile(r'[0-9a-f]{64}\Z')


def capacity(path,additional=0,strict=True):
    usage=shutil.disk_usage(path)
    reserve=max(64*1024*1024,usage.total//100)
    if additional<0 or (strict and usage.free-additional<reserve):
        raise OSError(28,'Insufficient storage capacity including safety reserve')
    return {'free_bytes':usage.free,'total_bytes':usage.total,'reserve_bytes':reserve,'capacity_warning':usage.free-additional<reserve}


def safe_path(path):
    path=Path(path).expanduser().absolute()
    if '..' in path.parts or any(p.is_symlink() for p in (path,*path.parents)):
        raise ValueError('Symbolic links and parent traversal are forbidden.')
    return path


@contextmanager
def input_file(path):
    """Directory handles prevent parent symlink swaps and reject special files."""
    path=Path(path).expanduser().absolute()
    if '..' in path.parts:raise ValueError('Parent traversal forbidden.')
    descriptors=[]
    try:
        fd=os.open('/',os.O_RDONLY|os.O_DIRECTORY);descriptors.append(fd)
        for part in path.parts[1:-1]:
            fd=os.open(part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=fd);descriptors.append(fd)
        source=os.open(path.name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=fd)
        if not stat.S_ISREG(os.fstat(source).st_mode):
            os.close(source);raise ValueError('A regular file is required.')
        with os.fdopen(source,'rb') as stream:yield stream
    finally:
        for fd in reversed(descriptors):os.close(fd)


def atomic_json(path,value):
    temporary=path.with_name(path.name+'.'+uuid4().hex+'.new')
    with temporary.open('x') as output:
        json.dump(value,output,sort_keys=True,allow_nan=False);output.flush();os.fsync(output.fileno())
    os.replace(temporary,path);sync(path.parent)


def object_path(root,digest):
    if not isinstance(digest,str) or not DIGEST.fullmatch(digest):raise ValueError('Invalid content digest.')
    path=root/'objects'/digest[:2]/digest[2:]
    return safe_path(path)


def object_chunks(root,row,deadline=None):
    digest,raw_size,stored_size,codec=tuple(row)
    if type(raw_size) is not int or raw_size<0 or stored_size<0 or codec not in ('raw','zlib'):
        raise ValueError('Malformed managed object metadata.')
    path=object_path(root,digest)
    hasher=hashlib.sha256();total=0
    decoder=zlib.decompressobj() if codec=='zlib' else None
    with input_file(path) as stream:
        if os.fstat(stream.fileno()).st_size!=stored_size:raise ValueError('Managed object size mismatch.')
        while part:=stream.read(BLOCK):
            if deadline and time.monotonic()>deadline:raise TimeoutError('Object verification deadline reached.')
            pending=part
            while pending:
                try:output=decoder.decompress(pending,BLOCK) if decoder else pending
                except zlib.error as error:raise ValueError('Corrupt compressed managed object.') from error
                pending=decoder.unconsumed_tail if decoder else b''
                total+=len(output)
                if total>raw_size:raise ValueError('Compressed object exceeds declared original size.')
                hasher.update(output)
                if output:yield output
            if decoder and decoder.unused_data:raise ValueError('Trailing compressed object data.')
        if decoder and not decoder.eof:raise ValueError('Truncated compressed object.')
    if total!=raw_size or hasher.hexdigest()!=digest:raise ValueError('Managed object original integrity failed.')


@write_operation
def import_object(memory,path,*,fault=None,reuse_legacy=False):
    """Install immutable content before committing references; recover full orphans."""
    root=memory.config.data_dir
    staging=safe_path(root/'staging');staging.mkdir(mode=0o700,exist_ok=True)
    identifier=uuid4().hex
    part=staging/(identifier+'.part');journal=staging/(identifier+'.json')
    digest=hashlib.sha256();raw_size=0;encoder=zlib.compressobj(level=1)
    with input_file(path) as source:
        before=os.fstat(source.fileno())
        capacity(root,before.st_size+before.st_size//1000+8192)
        with part.open('xb') as output:
            part.chmod(0o600)
            while chunk:=source.read(BLOCK):
                raw_size+=len(chunk)
                if raw_size>before.st_size:raise ValueError('Source grew during import.')
                digest.update(chunk)
                encoded=encoder.compress(chunk)
                capacity(root,len(encoded));output.write(encoded)
            output.write(encoder.flush());output.flush();os.fsync(output.fileno())
        after=os.fstat(source.fileno())
        if (before.st_size,before.st_mtime_ns,before.st_ctime_ns)!=(after.st_size,after.st_mtime_ns,after.st_ctime_ns):
            raise ValueError('Source changed during import; not committed.')
    key=digest.hexdigest();size=part.stat().st_size
    if reuse_legacy:
        legacy=memory.db.execute('SELECT length(body) FROM blobs WHERE sha256=?',(key,)).fetchone()
        external=memory.db.execute('SELECT 1 FROM external_originals WHERE digest=?',(key,)).fetchone()
        if legacy is not None and external is None:
            if not 0<=legacy[0]<=16*1024*1024:raise ValueError('Invalid legacy original size.')
            body=memory.db.execute('SELECT body FROM blobs WHERE sha256=?',(key,)).fetchone()[0]
            if len(body)!=raw_size or hashlib.sha256(body).hexdigest()!=key:raise ValueError('Corrupt legacy original.')
            part.unlink();sync(staging)
            return key
    info={'format':1,'digest':key,'raw_bytes':raw_size,'stored_bytes':size,'codec':'zlib'}
    target=object_path(root,key);target.parent.mkdir(parents=True,mode=0o700,exist_ok=True)
    if target.exists():
        existing=memory.db.execute('SELECT * FROM managed_objects WHERE digest=?',(key,)).fetchone()
        descriptor=existing if existing else (key,raw_size,target.stat().st_size,'zlib')
        for _ in object_chunks(root,descriptor):pass
        info['stored_bytes']=target.stat().st_size
        info['codec']=descriptor[3]
    atomic_json(journal,info)
    if not target.exists():
        os.link(part,target);sync(target.parent);sync(target.parent.parent)
    sync(target.parent);sync(target.parent.parent);sync(root)
    if fault:fault('object-installed')
    memory.db.execute('INSERT OR IGNORE INTO managed_objects VALUES (?,?,?,?)',
                      (key,raw_size,info['stored_bytes'],info['codec']))
    part.unlink();journal.unlink();sync(staging)
    return key


@write_operation
def recover_objects(memory):
    root=memory.config.data_dir;staging=safe_path(root/'staging')
    if not staging.exists():return {'recovered':0,'incomplete':[]}
    count=0;incomplete=[]
    for journal in staging.iterdir():
        if journal.suffix!='.json':continue
        from vector_core.portable import read_json
        info=read_json(journal)
        if set(info)!={'format','digest','raw_bytes','stored_bytes','codec'} or info['format']!=1:
            raise ValueError('Unknown storage recovery journal.')
        target=object_path(root,info['digest']);part=journal.with_suffix('.part')
        if not target.exists():
            if not part.exists():raise ValueError('Recovery content missing; no acknowledgement possible.')
            target.parent.mkdir(parents=True,mode=0o700,exist_ok=True)
            os.link(part,target);sync(target.parent);sync(target.parent.parent);sync(root)
        descriptor=(info['digest'],info['raw_bytes'],info['stored_bytes'],info['codec'])
        for _ in object_chunks(root,descriptor):pass
        memory.db.execute('INSERT OR IGNORE INTO managed_objects VALUES (?,?,?,?)',descriptor)
        if part.exists():part.unlink()
        journal.unlink();count+=1
    incomplete_count=0
    for item in staging.iterdir():
        incomplete_count+=1
        if len(incomplete)<100:incomplete.append(item.name)
    sync(staging)
    return {'recovered':count,'incomplete':incomplete,'incomplete_count':incomplete_count,'preview_truncated':incomplete_count>len(incomplete),
            'policy':'Incomplete unacknowledged parts are retained; retry explicit source import or review before removal.'}


@write_operation
def usage(memory):
    root=memory.config.data_dir
    info=capacity(root,strict=False)
    info['database_bytes']=sum(p.stat().st_size for p in root.glob('vector.sqlite3*') if p.is_file())
    row=memory.db.execute('SELECT count(*),coalesce(sum(raw_bytes),0),coalesce(sum(stored_bytes),0) FROM managed_objects').fetchone()
    info.update(objects=row[0],logical_object_bytes=row[1],stored_object_bytes=row[2])
    info['submission_events']=memory.db.execute('SELECT count(*) FROM events').fetchone()[0]
    info['original_deletion_policy']='never automatically delete originals or managed objects'
    from vector_core.memory import now
    previous=memory.db.execute('SELECT created,free_bytes FROM capacity_samples ORDER BY id DESC LIMIT 1').fetchone()
    moment=now();info['estimated_seconds_until_reserve']=None
    if previous:
        from datetime import datetime
        elapsed=(datetime.fromisoformat(moment)-datetime.fromisoformat(previous[0])).total_seconds()
        consumed=previous[1]-info['free_bytes']
        if elapsed>0 and consumed>0:info['estimated_seconds_until_reserve']=(info['free_bytes']-info['reserve_bytes'])*elapsed/consumed
    import sqlite3
    try:
        memory.db.execute('INSERT INTO capacity_samples(created,free_bytes,total_bytes) VALUES (?,?,?)',
                          (moment,info['free_bytes'],info['total_bytes']))
        info['sample_recorded']=True
    except sqlite3.Error:info['sample_recorded']=False
    info['forecast_scope']='Whole-volume recent free-space trend, not a guaranteed VECTOR-only forecast.'
    return info
