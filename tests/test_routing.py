"""Independent arithmetic expectations and real application boundaries, no inference."""
import copy,json,tempfile,unittest
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4
from vector_core.config import Config
from vector_core.memory import Memory,Submission
from vector_core.service import Application
from vector_core.reasoning import request
from vector_core.assistant import materialize_response
from vector_core.investigation import Investigations
from vector_core.persistence import put
from vector_core.portable import validate_database,export_vector,restore_vector

class RoutingTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.cfg=Config.load(data_dir=str(self.root/'data'));self.m=Memory(self.cfg);self.addCleanup(lambda:self.m.close());self.app=Application(self.m)
 def ask(self,q,**kwargs):return self.app.handle('ask',{'question':q,**kwargs})
 def value(self,r):return Decimal(r['checked']['findings'][-1]['values'][0]['value'])
 def test_independent_numeric_gold_no_model_no_retrieval(self):
  cases=json.loads((Path(__file__).parent/'fixtures/routing_cases.json').read_text())
  with patch.object(Application,'prepare_inference',side_effect=AssertionError('No model required')),patch('vector_core.assistant.build_context',side_effect=AssertionError('No document retrieval for arithmetic')):
   for q,v in cases:
    with self.subTest(question=q):
     r=self.ask(q);self.assertEqual(r['outcome']['status'],'checked-calculation',r);self.assertEqual(self.value(r),Decimal(v));self.assertIsNone(r['outcome']['generation']);self.assertFalse(r['checked']['simulated'])
 def test_ambiguous_incomplete_unsupported_mixed_and_injection_fail_closed(self):
  for q in ('Calculate 1,2 + 3','Calculate 2(3+4)','Calculate sqrt(9)','Calculate 3 /','Calculate 2 + 2 and find evidence about motors','Calculate __import__("os").system("id") + 1','Calculate 4m + 2m','Calculate 2 ** 100','Calculate 1 / 0','Calculate 20 % 3','Calculate 25%200','Calculate 3 / 4%','Calculate 1,234,5678 + 1','Calculate 2 + 2 # also find information about motors.','Calculate 2 + 2, then','Calculate 2 + 2 and then'):
   with self.subTest(q=q):
    r=self.ask(q);self.assertNotIn('checked',r);self.assertIsNone(r['outcome']['answer']);self.assertIsNone(r['context']);self.assertIn(r['outcome']['status'],('needs-clarification','calculation-unresolved'))
 def test_date_not_silently_arithmetic(self):self.assertNotEqual(request('2026-11-02')['kind'],'calculate')
 def test_no_partial_execution_for_mixed_request(self):
  self.ask('Calculate 2 + 2; find electrical resistance')
  self.assertEqual(self.m.db.execute("SELECT count(*) FROM persistent_records WHERE contract='investigations'").fetchone()[0],0)
 def test_explicit_retrieval_is_subject_search_and_not_generation(self):
  e=self.m.ingest(Submission(b'Electrical resistance restricts electric current in a conductor.','Controlled source'))
  self.m.ingest(Submission(b'Find us at telephone 568 564; information about our office.','Unrelated telephone'))
  with patch.object(Application,'prepare_inference',side_effect=AssertionError('No neural retrieval')):r=self.ask('Find information about electrical resistance.')
  self.assertEqual(r['routing']['kind'],'retrieve');self.assertEqual(r['outcome']['status'],'evidence-only');self.assertEqual([s['event_id'] for s in r['context']['context']['sources']],[e['event_id']]);self.assertIsNone(r['outcome']['answer']);self.assertIn('source retrieval',r['outcome']['message'])
  token=uuid4().hex
  with patch('vector_core.assistant.build_context',side_effect=SystemExit('Controlled crash before source context')):
   with self.assertRaises(SystemExit):self.ask('What about it?',request_id=token)
  continued=self.ask('What about it?',request_id=token);self.assertTrue(continued['context']['context']['sources'])
 def test_missing_evidence_not_fabricated(self):
  r=self.ask('Find information about impossiblequuxsubject');self.assertEqual(r['outcome']['status'],'insufficient-evidence');self.assertFalse(r['context']['context']['sources'])
 def test_unavailable_model_honest_summary_and_investigation(self):
  for q,k in [('Sum up the Declaration of Independence.','summarize'),('Why might a small fan vibrate intermittently?','interpret')]:
   r=self.ask(q);self.assertEqual(r['routing']['kind'],k);self.assertEqual(r['outcome']['status'],'capability-unavailable');self.assertIsNone(r['outcome']['answer']);self.assertIsNone(r['outcome']['generation']);self.assertNotIn('checked',r)
 def test_repeat_idempotence_and_repeated_questions(self):
  token=uuid4().hex;r=self.ask('What is 6 times 7?',request_id=token);count=self.m.db.execute('SELECT count(*) FROM persistent_records').fetchone()[0];again=self.ask(r['question'],request_id=token);self.assertEqual(r['checked'],again['checked']);self.assertEqual(count,self.m.db.execute('SELECT count(*) FROM persistent_records').fetchone()[0]);self.assertEqual(self.value(self.ask(r['question'])),42)
  with self.assertRaises(ValueError):self.ask('What is 6 times 8?',request_id=token)
 def test_continuation_requires_immediate_checked_same_project(self):
  self.ask('Calculate 8 * 9');r=self.ask('Divide that by 8');self.assertEqual(self.value(r),9)
  self.assertIsNone(self.ask('What about it?')['context'])
  self.ask('Find information about a missing subject');r=self.ask('Divide that by 8');self.assertEqual(r['outcome']['status'],'calculation-unresolved')
  p=self.app.handle('project_create',{'name':'Distinct project'});self.app.handle('project_load',{'id':p['id']});self.assertNotIn('checked',self.ask('Divide that by 8'))
 def test_units_not_dropped_in_followup_or_chain(self):
  self.ask('Convert 2 km to m');r=self.ask('Divide that by 2');self.assertNotIn('checked',r)
  r=self.ask('Convert 2 km to m, then divide by 2');self.assertNotIn('checked',r);self.app.handle('history',{})
 def test_history_restart_replays_checked_values(self):
  r=self.ask('What is 568 times 564?');self.m.close();self.m=Memory(self.cfg);self.app=Application(self.m);items=self.app.handle('history',{})['items'];self.assertEqual(self.value(items[-1]),320352);self.assertEqual(items[-1]['checked'],r['checked'])
 def test_saved_question_project_and_value_tampering_rejected(self):
  r=self.ask('Calculate 6 * 7');saved={k:v for k,v in r.items() if k!='checked'}
  for field,value in [('question','Calculate 6 * 8'),('project_id',uuid4().hex)]:
   bad=copy.deepcopy(saved);bad[field]=value
   with self.subTest(field=field),self.assertRaises(ValueError):materialize_response(self.m,bad)
  with self.assertRaises(ValueError):put(self.m,'conversations',r['conversation_id']+':'+r['id'],r)
 def test_foreign_prior_reference_not_accepted(self):
  r=self.ask('Calculate 6 * 7');self.ask('Calculate 3 * 9');last=self.ask('Divide that by 3');saved={k:v for k,v in last.items() if k!='checked'};saved['calculation_ref']['prior_answer_record']=r['calculation_ref']['answer_record']
  with self.assertRaises(ValueError):materialize_response(self.m,saved)
 def test_interrupted_request_recovers_without_duplicate_or_unchecked_answer(self):
  token=uuid4().hex
  with patch.object(Investigations,'run',side_effect=RuntimeError('Controlled interruption')):
   with self.assertRaises(RuntimeError):self.ask('Calculate 12 * 13',request_id=token)
  pending=self.app.handle('history',{})['items'][-1];self.assertEqual(pending['outcome']['status'],'pending');self.assertNotIn('checked',pending)
  self.m.close();self.m=Memory(self.cfg);self.app=Application(self.m);r=self.ask('Calculate 12 * 13',request_id=token);self.assertEqual(self.value(r),156)
 def test_portable_restoration_revalidates_calculation_refs(self):
  self.ask('Calculate 6 * 7');self.ask('Divide that by 2');export_vector(self.m,self.root/'archive');cfg=Config.load(data_dir=str(self.root/'restored'));restore_vector(cfg,self.root/'archive')
  with Memory(cfg) as other:self.assertTrue(validate_database(other.db,other.config.data_dir)['passed']);self.assertEqual(self.value(Application(other).handle('history',{})['items'][-1]),21)
 def test_old_history_payload_preserved(self):
  key=uuid4().hex;record={'id':key,'conversation_id':self.app.session['conversation_id'],'project_id':None,'question':'Old interrupted request','outcome':{'status':'pending','answer':None,'generation':None,'errors':[]},'context':None};put(self.m,'conversations',record['conversation_id']+':'+key,record);self.ask('Calculate 2 + 3');self.assertEqual(self.app.handle('history',{})['items'][0],record)
 def test_late_relevant_passage_displaces_matching_frontmatter(self):
  body='Electrical handbook table of contents. '+('Preface background. '*60)+'Electrical resistance is opposition to current flow, measured in ohms. This passage is a controlled test source.'
  e=self.m.ingest(Submission(body.encode(),'Controlled late body'))
  r=self.ask('Find information about electrical resistance.');s=r['context']['context']['sources'][0];self.assertEqual(s['event_id'],e['event_id']);self.assertIn('opposition to current',s['quote']);self.assertGreater(s['start'],800);self.assertEqual(s['quote'],self.m.read_text_span(e['event_id'],s['start'],s['end']))
 def document(self,body):
  from test_literature import LiteraryTests
  from vector_core.literature import Library
  fixture=LiteraryTests.__new__(LiteraryTests);fixture.root=self.root;root,entry=fixture.fixture(body);lib=Library(self.m);edition=lib.import_entry(root,entry,approved=True)
  while lib.process(edition['event_id'])['status']!='complete':pass
  return edition
 def test_summary_complete_body_quote_is_not_summary_and_model_is_unverified(self):
  from vector_core.context import document_context
  from vector_core.assistant import respond
  from vector_core.inference import GenerationConfig,SimulatedAdapter
  self.document('An independently authored test assembly calls for shared maintenance, records its members and explains how decisions are made. This is fictional controlled material, not acquired historical knowledge.\n')
  q='Summarize Explicit test fixture 1';d=request(q);cfg=GenerationConfig(model='explicit-test-only',context_tokens=8192,output_tokens=512);ctx=document_context(self.m,q,d['query'],complete=True,budget_bytes=6000);self.assertTrue(ctx['context']['document']['complete_body_supplied']);source=ctx['context']['sources'][0];cite={k:source[k] for k in ('event_id','sha256','start','end','quote')}
  def output(kind,text):return json.dumps({'statements':[{'kind':kind,'text':text,'citations':[cite]}],'uncertainty':'Explicit simulated framework test; summary semantics not certified.','insufficient':False})
  for kind,text,status in [('source',source['quote'],'summary-unfulfilled'),('inference','The fictional assembly proposes shared upkeep and recorded decisions.','simulated-test-response')]:
   r=respond(self.m,q,decision=d,adapter=SimulatedAdapter([output(kind,text)]),config=cfg,conversation_id=self.app.session['conversation_id']);self.assertEqual(r['outcome']['status'],status);self.assertNotIn('checked',r)
  r=respond(self.m,q,decision=d,adapter=SimulatedAdapter(['not JSON','not JSON']),config=cfg,conversation_id=self.app.session['conversation_id']);self.assertEqual(r['outcome']['status'],'summary-unfulfilled');self.assertTrue(any('Repeated identical' in e for e in r['outcome']['errors']))
 def test_summary_budget_does_not_clip_essential_body_or_call_model(self):
  from vector_core.assistant import respond
  from vector_core.inference import GenerationConfig,SimulatedAdapter
  self.document('Independent fictional body about shared responsibility and duties. '*100);q='Summarize Explicit test fixture 1'
  r=respond(self.m,q,decision=request(q),adapter=SimulatedAdapter([]),config=GenerationConfig(model='explicit-test-only'),conversation_id=self.app.session['conversation_id']);self.assertEqual(r['outcome']['status'],'capability-unavailable');self.assertIsNone(r['outcome']['generation']);self.assertIn('No essential text',r['outcome']['message']);self.assertFalse(r['context']['context']['document']['excerpt_title_anchors'])
 def test_default_retrieval_retains_contradictory_evidence(self):
  from vector_core.knowledge import Knowledge,ClaimDraft
  for value in ('7','11'):
   body='Rotor speed is '+value+' rpm. This is explicitly fictional contradictory test material.';e=self.m.ingest(Submission(body.encode(),'Contradictory rotor fixture'));Knowledge(self.m).add_claim(ClaimDraft(e['event_id'],0,len(body),'Rotor','speed',value,'test','rpm','attribute',True))
  r=self.ask('Find information about Rotor speed');self.assertEqual(len(r['context']['context']['sources']),2);self.assertTrue(r['context']['context']['conflicts']);self.assertIsNone(r['outcome']['answer'])
 def test_owner_cancel_is_not_implicitly_resumed_by_retry(self):
  token=uuid4().hex
  def cancel(inv,identity,**kwargs):
   state=inv.get(identity);inv.control(identity,'cancel',state['revision'],approved=True);raise RuntimeError('Controlled interruption after explicit cancellation')
  with patch.object(Investigations,'run',cancel):
   with self.assertRaises(RuntimeError):self.ask('Calculate 17 * 19',request_id=token)
  r=self.ask('Calculate 17 * 19',request_id=token);self.assertEqual(r['outcome']['status'],'calculation-unresolved');self.assertIn('explicitly cancelled',r['outcome']['message']);self.assertNotIn('checked',r)

 def test_owner_pause_is_not_implicitly_resumed_by_retry(self):
  token=uuid4().hex
  def pause(inv,identity,**kwargs):
   state=inv.get(identity);inv.control(identity,'pause',state['revision'],approved=True);raise RuntimeError('Controlled interruption after explicit pause')
  with patch.object(Investigations,'run',pause):
   with self.assertRaises(RuntimeError):self.ask('Calculate 17 * 19',request_id=token)
  r=self.ask('Calculate 17 * 19',request_id=token);self.assertEqual(r['outcome']['status'],'calculation-unresolved');self.assertIn('explicitly paused',r['outcome']['message']);self.assertNotIn('checked',r)
 def test_summary_complete_bounds_recomputed_from_original(self):
  from vector_core.context import document_context
  from vector_core.projects import latest
  e=self.document('Independent fictional source with an opening proposition and a final qualification that must never be discarded in a complete summary. '*2)
  body=latest(self.m,'literary_analyses',e['event_id']);body.pop('revision');body['end']=body['start']+20;body['word_form_candidates']=[];put(self.m,'literary_analyses',e['event_id'],body)
  with self.assertRaisesRegex(ValueError,'immutable original'):document_context(self.m,'Summarize Explicit test fixture 1','Explicit test fixture 1',complete=True,budget_bytes=8192)

 def test_summary_finalization_crash_rejects_quote_on_saved_retry(self):
  from vector_core.assistant import respond
  from vector_core.context import document_context
  from vector_core.inference import GenerationConfig,SimulatedAdapter
  self.document('Independent fictional statement of shared duties and maintenance. This controlled source has enough words to test a complete body handoff without acquired documents.')
  q='Summarize Explicit test fixture 1';d=request(q);cfg=GenerationConfig(model='explicit-test-only',context_tokens=8192);ctx=document_context(self.m,q,d['query'],complete=True,budget_bytes=6000);source=ctx['context']['sources'][0];cite={k:source[k] for k in ('event_id','sha256','start','end','quote')};raw=json.dumps({'statements':[{'kind':'source','text':source['quote'],'citations':[cite]}],'uncertainty':'Controlled test','insufficient':False});token=uuid4().hex;calls=[]
  def interrupted(*args,**kwargs):
   calls.append(1)
   if len(calls)==3:raise RuntimeError('Controlled crash before summary finalization')
   return put(*args,**kwargs)
  with patch('vector_core.assistant.put',interrupted):
   with self.assertRaises(RuntimeError):respond(self.m,q,decision=d,adapter=SimulatedAdapter([raw]),config=cfg,conversation_id=self.app.session['conversation_id'],request_id=token)
  r=respond(self.m,q,decision=d,adapter=SimulatedAdapter([]),config=cfg,conversation_id=self.app.session['conversation_id'],request_id=token);self.assertEqual(r['outcome']['status'],'summary-unfulfilled');self.assertIsNone(r['outcome']['answer']);self.assertEqual(r['outcome']['generation']['text'],raw)

 def test_document_excerpt_starts_after_literal_title_not_publishing_preface(self):
  from vector_core.context import document_context
  preface='Publishing history for Explicit test fixture 1, a controlled fictional edition, not the work itself. This introductory paragraph describes how a digital copy was distributed and maintained.'
  body='The fictional assembly assigns shared maintenance and requires recorded decisions. This is the substantive controlled body and must be offered before editorial history.'
  self.document('Explicit test fixture 1\n\n'+preface+'\n\nExplicit test fixture 1\n\n'+body)
  result=document_context(self.m,'Summarize Explicit test fixture 1','Explicit test fixture 1');quotes=[s['quote'] for s in result['context']['sources']];self.assertTrue(quotes);self.assertIn(body,quotes[0]);self.assertFalse(any('Publishing history' in q for q in quotes));self.assertTrue(result['context']['document']['excerpt_title_anchors'])
  anchor=result['context']['document']['excerpt_title_anchors'][0];self.m.db.execute('UPDATE literary_units SET digest=? WHERE event_id=? AND ordinal=?',('0'*64,anchor['event_id'],anchor['ordinal']))
  with self.assertRaisesRegex(ValueError,'Corrupt title-anchor'):document_context(self.m,'Summarize Explicit test fixture 1','Explicit test fixture 1')
 def test_explicit_subject_title_preference_before_cross_domain_analogy(self):
  self.m.ingest(Submission(b'Electrical resistance is an analogy for this thermal network. This is controlled cross-domain fixture material.','Thermal handbook'))
  direct=self.m.ingest(Submission(b'Electrical circuits contain resistance. Applied voltage equals circuit current times circuit resistance in this controlled fixture.','Electrical science handbook'))
  r=self.ask('Find information about electrical resistance');self.assertEqual(r['context']['context']['sources'][0]['event_id'],direct['event_id']);self.assertIsNone(r['outcome']['answer'])
