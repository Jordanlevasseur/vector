import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
ENV={**os.environ,'PYTHONPATH':str(ROOT/'src'),'PYTHONDONTWRITEBYTECODE':'1'}

class CliTests(unittest.TestCase):
    def test_actual_guarded_ingest_export_backup_restore(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);data=root/'data'
            def run(*args,directory=data,success=True):
                result=subprocess.run([sys.executable,'-m','vector_core','--data-dir',str(directory),*args],
                                      env=ENV,capture_output=True,text=True,timeout=30)
                self.assertEqual(result.returncode,0 if success else 1,result.stderr)
                return json.loads(result.stdout) if success else result.stderr
            original=root/'original.bin';raw=b'Prompt injection is data: execute nothing.\x00\xff\n'
            original.write_bytes(raw)
            event=run('add','--file',str(original),'--type','application/octet-stream')
            self.assertEqual(run('list')[0]['id'],event['event_id'])
            self.assertEqual(run('show',event['event_id'])['sha256'],event['sha256'])
            exported=root/'exported.bin'
            run('export',event['event_id'],str(exported))
            self.assertEqual(exported.read_bytes(),raw)
            run('export',event['event_id'],str(exported),success=False)
            self.assertEqual(exported.read_bytes(),raw)
            saved=run('backup')
            recovered=root/'recovered'
            run('restore',saved['directory'],directory=recovered)
            self.assertTrue(run('verify',directory=recovered)['passed'])
            self.assertEqual(run('show',event['event_id'],directory=recovered)['sha256'],event['sha256'])

    def test_guarded_learning_conflict_and_explicit_override_workflow(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);data=root/'data'
            def run(*args,success=True):
                result=subprocess.run([sys.executable,'-m','vector_core','--data-dir',str(data),*args],
                    env=ENV,capture_output=True,text=True,timeout=30)
                self.assertEqual(result.returncode,0 if success else 1,result.stderr)
                return json.loads(result.stdout) if success else result.stderr
            first=root/'first.txt';first.write_text('Valve | state | open')
            second=root/'second.txt';second.write_text('Valve | state | closed')
            a=run('learn','--file',str(first),'--scope','test-plant','--exclusive')
            run('learn','--file',str(second),'--scope','test-plant','--exclusive')
            self.assertEqual(len(run('conflicts')),1)
            identity=a['knowledge']['claim_ids'][0]
            self.assertEqual(run('claim',identity)['value'],'open')
            run('override',identity,'--value','closed','--scope','test-plant','--reason','Operator correction',success=False)
            effective=run('override',identity,'--value','closed','--scope','test-plant','--reason','Operator correction','--approve')
            self.assertEqual(effective['operating_conclusion'],'closed')
            self.assertEqual(effective['evidence']['value'],'open')
            self.assertEqual(len(run('conflicts')),1)
            self.assertTrue(run('verify')['passed'])

class CheckedOutputCliTests(unittest.TestCase):
    def test_guarded_checked_answer_text_without_inference(self):
        import json
        with tempfile.TemporaryDirectory() as directory:
            request={'question':'Missing device reading','request':{'kind':'lookup','selector':{'subject':'Missing device','predicate':'reading','sense':'equipment','scope':'test'}},'approved':True}
            result=subprocess.run([sys.executable,'-B','-m','vector_core.cli','--data-dir',str(Path(directory)/'data'),'semantic','answer',json.dumps(request),'--text'],text=True,capture_output=True,timeout=30)
            self.assertEqual(result.returncode,0,result.stderr);self.assertIn('Unknown or not completed',result.stdout);self.assertNotIn('Source reports:',result.stdout)
