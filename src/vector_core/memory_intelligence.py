"""Deterministic memory views and evidence comparisons; no claims of understanding."""
import json
import re
from uuid import uuid4
from vector_core.memory import now
from vector_core.projects import Projects,append,identity,latest,page,LINK_KINDS
from vector_core.retrieval import search,timestamp
from vector_core.knowledge import Knowledge,normalized

VIEWS=('episodic','semantic','procedural','project','working')

def recall(memory,query='',*,view='episodic',project_id=None,conversation_id=None,since=None,until=None,source_id=None,limit=30,after=0):
    if view not in VIEWS:raise ValueError('Unknown memory view.')
    page(after,limit)
    if view=='working':
        identity(conversation_id)
        if source_id is not None:raise ValueError('Source filters apply to archived-source views, not saved conversation questions.')
        if since and until and timestamp(since)>timestamp(until):raise ValueError('Time range is reversed.')
        if project_id:Projects(memory).get(project_id)
        if not isinstance(query,str) or len(query)>512:raise ValueError('Invalid working-memory query.')
        # Latest version per turn, with cursor paging; originals are not summarized away.
        conditions=[];parameters=[conversation_id,after,query,query]
        for value,operator in ((since,'>='),(until,'<=')):
            if value:conditions.append("json_extract(payload,'$.created')"+operator+'?');parameters.append(timestamp(value))
        if project_id:conditions.append("json_extract(payload,'$.project_id')=?");parameters.append(project_id)
        rows=memory.db.execute("SELECT rowid AS cursor,payload FROM persistent_records r WHERE contract='conversations' AND substr(record_key,1,32)=? AND rowid>? AND rowid=(SELECT max(rowid) FROM persistent_records WHERE contract='conversations' AND record_key=r.record_key) AND (?='' OR instr(lower(json_extract(payload,'$.question')),lower(?))>0) "+('AND '+' AND '.join(conditions) if conditions else '')+" ORDER BY rowid LIMIT ?",parameters+[limit]).fetchall()
        return {'view':view,'items':[{'cursor':r['cursor'],**{k:v for k,v in json.loads(r['payload']).items() if k in ('id','conversation_id','project_id','question','created')},'status':json.loads(r['payload']).get('outcome',{}).get('status')} for r in rows],'next_cursor':rows[-1]['cursor'] if rows else after,'limits':'Exact saved user questions/turns, not model summaries or semantic recall.'}
    results=search(memory,query,limit=limit,project_id=project_id,category=view,since=since,until=until,source_id=source_id)
    return {'view':view,'items':results,'limits':'Bounded literal query; explicit filters. No semantic equivalence or calibrated relevance.'}

def compare(memory,event_id,limit=20):
    from vector_core.projects import page
    page(0,limit);event=memory.event(identity(event_id))
    duplicates=[dict(r) for r in memory.db.execute('SELECT id AS event_id,source_id,occurred,parent_id FROM events WHERE sha256=? AND id!=? ORDER BY occurred,id LIMIT ?',(event['sha256'],event_id,limit))]
    text=memory.original(event_id).decode('utf-8') if event['byte_count']<=memory.config.max_source_bytes and event['media_type'].startswith('text/') else ''
    terms=list(dict.fromkeys(re.findall(r'[^\W_]+',text)))[:4];candidates={}
    for term in terms:
        for result in search(memory,term,limit=limit):
            if result['event_id']!=event_id and result['sha256']!=event['sha256']:candidates[result['event_id']]=result
    revision=[dict(r) for r in memory.db.execute('SELECT id AS event_id,parent_id,occurred FROM events WHERE source_id=? ORDER BY occurred,id LIMIT ?',(event['source_id'],limit))]
    return {'event_id':event_id,'exact_duplicate_events':duplicates,'overlap_candidates':list(candidates.values())[:limit],'source_versions':revision,'parent_id':event['parent_id'],'limits':'Exact hashes prove duplicate bytes, not duplicate submission intent. Lexical overlap is a candidate only. Bounded preview, originals retained.'}

def link(memory,event_id,target_id,kind,reason,*,approved=False):
    if approved is not True:raise PermissionError('Explicit evidence relationship approval required.')
    p={'id':uuid4().hex,'event_id':event_id,'target_id':target_id,'kind':kind,'reason':reason,'created':now()}
    return append(memory,'memory_links',p['id'],p,new=True)

