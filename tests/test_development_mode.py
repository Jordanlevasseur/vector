"""Manual operation and explicit resource policy; test adapters are simulated."""
from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace
import json,tempfile,time,unittest
from unittest.mock import patch
from test_response_pipeline import Responses,A,B
import test_dual_runtime as guards
from vector_core.config import Config
from vector_core.memory import Memory
from vector_core.service import Application
from vector_core.inference import GenerationConfig,InferenceError
from vector_core.worker_launcher import desktop_runtime,save_runtime_options,WorkerTransport

class DevelopmentModeTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
  self.memory=Memory(Config.load(data_dir=str(self.root/'data')));self.addCleanup(self.memory.close)
  self.app=Application(self.memory);self.raw=Responses();self.app.raw_adapter=self.raw;self.app.model_controller.raw=self.raw;self.app.prepare_model=lambda name:None
  s=self.app.model_controller.settings(discover=True);s['generation']=asdict(GenerationConfig('',4096,192,300));self.app.handle('model_mode_set',{'mode':'a','settings':s})
 def test_wrong_answer_and_decline_do_not_block_next_manual_request(self):
  self.raw.responses=iter(['5',"I'm sorry, but I can't assist with that request.",'Hello'])
  records=[self.app.handle('ask',{'question':q,'manual':True}) for q in ('2+2','How are you?','Hi')]
  for r in records:self.assertEqual(r['model_run']['status'],'complete');self.assertEqual(r['outcome']['evaluations']['functionality']['status'],'passed')
  self.assertEqual(records[0]['outcome']['evaluations']['accuracy']['status'],'contradicted-by-independent-calculation');self.assertEqual(records[0]['outcome']['errors'],[])
  health=self.app.handle('health',{});self.assertEqual(health['build_mode'],'development');self.assertFalse(health['release_ready']);self.assertFalse(health['evaluations']['production']['blocks_manual_operation'])
 def test_manual_complex_request_uses_one_real_adapter_call_and_frozen_selection(self):
  self.raw.responses=iter(['An experimental reply'])
  r=self.app.handle('ask',{'question':'Design a test for an unfamiliar material and then compare two possible explanations for its behavior.','manual':True})
  self.assertEqual(len(self.raw.calls),1);run=self.app.model_controller.get(r['model_run_ref']);self.assertEqual(run['workflow'],'direct')
  run['context']['manual_operation']=False
  from vector_core.persistence import put
  put(self.memory,'model_runs',run['id'],run)
  with self.assertRaisesRegex(ValueError,'workflow'):self.app.model_controller.get(run['id'])
 def test_runtime_options_require_explicit_acknowledgment_and_preserve_model_roots(self):
  path=self.root/'runtime.json';original={'model_directories':['/authorized/a','/authorized/b'],'memory_bytes':1536*1048576,'tasks':64};path.write_text(json.dumps(original));path.chmod(0o600)
  with self.assertRaises(PermissionError):save_runtime_options(path,memory_mib=2048,experimental=True)
  self.assertEqual(json.loads(path.read_text()),original)
  r=save_runtime_options(path,memory_mib=2048,experimental=True,acknowledged=True);self.assertTrue(r['restart_required']);saved=json.loads(path.read_text());self.assertEqual(saved['model_directories'],original['model_directories']);self.assertEqual(saved['tasks'],64);self.assertTrue(saved['experimental_memory']);self.assertEqual(path.stat().st_mode&0o777,0o600)
  with patch('vector_core.worker_launcher.launch',return_value='EXPLICIT FIXTURE') as launch:
   self.assertEqual(desktop_runtime(path),'EXPLICIT FIXTURE');self.assertTrue(launch.call_args.kwargs['experimental']);self.assertEqual(launch.call_args.kwargs['memory_bytes'],2048*1048576)
  for value in (0,1048577,True):
   with self.assertRaises(ValueError):save_runtime_options(path,memory_mib=value,experimental=True,acknowledged=True)
 def test_experimental_pressure_is_advisory_but_hard_stops_remain(self):
  for changed in ('pressure','swapout','reserve','swap','oom','monitor'):
   t=WorkerTransport(SimpleNamespace(poll=lambda:None),{'runtime_version':'fixture','cgroup':'/fixture','experimental_memory':True});t.resource_watch=guards.RuntimeGuardTests.monitor_watch();t.resource_watch['pressure_since']=80
   with patch.object(Path,'read_text',guards.RuntimeGuardTests.monitor_read(changed)),patch('vector_core.worker_launcher.time.monotonic',return_value=100):
    if changed in ('pressure','swapout'):t._check(110,None);self.assertTrue(t.resource_watch['experimental_advisories'])
    else:
     with self.assertRaises(InferenceError):t._check(110,None)
 def test_stopped_runtime_keeps_models_selectable_and_exact_reason_visible(self):
  self.app.transport=SimpleNamespace(qualified=False);self.app.installed_models=[{'name':A,'installed':True},{'name':B,'installed':True}];self.app.startup_error='Explicit test: private Ollama readiness timed out.'
  self.app.handle('model_mode_set',{'mode':'b'});catalog=self.app.handle('model_modes',{});self.assertEqual(catalog['mode'],'b');self.assertEqual(len(catalog['models']),2);self.assertFalse(catalog['available']);self.assertEqual(catalog['reason'],self.app.startup_error)
 def test_desktop_entry_point_uses_profile_even_with_explicit_data_directory(self):
  from vector_core.desktop import configure_startup
  profile=self.root/'.config/vector/local-inference.json';profile.parent.mkdir(parents=True);profile.write_text('{}')
  args=SimpleNamespace(data_dir='/private/data',no_inference=False,models_directory=None,managed=False,runtime_profile=None)
  with patch.object(Path,'home',return_value=self.root):configure_startup(args)
  self.assertEqual(args.runtime_profile,str(profile));args.no_inference=True;args.runtime_profile=None
  with patch.object(Path,'home',return_value=self.root):configure_startup(args)
  self.assertIsNone(args.runtime_profile)
 def test_actual_kernel_oom_evidence_is_reported_as_loading_failure(self):
  process=SimpleNamespace(stdin=tempfile.TemporaryFile(),stdout=tempfile.TemporaryFile(),poll=lambda:1)
  transport=WorkerTransport(process,{'runtime_version':'fixture','cgroup':'/fixture','memory_max':2048*1048576})
  with patch.object(Path,'read_text',return_value='oom_kill 1\nmax 2\noom 1\n'):
   with self.assertRaises(InferenceError) as failure:transport.request({'operation':'discover'},1)
  self.assertEqual(failure.exception.code,'KERNEL_MEMORY_LIMIT');self.assertIn('oom_kill=1',str(failure.exception))
 def test_old_startup_cancellation_is_not_a_new_request_cancellation(self):
  self.app.startup_error='Runtime startup was cancelled earlier.';self.raw.discover=lambda:{'available':False,'models':[]}
  self.raw.responses=iter(())
  r=self.app.handle('ask',{'question':'Hi','manual':True});self.assertEqual(r['model_run']['status'],'failed');self.assertEqual(r['outcome']['failure']['code'],'MODEL_UNAVAILABLE')
 def test_experimental_runtime_keeps_real_kernel_isolation_and_pids_limit(self):
  from vector_core.worker_launcher import launch
  roots=[self.root/'models-a',self.root/'models-b']
  for root in roots:(root/'blobs').mkdir(parents=True);(root/'manifests').mkdir()
  transport=launch(roots[0],additional_model_directories=[roots[1]],memory_bytes=512*1048576,tasks=32,experimental=True);self.addCleanup(transport.close)
  r=transport.report;self.assertTrue(r['experimental_memory']);self.assertEqual(r['memory_max'],512*1048576);self.assertEqual(r['pids_max'],32);self.assertEqual(r['memory_swap_max'],0);self.assertTrue(r['external_denied']);self.assertTrue(r['nested_userns_denied']);self.assertTrue(r['model_blobs_readonly'])
  probe=transport.request({'operation':'resource_probe'},15);self.assertTrue(probe['pids_exhaustion_denied']);self.assertGreater(probe['children_cleaned'],0)
 def test_startup_progress_does_not_consume_the_pending_request(self):
  from vector_core.desktop import Client
  stdin=tempfile.TemporaryFile();stdout=tempfile.TemporaryFile();self.addCleanup(stdin.close);self.addCleanup(stdout.close)
  stdout.write(b'{"startup_progress":"Verifying local files"}\n');stdout.seek(0)
  client=Client(SimpleNamespace(stdin=stdin,stdout=stdout,poll=lambda:None));observed=[];client.on_progress=observed.append;client.start('health',{},lambda r:None);pending=client.pending
  client.poll();self.assertEqual(observed[0]['phase'],'startup');self.assertEqual(client.pending,pending)

if __name__=='__main__':unittest.main()
