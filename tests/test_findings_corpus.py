"""Blind output-level scoring over retained and new independent test premises."""
import importlib.util,json,sys,tempfile,unittest
from pathlib import Path
class CognitiveCorpusTests(unittest.TestCase):
 def test_original_and_unseen_checked_answers_without_model(self):
  root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'tools'));self.addCleanup(lambda:sys.path.remove(str(root/'tools')))
  from evaluate_stage6c import deterministic,merge_corpora
  from evaluate_stage6b import read_corpus
  original=read_corpus(root/'tests/fixtures/stage6b-corpus.json');unseen=json.loads((root/'tests/fixtures/stage6c-unseen.json').read_text());combined=merge_corpora(original,unseen)
  self.assertEqual(len(combined['sources']),len(original['sources'])+len(unseen['sources']));self.assertEqual(len({x['key'] for x in combined['sources']}),len(combined['sources']))
  from vector_core.config import Config
  from vector_core.memory import Memory
  from evaluate_stage6b import load_fixture
  with tempfile.TemporaryDirectory() as merge_dir,Memory(Config.load(data_dir=str(Path(merge_dir)/'data'))) as memory:
   mapping=load_fixture(memory,combined);self.assertEqual(len(mapping['claims']),len(combined['claims']))
  with tempfile.TemporaryDirectory() as tmp:
   result=deterministic(read_corpus(root/'tests/fixtures/stage6b-corpus.json'),json.loads((root/'tests/fixtures/stage6c-unseen.json').read_text()),tmp)
   self.assertEqual(len(result['rows']),52)
   for r in result['rows']:
    with self.subTest(case=r['id']):self.assertTrue(r['grade']['objective_passed'],r['grade'])
   self.assertTrue(result['integrity']['passed'])

 def test_cancelled_live_run_preserves_guard_failure_and_defers_cleanup_verdict(self):
  import contextlib,io
  from types import SimpleNamespace
  from unittest.mock import patch
  from vector_core.config import Config
  from vector_core.memory import Memory
  from vector_core.inference import InferenceError
  root=Path(__file__).resolve().parents[1];driver=root/'tools/evaluate_stage6b_live.py';prefix=driver.read_text().split('\nmemory=None\ntry:',1)[0];old_path=sys.path[:]
  try:
   with tempfile.TemporaryDirectory() as tmp,Memory(Config.load(data_dir=str(Path(tmp)/'data'))) as memory:
    args=[str(driver),'--corpus',str(root/'tests/fixtures/stage6b-corpus.json'),'--directory',str(Path(tmp)/'run'),'--models-directory',str(Path(tmp)/'unused')]
    namespace={'__name__':'explicit_cancellation_fixture','__file__':str(driver)}
    with patch.object(sys,'argv',args):exec(compile(prefix,str(driver),'exec'),namespace)
    from evaluate_stage6b import load_fixture
    pack=json.loads((root/'tests/fixtures/stage6c-unseen.json').read_text());mapping=load_fixture(memory,pack);recording=SimpleNamespace(prompts=[],raw=None)
    class CancelledFixture:
     def generate(self,prompt,*a,**kw):
      recording.prompts.append(prompt);namespace['cancel'].cancel();raise InferenceError('Explicit cancelled test fixture; no actual model called.')
    namespace.update(memory=memory,corpus=pack,recording=recording,adapter=CancelledFixture(),transport=SimpleNamespace(qualified=True),monitor=SimpleNamespace(is_alive=lambda:True),rows=[{'processes':[{'runner':True}]}])
    with contextlib.redirect_stdout(io.StringIO()):namespace['run_cell']('A',pack['cases'][0],mapping)
    row=namespace['report']['results'][0];self.assertIsNone(row['runner_unloaded']);self.assertIn('Cancelled',row['unload_status']);self.assertIn('cancelled test fixture',row['error']);self.assertFalse(row['model_grade']['objective_passed'])
  finally:sys.path[:]=old_path