def links(memory,event_id,after=0,limit=30):
    memory.event(identity(event_id));page(after,limit)
    rows=memory.db.execute("SELECT rowid AS cursor,payload FROM persistent_records WHERE contract='memory_links' AND rowid>? AND (json_extract(payload,'$.event_id')=? OR json_extract(payload,'$.target_id')=?) ORDER BY rowid LIMIT ?",(after,event_id,event_id,limit)).fetchall()
    return {'items':[{**json.loads(r['payload']),'cursor':r['cursor'],'status':'User-authored relationship; unverified.'} for r in rows],'next_cursor':rows[-1]['cursor'] if rows else after}

def defer(memory,event_id,reason='Model extraction deferred; original retained. Deterministic learning may be used explicitly.'):
    return append(memory,'learning_queue',event_id,{'event_id':event_id,'status':'deferred','reason':reason,'created':now()})

def queue(memory,after=0,limit=50):
    page(after,limit)
    rows=memory.db.execute("SELECT rowid AS cursor,payload FROM persistent_records r WHERE contract='learning_queue' AND rowid>? AND rowid=(SELECT max(rowid) FROM persistent_records WHERE contract='learning_queue' AND record_key=r.record_key) ORDER BY rowid LIMIT ?",(after,limit)).fetchall()
    return {'items':[{**json.loads(r['payload']),'cursor':r['cursor']} for r in rows],'next_cursor':rows[-1]['cursor'] if rows else after}

def learning_history(memory,event_id,after=0,limit=50):
    memory.event(identity(event_id));page(after,limit)
    runs=[dict(r) for r in memory.db.execute('SELECT rowid AS cursor,* FROM extraction_runs WHERE event_id=? AND rowid>? ORDER BY rowid LIMIT ?',(event_id,after,limit))]
    claims=Knowledge(memory).claim_page(event_id=event_id,limit=limit)
    return {'extraction_runs':runs,'next_cursor':runs[-1]['cursor'] if runs else after,'claims':claims,'deferred':latest(memory,'learning_queue',event_id) if memory.db.execute("SELECT 1 FROM persistent_records WHERE contract='learning_queue' AND record_key=?",(event_id,)).fetchone() else None,'original_retained':True}

def continuity(memory,conversation_id,question,limit=4):
    """Recent user questions only; answers and instructions are never authority."""
    identity(conversation_id)
    if type(limit) is not int or not 1<=limit<=4:raise ValueError('Continuity uses 1–4 prior questions per context.')
    rows=memory.db.execute("SELECT payload FROM persistent_records r WHERE contract='conversations' AND substr(record_key,1,32)=? AND rowid=(SELECT max(rowid) FROM persistent_records WHERE contract='conversations' AND record_key=r.record_key) ORDER BY rowid DESC LIMIT ?",(conversation_id,limit+1)).fetchall()
    return [{'turn_id':p['id'],'question':p['question'][:300],'status':'Untrusted prior user context; not source evidence.'} for p in (json.loads(r[0]) for r in rows) if p.get('question')!=question and 'id' in p][:limit]

def reconcile(memory,event_id,limit=20):
    """Compare explicit scoped literal claims; never choose a winner automatically."""
    memory.event(identity(event_id));page(0,limit);knowledge=Knowledge(memory);comparisons=[]
    for row in memory.db.execute('SELECT * FROM claims WHERE event_id=? ORDER BY id LIMIT ?',(event_id,limit)):
        others=memory.db.execute('SELECT id,value_key,event_id FROM claims WHERE subject_id=? AND predicate=? AND scope=? AND unit=? AND id!=? ORDER BY created DESC,id LIMIT ?',
                                (row['subject_id'],row['predicate'],row['scope'],row['unit'],row['id'],limit)).fetchall()
        for other in others:
            candidate=knowledge.claim(other['id'])
            if other['value_key']==row['value_key']:relation='same literal value; independent truth not established'
            elif row['exclusive'] and candidate['exclusive']:relation='potential scoped disagreement; reassessment needed'
            else:relation='different literal value; comparability not established'
            comparisons.append({'claim_id':row['id'],'other_claim_id':other['id'],'other_event_id':other['event_id'],'relationship':relation,'effective':knowledge.effective(other['id'],candidate['scope'])})
            if len(comparisons)>=limit:break
        if len(comparisons)>=limit:break
    needs_review=any('reassessment needed' in row['relationship'] for row in comparisons)
    if needs_review:
        append(memory,'learning_queue',event_id,{'event_id':event_id,'status':'review-needed','reason':'Comparable source claims disagree; user review required. Existing assessments and overrides preserved.','created':now()})
    return {'event_id':event_id,'comparisons':comparisons,'review_needed':needs_review,'bounded_preview':len(comparisons)>=limit,'original_modified':False,'limits':'Literal same-scope/unit comparison, not semantic equivalence, unit normalization or automatic truth adjudication.'}
