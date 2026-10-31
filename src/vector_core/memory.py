"""Transactional original bytes and distinct, immutable submission events."""
from dataclasses import dataclass,field
from datetime import datetime,timezone
from vector_core.coordination import write_operation

import hashlib
import json
from uuid import uuid4

from vector_core.database import connect


def now():
    return datetime.now(timezone.utc).isoformat(timespec='microseconds')


def canonical(value):
    return json.dumps(value,sort_keys=True,ensure_ascii=False,allow_nan=False,separators=(',',':'))


@dataclass(frozen=True)
class Submission:
    content: bytes
    name: str
    media_type: str='text/plain'
    metadata: dict=field(default_factory=dict)
    source_id: str|None=None
    parent_id: str|None=None


class Memory:
    def __init__(self,config):
        self.config=config
        self.db=connect(config)
        from vector_core.persistence import put
        saved=self.db.execute("SELECT payload FROM persistent_records WHERE contract='preferences' AND record_key='__vector_runtime__' ORDER BY rowid DESC LIMIT 1").fetchone()
        settings=json.loads(saved[0]) if saved else None
        if settings is not None and (set(settings)!={'max_source_bytes'} or type(settings['max_source_bytes']) is not int or not 1024<=settings['max_source_bytes']<=16*1024*1024):
            self.db.close();raise ValueError('Unsupported persistent runtime preferences.')
        if saved and not config.settings_explicit:
            from dataclasses import replace
            self.config=replace(config,max_source_bytes=settings['max_source_bytes'])
        elif not saved or settings['max_source_bytes']!=config.max_source_bytes:
            put(self,'preferences','__vector_runtime__',{'max_source_bytes':config.max_source_bytes})

    def close(self): self.db.close()
    def __enter__(self): return self
    def __exit__(self,*args): self.close()

    def ingest(self,submission):
        return self.ingest_batch([submission])[0]

    @write_operation
    def ingest_batch(self,submissions):
        if not isinstance(submissions,list) or not 1<=len(submissions)<=64:
            raise ValueError('Batch requires 1-64 submissions.')
        validated=[]
        size=0
        for item in submissions:
            if not isinstance(item,Submission) or not isinstance(item.content,bytes):
                raise ValueError('Original content must be bytes.')
            size+=len(item.content)
            if len(item.content)>self.config.max_source_bytes or size>16*1024*1024:
                raise ValueError('Source/batch byte limit exceeded.')
            if not isinstance(item.name,str) or not 1<=len(item.name)<=512:
                raise ValueError('Source name required (up to 512 characters).')
            if not isinstance(item.media_type,str) or not 1<=len(item.media_type)<=128:
                raise ValueError('Bounded media type required.')
            if not isinstance(item.metadata,dict) or any(not isinstance(k,str) for k in item.metadata):
                raise ValueError('Metadata must be an object with text keys.')
            metadata=canonical(item.metadata)
            if len(metadata.encode())>16384: raise ValueError('Metadata exceeds 16 KiB.')
            validated.append((item,metadata,hashlib.sha256(item.content).hexdigest()))
        from vector_core.storage import capacity
        capacity(self.config.data_dir,size*3+1024*1024)
        results=[]
        self.db.execute('BEGIN IMMEDIATE')
        try:
            for item,metadata,digest in validated:
                source=item.source_id
                if item.parent_id:
                    parent=self.db.execute('SELECT source_id FROM events WHERE id=?',(item.parent_id,)).fetchone()
                    if parent is None or (source is not None and source!=parent[0]):
                        raise ValueError('Revision parent must exist and belong to the same source.')
                    source=parent[0]
                if source is None:
                    source=uuid4().hex
                    self.db.execute('INSERT INTO sources VALUES (?,?,?)',(source,item.name,now()))
                elif self.db.execute('SELECT 1 FROM sources WHERE id=?',(source,)).fetchone() is None:
                    raise ValueError('Unknown source ID.')
                existing=self.db.execute('SELECT length(body) FROM blobs WHERE sha256=?',(digest,)).fetchone()
                if existing is not None:
                    managed=self.db.execute('SELECT o.digest,o.raw_bytes,o.stored_bytes,o.codec FROM external_originals x JOIN managed_objects o ON o.digest=x.object_digest WHERE x.digest=?',(digest,)).fetchone()
                    if managed is not None:
                        from vector_core.storage import object_chunks
                        if b''.join(object_chunks(self.config.data_dir,managed))!=item.content:raise ValueError('Stored managed original differs.')
                    elif existing[0]!=len(item.content) or self.db.execute('SELECT body FROM blobs WHERE sha256=?',(digest,)).fetchone()[0]!=item.content:
                        raise ValueError('Stored blob differs from its content hash; ingestion refused.')
                if existing is None:
                    self.db.execute('INSERT INTO blobs VALUES (?,?,?)',(digest,item.content,len(item.content)))
                event=uuid4().hex
                occurred=now()
                self.db.execute('INSERT INTO events VALUES (?,?,?,?,?,?,?,?)',
                    (event,source,digest,occurred,item.media_type,item.name,metadata,item.parent_id))
                text,status=extract(item.content,item.media_type)
                self.db.execute('INSERT INTO texts VALUES (?,?,?)',(event,text,status))
                from vector_core.retrieval import index_event
                index_event(self.db,event,text,status)
                self.db.execute('INSERT INTO audit(occurred,action,detail) VALUES (?,?,?)',
                    (occurred,'submission',canonical({'event_id':event,'sha256':digest,'source_id':source})))
                results.append({'event_id':event,'source_id':source,'sha256':digest,
                                'bytes':len(item.content),'extraction_status':status})
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        return results  # Only returned after successful FULL synchronous COMMIT.

    def event(self,event_id):
        row=self.db.execute('SELECT e.*,s.name,COALESCE(o.raw_bytes,b.byte_count) AS byte_count FROM events e JOIN sources s ON s.id=e.source_id '
                            'JOIN blobs b ON b.sha256=e.sha256 LEFT JOIN external_originals x ON x.digest=b.sha256 '
                            'LEFT JOIN managed_objects o ON o.digest=x.object_digest WHERE e.id=?',(event_id,)).fetchone()
        if row is None: raise KeyError('Submission event not found.')
        result=dict(row);result['metadata']=json.loads(result['metadata'])
        return result

    def original(self,event_id):
        external=self.db.execute('SELECT o.raw_bytes FROM events e JOIN external_originals x ON x.digest=e.sha256 '
                                 'JOIN managed_objects o ON o.digest=x.object_digest WHERE e.id=?',(event_id,)).fetchone()
        if external is not None:
            if external[0]>16*1024*1024:raise ValueError('Large original: use original_chunks/export_original for bounded memory.')
            return b''.join(self.original_chunks(event_id))
        descriptor=self.db.execute('SELECT b.sha256,length(b.body),b.byte_count FROM events e JOIN blobs b ON b.sha256=e.sha256 WHERE e.id=?',
                                   (event_id,)).fetchone()
        if descriptor is None:raise KeyError('Submission event not found.')
        if descriptor[1]!=descriptor[2] or not 0<=descriptor[1]<=16*1024*1024:
            raise ValueError('Original byte count outside supported integrity/resource bounds.')
        body=self.db.execute('SELECT body FROM blobs WHERE sha256=?',(descriptor[0],)).fetchone()[0]
        if hashlib.sha256(body).hexdigest()!=descriptor[0]:
            raise ValueError('Original content integrity failure; not returned as valid.')
        return body

    def recent(self,limit=30):
        if type(limit) is not int or not 1<=limit<=100: raise ValueError('Result limit must be 1-100.')
        return [dict(row) for row in self.db.execute('SELECT e.id,e.source_id,e.sha256,e.occurred,s.name '
            'FROM events e JOIN sources s ON s.id=e.source_id ORDER BY occurred DESC,e.id DESC LIMIT ?',(limit,))]

    def original_chunks(self,event_id):
        from vector_core.storage import object_chunks,BLOCK
        row=self.db.execute('SELECT o.digest,o.raw_bytes,o.stored_bytes,o.codec,e.sha256 FROM events e '
                            'JOIN external_originals x ON x.digest=e.sha256 JOIN managed_objects o ON o.digest=x.object_digest '
                            'WHERE e.id=?',(event_id,)).fetchone()
        if row is not None:
            if row[0]!=row[4]:raise ValueError('Original object reference digest mismatch.')
            yield from object_chunks(self.config.data_dir,row[:4])
            return
        row=self.db.execute('SELECT b.rowid,b.sha256,length(b.body),b.byte_count FROM events e '
                            'JOIN blobs b ON b.sha256=e.sha256 WHERE e.id=?',(event_id,)).fetchone()
        if row is None:raise KeyError('Submission event not found.')
        if row[2]!=row[3] or not 0<=row[2]<=16*1024*1024:raise ValueError('Legacy original size invalid.')
        hasher=hashlib.sha256()
        with self.db.blobopen('blobs','body',row[0],readonly=True) as stream:
            while chunk:=stream.read(BLOCK):hasher.update(chunk);yield chunk
        if hasher.hexdigest()!=row[1]:raise ValueError('Original checksum mismatch.')

    def export_original(self,event_id,path):
        from vector_core.intake import write_new_chunks
        write_new_chunks(path,self.original_chunks(event_id))
        return {'event_id':event_id,'output':str(path),'complete':True}

    @write_operation
    def ingest_file(self,path,*,name=None,media_type='application/octet-stream',metadata=None,parent_id=None,source_id=None):
        from pathlib import Path
        from vector_core.storage import import_object
        name=name or Path(path).name
        if not isinstance(name,str) or not 1<=len(name)<=512:raise ValueError('Source name required.')
        if not isinstance(media_type,str) or not 1<=len(media_type)<=128:raise ValueError('Media type required.')
        encoded=canonical(metadata or {})
        if len(encoded.encode())>16384:raise ValueError('Metadata too large.')
        digest=import_object(self,path,reuse_legacy=True)
        obj=self.db.execute('SELECT raw_bytes FROM managed_objects WHERE digest=?',(digest,)).fetchone()
        self.db.execute('BEGIN IMMEDIATE')
        try:
            if parent_id:
                parent=self.db.execute('SELECT source_id FROM events WHERE id=?',(parent_id,)).fetchone()
                if parent is None or (source_id and parent[0]!=source_id):raise ValueError('Revision source mismatch.')
                source_id=parent[0]
            if source_id is None:
                source_id=uuid4().hex
                self.db.execute('INSERT INTO sources VALUES (?,?,?)',(source_id,name,now()))
            elif self.db.execute('SELECT 1 FROM sources WHERE id=?',(source_id,)).fetchone() is None:raise ValueError('Unknown source.')
            if obj is not None:
                self.db.execute('INSERT OR IGNORE INTO blobs VALUES (?,?,?)',(digest,b'',0))
                self.db.execute('INSERT OR IGNORE INTO external_originals VALUES (?,?)',(digest,digest))
                size=obj[0]
            else:size=self.db.execute('SELECT byte_count FROM blobs WHERE sha256=?',(digest,)).fetchone()[0]
            event=uuid4().hex;occurred=now()
            self.db.execute('INSERT INTO events VALUES (?,?,?,?,?,?,?,?)',
                            (event,source_id,digest,occurred,media_type,name,encoded,parent_id))
            if size<=self.config.max_source_bytes:
                raw=b''.join(self.original_chunks(event));text,status=extract(raw,media_type)
            else:text,status=None,'streamed-original-preserved-index-deferred'
            self.db.execute('INSERT INTO texts VALUES (?,?,?)',(event,text,status))
            from vector_core.retrieval import index_event
            index_event(self.db,event,text,status)
            self.db.execute('INSERT INTO audit(occurred,action,detail) VALUES (?,?,?)',
                            (occurred,'streamed-submission',canonical({'event_id':event,'sha256':digest})))
            self.db.commit()
        except Exception:self.db.rollback();raise
        return {'event_id':event,'source_id':source_id,'sha256':digest,'bytes':size,'extraction_status':status}

    def read_text_span(self,event_id,start,end):
        import codecs
        if type(start) is not int or type(end) is not int or not 0<=start<end or end-start>4000:
            raise ValueError('Bounded original character span required.')
        decoder=codecs.getincrementaldecoder('utf-8')();position=0;parts=[]
        for chunk in self.original_chunks(event_id):
            text=decoder.decode(chunk)
            left=max(0,start-position);right=min(len(text),end-position)
            if left<right:parts.append(text[left:right])
            position+=len(text)
        tail=decoder.decode(b'',final=True)
        if tail:
            left=max(0,start-position);right=min(len(tail),end-position)
            if left<right:parts.append(tail[left:right])
            position+=len(tail)
        if end>position:raise ValueError('Claim span outside original text.')
        return ''.join(parts)

    def text_lines(self,event_id):
        import io
        chunks=self.original_chunks(event_id)
        class Reader(io.RawIOBase):
            def __init__(self):self.pending=b''
            def readable(self):return True
            def readinto(self,buffer):
                while not self.pending:
                    try:self.pending=memoryview(next(chunks))
                    except StopIteration:return 0
                count=min(len(buffer),len(self.pending));buffer[:count]=self.pending[:count]
                self.pending=self.pending[count:];return count
            def close(self):
                chunks.close();super().close()
        position=0
        with io.TextIOWrapper(io.BufferedReader(Reader()),encoding='utf-8',newline='') as text:
            while True:
                physical=text.readline(4097)
                if not physical:break
                start=position;position+=len(physical)
                if len(physical)==4097 and not physical.endswith(('\n','\r')):
                    while physical and not physical.endswith(('\n','\r')):
                        physical=text.readline(4097);position+=len(physical)
                    yield start,position,None
                else:yield start,position,physical

    def ingest_iter(self,submissions):
        batch=[];size=0
        for item in submissions:
            if not isinstance(item,Submission):raise ValueError('Submission iterator required.')
            if batch and (len(batch)==64 or size+len(item.content)>16*1024*1024):
                yield from self.ingest_batch(batch);batch=[];size=0
            batch.append(item);size+=len(item.content)
        if batch:yield from self.ingest_batch(batch)

    def event_page(self,after='',limit=100):
        if not isinstance(after,str) or type(limit) is not int or not 1<=limit<=1000:raise ValueError('Invalid event page.')
        rows=[dict(row) for row in self.db.execute('SELECT id,source_id,sha256,occurred,submission_name FROM events WHERE id>? ORDER BY id LIMIT ?',(after,limit))]
        return {'items':rows,'next_cursor':rows[-1]['id'] if rows else after,'consistency':'Refresh after concurrent insertions; no total collection cap.'}

    def verify(self): return verify_connection(self.db,self.config.data_dir)


