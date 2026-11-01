"""Independent frozen gold questions, never used as production reasoning rules."""
import importlib.util,tempfile,unittest
from pathlib import Path

class ExternalSemanticCorpusTests(unittest.TestCase):
 def test_forty_external_gold_cases_through_service_controller(self):
  root=Path(__file__).resolve().parents[1]
  spec=importlib.util.spec_from_file_location('stage6b_gold',root/'tools/evaluate_stage6b.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
  corpus=module.read_corpus(root/'tests/fixtures/stage6b-corpus.json')
  with tempfile.TemporaryDirectory() as directory:
   result=module.deterministic(corpus,Path(directory)/'evaluation')
   self.assertEqual(len(result['rows']),40)
   for row in result['rows']:
    with self.subTest(case=row['id']):self.assertTrue(row['C']['objective_passed'],row)
   self.assertTrue(result['integrity']['passed'],result['integrity'])
