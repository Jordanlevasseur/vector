from pathlib import Path
import tempfile
import unittest
from vector_core.config import Config
from vector_core.memory import Memory
from vector_core.service import Application
from vector_core.portable import export_vector,restore_vector

class ApplicationTests(unittest.TestCase):
    def test_actual_subsystems_project_restart_errors_and_portability(self):
        with tempfile.TemporaryDirectory() as folder:
            base=Path(folder);config=Config.load(data_dir=str(base/'data'))
            with Memory(config) as memory:
                app=Application(memory)
                project=app.handle('project_create',{'name':'Pump research'})
                app.handle('project_load',{'id':project['id']});conversation=app.session['conversation_id']
                event=app.handle('ingest',{'text':'Pump speed is 20 rpm.'})
                result=app.handle('ask',{'question':'Pump speed'})
                self.assertEqual(result['outcome']['status'],'evidence-only')
                self.assertFalse(app.handle('models',{})['available'])
                self.assertEqual(app.handle('search',{'query':'Pump'})[0]['event_id'],event['event_id'])
                self.assertIn('20 rpm',app.handle('show',{'event_id':event['event_id']})['preview'])
                with self.assertRaises(ValueError):app.handle('shell',{'command':'id'})
                with self.assertRaises(PermissionError):app.handle('tool',{'name':'arithmetic','parameters':{'expression':'2+2'}})
                self.assertEqual(app.handle('tool',{'name':'arithmetic','parameters':{'expression':'2+2'},'approved':True})['result']['value'],'4')
                query="EXPLAIN QUERY PLAN SELECT rowid,payload FROM persistent_records WHERE contract='conversations' AND substr(record_key,1,32)=? AND rowid>? ORDER BY rowid LIMIT 100"
                detail=' '.join(row[3] for row in memory.db.execute(query,(conversation,0)))
                self.assertIn('conversation_cursor',detail);self.assertNotIn('TEMP B-TREE',detail)
                export_vector(memory,base/'archive')
            with Memory(config) as memory:
                app=Application(memory);self.assertEqual(app.session['project_id'],project['id']);self.assertEqual(app.session['conversation_id'],conversation)
                self.assertEqual(app.handle('history',{})['items'][0]['question'],'Pump speed')
                app.handle('project_load',{'id':project['id']});self.assertEqual(app.session['conversation_id'],conversation)
            target=Config.load(data_dir=str(base/'restored'));restore_vector(target,base/'archive')
            with Memory(target) as memory:
                app=Application(memory);self.assertEqual(app.session['project_id'],project['id'])
                self.assertEqual(app.handle('history',{})['items'][0]['question'],'Pump speed')
                self.assertEqual(memory.original(event['event_id']),b'Pump speed is 20 rpm.')

class LauncherTests(unittest.TestCase):
    def test_launcher_uses_fixed_executable_and_real_actions(self):
        from vector_core.install_desktop import launcher_text
        text=launcher_text('/private/vector/bin/vector-desktop')
        self.assertIn('Exec="/private/vector/bin/vector-desktop"',text)
        for option in ('--choose-models','--managed','--choose-data'):self.assertIn(option,text)
        self.assertNotIn('sh -c',text)

class ProposalReviewTests(unittest.TestCase):
    def test_review_returns_exact_original_before_explicit_application(self):
        with tempfile.TemporaryDirectory() as folder:
            with Memory(Config.load(data_dir=str(Path(folder)/'data'))) as memory:
                app=Application(memory);event=app.handle('ingest',{'text':'Pump | speed | 20 rpm'})
                draft={'event_id':event['event_id'],'start':0,'end':len('Pump | speed | 20 rpm'),'subject':'Pump','predicate':'speed','value':'20 rpm','scope':'lab'}
                proposal=app.handle('propose',{'drafts':[draft],'origin':'EXPLICIT TEST FIXTURE'})
                summary=app.handle('proposals',{})
                self.assertEqual(summary['items'][0]['id'],proposal['id'])
                detail=app.handle('proposal_detail',{'id':proposal['id']})
                self.assertEqual(detail['original_quotes'][0]['quote'],'Pump | speed | 20 rpm')
                with self.assertRaises(PermissionError):app.handle('approve_proposal',{'id':proposal['id']})
                self.assertEqual(app.handle('approve_proposal',{'id':proposal['id'],'approved':True})['status'],'applied')
