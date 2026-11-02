import json
import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

from vector_core.inference import InferenceError
from vector_core.worker_launcher import WorkerTransport,desktop_runtime

class ActualUnionWorkerTests(unittest.TestCase):
    def test_two_store_namespace_is_readonly_isolated_and_cleans_up(self):
        import shutil
        from vector_core.worker_launcher import launch
        for executable in ('ollama','bwrap','systemd-run'):
            if not shutil.which(executable):self.skipTest('Actual two-store qualification blocked: missing '+executable)
        with tempfile.TemporaryDirectory() as directory:
            roots=[Path(directory)/'a',Path(directory)/'b']
            for root in roots:
                (root/'blobs').mkdir(parents=True);(root/'manifests').mkdir()
            try:transport=launch(roots[0],additional_model_directories=[roots[1]])
            except InferenceError as error:
                if 'RESOURCE_BLOCKED' in str(error):self.skipTest(str(error))
                raise
            group=Path(transport.report['cgroup'])
            try:
                self.assertTrue(transport.report['model_blobs_readonly']);self.assertTrue(transport.report['external_denied']);self.assertTrue(transport.report['nested_userns_denied'])
                self.assertEqual(transport.report['memory_swap_max'],0);self.assertEqual(len(transport.model_directories),2)
                self.assertEqual(transport.request({'operation':'discover'},5)['models'],[])
            finally:transport.close()
            for _ in range(50):
                if not group.exists() or (group/'pids.current').read_text().strip()=='0':break
                time.sleep(.1)
            self.assertTrue(not group.exists() or (group/'pids.current').read_text().strip()=='0')

class OverlayTests(unittest.TestCase):
    def test_manifest_digest_aliases_and_conflicting_selectors(self):
        import hashlib
        from vector_core.models import runtime_files
        with tempfile.TemporaryDirectory() as directory:
            def store(root,name,weights):
                (root/'blobs').mkdir(parents=True)
                def blob(raw):
                    digest=hashlib.sha256(raw).hexdigest();(root/'blobs'/('sha256-'+digest)).write_bytes(raw)
                    return {'digest':'sha256:'+digest,'size':len(raw)}
                body=json.dumps({'config':blob(b'{}'),'layers':[blob(weights)]}).encode()
                manifest=root/'manifests/registry.ollama.ai/library'/name/'test';manifest.parent.mkdir(parents=True);manifest.write_bytes(body)
                return body
            a=Path(directory)/'a';b=Path(directory)/'b';raw_a=store(a,'model-a',b'EXPLICIT INERT A');raw_b=store(b,'model-b',b'EXPLICIT INERT B')
            overlay=runtime_files([a,b])
            for raw in (raw_a,raw_b):
                row=overlay['blobs/sha256-'+hashlib.sha256(raw).hexdigest()];self.assertEqual(row['path'].read_bytes(),raw)
            c=Path(directory)/'c';store(c,'model-a',b'EXPLICIT CONFLICT')
            with self.assertRaisesRegex(ValueError,'Conflicting'):runtime_files([a,c])

