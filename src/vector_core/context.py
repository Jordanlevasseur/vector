"""Deterministic original-verified retrieval, bounded by explicit bytes."""
import hashlib
import json
import re
import time
from vector_core.retrieval import search
from vector_core.knowledge import Knowledge
from vector_core.memory import canonical

STOP={'what','which','where','when','why','how','is','are','was','the','a','an','of','to','and','in','does','do','please','tell','me','about'}

def display_notices(memory,event_ids):
    notices=[]
    from vector_core.literature import PG_NOTICE
    for event_id in event_ids:
        from vector_core.botany import provenance as botanical_provenance
        botanical=botanical_provenance(memory,event_id)
        if botanical:notices.append({'event_id':event_id,'notice':'Botanical source: '+botanical['title']+' • '+botanical['temporal_status']+'. '+botanical['uncertainty'],'botanical_provenance':botanical})
        row=memory.db.execute("SELECT json_extract(payload,'$.metadata.rights.status') AS status,json_extract(payload,'$.rights_event_id') AS evidence FROM persistent_records WHERE contract='literary_editions' AND json_extract(payload,'$.event_id')=? LIMIT 1",(event_id,)).fetchone()
        if row and row['status']=='provider-unrestricted-us':notices.append({'event_id':event_id,'notice':PG_NOTICE,'rights_event_id':row['evidence']})
    return notices

def _focus(text,terms):
    """Smallest bounded all-term window, preserving original character offsets."""
    pattern=re.compile(r'(?<!\w)(?:'+'|'.join(re.escape(t) for t in terms)+r')(?!\w)',re.I)
    required={t.casefold() for t in terms};seen={};best=None
    for index,match in enumerate(pattern.finditer(text)):
        if index>=4096:break
        seen[match[0].casefold()]=(match.start(),match.end())
        if required<=seen.keys():
            left=min(p[0] for p in seen.values());right=max(p[1] for p in seen.values())
            if best is None or right-left<best[1]-best[0]:best=(left,right)
    if best is None or best[1]-best[0]>380:return None
    start=max(0,best[0]-100);end=min(len(text),max(start+650,best[1]+100))
    return start,end,text[start:end]


def build_context(memory,question,*,budget_bytes=8192,limit=8,scope=None,project_id=None,conversation_id=None,project_only=False,semantic=False,semantic_selector=None,investigation_id=None,retrieval_query=None,strict_query=False,content_only=False):
    if type(semantic) is not bool:raise ValueError('Semantic retrieval flag must be boolean.')
    if semantic:
        from vector_core.semantic import build_context as connected_context
        return connected_context(memory,question,budget_bytes=budget_bytes,limit=limit,scope=scope,project_id=project_id,conversation_id=conversation_id,project_only=project_only,selector=semantic_selector,investigation_id=investigation_id)
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
    retrieval_question=retrieval_query if retrieval_query is not None else question
    # Prior questions aid short follow-ups; old generated answers are never evidence.
    if retrieval_query is None and prior and len(question.split())<=5:retrieval_question+=' '+prior[0]['question']
    terms=list(dict.fromkeys(word for word in re.findall(r'[^\W_]+',retrieval_question,flags=re.UNICODE) if word.lower() not in STOP))[:12]
    candidates={}
    # AND search first; bounded per-term alternatives support multi-document synthesis.
    queries=[' '.join(terms)] if terms else []
    if not strict_query:queries+=terms[:4]
    for query in queries:
        for result in search(memory,query[:512],limit=min(20,limit*2),project_id=project_id if project_only else None,omit_literary=True):
            if strict_query:
                focused=_focus(memory.original(result['event_id']).decode('utf-8'),terms)
                if focused is None:continue
                result.update(start=focused[0],end=focused[1],excerpt=focused[2])
            score=sum(term.casefold() in result['excerpt'].casefold() for term in terms)
            previous=candidates.get(result['event_id'])
            if previous is None:candidates[result['event_id']]={**result,'overlap':score}
    from vector_core.literature import Library
    library=Library(memory);linguistic=[]
    for query in queries:
        for result in library.search(query[:512],limit=min(12,limit*2),content_only=content_only):
            if project_only and not memory.db.execute("SELECT 1 FROM persistent_records WHERE contract='project_sources' AND record_key=?",(project_id+':'+result['event_id'],)).fetchone():continue
            score=sum(term.casefold() in result['excerpt'].casefold() for term in terms)
            if result['event_id'] not in candidates:candidates[result['event_id']]={**result,'overlap':score}
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
    for term in terms[:4]:
        for node in library.concepts(term,limit=4)['items']:
            if node['status']!='approved-interpretation':continue
            expanded=[node]
            for relation in node['relationships'][:4]:
                target=relation['right'] if relation['left']==node['id'] else relation['left']
                from vector_core.projects import latest
                related=latest(memory,'linguistic_records',target)
                if related['status']=='approved-interpretation':expanded.append(related)
            for record in expanded[:5]:
                if record['id'] in {r['id'] for r in linguistic}:continue
                for a in record['attestations']:
                    if memory.read_text_span(a['event_id'],a['start'],a['end'])!=a['quote']:raise ValueError('Invalid linguistic context attestation.')
                    add_event(a['event_id'],a['start'])
                linguistic.append({**record,'interpretation_status':'Source-attested human interpretation, not independently verified fact.'})
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
    if strict_query:
        candidates={key:row for key,row in candidates.items() if all(term.casefold() in row['excerpt'].casefold() for term in terms)}
    ordered=sorted(candidates.values(),key=lambda row:(-int(row['project_match']),-row['overlap'],-sum(term.casefold() in row['name'].casefold() for term in terms) if strict_query else 0,-int(strict_query and ' '.join(terms).casefold() in row['excerpt'].casefold()),row['rank'],row['event_id']))
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
        if row.get('scientific_provenance'):source['scientific_provenance']=row['scientific_provenance']
        if row.get('botanical_provenance'):source['botanical_provenance']=row['botanical_provenance']
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
    if linguistic:optional('linguistic_records',linguistic[:8])
    if project_id:optional('project',{'id':project_id,'selection':'project-only' if project_only else 'project preferred; global sources allowed'})
    unanswered=[]
    if not context['sources']:unanswered.append('Matching originals were omitted by the selected context budget; increase the budget or narrow the question.' if candidates else 'No matching source evidence found in the selected bounded search.')
    if context['conflicts']:unanswered.append('Comparable source disagreement remains unresolved; user overrides are assumptions.')
    if unanswered:optional('unanswered_questions',unanswered)
    context['truncated']|=len(ordered)>len(context['sources'])
    notices=display_notices(memory,selected)
    return {'display_notices':notices,'context':context,'bytes':len(canonical(context).encode()),'seconds':time.perf_counter()-started,
            'sha256':hashlib.sha256(canonical(context).encode()).hexdigest(),'ranking':'explicit project preference, literal overlap, FTS rank, stable ID; exact-entity/one-hop expansion; not semantic ranking'}


