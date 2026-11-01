"""External gold evaluation; no expected answers enter the cognitive implementation.

Fixture objects are controlled premises, not world observations. Local publication
quotes carry original/container/page provenance and U.S.-only rights metadata.
"""
import argparse,hashlib,json,re,time
from decimal import Decimal,InvalidOperation
from pathlib import Path
from vector_core.config import Config
from vector_core.memory import Memory,Submission
from vector_core.knowledge import ClaimDraft,Knowledge
from vector_core.semantic import Semantics,reason,validate_result
from vector_core.context import build_context
from vector_core.investigation import Investigations,Budget
from vector_core.service import Application
from vector_core.portable import unique

def normalized(value):return ' '.join(str(value).split()).strip(' .:;\"\'').casefold()
def read_corpus(path):
 corpus=json.loads(Path(path).read_text(),object_pairs_hook=unique)
 if corpus.get('format')!='vector-stage6b-gold-v1' or corpus.get('jurisdiction')!='US':raise ValueError('Unknown corpus/rights scope.')
 if not 36<=len(corpus['cases'])<=200 or len({c['id'] for c in corpus['cases']})!=len(corpus['cases']):raise ValueError('At least36 independent uniquely named gold cases required.')
 if not 1<=len(corpus['sources'])<=200 or not 1<=len(corpus['claims'])<=400:raise ValueError('Corpus exceeds this bounded evaluation slice.')
 return corpus

def verify_local_sources(corpus,pack):
 pack=Path(pack);entries={e['provider_id']:e for e in map(json.loads,(pack/'manifest.ndjson').read_text().splitlines()[1:])};checked={};report=[]
 for source in corpus['sources']:
  if source['kind']!='verified-local-excerpt':continue
  proof=source['provenance'];entry=entries[proof['provider_id']]
  if entry['original']['sha256']!=proof['original_sha256'] or entry['publication_date']!=proof['publication_date'] or entry['rights']!=proof['rights']:raise ValueError('Changed source identity/date/rights.')
  digest=proof['original_sha256']
  if digest not in checked:
   h=hashlib.sha256()
   with (pack/'objects'/digest).open('rb') as f:
    while b:=f.read(1048576):h.update(b)
   if h.hexdigest()!=digest:raise ValueError('Complete original checksum differs.')
   checked[digest]=True
  spec=json.loads((pack/'objects'/entry['extraction_sha256']).read_text());page=spec['pages'][proof['page']-1]
  raw=(pack/'objects'/page['sha256']).read_bytes()
  if hashlib.sha256(raw).hexdigest()!=proof['derived_page_sha256'] or page['sha256']!=proof['derived_page_sha256'] or page['locator']!=proof['locator'] or raw.decode()[proof['start']:proof['end']]!=source['text']:raise ValueError('Gold source span differs from preserved local extraction.')
  report.append({'source':source['key'],'original_sha256':digest,'page_sha256':page['sha256'],'locator':page['locator'],'exact_excerpt_verified':True})
 return {'passed':True,'excerpts':report,'complete_originals_rehashed':len(checked)}

def load_fixture(memory,corpus):
 events={};claims={}
 for source in corpus['sources']:
  metadata={'evaluation_source':source['key'],'fixture_kind':source['kind'],'source_provenance':source['provenance']}
  event=memory.ingest(Submission(source['text'].encode(),source['name'],metadata=metadata));events[source['key']]=event['event_id']
 sem=Semantics(memory)
 for record in corpus['claims']:
  source=next(s for s in corpus['sources'] if s['key']==record['source']);draft=ClaimDraft(event_id=events[record['source']],**record['draft']);quote=source['text'][draft.start:draft.end]
  if draft.subject not in quote or draft.value not in quote:raise ValueError('Gold interpretation lacks literal source anchors.')
  claim=Knowledge(memory).add_claim(draft);sem.qualify(claim['id'],record['qualification'],approved=True);claims[record['key']]=claim['id']
 return {'events':events,'claims':claims}

def validate_citations(memory,citations):
 for c in citations:
  e=memory.event(c['event_id'])
  if c['sha256']!=e['sha256'] or memory.read_text_span(c['event_id'],c['start'],c['end'])!=c['quote']:return False
 return True

def core_answer(result):
 if result['status'] in {'insufficient','disputed'}:return result['status']
 if result.get('kind')=='grounded-calculation':return result.get('value','')
 return '; '.join(('not ' if v['polarity']=='negated' else '')+v['value'] for v in result['values'])

def answer_matches(actual,gold):
 if gold['numeric']:
  try:return Decimal(str(actual).strip())==Decimal(gold['value'])
  except (InvalidOperation,ValueError):return False
 return normalized(actual)==normalized(gold['value'])

def grade_core(memory,case,result,mapping):
 expected=case['gold'];required={mapping['events'][s] for s in expected['sources']};cites=result.get('citations',[])
 valid=validate_citations(memory,cites);sources=required<=set(c['event_id'] for c in cites)
 answer=core_answer(result);status=result['status']==expected['status'];correct=answer_matches(answer,expected)
 return {'status_correct':status,'answer_correct':correct,'required_sources_present':sources,'citation_provenance_valid':valid,'objective_passed':status and correct and sources and valid,'answer':answer,'expected':expected,'actual_status':result['status']}

