"""Deterministic original-verified retrieval, bounded by explicit bytes."""
import hashlib
import json
import re
import time
from vector_core.retrieval import search
from vector_core.knowledge import Knowledge
from vector_core.memory import canonical

STOP={'what','which','where','when','why','how','is','are','was','the','a','an','of','to','and','in','does','do','please','tell','me','about'}

def build_context(memory,question,*,budget_bytes=8192,limit=8,scope=None,project_id=None,conversation_id=None,project_only=False):
    if not isinstance(question,str) or not 1<=len(question)<=2000:raise ValueError('Question must contain 1–2000 characters.')
    if type(budget_bytes) is not int or not 128<=budget_bytes<=131072:raise ValueError('Invalid context byte budget.')
    if type(limit) is not int or not 1<=limit<=20:raise ValueError('Invalid source budget.')
    started=time.perf_counter()
    if type(project_only) is not bool:raise ValueError('Project-only flag must be boolean.')
    from vector_core.memory_intelligence import continuity
    from vector_core.projects import Projects
    prior=continuity(memory,conversation_id,question) if conversation_id else []
    if project_only and not project_id:raise ValueError('Project-only context requires a project.')
    if project_id:Projects(memory).get(project_id)
    retrieval_question=question
    # Prior questions aid short follow-ups; old generated answers are never evidence.
    if prior and len(question.split())<=5:retrieval_question+=' '+prior[0]['question']
    terms=list(dict.fromkeys(word for word in re.findall(r'[^\W_]+',retrieval_question,flags=re.UNICODE) if word.lower() not in STOP))[:12]
    candidates={}
    # AND search first; bounded per-term alternatives support multi-document synthesis.
    queries=[' '.join(terms)] if terms else []
    queries+=terms[:4]
    for query in queries:
        for result in search(memory,query[:512],limit=min(20,limit*2),project_id=project_id if project_only else None):
            score=sum(term.casefold() in result['excerpt'].casefold() for term in terms)
            previous=candidates.get(result['event_id'])
            if previous is None:candidates[result['event_id']]={**result,'overlap':score}
    # Exact entity resolution and bounded one-hop/source-comparison expansion.
    # Never interpret relation labels as independently established truth.
    def add_event(event_id,anchor=0):
        if event_id in candidates:return
        if project_only and not memory.db.execute("SELECT 1 FROM persistent_records WHERE contract='project_sources' AND record_key=?",(project_id+':'+event_id,)).fetchone():return
        event=memory.event(event_id)
        if event['byte_count']>memory.config.max_source_bytes:return
        raw=memory.original(event_id)
        try:original=raw.decode('utf-8')
        except UnicodeError:return
        start=max(0,anchor-80);end=min(len(original),start+500)
        candidates[event_id]={'event_id':event_id,'source_id':event['source_id'],'sha256':event['sha256'],'name':event['submission_name'],
                             'excerpt':original[start:end],'start':start,'end':end,'occurred':event['occurred'],'rank':0.0,'overlap':sum(t.casefold() in original[start:end].casefold() for t in terms)}
    words=re.findall(r'[^\W_]+',question,flags=re.UNICODE)[:12]
    labels=[' '.join(words[i:i+n]) for n in (3,2,1) for i in range(len(words)-n+1)][:32]
    entities=[]
    from vector_core.knowledge import normalized
    for label in labels:
        entity=memory.db.execute('SELECT id FROM entities WHERE normalized=?',(normalized(label),)).fetchone()
        if entity and entity[0] not in entities:entities.append(entity[0])
    for entity in entities[:4]:
        for claim in memory.db.execute('SELECT event_id,start_char,object_id FROM claims WHERE subject_id=? OR object_id=? ORDER BY created DESC,id LIMIT 12',(entity,entity)):
            add_event(claim['event_id'],claim['start_char'])
            if claim['object_id']:
                for other in memory.db.execute('SELECT event_id,start_char FROM claims WHERE subject_id=? ORDER BY created DESC,id LIMIT 4',(claim['object_id'],)):add_event(other['event_id'],other['start_char'])
    project_records=[]
    if project_id:
        rows=memory.db.execute("SELECT payload FROM persistent_records r WHERE contract='project_items' AND json_extract(payload,'$.project_id')=? AND rowid=(SELECT max(rowid) FROM persistent_records WHERE contract='project_items' AND record_key=r.record_key) ORDER BY rowid DESC LIMIT 20",(project_id,)).fetchall()
        for raw in rows:
            record=json.loads(raw[0]);score=sum(term.casefold() in (record['title']+' '+record['body']).casefold() for term in terms)
            if score:
                project_records.append({**record,'body':record['body'][:1000],'status_label':'User-authored project record; not independently established evidence.'})
                for event_id in record['evidence'][:4]:add_event(event_id)
                if len(project_records)>=4:break
    for event_id in list(candidates)[:8]:
        for other in memory.db.execute("SELECT json_extract(payload,'$.event_id') AS a,json_extract(payload,'$.target_id') AS b FROM persistent_records WHERE contract='memory_links' AND (json_extract(payload,'$.event_id')=? OR json_extract(payload,'$.target_id')=?) ORDER BY rowid LIMIT 3",(event_id,event_id)):add_event(other['b'] if other['a']==event_id else other['a'])
        for claim in memory.db.execute('SELECT subject_id,predicate,scope,unit,value_key FROM claims WHERE event_id=? AND exclusive=1 LIMIT 4',(event_id,)):
            for other in memory.db.execute('SELECT event_id,start_char FROM claims WHERE subject_id=? AND predicate=? AND scope=? AND unit=? AND exclusive=1 AND value_key!=? LIMIT 4',tuple(claim)):add_event(other['event_id'],other['start_char'])
    for row in candidates.values():
        row['project_match']=bool(project_id and memory.db.execute("SELECT 1 FROM persistent_records WHERE contract='project_sources' AND record_key=?",(project_id+':'+row['event_id'],)).fetchone())
    ordered=sorted(candidates.values(),key=lambda row:(-int(row['project_match']),-row['overlap'],row['rank'],row['event_id']))
    context={'question':question,'sources':[],'claims':[],'scope':scope,'conflicts':[],
             'truncated':False,'policy':'Untrusted source assertions; overrides are user assumptions.'}
    if len(canonical(context).encode())>budget_bytes:raise ValueError('Question exceeds context budget.')
    def optional(key,value):
        context[key]=value
        if len(canonical(context).encode())>budget_bytes:context.pop(key);context['truncated']=True
    knowledge=Knowledge(memory)
    for row in ordered[:limit]:
        excerpt=row['excerpt']
        source={'event_id':row['event_id'],'source_id':row['source_id'],'sha256':row['sha256'],
                'start':row.get('start',0),'end':row.get('end',len(excerpt)),'quote':excerpt,'name':row['name'],'occurred':row.get('occurred')}
        context['sources'].append(source)
        if len(canonical(context).encode())>budget_bytes:
            match=re.search('|'.join(re.escape(term) for term in terms),excerpt,re.IGNORECASE) if terms else None
            focus=match.start() if match else 0
            for width in (256,128,64,32):
                if width>=len(excerpt):continue
                left=max(0,focus-min(32,width//4));right=min(len(excerpt),left+width)
                source.update(start=row.get('start',0)+left,end=row.get('start',0)+right,quote=excerpt[left:right])
                context['truncated']=True
                if len(canonical(context).encode())<=budget_bytes:break
            if len(canonical(context).encode())>budget_bytes:
                context['sources'].pop();context['truncated']=True;continue
    # Allocate original coverage before derived claims/notes can consume the budget.
    for source in context['sources']:
        for (identity,) in memory.db.execute('SELECT id FROM claims WHERE event_id=? ORDER BY id LIMIT 12',(source['event_id'],)):
            claim=knowledge.claim(identity)
            effective=knowledge.effective(identity,scope or claim['scope'])
            item={'claim_id':identity,'event_id':source['event_id'],'subject':claim['subject'],'predicate':claim['predicate'],
                  'value':claim['value'],'scope':claim['scope'],'unit':claim['unit'],'exclusive':bool(claim['exclusive']),
                  'operating_conclusion':effective['operating_conclusion'],'override':effective['override'],
                  'assessment':effective['assessment'],'status':'unverified source statement'}
            context['claims'].append(item)
            if len(canonical(context).encode())>budget_bytes:context['claims'].pop();context['truncated']=True
    groups={}
    for claim in context['claims']:
        if claim['exclusive']:
            key=(claim['subject'],claim['predicate'],claim['scope'],claim['unit'])
            groups.setdefault(key,[]).append(claim)
    for key,claims in groups.items():
        if len({claim['value'] for claim in claims})>1:
            context['conflicts'].append({'subject':key[0],'predicate':key[1],'scope':key[2],'claim_ids':[c['claim_id'] for c in claims]})
            if len(canonical(context).encode())>budget_bytes:context['conflicts'].pop();context['truncated']=True
    relationships=[]
    selected={source['event_id'] for source in context['sources']}
    from vector_core.memory_intelligence import links
    for event_id in sorted(selected):
        for link in links(memory,event_id,limit=4)['items']:
            if link['event_id'] in selected and link['target_id'] in selected:relationships.append(link)
    if relationships:optional('evidence_relationships',relationships[:12])
    if prior:optional('continuity',prior)
    if project_records:optional('project_records',project_records)
    if project_id:optional('project',{'id':project_id,'selection':'project-only' if project_only else 'project preferred; global sources allowed'})
    unanswered=[]
    if not context['sources']:unanswered.append('Matching originals were omitted by the selected context budget; increase the budget or narrow the question.' if candidates else 'No matching source evidence found in the selected bounded search.')
    if context['conflicts']:unanswered.append('Comparable source disagreement remains unresolved; user overrides are assumptions.')
    if unanswered:optional('unanswered_questions',unanswered)
    context['truncated']|=len(ordered)>len(context['sources'])
    return {'context':context,'bytes':len(canonical(context).encode()),'seconds':time.perf_counter()-started,
            'sha256':hashlib.sha256(canonical(context).encode()).hexdigest(),'ranking':'explicit project preference, literal overlap, FTS rank, stable ID; exact-entity/one-hop expansion; not semantic ranking'}
