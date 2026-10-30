import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from vector_core.config import Config
from vector_core.memory import Memory,Submission
from vector_core.projects import Projects
from vector_core.service import Application
from vector_core.memory_intelligence import recall,compare,links,link
from vector_core.context import build_context
from vector_core.knowledge import Knowledge,ClaimDraft
from vector_core.portable import export_vector,restore_vector,validate_database

class MemoryProjectTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        self.config=Config.load(data_dir=str(self.root/'data'));self.memory=Memory(self.config);self.addCleanup(self.memory.close)
        self.app=Application(self.memory);self.projects=Projects(self.memory)
    def project(self,name='Plant'):
        p=self.app.handle('project_create',{'name':name});self.app.handle('project_load',{'id':p['id']});return p
    def ingest(self,text,name='source'):return self.app.handle('ingest',{'text':text,'name':name})
    def test_many_project_reuse_archive_restart_and_full_portability(self):
        first=self.project('Thermal');event=self.ingest('Valve | state | open')
        second=self.project('Mechanical');self.app.handle('project_link',{'event_id':event['event_id'],'approved':True})
        self.assertEqual(self.memory.db.execute('SELECT count(*) FROM events').fetchone()[0],1)
        for project in (first,second):self.assertEqual(self.projects.sources(project['id'])['items'][0]['event_id'],event['event_id'])
        goal=self.projects.item(second['id'],'goal','Efficiency','Measure flow',evidence=[event['event_id']],approved=True)
        decision=self.projects.item(second['id'],'decision','Instrumentation','Use sensor',evidence=[event['event_id']],approved=True)
        self.app.handle('ask',{'question':'Valve state'});conversation=self.app.session['conversation_id']
        archived=self.projects.archive(second['id'],True,second['revision'],approved=True)
        self.assertTrue(self.projects.get(second['id'])['archived'])
        self.assertTrue(recall(self.memory,'Valve',project_id=second['id'],view='project')['items'])
        self.assertTrue(recall(self.memory,'Valve')['items'])
        self.projects.archive(second['id'],False,archived['revision'],approved=True)
        history=self.projects.history(second['id'])['items'];self.assertTrue(any(r['contract']=='project_items' for r in history))
        restarted=Application(self.memory);self.assertEqual(restarted.session['conversation_id'],conversation)
        export_vector(self.memory,self.root/'archive')
        config=Config.load(data_dir=str(self.root/'restored'));restore_vector(config,self.root/'archive')
        with Memory(config) as restored:
            app=Application(restored);self.assertEqual(app.session['project_id'],second['id'])
            self.assertEqual(restored.original(event['event_id']),b'Valve | state | open')
            self.assertEqual(Projects(restored).entries('project_items',second['id'])['items'][0]['id'],goal['id'])
            self.assertEqual(len(Projects(restored).sources(first['id'])['items']),1)
            self.assertTrue(app.handle('history',{})['items']);self.assertTrue(app.handle('learning_queue',{})['items'])
    def test_versions_optimistic_conflict_authorization_and_atomic_failure(self):
        p=self.project();task=self.projects.item(p['id'],'task','Test pump','Run controlled test',approved=True)
        with self.assertRaises(PermissionError):self.projects.item(p['id'],'task','No','No')
        done=self.projects.item(p['id'],'task','Test pump','Known result recorded',status='done',item_id=task['id'],revision=task['revision'],approved=True)
        with self.assertRaises(ValueError):self.projects.item(p['id'],'task','Test pump','Stale',item_id=task['id'],revision=task['revision'],approved=True)
        before=self.memory.db.execute('SELECT count(*) FROM persistent_records').fetchone()[0]
        self.memory.db.execute("CREATE TRIGGER fixture_abort BEFORE INSERT ON audit BEGIN SELECT RAISE(ABORT,'independent failure fixture'); END")
        with self.assertRaises(Exception):self.projects.item(p['id'],'task','Atomic','Must rollback',approved=True)
        self.memory.db.execute('DROP TRIGGER fixture_abort')
        self.assertEqual(self.memory.db.execute('SELECT count(*) FROM persistent_records').fetchone()[0],before)
        versions=[r for r in self.projects.history(p['id'])['items'] if r['contract']=='project_items']
        self.assertEqual([r['payload']['status'] for r in versions],['open','done'])
    def test_memory_views_chronology_source_filter_and_late_file_recall(self):
        p=self.project()
        with patch('vector_core.memory.now',return_value='2014-03-01T00:00:00.000000+00:00'):
            old=self.ingest('Preface. '*180+'Archived zinc sensor reports 42 pascals.','old log')
        self.ingest('Recent zinc sensor reports 19 pascals.','recent log')
        results=recall(self.memory,'zinc sensor',since='2010-01-01T00:00:00+00:00',until='2015-01-01T00:00:00+00:00')['items']
        self.assertEqual([r['event_id'] for r in results],[old['event_id']]);self.assertIn('42 pascals',results[0]['excerpt']);self.assertGreater(results[0]['start'],500)
        built=build_context(self.memory,'Archived zinc sensor',project_id=p['id'])['context']
        source=next(r for r in built['sources'] if r['event_id']==old['event_id'])
        self.assertEqual(self.memory.read_text_span(old['event_id'],source['start'],source['end']),source['quote'])
        self.assertEqual(recall(self.memory,'',source_id=old['source_id'])['items'][0]['event_id'],old['event_id'])
        proc=self.app.handle('learn',{'text':'Rotor | procedure | inspect bearing','scope':'lab'})
        self.assertEqual(recall(self.memory,'Rotor',view='semantic')['items'][0]['event_id'],proc['event']['event_id'])
        draft=ClaimDraft(proc['event']['event_id'],0,len('Rotor | procedure | inspect bearing'),'Rotor','procedure','inspect bearing','lab',kind='procedure')
        Knowledge(self.memory).add_claim(draft)
        self.assertTrue(recall(self.memory,'Rotor',view='procedural')['items'])
        self.assertTrue(recall(self.memory,'',view='episodic')['items'])
        self.assertTrue(recall(self.memory,'',view='project',project_id=p['id'])['items'])
    def test_duplicates_overlaps_relationships_and_revisions_remain_distinct(self):
        self.project();a=self.ingest('Copper wire carries current.');b=self.ingest('Copper wire carries current.');c=self.ingest('Copper wire has resistance.')
        compared=compare(self.memory,a['event_id']);self.assertEqual(compared['exact_duplicate_events'][0]['event_id'],b['event_id']);self.assertTrue(any(r['event_id']==c['event_id'] for r in compared['overlap_candidates']))
        with self.assertRaises(PermissionError):link(self.memory,a['event_id'],c['event_id'],'related','Related')
        link(self.memory,a['event_id'],c['event_id'],'related','Electrical and thermal research',approved=True)
        self.assertEqual(links(self.memory,c['event_id'])['items'][0]['event_id'],a['event_id'])
        self.assertEqual(self.memory.db.execute('SELECT count(*) FROM events').fetchone()[0],3)
        self.assertEqual(self.memory.db.execute('SELECT count(*) FROM blobs').fetchone()[0],2)
        revision=self.memory.ingest(Submission(b'Copper wire revised resistance.', 'revision',source_id=a['source_id'],parent_id=a['event_id']))
        versions=compare(self.memory,revision['event_id'])
        self.assertEqual(versions['parent_id'],a['event_id']);self.assertEqual(len(versions['source_versions']),2)
    def test_entity_cross_document_conflict_override_and_uncertainty(self):
        p=self.project()
        source=self.ingest('Turbine | uses | Coolant')
        Knowledge(self.memory).add_claim(ClaimDraft(source['event_id'],0,len('Turbine | uses | Coolant'),'Turbine','uses','Coolant','lab',kind='relationship'))
        a=self.app.handle('learn',{'text':'Coolant | phase | liquid','scope':'lab','exclusive':True})
        b=self.app.handle('learn',{'text':'Coolant | phase | gas','scope':'lab','exclusive':True})
        claim=a['knowledge']['claim_ids'][0]
        self.app.handle('override',{'claim_id':claim,'value':'liquid','scope':'lab','reason':'Explicit operating assumption','approved':True})
        self.app.handle('assess',{'claim_id':claim,'state':'disputed','confidence':0.25,'reason':'Sources disagree','approved':True})
        built=build_context(self.memory,'Turbine',project_id=p['id'],scope='lab',budget_bytes=16000)['context']
        self.assertTrue({source['event_id'],a['event']['event_id'],b['event']['event_id']}<={r['event_id'] for r in built['sources']})
        self.assertTrue(b['reconciliation']['review_needed'])
        self.assertTrue(built['conflicts']);self.assertTrue(built['unanswered_questions']);self.assertTrue(any(c['override'] for c in built['claims']))
        self.assertEqual(self.app.handle('assessment_history',{'claim_id':claim})['assessments'][0]['state'],'disputed')
        self.assertEqual(self.memory.original(b['event']['event_id']),b'Coolant | phase | gas')
    def test_old_conversations_resume_and_bounded_context_continuity(self):
        self.project();self.ingest('Neon pump flow is 9 L/s.');first=self.app.handle('ask',{'question':'Neon pump flow'})
        conversation=self.app.session['conversation_id'];self.app.handle('new_conversation',{})
        self.app.handle('conversation_resume',{'conversation_id':conversation})
        result=self.app.handle('ask',{'question':'What about it?'})
        self.assertEqual(result['context']['context']['continuity'][0]['question'],'Neon pump flow')
        self.assertTrue(result['context']['context']['sources'])
        self.assertEqual(len(recall(self.memory,view='working',conversation_id=conversation)['items']),2)
        self.assertTrue(self.app.handle('conversation_browse',{})['items'])
    def test_project_filter_explicit_global_recall_and_invalid_references(self):
        first=self.project('First');a=self.ingest('Lithium voltage log')
        second=self.project('Second');b=self.ingest('Lithium mass log')
        self.assertEqual({r['event_id'] for r in recall(self.memory,'Lithium')['items']},{a['event_id'],b['event_id']})
        self.assertEqual([r['event_id'] for r in recall(self.memory,'Lithium',view='project',project_id=second['id'])['items']],[b['event_id']])
        context=build_context(self.memory,'Lithium',project_id=second['id'])['context'];self.assertEqual(context['sources'][0]['event_id'],b['event_id']);self.assertEqual(len(context['sources']),2)
        for bad in ('../escape','0'*32):
            with self.assertRaises(ValueError):self.projects.link(first['id'],bad)
        with self.assertRaises(ValueError):self.projects.item(first['id'],'decision','Bad evidence','No such original',evidence=['0'*32],approved=True)
    def test_portable_validation_rejects_dangling_source_reference(self):
        p=self.project();event=self.ingest('Source')
        # An independently constructed invalid imported payload must fail closed.
        with self.assertRaises(ValueError):
            from vector_core.projects import validate_record
            validate_record(self.memory.db,'project_sources',p['id']+':'+'0'*32,{'project_id':p['id'],'event_id':'0'*32,'created':'fixture'})
        self.assertTrue(self.memory.verify()['passed'])

    def test_originals_take_priority_over_project_notes_under_small_context_budget(self):
        from vector_core.inference import GenerationConfig
        p=self.project();event=self.ingest('Valve state is open.')
        for i in range(4):self.projects.item(p['id'],'note','Valve note '+str(i),'Valve '*300,evidence=[event['event_id']],approved=True)
        result=self.app.handle('ask',{'question':'Valve state'})
        self.assertEqual(result['outcome']['status'],'evidence-only')
        self.assertEqual(result['context']['context']['sources'][0]['event_id'],event['event_id'])
        self.assertTrue(result['context']['context']['truncated'])
        self.assertIsNone(result['outcome']['generation'])

    def test_long_history_byte_pages_preserve_every_saved_turn(self):
        import copy
        from uuid import uuid4
        from vector_core.persistence import put
        self.project();self.ingest('Archive pump log')
        turn=self.app.handle('ask',{'question':'Archive pump'})
        expected={turn['id']}
        # Controlled large audit traces test framing without model simulation.
        for i in range(24):
            fixture=copy.deepcopy(turn);fixture['id']=uuid4().hex;fixture['trace']=[{'fixture_audit':'x'*50000}]
            put(self.memory,'conversations',self.app.session['conversation_id']+':'+fixture['id'],fixture);expected.add(fixture['id'])
        found=set();after=0;pages=0
        while True:
            result=self.app.handle('history',{'after':after})
            self.assertLess(len(json.dumps(result).encode()),1024*1024)
            if not result['items']:break
            found.update(item['id'] for item in result['items']);after=result['next_cursor'];pages+=1
        self.assertEqual(found,expected);self.assertGreater(pages,1)
        self.assertTrue(all('fixture_audit' not in json.dumps(r) for r in self.projects.history(self.app.session['project_id'])['items']))

    def test_bulk_association_is_authorized_atomic_idempotent_and_has_no_total_cap(self):
        p=self.project();events=[]
        for batch in range(2):events.extend(self.memory.ingest_batch([Submission(('Bulk '+str(batch)+' '+str(i)).encode(),'source') for i in range(64)]))
        ids=[event['event_id'] for event in events]
        with self.assertRaises(PermissionError):self.projects.link_many(p['id'],ids[:64])
        with self.assertRaises(ValueError):self.projects.link_many(p['id'],ids[:63]+['0'*32],approved=True)
        self.assertEqual(self.projects.sources(p['id'])['items'],[])
        self.projects.link_many(p['id'],ids[:64],approved=True);self.projects.link_many(p['id'],ids[64:],approved=True)
        self.projects.link_many(p['id'],ids[:64],approved=True)
        self.assertEqual(self.memory.db.execute("SELECT count(*) FROM persistent_records WHERE contract='project_sources'").fetchone()[0],128)
        first=self.projects.sources(p['id'],limit=100);second=self.projects.sources(p['id'],after=first['next_cursor'],limit=100)
        self.assertEqual(len(first['items'])+len(second['items']),128)
        self.assertEqual(self.memory.db.execute('SELECT count(*) FROM events').fetchone()[0],128)

    def test_complete_new_state_snapshot_preserves_all_versions_and_associations(self):
        first=self.project('Evidence lab');a=self.app.handle('learn',{'text':'Valve | state | open','scope':'plant','exclusive':True})
        b=self.app.handle('learn',{'text':'Valve | state | closed','scope':'plant','exclusive':True})
        claim=a['knowledge']['claim_ids'][0]
        self.app.handle('override',{'claim_id':claim,'value':'open','scope':'plant','reason':'Working assumption','approved':True})
        self.app.handle('assess',{'claim_id':claim,'state':'disputed','confidence':0.1,'reason':'Conflicting documents','approved':True})
        link(self.memory,a['event']['event_id'],b['event']['event_id'],'contradicts','Explicit same-scope comparison',approved=True)
        for kind in ('goal','requirement','note','decision','task','milestone','question','hypothesis'):
            record=self.projects.item(first['id'],kind,'Valve '+kind,'Determine Valve state',evidence=[a['event']['event_id']],confidence=0.2,approved=True)
            self.projects.item(first['id'],kind,'Valve '+kind,'Revised user record',evidence=record['evidence'],item_id=record['id'],revision=record['revision'],status='deferred',approved=True)
        self.app.handle('ask',{'question':'Valve state'})
        tables=('persistent_records','claims','assessments','assessment_evidence','overrides')
        expected={name:[tuple(r) for r in self.memory.db.execute('SELECT * FROM '+name+' ORDER BY rowid')] for name in tables}
        export_vector(self.memory,self.root/'complete')
        target=Config.load(data_dir=str(self.root/'complete-restored'));restore_vector(target,self.root/'complete')
        with Memory(target) as memory:
            for name in tables:self.assertEqual([tuple(r) for r in memory.db.execute('SELECT * FROM '+name+' ORDER BY rowid')],expected[name],name)
            self.assertTrue(links(memory,a['event']['event_id'])['items'])
            self.assertTrue(build_context(memory,'Valve',project_id=first['id'])['context'].get('project_records'))
            self.assertEqual(memory.original(b['event']['event_id']),b'Valve | state | closed')

