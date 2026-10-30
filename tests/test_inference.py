import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from vector_core.inference import GenerationConfig,InferenceError,Cancellation,OllamaAdapter
from vector_core.worker_launcher import WorkerTransport,launch
from vector_core.models import validate_layout

class TransportTests(unittest.TestCase):
    def transport(self,script):
        process=subprocess.Popen([sys.executable,'-c',script],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,bufsize=0)
        transport=WorkerTransport(process,{'runtime_version':'EXPLICIT TRANSPORT FIXTURE'})
        self.addCleanup(transport.close);return transport
    def test_crash_timeout_cancellation_and_malformed_output_fail_closed(self):
        for script,timeout in [('import sys;sys.exit(3)',1),('import time;time.sleep(5)',.1),('print("malformed",flush=True)',1),('print("x"*1048577,flush=True)',1)]:
            with self.subTest(script=script):
                transport=self.transport(script)
                with self.assertRaises(InferenceError):transport.request({'operation':'fixture'},timeout)
                self.assertFalse(transport.qualified);self.assertIsNotNone(transport.process.poll())
        transport=self.transport('import time;time.sleep(5)');cancel=Cancellation();cancel.cancel()
        with self.assertRaisesRegex(InferenceError,'Cancelled'):transport.request({},1,cancel)
    def test_local_adapter_checks_actual_token_usage_and_completion(self):
        class Fixture:
            qualified=True;runtime_version='explicit fixture'
            def request(self,*args):return {'done':True,'response':'{}','prompt_eval_count':1900,'model_digest':'fixture'}
        config=GenerationConfig(model='fixture',context_tokens=2048,output_tokens=256)
        with self.assertRaises(InferenceError):OllamaAdapter(Fixture()).generate('prompt',config)
        Fixture.qualified=False
        with self.assertRaises(InferenceError):OllamaAdapter(Fixture())
    def test_model_selector_escape_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/'blobs').mkdir();(root/'manifests').mkdir();(root/'manifests-v2').mkdir()
            (root/'manifests-v2'/'escape').symlink_to('/etc/passwd')
            with self.assertRaises(ValueError):validate_layout(root)

class ActualWorkerTests(unittest.TestCase):
    def test_actual_empty_worker_namespace_limits_process_exhaustion_and_cleanup(self):
        for tool in ('ollama','bwrap','systemd-run'):
            if not shutil.which(tool):self.skipTest('Actual local inference qualification blocked: missing '+tool)
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/'blobs').mkdir();(root/'manifests').mkdir()
            try:transport=launch(root)
            except InferenceError as error:
                if 'RESOURCE_BLOCKED' in str(error):self.skipTest(str(error))
                raise
            cgroup=Path(transport.report['cgroup'])
            try:
                self.assertTrue(transport.report['external_denied']);self.assertTrue(transport.report['nested_userns_denied'])
                self.assertTrue(transport.report['model_blobs_readonly']);self.assertTrue(transport.report['host_home_absent'])
                self.assertEqual(transport.request({'operation':'discover'},5)['models'],[])
                probe=transport.request({'operation':'resource_probe'},10)
                self.assertTrue(probe['pids_exhaustion_denied']);self.assertGreater(probe['children_cleaned'],0)
            finally:transport.close()
            import time
            for _ in range(30):
                if not cgroup.exists() or (cgroup/'pids.current').read_text().strip()=='0':break
                time.sleep(.05)
            self.assertTrue(not cgroup.exists() or (cgroup/'pids.current').read_text().strip()=='0','Inference descendants survived cleanup')
