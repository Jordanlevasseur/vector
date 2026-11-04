"""Policy/control regression fixtures; these are explicitly simulated inference."""
from dataclasses import asdict
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from vector_core.config import Config
from vector_core.memory import Memory
from vector_core.service import Application
from vector_core.inference import GenerationConfig,InferenceError,checked_result,CHAT_FORMAT,chat_prompt
from vector_core.runtime_policy import MIB

SMALL='other/small:local';LARGE='other/large:q4'
def host(memory=4*1024*MIB):return {'physical_memory':memory,'effective_total':memory,'effective_available':memory-512*MIB,'effective_cores':2,'parent_pids_max':None,'fingerprint':'test-hardware'}
def models():return [{'name':name,'digest':hashlib.sha256(name.encode()).hexdigest(),'installed':True,'compatible':None,'weight_bytes':weight,'parameter_count':parameters,'context_length':32768} for name,weight,parameters in [(SMALL,400*MIB,500000000),(LARGE,1200*MIB,2000000000)]]
class Proxy:
    qualified=False
    managed=False
    report={}
    def __init__(self):self.boot={'models':models(),'hardware':host(),'experimental_authorized':False};self.starts=[];self.stops=0;self.runtime_version='SIMULATED-CONTROL'
    def ensure(self,plan):self.starts.append(plan);self.qualified=True;self.report={'memory_max':plan['memory_bytes'],'experimental_memory':False,'qualified':True,'simulated':True};return {'report':self.report}
    def request(self,payload,timeout,cancellation=None):
        if payload['operation']=='discover':return {'available':True,'models':self.boot['models'],'simulated':True}
        if payload['operation']=='inspect':return {'capabilities':['completion']}
        raise AssertionError('Fixture cannot perform real inference')
    def close(self):self.stops+=1;self.qualified=False
class Fixture:
    simulated=True
    def __init__(self,manager,responses):self.manager=manager;self.responses=iter(responses);self.calls=[]
    def discover(self):return {'available':True,'models':self.manager.models,'simulated':True}
    def generate(self,prompt,config,cancellation=None,*,response_kind=None):
        self.calls.append(config.model);value=next(self.responses)
        if isinstance(value,BaseException):raise value
        return checked_result(value,config,simulated=True,runtime='EXPLICIT TEST FIXTURE',model_version=next(m['digest'] for m in self.manager.models if m['name']==config.model))
