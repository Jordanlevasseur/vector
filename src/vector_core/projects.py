"""Durable user-controlled organization. Associations never copy/delete originals."""
import json
import math
import re
from uuid import uuid4
from vector_core.coordination import write_operation
from vector_core.memory import canonical,now

ITEM_KINDS={'goal','requirement','note','decision','task','milestone','question','hypothesis'}
STATUSES={'open','done','blocked','deferred'}
LINK_KINDS={'related','supports','contradicts','overlaps','revises'}

def identity(value):
    if not isinstance(value,str) or not re.fullmatch('[0-9a-f]{32}',value):raise ValueError('Invalid record identity.')
    return value

def text(value,maximum):
    if not isinstance(value,str) or not value.strip() or len(value)>maximum:raise ValueError('Bounded nonempty text required.')
    return value

def page(after,limit):
    if type(after) is not int or after<0 or type(limit) is not int or not 1<=limit<=100:raise ValueError('Invalid page cursor/limit.')

def latest(memory,contract,key):
    row=memory.db.execute('SELECT id,payload FROM persistent_records WHERE contract=? AND record_key=? ORDER BY rowid DESC LIMIT 1',(contract,key)).fetchone()
    if row is None:raise ValueError('Record not found.')
    return {**json.loads(row['payload']),'revision':row['id']}

def validate_record(db,contract,key,p):
    """Also used on portable imports, before activation of externally supplied state."""
    if contract not in {'project_sources','project_items','memory_links','learning_queue'}:return
    if not isinstance(p,dict):raise ValueError('Invalid organization record.')
    def event(value):
        identity(value)
        if not db.execute('SELECT 1 FROM events WHERE id=?',(value,)).fetchone():raise ValueError('Missing original reference.')
    if contract in {'project_sources','project_items'}:
        identity(p.get('project_id'))
        row=db.execute("SELECT payload FROM persistent_records WHERE contract='projects' AND record_key=? ORDER BY rowid DESC LIMIT 1",(p['project_id'],)).fetchone()
        if row is None or json.loads(row[0]).get('kind')!='project':raise ValueError('Missing project reference.')
    if contract=='project_sources':
        if set(p)!={'project_id','event_id','created'} or key!=p['project_id']+':'+p['event_id']:raise ValueError('Invalid source association.')
        event(p['event_id']);text(p['created'],64)
    if contract=='project_items':
        if set(p)!={'id','project_id','kind','title','body','status','evidence','confidence','uncertainty','created','updated'}:raise ValueError('Invalid project item fields.')
        if key!=identity(p['id']) or p['kind'] not in ITEM_KINDS or p['status'] not in STATUSES:raise ValueError('Invalid project item kind/status.')
        text(p['title'],200);text(p['body'],8000);text(p['uncertainty'],1000)
        for field in ('created','updated'):text(p[field],64)
        if not isinstance(p['evidence'],list) or len(p['evidence'])>20:raise ValueError('At most 20 evidence references per item.')
        for value in p['evidence']:event(value)
        if p['confidence'] is not None and (type(p['confidence']) not in (int,float) or not math.isfinite(p['confidence']) or not 0<=p['confidence']<=1):raise ValueError('Confidence must be a subjective finite 0–1 value or null.')
    if contract=='memory_links':
        if set(p)!={'id','event_id','target_id','kind','reason','created'} or key!=identity(p['id']) or p['kind'] not in LINK_KINDS:raise ValueError('Invalid memory link.')
        event(p['event_id']);event(p['target_id']);text(p['reason'],2000);text(p['created'],64)
        if p['event_id']==p['target_id']:raise ValueError('A relationship needs distinct originals.')
    if contract=='learning_queue':
        if set(p)!={'event_id','status','reason','created'} or key!=p['event_id'] or p['status'] not in {'deferred','proposed','review-needed'}:raise ValueError('Invalid learning queue record.')
        event(p['event_id']);text(p['reason'],2000);text(p['created'],64)

@write_operation
def append(memory,contract,key,payload,*,expected=None,new=False):
    from vector_core.persistence import require
    require(memory,contract);db=memory.db;db.execute('BEGIN IMMEDIATE')
    try:
        validate_record(db,contract,key,payload)
        row=db.execute('SELECT id FROM persistent_records WHERE contract=? AND record_key=? ORDER BY rowid DESC LIMIT 1',(contract,key)).fetchone()
        previous=row[0] if row else None
        if (new and previous) or (expected is not None and previous!=expected):raise ValueError('Record changed; reload before updating.')
        record=uuid4().hex
        db.execute('INSERT INTO persistent_records VALUES (?,?,?,?,?,?)',(record,contract,key,canonical(payload),previous,now()))
        db.execute('INSERT INTO audit(occurred,action,detail) VALUES (?,?,?)',(now(),'organization-'+contract,canonical({'key':key,'revision':record})))
        db.commit()
    except BaseException:db.rollback();raise
    return {**payload,'revision':record}

