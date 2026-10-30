"""Transactional original bytes and distinct, immutable submission events."""
from dataclasses import dataclass,field
from datetime import datetime,timezone
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

    def close(self): self.db.close()
    def __enter__(self): return self
    def __exit__(self,*args): self.close()

    def ingest(self,submission):
        return self.ingest_batch([submission])[0]

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
                    if existing[0]!=len(item.content) or self.db.execute('SELECT body FROM blobs WHERE sha256=?',(digest,)).fetchone()[0]!=item.content:
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
        row=self.db.execute('SELECT e.*,s.name,b.byte_count FROM events e JOIN sources s ON s.id=e.source_id '
                            'JOIN blobs b ON b.sha256=e.sha256 WHERE e.id=?',(event_id,)).fetchone()
        if row is None: raise KeyError('Submission event not found.')
        result=dict(row);result['metadata']=json.loads(result['metadata'])
        return result

    def original(self,event_id):
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

    def verify(self): return verify_connection(self.db)


def extract(content,media_type):
    if not (media_type.startswith('text/') or media_type in ('application/json','application/xml')):
        return None,'unsupported-preserved'
    try: return content.decode('utf-8'),'utf8-extracted'
    except UnicodeDecodeError: return None,'invalid-utf8-preserved'


def verify_connection(db):
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
    count=0
    for digest,length,declared in db.execute('SELECT sha256,length(body),byte_count FROM blobs'):
        count+=1
        if length!=declared or not 0<=length<=16*1024*1024:
            errors.append('Unsupported original byte count: '+digest)
            if len(errors)>=100:break
            continue
        body=db.execute('SELECT body FROM blobs WHERE sha256=?',(digest,)).fetchone()[0]
        if hashlib.sha256(body).hexdigest()!=digest:
            errors.append('Content hash mismatch: '+digest)
        if len(errors)>100: break
    return {'passed':not errors,'checked_blobs':count,'events':db.execute('SELECT count(*) FROM events').fetchone()[0],
            'errors':errors[:100]}
