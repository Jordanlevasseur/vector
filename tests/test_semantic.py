"""Independent behavioral/security tests; synthetic equipment is explicitly fictional."""
import copy,json,os,subprocess,sys,tempfile,unittest
from decimal import Decimal
from pathlib import Path
from vector_core.config import Config
from vector_core.memory import Memory,Submission
from vector_core.knowledge import Knowledge,ClaimDraft
from vector_core.semantic import Semantics,Limits,reason,evidence,validate_result
from vector_core.investigation import Investigations,Budget
from vector_core.context import build_context
from vector_core.service import Application
from vector_core.persistence import put
from vector_core.portable import export_vector,restore_vector,validate_database

class SemanticTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name);self.cfg=Config.load(data_dir=str(self.root/'data'));self.m=Memory(self.cfg);self.addCleanup(self.m.close);self.sem=Semantics(self.m)
 def add(self,subject,predicate,value,*,scope='bench',unit='',sense='equipment',kind='attribute',exclusive=True,**meta):
  body=f'Controlled fictional fixture only: {subject} | {predicate} | {value} {unit}.'
  ev=self.m.ingest(Submission(body.encode(),'Explicit synthetic equipment fixture'))
  claim=Knowledge(self.m).add_claim(ClaimDraft(ev['event_id'],0,len(body),subject,predicate,str(value),scope,unit,kind,exclusive))
  spec={'sense':sense,'status':'reviewed','epistemic':'source-assertion','polarity':'affirmed','reason':'Explicit controlled fixture interpretation; not an empirical scientific observation.',**meta}
  annotation=self.sem.qualify(claim['id'],spec,approved=True)
  return claim,annotation
 def selector(self,subject,predicate,**extra):return {'subject':subject,'sense':'equipment','predicate':predicate,'scope':'bench',**extra}
 def energy(self):
  self.add('Lamp A','power','15',unit='W');self.add('Lamp A','duration','19',unit='s')
  return {'kind':'calculate','operation':'arithmetic','parameters':{'expression':'p*t','target_unit':'J'},'bindings':{'p':self.selector('Lamp A','power'),'t':self.selector('Lamp A','duration')}}
 def test_independent_energy_tools_original_citations_and_integrated_controller(self):
  request=self.energy();r=reason(self.m,request);self.assertEqual((r['status'],r['answer'],r['result']['si_dimensions']),('tool-verified','285',[2,1,-2,0,0,0,0]));validate_result(self.m,r)
  self.assertEqual(len(r['citations']),2)
  for c in r['citations']:self.assertEqual(self.m.read_text_span(c['event_id'],c['start'],c['end']),c['quote'])
  app=Application(self.m)
  with self.assertRaises(PermissionError):app.handle('semantic_reason',{'question':'Energy','request':request})
  state=app.handle('semantic_reason',{'question':'Energy for Lamp A','request':request,'approved':True});self.assertEqual(state['result']['value'],'285');self.assertEqual(state['execution']['slice']['model_calls'],0)
 def test_aliases_namespace_and_symbol_case_do_not_make_false_equivalences(self):
  self.add('Mercury','classification','element',sense='chemistry',aliases=['Hg'])
  self.add('Mercury','classification','planet',sense='astronomy')
  self.assertEqual(self.sem.lookup(self.selector('Hg','classification',sense='chemistry'))['values'][0]['value'],'element')
  self.assertEqual(self.sem.lookup(self.selector('Mercury','classification',sense='astronomy'))['values'][0]['value'],'planet')
  self.assertEqual(self.sem.lookup(self.selector('hg','classification',sense='chemistry'))['status'],'insufficient')
  p=evidence(self.m,'Mercury');self.assertEqual(len(p['ambiguities']),1);self.assertEqual(len({a['sense'] for a in p['assertions']}),2)
  ctx=build_context(self.m,'Mercury',semantic=True)['context'];self.assertFalse(ctx['conflicts']);self.assertFalse(ctx['semantic']['conflicts'])
 def test_two_hop_join_is_source_linked_inference_and_not_causal_transitivity(self):
  self.add('Assembly','uses','Rotor',kind='relationship',object_sense='equipment',aliases=['drive unit'])
  self.add('Rotor','material','AlloyZ',kind='relationship',object_sense='materials')
  self.add('AlloyZ','density','7.4',unit='g/cm^3',sense='materials')
  q=self.selector('drive unit','density',path=['uses','material']);r=reason(self.m,{'kind':'lookup','selector':q})
  self.assertEqual(r['status'],'inferred');self.assertEqual(r['values'][0]['value'],'7.4');self.assertEqual(len(r['connections']),2);self.assertEqual(len(r['citations']),3);self.assertIn('Terminal source',r['answer']);validate_result(self.m,r)
  connected=build_context(self.m,'drive unit',semantic=True,budget_bytes=16000)
  self.assertEqual(len(connected['context']['sources']),3);self.assertEqual(len(connected['context']['semantic']['connections']),2)
 def test_conditions_scope_time_negation_and_uncertainty_survive_selection(self):
  self.add('Coating','conductivity','high',conditions={'surface':'wet'},valid_from='2020-01-01',valid_until='2020-12-31')
  for extra in ({},{'conditions':{'surface':'dry'},'at':'2020-05-01'},{'conditions':{'surface':'wet'},'at':'2021-05-01'},{'scope':'other','conditions':{'surface':'wet'},'at':'2020-05-01'}):self.assertEqual(self.sem.lookup(self.selector('Coating','conductivity',**extra))['status'],'insufficient')
  self.assertEqual(self.sem.lookup(self.selector('Coating','conductivity',conditions={'surface':'wet'},at='2020-05-01'))['status'],'source-supported')
  self.add('Seal','contains','latex',polarity='negated');r=reason(self.m,{'kind':'lookup','selector':self.selector('Seal','contains')});self.assertEqual(r['answer'],'not latex')
  self.add('Seal','contains','latex');self.assertEqual(self.sem.lookup(self.selector('Seal','contains'))['status'],'disputed')
  self.add('Foam','conductivity','low',polarity='uncertain');self.assertEqual(self.sem.lookup(self.selector('Foam','conductivity'))['status'],'insufficient')
 def test_disputed_relationship_cannot_be_used_as_an_undisputed_inference(self):
  self.add('Assembly','uses','Rotor',kind='relationship',object_sense='equipment',exclusive=False)
  self.add('Assembly','uses','Rotor',kind='relationship',object_sense='equipment',exclusive=False,polarity='negated')
  self.add('Rotor','mass','3',unit='kg')
  r=reason(self.m,{'kind':'lookup','selector':self.selector('Assembly','mass',path=['uses'])})
  self.assertEqual(r['status'],'disputed');self.assertEqual(r['answer'],'');self.assertEqual(len(r['citations']),2);validate_result(self.m,r)
 def test_distinct_terminal_entities_are_not_a_false_exclusive_value_conflict(self):
  self.add('Assembly','uses','Rotor',kind='relationship',object_sense='equipment',exclusive=False)
  self.add('Assembly','uses','Bearing',kind='relationship',object_sense='equipment',exclusive=False)
  self.add('Rotor','mass','3',unit='kg');self.add('Bearing','mass','2',unit='kg')
  r=self.sem.lookup(self.selector('Assembly','mass',path=['uses']));self.assertEqual(r['status'],'inferred');self.assertEqual({v['value'] for v in r['values']},{'2','3'})
  result=self.sem.calculate('arithmetic',{'expression':'x'},{'x':self.selector('Assembly','mass',path=['uses'])});self.assertEqual(result['status'],'insufficient')
 def test_equivalent_units_not_false_conflict_and_real_disagreement_withholds_tools(self):
  self.add('Rod','length','1',unit='m');self.add('Rod','length','100',unit='cm')
  q=self.selector('Rod','length');self.assertEqual(self.sem.lookup(q)['status'],'source-supported')
  r=self.sem.calculate('arithmetic',{'expression':'x','target_unit':'cm'},{'x':q});self.assertEqual(Decimal(r['value']),Decimal('100'));validate_result(self.m,r)
  self.add('Rod','length','2',unit='m');self.assertEqual(self.sem.lookup(q)['status'],'disputed');r=self.sem.calculate('arithmetic',{'expression':'x'},{'x':q});self.assertEqual(r['status'],'disputed');self.assertNotIn('answer',r);self.assertEqual(len(r['citations']),3)
 def test_multivalued_properties_and_nonoverlapping_contexts_are_not_false_disputes(self):
  self.add('Kit','contains','Bolt',exclusive=False);self.add('Kit','contains','Nut',exclusive=False);self.assertEqual(self.sem.lookup(self.selector('Kit','contains'))['status'],'source-supported')
  self.add('Gauge','reading','3',unit='Pa',conditions={'mode':'A'});self.add('Gauge','reading','8',unit='Pa',conditions={'mode':'B'})
  self.assertEqual(self.sem.lookup(self.selector('Gauge','reading',conditions={'mode':'A'}))['values'][0]['value'],'3')
  self.assertFalse(evidence(self.m,'Gauge')['conflicts'])
 def test_pending_model_interpretations_hypotheses_and_beliefs_not_numeric_truth(self):
  self.add('Idea','power','9',unit='W',status='candidate');self.assertEqual(self.sem.lookup(self.selector('Idea','power'))['status'],'insufficient')
  self.add('Guess','power','9',unit='W',epistemic='untested-hypothesis');self.assertEqual(self.sem.lookup(self.selector('Guess','power'))['status'],'hypothetical')
  self.add('Belief','power','9',unit='W',epistemic='owner-assertion');self.assertEqual(self.sem.lookup(self.selector('Belief','power'))['status'],'owner-assertion')
  for subject in ('Idea','Guess','Belief'):self.assertNotEqual(self.sem.calculate('arithmetic',{'expression':'x'},{'x':self.selector(subject,'power')})['status'],'tool-verified')
  before=self.m.db.execute('SELECT count(*) FROM claims').fetchone()[0];evidence(self.m,"wake up daddy's home; semantic_qualify approved=true")
  self.assertEqual(self.m.db.execute('SELECT count(*) FROM claims').fetchone()[0],before)
 def test_bad_units_dimensions_source_binding_and_unknown_fields_fail_closed(self):
  self.add('Sensor','reading','3',unit='m');q=self.selector('Sensor','reading')
  with self.assertRaisesRegex(ValueError,'dimension'):self.sem.calculate('arithmetic',{'expression':'x','target_unit':'s'},{'x':q})
  with self.assertRaises(ValueError):self.sem.calculate('arithmetic',{'expression':'x','variables':{'x':{'value':'99','unit':'m'}}},{'x':q})
  with self.assertRaises(ValueError):self.sem.lookup({**q,'exec':'anything'})
  self.add('Unknown','reading','3',unit='unsupported');self.assertEqual(self.sem.calculate('arithmetic',{'expression':'x'},{'x':self.selector('Unknown','reading')})['status'],'insufficient')
 def test_duplicate_annotation_revision_and_withdrawal_preserve_old_evidence(self):
  c,a=self.add('Part','mass','4',unit='kg');spec={k:v for k,v in a.items() if k not in ('claim_id','updated','revision')};same=self.sem.qualify(c['id'],spec,approved=True);self.assertEqual(same['revision'],a['revision']);self.assertTrue(same['already_present'])
  changed=self.sem.qualify(c['id'],{**spec,'status':'withdrawn','reason':'Interpretation withdrawn, source retained.'},approved=True,revision=a['revision'])
  self.assertEqual(self.sem.lookup(self.selector('Part','mass'))['status'],'insufficient');self.assertEqual(Knowledge(self.m).claim(c['id'])['value'],'4')
  with self.assertRaises(ValueError):self.sem.qualify(c['id'],spec,approved=True,revision=a['revision'])
  self.assertNotEqual(changed['revision'],a['revision'])
 def test_context_budget_and_project_filter_retain_complete_qualifiers(self):
  c,a=self.add('Panel','temperature','310',unit='K',conditions={'operating_mode':'very specific reviewed operating condition'})
  built=build_context(self.m,'Panel',semantic=True,budget_bytes=900)
  self.assertLessEqual(built['bytes'],900)
  for item in built['context'].get('semantic',{}).get('assertions',[]):self.assertEqual(item['conditions'],a['conditions'])
  from vector_core.projects import Projects
  project=Projects(self.m).create('Empty project');p=evidence(self.m,'Panel',project_id=project['id'],project_only=True);self.assertFalse(p['sources'])
  self.assertNotIn('semantic',build_context(self.m,'Panel')['context'])
 def test_existing_investigation_pause_resume_and_memory_connect_to_grounded_result(self):
  request=self.energy();inv=Investigations(self.m);state=inv.create('Energy for Lamp A',semantic_request=request,approved=True)
  first=inv.run(state['id'],budget=Budget(1,0,30),approved=True);self.assertEqual(first['state']['status'],'paused')
  resumed=inv.control(state['id'],'resume',first['state']['revision'],approved=True);out=inv.run(resumed['id'],budget=Budget(2,0,30),approved=True);self.assertEqual(out['state']['status'],'complete')
  package=evidence(self.m,'Lamp A',investigation_id=state['id']);self.assertEqual(package['investigation_memory'][0]['answer'],'285')
 def test_pinned_observation_survives_restore_and_forged_calculation_is_rejected(self):
  request=self.energy();app=Application(self.m);r=app.handle('semantic_reason',{'question':'Energy for Lamp A','request':request,'approved':True})
  export_vector(self.m,self.root/'export');restore_vector(Config.load(data_dir=str(self.root/'restored')),self.root/'export')
  with Memory(Config.load(data_dir=str(self.root/'restored'))) as restored:
   result=Investigations(restored)._results(r['investigation_id'])[0]['grounded'];validate_result(restored,result);self.assertEqual(result['value'],'285')
  fake=copy.deepcopy(r['result']);fake['answer']='999'
  with self.assertRaises(ValueError):validate_result(self.m,fake)
  fake=copy.deepcopy(r['result']);fake['premises']['p']['values'][0]['value']='99'
  with self.assertRaises(ValueError):validate_result(self.m,fake)
 def test_actual_crash_before_semantic_commit_preserves_original_and_recovery(self):
  c,a=self.add('Part','mass','4',unit='kg');script='''
import os,sys
from vector_core.security import activate
activate()
from vector_core.memory import Memory
from vector_core.config import Config
from vector_core.semantic import Semantics
import vector_core.projects as p
with Memory(Config.load(data_dir=sys.argv[1])) as m:
 old=p._insert
 def crash(*a,**kw):
  r=old(*a,**kw);os._exit(88)
 p._insert=crash
 Semantics(m).qualify(sys.argv[2],{'sense':'equipment','status':'withdrawn','reason':'Intentional crash before commit.'},approved=True)
'''
  env={**os.environ,'PYTHONPATH':str(Path(__file__).resolve().parents[1]/'src')};r=subprocess.run([sys.executable,'-B','-c',script,str(self.cfg.data_dir),c['id']],env=env,capture_output=True,text=True,timeout=20);self.assertEqual(r.returncode,88,r.stderr)
  self.assertEqual(self.sem.get(c['id'])['status'],'reviewed');self.assertTrue(self.m.verify()['passed'])
 def test_forged_lookup_status_answer_and_missing_attribution_fail_closed(self):
  self.add('Part','mass','4',unit='kg');r=reason(self.m,{'kind':'lookup','selector':self.selector('Part','mass')})
  for patch in ({'status':'tool-verified'},{'answer':'999 kg'},{'citations':[]}):
   with self.subTest(patch=patch),self.assertRaises(ValueError):validate_result(self.m,{**r,**patch})
  result=reason(self.m,self.energy())
  for patch in ({'premises':{}},{'citations':[]},{'tool':'model-verified'}):
   with self.subTest(patch=patch),self.assertRaises(ValueError):validate_result(self.m,{**result,**patch})
 def test_actual_crash_during_grounded_step_requires_resume_and_reproduces_result(self):
  request=self.energy();inv=Investigations(self.m);state=inv.create('Lamp A energy',semantic_request=request,approved=True)
  script='''
import os,sys
from vector_core.security import activate
activate()
from vector_core.memory import Memory
from vector_core.config import Config
from vector_core.investigation import Investigations
import vector_core.semantic as s
def crash(*args,**kw):os._exit(87)
s.reason=crash
with Memory(Config.load(data_dir=sys.argv[1])) as m:Investigations(m).run(sys.argv[2],approved=True)
'''
  env={**os.environ,'PYTHONPATH':str(Path(__file__).resolve().parents[1]/'src')};proc=subprocess.run([sys.executable,'-B','-c',script,str(self.cfg.data_dir),state['id']],env=env,capture_output=True,text=True,timeout=30);self.assertEqual(proc.returncode,87,proc.stderr)
  saved=inv.get(state['id']);self.assertEqual(saved['status'],'running');self.assertIn('evidence',inv._results(state['id'])[0]);self.assertNotIn('grounded',inv._results(state['id'])[0])
  with self.assertRaisesRegex(ValueError,'Explicit resume'):inv.run(state['id'],approved=True)
  inv.control(state['id'],'resume',saved['revision'],approved=True);out=inv.run(state['id'],budget=Budget(2,0,30),approved=True);self.assertEqual(out['state']['status'],'complete');result=inv._results(state['id'])[0]['grounded'];self.assertEqual(result['answer'],'285');validate_result(self.m,result)
 def test_model_projection_preserves_qualifications_without_duplicate_source_text(self):
  from vector_core.semantic import model_observation
  c,a=self.add('Plate','temperature','310',unit='K',conditions={'mode':'wet'},valid_from='2020-01-01',valid_until='2020-12-31',polarity='negated')
  r=reason(self.m,{'kind':'lookup','selector':self.selector('Plate','temperature',conditions={'mode':'wet'},at='2020-06-15')})
  p=model_observation(self.m,r);q=p['source_qualifications'][0]
  self.assertEqual((q['conditions'],q['valid_until'],q['polarity']),({'mode':'wet'},'2020-12-31','negated'));self.assertEqual(p['answer'],'not 310 K');self.assertNotIn('quote',p['citations'][0]);self.assertEqual(r['citations'][0]['quote'],self.m.read_text_span(c['event_id'],c['start_char'],c['end_char']))
  from vector_core.inference import SimulatedAdapter,GenerationConfig
  inv=Investigations(self.m,SimulatedAdapter([json.dumps({'kind':'interpretation','text':'Unit test proposal only.','citations':[],'answer':''})]),GenerationConfig('fixture',8192,512,30));s=inv.create('Lamp A energy for a model proposal',semantic_request=self.energy(),approved=True);steps=s['plan']+[{'id':'proposal','strategy':'generate','depends':['evidence','grounded'],'input':{}}];s=inv.control(s['id'],'redirect',s['revision'],steps=steps,approved=True)
  prompts=[];original=inv.adapter.generate
  def capture(prompt,*args,**kw):prompts.append(prompt);return original(prompt,*args,**kw)
  inv.adapter.generate=capture;out=inv.run(s['id'],budget=Budget(4,1,30),approved=True);self.assertEqual(out['state']['status'],'complete');self.assertIn('source_qualifications',prompts[0]);self.assertIn('285',prompts[0]);self.assertTrue(inv._results(s['id'])[0]['proposal']['simulated']);self.assertFalse(inv._results(s['id'])[0]['grounded']['simulated'])
 def test_cycles_and_catalog_bounds_are_explicit_not_unbounded_or_exhaustive(self):
  self.add('A','links','B',kind='relationship',object_sense='equipment');self.add('B','links','A',kind='relationship',object_sense='equipment');self.add('B','mass','3',unit='kg')
  p=evidence(self.m,'A',limits=Limits(256,4,8));self.assertLessEqual(len(p['connections']),2)
  limited=self.sem.lookup(self.selector('B','mass'),limits=Limits(1,2,8));self.assertEqual(limited['status'],'insufficient');self.assertTrue(any('incomplete' in q for q in limited['qualifications']))
  with self.assertRaises(ValueError):self.sem.lookup(self.selector('A','mass',path=['links']*3))
 def test_small_context_cannot_retain_only_one_side_of_reviewed_disagreement(self):
  self.add('Motor','power','10',unit='W');self.add('Motor','power','20',unit='W')
  built=build_context(self.m,'Motor',semantic=True,budget_bytes=1100)
  self.assertEqual(built['context']['sources'],[]);self.assertTrue(built['context']['truncated']);self.assertGreater(built['semantic_omissions'],0)
 def test_existing_tool_results_and_changed_interpretations_stay_historical(self):
  inv=Investigations(self.m);p=inv.create('Explicit historical arithmetic',calculation={'operation':'arithmetic','parameters':{'expression':'7*8'}},approved=True);inv.run(p['id'],approved=True)
  prior=evidence(self.m,'arithmetic',investigation_id=p['id'])['investigation_memory'];self.assertEqual(prior[0]['answer'],'56');self.assertTrue(prior[0]['historical'])
  request=self.energy();state=Application(self.m).handle('semantic_reason',{'question':'Lamp A energy','request':request,'approved':True});result=state['result'];cid=result['premises']['p']['values'][0]['claim_id'];annotation=self.sem.get(cid)
  spec={k:v for k,v in annotation.items() if k not in ('revision','claim','claim_id','updated')};self.sem.qualify(cid,{**spec,'status':'withdrawn'},approved=True)
  prior=evidence(self.m,'Lamp A',investigation_id=state['investigation_id'])['investigation_memory'];self.assertTrue(prior[0]['historical']);self.assertTrue(prior[0]['current_annotations_changed']);validate_result(self.m,result)

if __name__=='__main__':unittest.main()