class Projects:
    def __init__(self,memory):self.memory=memory
    def get(self,project_id):
        p=latest(self.memory,'projects',identity(project_id))
        if p.get('kind')!='project':raise ValueError('Not a project.')
        return p
    def create(self,name):
        p={'id':uuid4().hex,'name':text(name,200),'kind':'project','conversation_id':uuid4().hex,'archived':False,'created':now()}
        return append(self.memory,'projects',p['id'],p,new=True)
    def archive(self,project_id,archived,revision,*,approved=False):
        if approved is not True:raise PermissionError('Explicit project status approval required.')
        if type(archived) is not bool:raise ValueError('Archive flag must be boolean.')
        p=self.get(project_id);p.pop('revision');p['archived']=archived
        return append(self.memory,'projects',project_id,p,expected=identity(revision))
    @write_operation
    def link(self,project_id,event_id):
        self.get(project_id);identity(event_id)
        if not self.memory.db.execute('SELECT 1 FROM events WHERE id=?',(event_id,)).fetchone():raise ValueError('Original source not found; association rejected.')
        key=project_id+':'+event_id
        try:return latest(self.memory,'project_sources',key)
        except ValueError:pass
        return append(self.memory,'project_sources',key,{'project_id':project_id,'event_id':event_id,'created':now()},new=True)
    def sources(self,project_id,after=0,limit=50):
        self.get(project_id);return self.entries('project_sources',project_id,after,limit)
    def entries(self,contract,project_id,after=0,limit=50):
        self.get(project_id);page(after,limit)
        rows=self.memory.db.execute("SELECT rowid AS cursor,id,payload FROM persistent_records r WHERE contract=? AND json_extract(payload,'$.project_id')=? AND rowid>? AND rowid=(SELECT max(rowid) FROM persistent_records WHERE contract=r.contract AND record_key=r.record_key) ORDER BY rowid LIMIT ?",(contract,project_id,after,limit)).fetchall()
        return {'items':[{**json.loads(r['payload']),'revision':r['id'],'cursor':r['cursor']} for r in rows],'next_cursor':rows[-1]['cursor'] if rows else after}
    def item(self,project_id,kind,title,body,*,evidence=None,status='open',confidence=None,uncertainty='User record; not independently verified.',item_id=None,revision=None,approved=False):
        if approved is not True:raise PermissionError('Explicit user action required for project records.')
        self.get(project_id)
        previous=latest(self.memory,'project_items',identity(item_id)) if item_id else None
        if previous and (previous['project_id']!=project_id or previous['kind']!=kind):raise ValueError('Cannot move/reclassify an existing item silently.')
        if previous and revision is None:raise ValueError('Expected revision required for updates.')
        p={'id':item_id or uuid4().hex,'project_id':project_id,'kind':kind,'title':title,'body':body,'status':status,'evidence':evidence or [],'confidence':confidence,'uncertainty':uncertainty,'created':previous['created'] if previous else now(),'updated':now()}
        return append(self.memory,'project_items',p['id'],p,expected=identity(revision) if previous else None,new=not previous)
    def history(self,project_id,after=0,limit=50):
        self.get(project_id);page(after,limit)
        rows=self.memory.db.execute("SELECT rowid AS cursor,id,contract,record_key,previous_id,created,CASE WHEN contract='conversations' THEN json_object('id',json_extract(payload,'$.id'),'question',substr(json_extract(payload,'$.question'),1,512),'status',json_extract(payload,'$.outcome.status'),'detail','Full turn remains in saved conversation history.') ELSE payload END AS payload FROM persistent_records WHERE rowid>? AND ((contract='projects' AND record_key=?) OR (contract IN ('project_sources','project_items','conversations') AND json_extract(payload,'$.project_id')=?)) ORDER BY rowid LIMIT ?",(after,project_id,project_id,limit)).fetchall()
        return {'items':[{**dict(r),'payload':json.loads(r['payload'])} for r in rows],'next_cursor':rows[-1]['cursor'] if rows else after}