class OrganizationCrashTests(unittest.TestCase):
    def test_actual_crash_during_version_write_rolls_back_and_preserves_original(self):
        with tempfile.TemporaryDirectory() as folder:
            data=str(Path(folder)/'data')
            script='''
import os,sys
from vector_core.security import activate
activate()
from vector_core.memory import Memory,Submission
from vector_core.config import Config
from vector_core.projects import Projects
import vector_core.projects as projects
with Memory(Config.load(data_dir=sys.argv[1])) as memory:
 event=memory.ingest(Submission(b'Permanent input','source'))
 p=Projects(memory).create('Crash test')
 projects.canonical=lambda value:os._exit(87)
 Projects(memory).item(p['id'],'task','Interrupted','No acknowledgement',approved=True)
'''
            env={**os.environ,'PYTHONPATH':str(Path(__file__).resolve().parents[1]/'src')}
            child=subprocess.run([sys.executable,'-c',script,data],env=env,capture_output=True,text=True,timeout=15)
            self.assertEqual(child.returncode,87,child.stderr)
            with Memory(Config.load(data_dir=data)) as memory:
                self.assertEqual(memory.db.execute("SELECT count(*) FROM persistent_records WHERE contract='project_items'").fetchone()[0],0)
                self.assertEqual(memory.db.execute('SELECT count(*) FROM events').fetchone()[0],1);self.assertTrue(memory.verify()['passed'])

    def test_actual_bulk_link_crash_cannot_publish_a_partial_association_batch(self):
        with tempfile.TemporaryDirectory() as folder:
            data=str(Path(folder)/'data')
            script='''
import os,sys
from vector_core.security import activate
activate()
from vector_core.memory import Memory,Submission
from vector_core.config import Config
from vector_core.projects import Projects
import vector_core.projects as module
with Memory(Config.load(data_dir=sys.argv[1])) as memory:
 p=Projects(memory).create('Atomic source batch')
 events=memory.ingest_batch([Submission(b'One','one'),Submission(b'Two','two')])
 original=module._insert
 def interrupted(*args,**kwargs):
  result=original(*args,**kwargs)
  os._exit(88)
 module._insert=interrupted
 Projects(memory).link_many(p['id'],[e['event_id'] for e in events],approved=True)
'''
            env={**os.environ,'PYTHONPATH':str(Path(__file__).resolve().parents[1]/'src')}
            child=subprocess.run([sys.executable,'-c',script,data],env=env,capture_output=True,text=True,timeout=15)
            self.assertEqual(child.returncode,88,child.stderr)
            with Memory(Config.load(data_dir=data)) as memory:
                self.assertEqual(memory.db.execute("SELECT count(*) FROM persistent_records WHERE contract='project_sources'").fetchone()[0],0)
                self.assertEqual(memory.db.execute('SELECT count(*) FROM events').fetchone()[0],2)
                self.assertTrue(memory.verify()['passed'])

