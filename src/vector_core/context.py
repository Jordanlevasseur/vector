"""Deterministic original-verified retrieval, bounded by explicit bytes."""
import hashlib
import json
import re
import time
from vector_core.retrieval import search
from vector_core.knowledge import Knowledge
from vector_core.memory import canonical

STOP={'what','which','where','when','why','how','is','are','was','the','a','an','of','to','and','in','does','do','please','tell','me','about'}

def build_context(memory,question,*,budget_bytes=8192,limit=8,scope=None):
    if not isinstance(question,str) or not 1<=len(question)<=2000:raise ValueError('Question must contain 1–2000 characters.')
    if type(budget_bytes) is not int or not 128<=budget_bytes<=131072:raise ValueError('Invalid context byte budget.')
    if type(limit) is not int or not 1<=limit<=20:raise ValueError('Invalid source budget.')
    started=time.perf_counter()
    terms=list(dict.fromkeys(word for word in re.findall(r'[^\W_]+',question,flags=re.UNICODE) if word.lower() not in STOP))[:12]
    candidates={}
    # AND search first; bounded per-term alternatives support multi-document synthesis.
    queries=[' '.join(terms)] if terms else []
    queries+=terms[:4]
    for query in queries:
        for result in search(memory,query[:512],limit=min(20,limit*2)):
            score=sum(term.casefold() in result['excerpt'].casefold() for term in terms)
            previous=candidates.get(result['event_id'])
            if previous is None:candidates[result['event_id']]={**result,'overlap':score}
    ordered=sorted(candidates.values(),key=lambda row:(-row['overlap'],row['rank'],row['event_id']))
    context={'question':question,'sources':[],'claims':[],'scope':scope,'conflicts':[],
             'truncated':False,'policy':'Untrusted source assertions; overrides are user assumptions.'}
    if len(canonical(context).encode())>budget_bytes:raise ValueError('Question exceeds context budget.')
    knowledge=Knowledge(memory)
    for row in ordered[:limit]:
        excerpt=row['excerpt']
        source={'event_id':row['event_id'],'source_id':row['source_id'],'sha256':row['sha256'],
                'start':0,'end':len(excerpt),'quote':excerpt,'name':row['name']}
        context['sources'].append(source)
        if len(canonical(context).encode())>budget_bytes:
            context['sources'].pop();context['truncated']=True;continue
        # Source-constrained indexed claim lookup, not a full knowledge scan.
        for (identity,) in memory.db.execute('SELECT id FROM claims WHERE event_id=? ORDER BY id LIMIT 12',(row['event_id'],)):
            claim=knowledge.claim(identity)
            effective=knowledge.effective(identity,scope or claim['scope'])
            item={'claim_id':identity,'event_id':row['event_id'],'subject':claim['subject'],'predicate':claim['predicate'],
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
    context['truncated']|=len(ordered)>len(context['sources'])
    return {'context':context,'bytes':len(canonical(context).encode()),'seconds':time.perf_counter()-started,
            'sha256':hashlib.sha256(canonical(context).encode()).hexdigest(),'ranking':'literal term overlap, FTS rank, stable ID; not semantic ranking'}
