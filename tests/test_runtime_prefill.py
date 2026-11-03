import io
import unittest
from unittest.mock import patch
from vector_core.inference import GenerationConfig,COLLABORATION_SCHEMA
from vector_core.inference_worker import generation_payload,stream_generation


class PrefillTests(unittest.TestCase):
    def test_process_local_memory_policy_requires_confirmed_disable(self):
        from vector_core.inference_worker import configure_cpu_memory
        for responses in ([0,1],[1],[0,0]):
            with self.subTest(responses=responses),patch('vector_core.inference_worker.ctypes.CDLL') as load:
                load.return_value.prctl.side_effect=responses
                if responses==[0,1]:
                    configure_cpu_memory()
                    self.assertEqual(load.return_value.prctl.call_args_list[0].args,(41,1,0,0,0))
                    self.assertEqual(load.return_value.prctl.call_args_list[1].args,(42,0,0,0,0))
                else:
                    with self.assertRaisesRegex(RuntimeError,'huge-page'):configure_cpu_memory()

    def test_small_batch_preserves_complete_prompt_schema_and_limits(self):
        config=GenerationConfig('local-model:test',4096,192,300)
        prompt='Complete task and evidence: '+('untrusted source bytes '*80)
        payload=generation_payload(config,prompt,'collaboration-v1')
        self.assertEqual(payload['prompt'],prompt)
        self.assertEqual(payload['format'],COLLABORATION_SCHEMA)
        self.assertEqual(payload['keep_alive'],0)
        self.assertEqual(payload['options'],{'num_ctx':4096,'num_predict':192,'temperature':0,'seed':0,'num_thread':2,'num_batch':32,'use_mmap':True})
        self.assertNotIn('tools',payload)

    def test_thinking_is_measured_without_exposing_hidden_text(self):
        class Connection:
            sock=None
            def request(self,*args):pass
            def close(self):pass
            def getresponse(self):
                response=io.BytesIO(b'{"thinking":"hidden text","response":"","done":false}\n{"response":"{}","done":true}\n')
                response.status=200;return response
        with patch('vector_core.inference_worker.http.client.HTTPConnection',return_value=Connection()):
            result=stream_generation({'options':{'num_predict':32}},1)
        self.assertEqual(result['response'],'{}')
        self.assertEqual(result['thinking_bytes'],11)
        self.assertNotIn('thinking',result)