def extract(content,media_type):
    if not (media_type.startswith('text/') or media_type in ('application/json','application/xml')):
        return None,'unsupported-preserved'
    try: return content.decode('utf-8'),'utf8-extracted'
    except UnicodeDecodeError: return None,'invalid-utf8-preserved'


def verify_connection(db,root=None,deadline=None):
    if deadline is None:
        return _verify_connection(db,root,deadline)
    import sqlite3,time
    def expired():return time.monotonic()>deadline
    if expired():raise TimeoutError('Integrity verification deadline reached.')
    # Long SQLite checks need VM cancellation, not only checks between rows.
    db.set_progress_handler(lambda:int(expired()),1000)
    try:
        result=_verify_connection(db,root,deadline)
        if expired():raise TimeoutError('Integrity verification deadline reached.')
        return result
    except sqlite3.OperationalError as error:
        if getattr(error,'sqlite_errorcode',None)==sqlite3.SQLITE_INTERRUPT and expired():
            raise TimeoutError('SQLite integrity verification deadline reached.') from error
        raise
    finally:
        db.set_progress_handler(None,0)


def _verify_connection(db,root=None,deadline=None):
    errors=[]
    for row in db.execute('PRAGMA integrity_check'):
        if row[0]!='ok':errors.append(row[0])
        if len(errors)>=100:break
    for row in db.execute('PRAGMA foreign_key_check'):
        errors.append('Broken reference: '+str(tuple(row)))
        if len(errors)>=100:break
    tables={r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if tables=={'audit'} and db.execute('PRAGMA user_version').fetchone()[0]==1:
        return {'passed':not errors,'checked_blobs':0,'events':0,'errors':errors[:100]}
    has_external='external_originals' in tables
    count=0
    for digest,length,declared in db.execute('SELECT sha256,length(body),byte_count FROM blobs'):
        if deadline:
            import time
            if time.monotonic()>deadline:raise TimeoutError('Original verification deadline reached.')
        count+=1
        external=db.execute('SELECT object_digest FROM external_originals WHERE digest=?',(digest,)).fetchone() if has_external else None
        if external is not None:
            if external[0]!=digest:errors.append('External original digest reference mismatch.')
            continue
        if length!=declared or not 0<=length<=16*1024*1024:
            errors.append('Unsupported original byte count: '+digest)
            if len(errors)>=100:break
            continue
        body=db.execute('SELECT body FROM blobs WHERE sha256=?',(digest,)).fetchone()[0]
        if hashlib.sha256(body).hexdigest()!=digest:
            errors.append('Content hash mismatch: '+digest)
        if len(errors)>100: break
    objects=0
    if 'managed_objects' in tables:
        from vector_core.storage import object_chunks
        for row in db.execute('SELECT digest,raw_bytes,stored_bytes,codec FROM managed_objects'):
            objects+=1
            if root is None:raise ValueError('Managed assets require their registered data root for integrity verification.')
            try:
                for _ in object_chunks(root,row,deadline):pass
            except (ValueError,OSError) as error:errors.append(str(error))
            if len(errors)>=100:break
    return {'passed':not errors,'checked_objects':objects,'checked_blobs':count,'events':db.execute('SELECT count(*) FROM events').fetchone()[0],
            'errors':errors[:100]}
