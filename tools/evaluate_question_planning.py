"""External planning/outcome scoring. Gold never enters the runtime planner."""
import argparse,hashlib,json,resource,statistics,time
from decimal import Decimal,InvalidOperation
from pathlib import Path
from evaluate_stage6b import load_fixture,validate_citations
from vector_core.config import Config
from vector_core.memory import Memory,canonical
from vector_core.service import Application
from vector_core.findings import validate_document

REQUIRED={'P01':['mass'],'P02':['alias'],'P03':['join1','join2','density'],'P04':['conflict1','conflict2'],'P05':['wet'],'P07':['time'],'P10':['sense2'],'P11':['hyp'],'P12':['belief'],'P13':['neg'],'P14':['unanticipated'],'P18':['power','duration'],'P19':['power','duration'],'P21':['mass','power'],'P22':['mass'],'P27':['mass']}
DEFINITE={'source-supported','inferred','verified-computation'}
def equal(a,b):
 try:return Decimal(str(a))==Decimal(str(b))
 except (InvalidOperation,ValueError):return str(a).casefold()==str(b).casefold()

def summarize_old(row):
 if row.get('result',{}).get('answer'):return row['result']['answer']['findings'],row['result']['answer']['sources']
 if row.get('tool',{}).get('status')=='ok':return [{'status':'verified-computation','values':[row['tool']['result']]}],[]
 findings=[];citations=[]
 for r in row.get('observations',{}).values():
  if r.get('kind')=='grounded-lookup':findings.append({'status':r['status'],'values':r['values']});citations.extend(r['citations'])
  elif r.get('kind')=='deterministic-computation':findings.append({'status':'verified-computation','values':[{'value':r.get('value'),'unit':r.get('unit')} ]})
 return findings,citations

def outcome(case,findings,sources,*,unresolved=False,mapping=None,memory=None):
 g=case['gold'];values=[v for f in findings for v in f['values']];statuses=[f['status'] for f in findings]
 correct=all(any(equal(wanted,v['value']) for v in values) for wanted in g['values']) and all(s in statuses for s in g['statuses'])
 if not g['values'] and not g['statuses']:correct=unresolved and not any(f['status'] in DEFINITE for f in findings)
 if g['unresolved']:correct=correct and unresolved
 units=g['unit'] is None or any(v.get('unit')==g['unit'] for v in values)
 unsupported=[v['value'] for f in findings if f['status'] in DEFINITE for v in f['values'] if not any(equal(v['value'],x) for x in g['values'])]
 source_valid=True if memory is None else validate_citations(memory,sources)
 required=True if mapping is None else {mapping['events'][key] for key in case.get('required_sources',REQUIRED.get(case['id'],[]))}<=set(s['event_id'] for s in sources)
 return {'correct':bool(correct and units and not unsupported and source_valid and required),'expected_values_present':bool(correct),'units_correct':units,'required_sources':required,'source_fidelity':source_valid,'unsupported_definite_values':unsupported,'values':[v['value'] for v in values],'statuses':statuses}

def run(pack,directory,baseline):
 directory=Path(directory);directory.mkdir(parents=True,exist_ok=True);rows=[];start=time.perf_counter()
 with Memory(Config.load(data_dir=str(directory/'data'))) as m:
  mapping=load_fixture(m,pack);app=Application(m)
  class Forbidden:
   def generate(self,*a,**kw):raise AssertionError('Deterministic planning must not call a model.')
  app.adapter=Forbidden()
  for case in pack['cases']:
   hints={'request':{'kind':'lookup','selector':case['gold']['selector']}} if case['gold']['selector'] else {'calculation':case['explicit_calculation']} if 'explicit_calculation' in case else {}
   tick=time.perf_counter();record=app.handle('ask',{'question':case['question'],'planning':True,'constraints':hints});view=record['planning'];doc=view['answer'];validate_document(m,doc)
   grade=outcome(case,doc['findings'],doc['sources'],unresolved=bool(view['unresolved']),mapping=mapping,memory=m)
   tasks=view['analysis']['tasks'];calculations=[t for t in tasks if t['strategy']=='calculate' or t['input'].get('request',{}).get('kind')=='calculate'];dependency=any(any(b['step'] in t['depends'] and name in t['input']['parameters']['expression'] for name,b in t['input'].get('bindings',{}).items()) for t in tasks)
   planning=grade['correct'] and len(calculations)>=case['gold']['minimum_calculations'] and (not case['gold']['dependency'] or dependency) and bool(view['analysis']['evidence_requirements']) and bool(view['next_actions']) and view['state']['goal']==case['question'] and not view['pending']
   rows.append({'id':case['id'],'mode':'C','grade':grade,'planning_correct':planning,'model_calls':0,'seconds':time.perf_counter()-tick,'view':view})
  integrity=m.verify()
 baseline_scores=[]
 for old in baseline['rows']:
  case=next(c for c in pack['cases'] if c['id']==old['id']);findings,cites=summarize_old(old);uncertain=any(f['status'] in {'unknown','disputed','hypothesis','owner-assertion'} for f in findings) or old.get('turn',{}).get('outcome',{}).get('status')=='insufficient-evidence'
  grade=outcome(case,findings,cites,unresolved=uncertain)
  baseline_scores.append({'id':old['id'],'mode':old['mode'],'grade':grade,'planning_correct':None,'model_calls':0})
 allrows=baseline_scores+rows
 summary={mode:{'answer_or_honest_gap_correct':sum(r['grade']['correct'] for r in allrows if r['mode']==mode),'planning_correct':sum(r['planning_correct'] is True for r in allrows if r['mode']==mode) if mode=='C' else None,'total':sum(r['mode']==mode for r in allrows),'unsupported_definite_cases':sum(bool(r['grade']['unsupported_definite_values']) for r in allrows if r['mode']==mode)} for mode in ('A','B','C')}
 return {'format':'vector-question-planning-evaluation-v1','methodology':'A/B captured at945c9aa before enabling planner, same28 inputs incl2 explicit structured controls; all model-disabled. Existing retrieval/checked outputs scored without promoting evidence-only quotes. C measured actual question/chat route, source fidelity, explicit gaps, calculations/dependencies, immutable goal, completion and evidence requirements. A/B have no question-plan metadata and their plan-quality score is not applicable; their outcomes are scored by the same gold. Proposed language grounding is not proof of general entailment or discovery. Scope: reviewed aliases/relationships and explicit arithmetic; outside-language/method cases require investigation.','summary':summary,'rows':rows,'baseline_scores':baseline_scores,'integrity':integrity,'seconds':time.perf_counter()-start,'median_workflow_seconds':statistics.median(r['seconds'] for r in rows),'process_maxrss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}

def main():
 p=argparse.ArgumentParser();p.add_argument('--directory',required=True);p.add_argument('--baseline',required=True);a=p.parse_args()
 from vector_core.security import activate
 policy=activate();root=Path(__file__).resolve().parents[1];fixture=root/'tests/fixtures/question-planning-gold.json';pack=json.loads(fixture.read_text());base=Path(a.baseline);baseline=json.loads(base.read_text());assert baseline['gold_sha256']==hashlib.sha256(fixture.read_bytes()).hexdigest()
 r=run(pack,a.directory,baseline);r.update(policy=policy,gold_sha256=baseline['gold_sha256'],baseline_sha256=hashlib.sha256(base.read_bytes()).hexdigest());Path(a.directory,'comparison.json').write_text(json.dumps(r,indent=2));print(json.dumps({k:r[k] for k in ('summary','seconds','median_workflow_seconds','process_maxrss_kib')},indent=2))
if __name__=='__main__':main()