class ProjectDesktopTests(unittest.TestCase):
    def test_actual_protected_project_learning_task_recall_and_backup_workflow(self):
        if not os.environ.get('DISPLAY'):self.skipTest('Local GUI access absent; actual project workflow not verified.')
        script=r'''
import argparse,json,tempfile,time,socket
from pathlib import Path
from vector_core.desktop import bootstrap,Desktop
with tempfile.TemporaryDirectory() as folder:
 args=argparse.Namespace(data_dir=str(Path(folder)/'data'),choose_data=False,choose_models=False,models_directory=None,managed=False)
 root,client=bootstrap(args);app=Desktop(root,client);errors=[]
 app.dialog.showerror=lambda *a,**k:errors.append(a)
 def wait():
  end=time.monotonic()+30
  while client.pending and time.monotonic()<end:root.update();time.sleep(.02)
  assert not client.pending,'UI request failed to finish'
 wait();app.project_name.insert(0,'Desktop research');app.create_project();wait()
 assert app.active_project
 app.learning.insert('1.0','Valve | state | open');app.learn_text();wait()
 event=app.last_response['result']['event']['event_id'];app.selected_event=event
 app.item_kind.set('task');app.item_title.insert(0,'Inspect valve');app.item_body.insert('1.0','Record evidence before deciding');app.save_item();wait()
 assert app.last_response['result']['evidence']==[event]
 app.project_items();wait();assert app.project_item_list.size()==1
 app.search.insert(0,'Valve');app.memory_view.set('project');app.recall_memories();wait();assert app.knowledge.get_children()
 app.question.insert(0,'Valve state');app.send_chat();wait();assert app.last_response['result']['outcome']['status']=='evidence-only'
 app.call('backup',{'directory':str(Path(folder)/'archive')});wait()
 app.call('verify_backup',{'directory':str(Path(folder)/'archive')});wait();assert app.last_response['result']['actual_restoration']
 for family in (socket.AF_INET,socket.AF_INET6,socket.AF_UNIX):
  try:socket.socket(family,socket.SOCK_STREAM)
  except PermissionError:pass
  else:raise AssertionError('Network allowed')
 assert not errors,errors
 app.close();print(json.dumps({'passed':True,'actual_project_workflow':True,'network_denied':True}))
'''
        env={**os.environ,'PYTHONPATH':str(Path(__file__).resolve().parents[1]/'src')}
        child=subprocess.run([sys.executable,'-c',script],env=env,capture_output=True,text=True,timeout=70)
        self.assertEqual(child.returncode,0,child.stderr);self.assertTrue(json.loads(child.stdout)['passed'])