def document_context(memory,question,title,*,complete=False,budget_bytes=8192):
    """Resolve archived title metadata, then verified body spans, never licence hits.

    None means no unambiguous complete source package in this operation budget.
    Originals, indexes, rights records and global retrieval behavior are unchanged.
    """
    from vector_core.literature import Library,body_bounds
    from vector_core.projects import latest
    library=Library(memory);found=library.editions(title,limit=30)['items']
    works={row['work_id'] for row in found}
    if not found or len(found)>=30 or (complete and len(works)!=1):return None
    edition=found[0];event_id=edition['event_id'];event=memory.event(event_id)
    sources=[];anchors=[]
    if complete:
        try:body=latest(memory,'literary_analyses',event_id)
        except ValueError:return None
        if event['byte_count']>memory.config.max_source_bytes or body['sha256']!=event['sha256']:return None
        actual=body_bounds(memory.original(event_id).decode('utf-8'),edition['metadata']['rights']['status'])
        if (body['start'],body['end'])!=actual:raise ValueError('Derived complete-body bounds differ from immutable original.')
        if body['end']-body['start']>budget_bytes:return None
        spans=[(edition,body['start'],body['end'])]
    else:
        spans=[]
        for candidate in found[:3]:
            # PG START markers bound the package, which may still contain a
            # transcriber's preface. Anchor excerpts after a literal short title
            # heading when one exists. This changes no stored passage or original.
            title_terms={w.casefold() for w in re.findall(r'[^\W_]+',candidate['metadata']['title']) if w.casefold() not in STOP}
            anchor=-1;candidate_event=memory.event(candidate['event_id'])
            if candidate_event['byte_count']>memory.config.max_source_bytes:continue
            original=memory.original(candidate['event_id']).decode('utf-8')
            for heading in memory.db.execute("SELECT ordinal,start_char,end_char,digest FROM literary_units WHERE event_id=? AND ordinal<128 AND end_char-start_char<=300 ORDER BY ordinal LIMIT 128",(candidate['event_id'],)):
                a,b=heading['start_char'],heading['end_char'];quote=original[a:b]
                if not 0<=a<b<=len(original) or hashlib.sha256(quote.encode()).hexdigest()!=heading['digest']:raise ValueError('Corrupt title-anchor passage; rebuild the derived index before use.')
                words=re.findall(r'[^\W_]+',quote)
                if title_terms and len(words)<=max(25,len(title_terms)+5) and title_terms=={w.casefold() for w in words if w.casefold() not in STOP}:
                    anchor=heading['ordinal']
            if anchor>=0:anchors.append({'event_id':candidate['event_id'],'ordinal':anchor,'method':'last exact normalized short title in the first128 units; not semantic certification'})
            rows=memory.db.execute("SELECT start_char,end_char FROM literary_units WHERE event_id=? AND ordinal>? AND kind NOT LIKE 'section%' AND end_char-start_char>=100 ORDER BY ordinal LIMIT 20",(candidate['event_id'],anchor)).fetchall()
            spans.extend((candidate,r['start_char'],r['end_char']) for r in rows)
    context={'question':question,'sources':[],'claims':[],'scope':None,'conflicts':[],'truncated':not complete,'policy':'Archived source assertions, not independent truth. Body excerpts are not a document summary.','document':{'title':edition['metadata']['title'],'event_id':event_id,'complete_body_supplied':complete,'unambiguous_title':len(works)==1,'excerpt_title_anchors':anchors}}
    for edition,start,end in spans:
        event_id=edition['event_id'];event=memory.event(event_id)
        quote=memory.read_text_span(event_id,start,end)
        if not complete and len(re.findall(r'[^\W_]+',quote))<12:continue
        source={'event_id':event_id,'source_id':event['source_id'],'sha256':event['sha256'],'start':start,'end':end,'quote':quote,'name':edition['metadata']['title'],'occurred':event['occurred']}
        context['sources'].append(source)
        if len(canonical(context).encode())>budget_bytes:
            context['sources'].pop()
            if complete:return None
            break
        if not complete and len(context['sources'])>=3:break
    if not context['sources']:return None
    return {'context':context,'display_notices':display_notices(memory,list(dict.fromkeys(s['event_id'] for s in context['sources']))),'bytes':len(canonical(context).encode()),'sha256':hashlib.sha256(canonical(context).encode()).hexdigest(),'seconds':0,'ranking':'Archived-title candidates; original-verified excerpts after exact title headings when present; no semantic relevance or summary certification.'}
