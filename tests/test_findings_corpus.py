"""Blind output-level scoring over retained and new independent test premises."""
import importlib.util,json,sys,tempfile,unittest
from pathlib import Path
class CognitiveCorpusTests(unittest.TestCase):
 def test_original_and_unseen_checked_answers_without_model(self):
  root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'tools'));self.addCleanup(lambda:sys.path.remove(str(root/'tools')))
  from evaluate_stage6c import deterministic
  from evaluate_stage6b import read_corpus
  with tempfile.TemporaryDirectory() as tmp:
   result=deterministic(read_corpus(root/'tests/fixtures/stage6b-corpus.json'),json.loads((root/'tests/fixtures/stage6c-unseen.json').read_text()),tmp)
   self.assertEqual(len(result['rows']),52)
   for r in result['rows']:
    with self.subTest(case=r['id']):self.assertTrue(r['grade']['objective_passed'],r['grade'])
   self.assertTrue(result['integrity']['passed'])
