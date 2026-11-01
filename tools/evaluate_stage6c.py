"""External answer-level scoring; expected outcomes never enter production prompts.

A/B are explicitly frozen historical runs. Deterministic C assembly and optional
neural commentary are different metrics; no rewritten model response is scored.
"""
import argparse,hashlib,json,time,resource
from pathlib import Path
from decimal import Decimal,InvalidOperation
from evaluate_stage6b import read_corpus,load_fixture,validate_citations,normalized
from vector_core.config import Config
from vector_core.memory import Memory,canonical
from vector_core.service import Application
from vector_core.findings import validate_document,handoff

def grade(memory,case,answer,mapping):
 gold=case['gold'];f=answer['findings'][0];status={'tool-verified':'verified-computation','insufficient':'unknown','hypothetical':'hypothesis'}.get(gold['status'],gold['status']);blocks=answer['blocks'];visible='\n'.join(b['text'] for b in blocks)
 values=f['values'];actual='; '.join(('not ' if v.get('polarity')=='negated' else '')+str(v['value']) for v in values)
 if status in {'unknown','disputed'}:
  correct=(not values if status=='unknown' else True) and ('Unknown or not completed' in visible if status=='unknown' else 'No single result is established' in visible)
 else:
  try:correct=Decimal(actual)==Decimal(gold['value']) if gold['numeric'] else normalized(actual)==normalized(gold['value'])
  except (ValueError,InvalidOperation):correct=False
  correct=correct and (str(values[0]['value']) in visible if gold['numeric'] else normalized(gold['value']) in normalized(visible))
 units='unit' not in gold or bool(values) and values[0]['unit']==gold['unit'] and gold['unit'] in visible
 required={mapping['events'][s] for s in gold['sources']};cites=answer['sources'];linked=required<=set(c['event_id'] for c in cites) and all(c['handle'] in visible for c in cites)
 fidelity=validate_citations(memory,cites);status_ok=f['status']==status and all(b['status']==status for b in blocks)
 # Independently check literal applicability retained, not just values/citations.
 qualifications=all(all(str(v) in visible for v in p['conditions'].values()) and all(not p[k] or p[k] in visible for k in ('valid_from','valid_until')) for p in f['premises'])
 return {'objective_passed':bool(correct and units and linked and fidelity and status_ok and qualifications),'answer_correct':bool(correct),'status_correct':status_ok,'units_correct':bool(units),'required_sources_visible':linked,'citation_fidelity':fidelity,'qualifiers_visible':qualifications,'expected':gold,'actual_status':f['status'],'actual_value':actual}

def merge_corpora(original,unseen):
 """Namespace fixture identities when evaluating two independent source packs."""
 from copy import deepcopy
 result=deepcopy(original);extra=deepcopy(unseen)
 for source in extra['sources']:source['key']='unseen/'+source['key']
 for claim in extra['claims']:
  claim['key']='unseen/'+claim['key'];claim['source']='unseen/'+claim['source']
 for case in extra['cases']:case['gold']['sources']=['unseen/'+s for s in case['gold']['sources']]
 for key in ('sources','claims','cases'):result[key].extend(extra[key])
 for key,identifier in (('sources','key'),('claims','key'),('cases','id')):
  if len({x[identifier] for x in result[key]})!=len(result[key]):raise ValueError('Colliding evaluation identities: '+key)
 return result

def deterministic(corpus,unseen,directory):
 directory=Path(directory);directory.mkdir(parents=True,exist_ok=True);memory=Memory(Config.load(data_dir=str(directory/'data')));rows=[];tick=time.perf_counter()
 try:
  app=Application(memory)
  class Forbidden:
   def generate(self,*a,**kw):raise AssertionError('No neural dependency allowed in checked output evaluation.')
  app.adapter=Forbidden()
  for label,pack in (('original',corpus),('unseen',unseen)):
   mapping=load_fixture(memory,pack)
   for case in pack['cases']:
    start=time.perf_counter();result=app.handle('semantic_answer',{'question':case['question'],'request':case['request'],'approved':True,'seconds':60});answer=result['answer']
    if answer is None:raise ValueError(result)
    validate_document(memory,answer);score=grade(memory,case,answer,mapping);package=handoff(memory,answer,budget_bytes=7424)
    rows.append({'id':case['id'],'set':label,'live':case['live'],'grade':score,'seconds':time.perf_counter()-start,'answer':answer,'handoff_bytes':package['required_bytes'],'handoff_fits_existing_guard':package['available'],'model_called':False})
  return {'format':'vector-stage6c-evaluation-v1','methodology':'Frozen original and independently specified unseen premises; output blocks, numeric values, units, statuses, visible source handles, exact original hashes/spans and condition/date clauses scored. No model called. Novel open-ended reasoning is not measured.','rows':rows,'integrity':memory.verify(),'seconds':time.perf_counter()-tick,'process_maxrss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'summary':{label:{'passed':sum(r['grade']['objective_passed'] for r in rows if r['set']==label),'total':sum(r['set']==label for r in rows)} for label in ('original','unseen')}}
 finally:memory.close()

def main():
 from vector_core.security import activate
 activate()
 p=argparse.ArgumentParser();p.add_argument('--directory',required=True);p.add_argument('--baseline',required=True);a=p.parse_args();root=Path(__file__).resolve().parents[1];old=Path(a.baseline);baseline=json.loads(old.read_text());result=deterministic(read_corpus(root/'tests/fixtures/stage6b-corpus.json'),json.loads((root/'tests/fixtures/stage6c-unseen.json').read_text()),a.directory);result['historical_baseline']={'sha256':hashlib.sha256(old.read_bytes()).hexdigest(),'path':str(old),'label':'Frozen previous real0.5B results, not rerun in Stage6C','scores':{mode:{'passed':sum(r['model_grade']['objective_passed'] for r in baseline['rows'] if r['mode']==mode),'total':sum(r['mode']==mode for r in baseline['rows'])} for mode in ('A','B','C')}};Path(a.directory,'comparison.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:result[k] for k in ('summary','seconds','process_maxrss_kib','historical_baseline')},indent=2))
if __name__=='__main__':main()