class AdaptiveTests(unittest.TestCase):
    def setUp(self):
        folder=tempfile.TemporaryDirectory();self.addCleanup(folder.cleanup);self.memory=Memory(Config.load(data_dir=str(Path(folder.name)/'data')));self.addCleanup(self.memory.close)
        self.hardware=patch('vector_core.adaptive_runtime.hardware',return_value=host());self.hardware.start();self.addCleanup(self.hardware.stop)
        self.proxy=Proxy();self.app=Application(self.memory,self.proxy);self.app.prepare_model=lambda name:None
    def wire(self,values):
        f=Fixture(self.app.adaptive,values);self.app.raw_adapter=f;self.app.model_controller.raw=f;return f
    def run_fixture(self):
        result=self.app.handle('ask',{'question':'Hi','manual':True})
        self.assertIn('model_run_ref',result,result)
        return self.app.model_controller.get(result['model_run_ref'])
    def test_default_auto_generic_discovery_is_lazy_and_no_model_registration_required(self):
        self.assertTrue(self.app.adaptive.automatic());catalog=self.app.handle('model_modes',{})
        self.assertEqual({r['name'] for r in catalog['models']},{SMALL,LARGE});self.assertFalse(self.proxy.starts);self.assertFalse(catalog['adaptive']['runtime_qualified'])
        self.assertEqual(self.app.adaptive.selection(),{'mode':'auto'})
    def test_auto_fallback_freezes_complete_request_and_keeps_failed_evidence(self):
        f=self.wire([InferenceError('Actual cap fixture',code='KERNEL_MEMORY_LIMIT'),'Hi from smaller fixture'])
        run=self.run_fixture();self.assertEqual(run['status'],'complete');self.assertEqual(f.calls,[LARGE,SMALL]);self.assertIsNotNone(run['parent'])
        parent=self.app.model_controller.get(run['parent']);self.assertEqual(parent['status'],'failed');self.assertEqual(parent['prompt_sha256'],run['prompt_sha256']);self.assertEqual(parent['context'],run['context']);self.assertEqual(parent['turn_id'],run['turn_id'])
        self.assertTrue(all(s['generation']['simulated'] for s in run['steps']));self.assertGreaterEqual(self.proxy.stops,1)
    def test_manual_exact_identity_never_falls_back_after_runtime_failure(self):
        self.app.handle('runtime_selection_set',{'mode':'model','model':LARGE});f=self.wire([InferenceError('Cap fixture',code='KERNEL_MEMORY_LIMIT')])
        run=self.run_fixture();self.assertEqual(run['status'],'failed');self.assertEqual(f.calls,[LARGE]);self.assertIsNone(run['parent']);self.assertEqual(self.app.adaptive.selection()['model'],LARGE)
    def test_bad_answer_and_cancellation_never_trigger_fallback(self):
        for value,status in [('2 + 2 = 9','complete'),(InferenceError('Cancelled',code='CANCELLED'),'cancelled')]:
            with self.subTest(status=status):
                f=self.wire([value]);run=self.run_fixture();self.assertEqual(run['status'],status);self.assertEqual(len(f.calls),1)
    def test_recovery_is_bounded_and_next_request_is_not_disabled(self):
        f=self.wire([InferenceError('gone',code='WORKER_CLOSED'),InferenceError('gone again',code='WORKER_CLOSED'),InferenceError('cap',code='KERNEL_MEMORY_LIMIT')])
        run=self.run_fixture();self.assertEqual(run['status'],'failed');self.assertEqual(len(f.calls),3);self.assertEqual(self.app.adaptive.excluded,[])
        f=self.wire(['Genuine fixture next request']);self.assertEqual(self.run_fixture()['status'],'complete');self.assertEqual(len(f.calls),1)
    def test_manual_both_keeps_five_stages_and_generic_bindings(self):
        self.app.handle('runtime_selection_set',{'mode':'both'});settings=self.app.model_controller.settings();settings['generation']=asdict(GenerationConfig('',8192,192,300));self.app.model_controller.select('both',settings=settings)
        f=self.wire(['one','two','review one','review two','final']);run=self.run_fixture()
        self.assertEqual(run['status'],'complete');self.assertEqual(f.calls,[SMALL,LARGE,SMALL,LARGE,LARGE]);self.assertEqual(self.proxy.starts[0]['execution'],'sequential')
    def test_new_hardware_reassessed_and_unknown_manual_model_refused(self):
        with patch('vector_core.adaptive_runtime.hardware',return_value=host(1800*MIB)):
            settings=self.app.model_controller.settings();self.assertEqual(settings['bindings'],{'a':SMALL})
        with patch('vector_core.adaptive_runtime.hardware',return_value=host(16*1024*MIB)):
            self.assertEqual(self.app.model_controller.settings()['bindings'],{'a':LARGE})
        with self.assertRaises(ValueError):self.app.handle('runtime_selection_set',{'mode':'model','model':'not-installed:latest'})
    def test_insufficient_memory_catalog_remains_browsable_without_qualification(self):
        with patch('vector_core.adaptive_runtime.hardware',return_value=host(700*MIB)):
            catalog=self.app.handle('model_modes',{});self.assertFalse(catalog['available']);self.assertIn('RESOURCE_BLOCKED',catalog['reason']);self.assertFalse(self.proxy.starts)

    def test_auto_catalogue_keeps_manual_models_available_and_bound_distinctly(self):
        catalog=self.app.handle('model_modes',{})
        self.assertEqual(catalog['manual_settings']['bindings'],{'a':SMALL,'b':LARGE})
        self.assertTrue(all(row['available'] for row in catalog['modes']))
        saved=catalog['manual_settings'];saved['bindings']={'a':LARGE}
        self.assertEqual(self.app.adaptive.manual_settings(saved)['bindings'],{'a':LARGE,'b':SMALL})
        self.assertTrue(self.app.adaptive.automatic())
    def test_integrity_or_invalid_output_never_triggers_auto_substitution(self):
        for code in ('MODEL_INTEGRITY','QUALIFICATION_FAILED','INVALID_OUTPUT','OUTPUT_TRUNCATED'):
            with self.subTest(code=code):
                f=self.wire([InferenceError('Explicit rejection fixture',code=code)]);run=self.run_fixture()
                self.assertEqual(run['status'],'failed');self.assertEqual(len(f.calls),1);self.assertIsNone(run['parent'])

    def test_answer_header_uses_actual_generic_model_identity_in_auto_role_a(self):
        self.wire(['Hi from the selected fixture'])
        result=self.app.handle('ask',{'question':'Hi','manual':True})
        self.assertEqual(result['outcome']['status'],'simulated-test-response')
        self.assertIn(LARGE,result['outcome']['message']);self.assertNotIn('Qwen',result['outcome']['message'])

    def test_saved_manual_ceiling_is_enforced_but_auto_remains_hardware_adaptive(self):
        self.proxy.boot.update(manual_limit=700*MIB,tasks_limit=32)
        self.wire(['Hi from AUTO fixture']);self.assertEqual(self.run_fixture()['status'],'complete')
        self.assertGreater(self.proxy.starts[-1]['memory_bytes'],700*MIB);self.assertEqual(self.proxy.starts[-1]['selection'],'auto');self.assertEqual(self.proxy.starts[-1]['tasks'],32)
        self.app.handle('runtime_selection_set',{'mode':'model','model':SMALL});self.wire(['Hi from manual fixture']);self.assertEqual(self.run_fixture()['status'],'complete')
        self.assertLessEqual(self.proxy.starts[-1]['memory_bytes'],700*MIB);self.assertEqual(self.proxy.starts[-1]['selection'],'manual');self.assertEqual(self.proxy.starts[-1]['tasks'],32)

    def test_auto_context_expands_for_complete_question_without_truncation(self):
        from vector_core.inference import chat_messages
        fixture=self.wire(['A fixture response']);captured=[];original=fixture.generate
        def generate(prompt,config,*args,**kwargs):captured.append((prompt,config));return original(prompt,config,*args,**kwargs)
        fixture.generate=generate;question='Hi '+('amber '*300)
        result=self.app.handle('ask',{'question':question,'manual':True})
        self.assertEqual(result['outcome']['status'],'simulated-test-response');self.assertGreater(captured[0][1].context_tokens,2048);self.assertEqual(chat_messages(captured[0][0])[-1]['content'],question)
    def test_oversized_complete_request_fails_without_inference_or_truncation(self):
        fixture=self.wire([]);question='Hi '+('amber '*7000)
        with self.assertRaisesRegex(ValueError,'Invalid question'):self.app.handle('ask',{'question':question,'manual':True})
        self.assertEqual(fixture.calls,[])
        self.assertEqual(self.memory.db.execute("SELECT count(*) FROM persistent_records WHERE contract='conversations'").fetchone()[0],0)

    def test_actual_controller_exit_is_unavailable_without_hiding_installed_models(self):
        from unittest.mock import Mock
        self.proxy.process=Mock();self.proxy.process.poll.return_value=2;self.app.startup_error='EXACT controller exit fixture'
        catalog=self.app.handle('model_modes',{});self.assertFalse(catalog['available']);self.assertFalse(catalog['adaptive']['controller_alive']);self.assertEqual(catalog['adaptive']['reason'],'EXACT controller exit fixture');self.assertEqual({m['name'] for m in catalog['models']},{SMALL,LARGE});self.assertTrue(self.app.adaptive.automatic())