def grade_model(memory,case,candidate,mapping):
 required={mapping['events'][s] for s in case['gold']['sources']};citations=candidate.get('citations',[]) if candidate else []
 actual=candidate.get('answer','') if candidate else '';valid=bool(candidate) and validate_citations(memory,citations)
 correct=bool(candidate) and answer_matches(actual,case['gold']);sources=required<=set(c['event_id'] for c in citations)
 negative=case['gold']['status'] in {'insufficient','disputed'}
 unsupported=bool(candidate) and negative and normalized(actual) not in {'insufficient','disputed','unknown','not established','cannot determine'}
 return {'valid_structure':bool(candidate),'answer_correct':correct,'required_sources_present':sources,'citation_provenance_valid':valid,'objective_passed':correct and sources and valid,'answer':actual,'unsupported_definite_answer_on_negative_control':unsupported if negative else None,'expected':case['gold']}

def grade_retrieval(memory,case,context,mapping,corpus):
 required={mapping['events'][s] for s in case['gold']['sources']};seen={s['event_id'] for s in context['sources']}
 complete=set()
 for source in corpus['sources']:
  event=mapping['events'][source['key']]
  if any(s['event_id']==event and s['start']==0 and s['end']>=len(source['text']) for s in context['sources']):complete.add(event)
 return {'required_source_count':len(required),'required_source_hits':len(required&seen),'all_required_sources':required<=seen if required else None,'full_gold_excerpt_coverage':required<=complete if required else None,'provenance_valid':validate_citations(memory,context['sources'])}

def run_grounded(memory,case):
 tick=time.perf_counter();continued=False
 if case.get('continuation'):
  inv=Investigations(memory);state=inv.create(case['question'],semantic_request=case['request'],approved=True)
  first=inv.run(state['id'],budget=Budget(1,0,60),approved=True)
  if first['state']['status']!='paused':raise ValueError('Continuation fixture did not reach its intended checkpoint.')
  config=memory.config;memory.close();memory=Memory(config);inv=Investigations(memory)
  saved=inv.get(state['id']);inv.control(saved['id'],'resume',saved['revision'],approved=True)
  execution=inv.run(saved['id'],budget=Budget(2,0,60),approved=True);continued=True;results,_=inv._results(saved['id']);result=results.get('grounded');key=saved['id']
 else:
  out=Application(memory).handle('semantic_reason',{'question':case['question'],'request':case['request'],'approved':True,'seconds':60});result=out['result'];execution=out['execution'];key=out['investigation_id']
 if result is None:raise ValueError('Grounded controller failed before producing a result: '+execution['state']['reason'])
 validate_result(memory,result)
 return memory,{'result':result,'investigation_id':key,'execution':execution,'continued_after_reopen':continued,'seconds':time.perf_counter()-tick}

def deterministic(corpus,directory):
 directory=Path(directory);directory.mkdir(parents=True,exist_ok=False);memory=Memory(Config.load(data_dir=str(directory/'data')));rows=[]
 try:
  mapping=load_fixture(memory,corpus)
  for case in corpus['cases']:
   row={'id':case['id'],'category':case['category']};rows.append(row)
   try:
    base=build_context(memory,case['question'],budget_bytes=8192)
    row['B_direct_retrieval']=grade_retrieval(memory,case,base['context'],mapping,corpus)
    memory,out=run_grounded(memory,case);row['C']=grade_core(memory,case,out['result'],mapping);row['C']['continued_after_reopen']=out['continued_after_reopen'];row['seconds']=out['seconds'];row['grounded_result']=out['result']
   except Exception as e:row['error']=repr(e);row.setdefault('C',{'objective_passed':False})
  integrity=memory.verify();report={'mode':'deterministic-external-gold','model_calls':0,'A':'Not applicable: no synthetic model outputs are substituted','C_passed':sum(r['C']['objective_passed'] for r in rows),'C_total':len(rows),'rows':rows,'integrity':integrity,'schema_version':memory.db.execute('PRAGMA user_version').fetchone()[0]}
  (directory/'results.json').write_text(json.dumps(report,indent=2));return report
 finally:memory.close()

def main():
 p=argparse.ArgumentParser();p.add_argument('--corpus',required=True);p.add_argument('--directory',required=True);p.add_argument('--science-pack');a=p.parse_args()
 from vector_core.security import activate
 policy=activate()
 corpus=read_corpus(a.corpus)
 if a.science_pack:proof=verify_local_sources(corpus,a.science_pack)
 else:proof={'status':'Local original archive verification not requested; fixed excerpts and provenance remain inspectable'}
 r=deterministic(corpus,a.directory);r['policy']=policy;r['local_original_verification']=proof;(Path(a.directory)/'results.json').write_text(json.dumps(r,indent=2))
 print(json.dumps({'C_passed':r['C_passed'],'C_total':r['C_total'],'failed':[{'id':x['id'],'error':x.get('error'),'grade':x['C']} for x in r['rows'] if not x['C']['objective_passed']],'integrity':r['integrity']},indent=2))
 return 0 if r['C_passed']==r['C_total'] and r['integrity']['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