class RuntimeGuardTests(unittest.TestCase):
    def test_low_ram_uses_stricter_ceiling_with_explicit_notice(self):
        from types import SimpleNamespace
        with tempfile.TemporaryDirectory() as directory:
            profile=Path(directory)/'profile.json';profile.write_text(json.dumps({'model_directories':['/local/a','/local/b'],'memory_bytes':1610612736,'tasks':64}));profile.chmod(0o600)
            transport=SimpleNamespace(report={})
            with patch('vector_core.worker_launcher.launch',side_effect=[InferenceError('RESOURCE_BLOCKED: explicit low RAM fixture'),transport]) as launch:
                actual=desktop_runtime(profile)
                self.assertEqual(launch.call_args.kwargs['memory_bytes'],768*1024*1024);self.assertIn('oversized',actual.report['resource_notice']);self.assertEqual(actual.report['requested_memory_max'],1610612736)
    def test_private_startup_profile_accepts_only_fixed_paths_and_limits(self):
        with tempfile.TemporaryDirectory() as directory:
            profile=Path(directory)/'profile.json'
            profile.write_text(json.dumps({'model_directories':['/local/a','/local/b'],'memory_bytes':1610612736,'tasks':64}));profile.chmod(0o600)
            with patch('vector_core.worker_launcher.launch',return_value='EXPLICIT LAUNCH FIXTURE') as launch:
                self.assertEqual(desktop_runtime(profile),'EXPLICIT LAUNCH FIXTURE');launch.assert_called_once_with('/local/a',additional_model_directories=['/local/b'],memory_bytes=1610612736,tasks=64)
            profile.chmod(0o644)
            with self.assertRaisesRegex(InferenceError,'private'):desktop_runtime(profile)
    def test_startup_profile_rejects_symlink_and_command_options(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);profile=root/'profile.json';profile.write_text('{"command":"curl"}');profile.chmod(0o600)
            with self.assertRaises(InferenceError):desktop_runtime(profile)
            linked=root/'linked';linked.symlink_to(profile)
            with self.assertRaises(InferenceError):desktop_runtime(linked)
    def test_memory_monitor_stops_on_reserve_swap_oom_and_monitor_failure(self):
        class Process:
            def poll(self):return None
        for changed in ('reserve','swap','oom','swapout','monitor'):
            transport=WorkerTransport(Process(),{'runtime_version':'EXPLICIT TEST FIXTURE','cgroup':'/fixture'})
            transport.resource_watch={'next':0,'pressure_since':None,'swap_out_initial':0,'oom_initial':0,'samples':0,'peak_memory_bytes':0,'peak_swap_bytes':0,'max_full_pressure':0,'minimum_host_available':2**63}
            def read(path,*args,**kwargs):
                path=str(path)
                if changed=='monitor':raise OSError('Explicit failed monitor fixture')
                if path=='/proc/meminfo':return 'MemAvailable: '+('10' if changed=='reserve' else '2097152')+' kB\n'
                if path=='/proc/vmstat':return 'pswpout '+('40000' if changed=='swapout' else '0')+'\noom_kill '+('1' if changed=='oom' else '0')+'\n'
                if path=='/proc/pressure/memory':return 'full avg10=0.00 avg60=0 avg300=0 total=0\n'
                if path=='/fixture/memory.current':return '1000000'
                if path=='/fixture/memory.swap.current':return '4096' if changed=='swap' else '0'
                raise AssertionError(path)
            with self.subTest(changed=changed),patch.object(Path,'read_text',read),self.assertRaisesRegex(InferenceError,'RESOURCE_BLOCKED') as failure:transport._check(time.monotonic()+10,None)
            if changed!='monitor':self.assertGreater(failure.exception.resources['samples'],0)
            if changed=='swapout':self.assertIn('host swap-out exceeded',str(failure.exception))
            if changed=='reserve':self.assertIn('host available RAM below',str(failure.exception))

class ModeDesktopTests(unittest.TestCase):
    def test_actual_gui_mode_controls_backend_preferences_and_history(self):
        if not os.environ.get('DISPLAY'):self.skipTest('No local display; GUI mode switching not verified.')
        import subprocess,sys
        script=r'''
import argparse,json,tempfile,time
from pathlib import Path
from vector_core.desktop import bootstrap,Desktop
with tempfile.TemporaryDirectory() as folder:
 args=argparse.Namespace(data_dir=str(Path(folder)/'data'),choose_data=False,choose_models=False,models_directory=None,managed=False)
 root,client=bootstrap(args);app=Desktop(root,client);errors=[];app.dialog.showerror=lambda *a,**k:errors.append(a)
 def wait():
  end=time.monotonic()+30
  for _ in range(3):
   while client.pending and time.monotonic()<end:root.update();time.sleep(.01)
   root.update();time.sleep(.03)
  assert not client.pending,'GUI request timeout'
 wait();app.question.insert(0,'2+2');app.send_chat();wait()
 before=app.chat.get('1.0','end');app.question.insert(0,'retained draft')
 app.model_mode.set('Both Models');app.change_mode();wait()
 assert app.mode_catalog['mode']=='both';assert app.question.get()=='retained draft';assert app.chat.get('1.0','end')==before
 assert not app.mode_catalog['available'],'Test has no inference worker, never simulated as available'
 app.default_mode.set('Qwen 3.5 2B');app.save_default_mode();wait();assert app.mode_catalog['default_mode']=='b'
 app.call('history',{},lambda r:None);wait();assert app.last_response['result']['items'][0]['question']=='2+2'
 app.call('new_conversation',{},lambda r:None);wait();app.call('model_modes',{},app.mode_status);wait();assert app.mode_catalog['mode']=='b'
 assert not errors,errors
 app.close();print(json.dumps({'passed':True,'real_backend':True,'inference':False}))
'''
        env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','PYTHONPATH':str(Path(__file__).resolve().parents[1]/'src')}
        child=subprocess.run([sys.executable,'-c',script],env=env,capture_output=True,text=True,timeout=60)
        self.assertEqual(child.returncode,0,child.stderr);self.assertTrue(json.loads(child.stdout)['passed'])
