"""Actual pipe protocol fixtures, never model/inference acceptance evidence."""
import json,subprocess,sys,time,unittest
from vector_core.runtime_supervisor import SupervisorProxy
from vector_core.inference import InferenceError

class SupervisorProtocolTests(unittest.TestCase):
    def proxy(self,script):
        p=subprocess.Popen([sys.executable,'-u','-c',script],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,bufsize=0)
        def cleanup():
            if p.poll() is None:p.terminate();p.wait(timeout=3)
            p.stdin.close();p.stdout.close()
        self.addCleanup(cleanup);return SupervisorProxy(p,'explicit-test.service',[])
    def test_remote_error_does_not_leave_phantom_pending_response(self):
        p=self.proxy("import sys,json\nfor raw in sys.stdin:\n r=json.loads(raw);bad=r['payload']['operation']=='fail';print(json.dumps({'id':r['id'],'ok':not bad,'result':{'error':'explicit fixture','code':'KERNEL_MEMORY_LIMIT'} if bad else {'stopped':True}}),flush=True)")
        with self.assertRaises(InferenceError) as c:p.call({'operation':'fail'},3)
        self.assertEqual(c.exception.code,'KERNEL_MEMORY_LIMIT');self.assertIsNone(p.abandoned)
        self.assertTrue(p.call({'operation':'stop'},3)['stopped'])
    def test_timeout_cancel_drains_original_reply_before_next_request(self):
        p=self.proxy("import sys,json\nr=json.loads(sys.stdin.readline());cancel=json.loads(sys.stdin.readline());assert cancel['payload']=={'operation':'cancel'};print(json.dumps({'id':r['id'],'ok':False,'result':{'error':'Cancelled fixture','code':'CANCELLED'}}),flush=True)\nr=json.loads(sys.stdin.readline());print(json.dumps({'id':r['id'],'ok':True,'result':{'stopped':True}}),flush=True)")
        with self.assertRaises(InferenceError) as c:p.call({'operation':'wait'},.1)
        self.assertEqual(c.exception.code,'INFERENCE_TIMEOUT');self.assertIsNotNone(p.abandoned)
        self.assertTrue(p.call({'operation':'stop'},3)['stopped']);self.assertIsNone(p.abandoned)
    def test_mismatched_response_and_excessive_frames_fail_closed(self):
        p=self.proxy("import sys,json\nr=json.loads(sys.stdin.readline());print(json.dumps({'id':r['id']+1,'ok':True,'result':{}}),flush=True)")
        with self.assertRaisesRegex(InferenceError,'protocol mismatch'):p.call({'operation':'status'},3)
        with self.assertRaisesRegex(InferenceError,'1MiB'):p._write({'x':'x'*(1024*1024)})
    def test_closed_control_pipe_is_diagnosed(self):
        p=self.proxy('pass');p.process.wait(timeout=3)
        with self.assertRaises(InferenceError):p.call({'operation':'status'},3)

    def test_missing_or_unsafe_store_does_not_hide_a_separate_approved_store(self):
        import tempfile
        from pathlib import Path
        from vector_core.runtime_supervisor import approved_stores
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)/'valid';(root/'blobs').mkdir(parents=True);(root/'manifests').mkdir()
            link=Path(folder)/'link';link.symlink_to(root,target_is_directory=True)
            available,errors=approved_stores([root,Path(folder)/'missing',link])
            self.assertEqual(available,[str(root)]);self.assertEqual(len(errors),2)
            self.assertTrue(all(e['compatible'] is False for e in errors))
