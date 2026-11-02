"""Frozen external answer and plan expectations, separate from production code."""
import json,sys,tempfile,unittest
from pathlib import Path
class PlanningCorpusTests(unittest.TestCase):
 def evaluate(self,name,total):
  root=Path(__file__).resolve().parents[1];old=sys.path[:];sys.path.insert(0,str(root/'tools'));self.addCleanup(lambda:sys.path.__setitem__(slice(None),old))
  from evaluate_question_planning import run
  pack=json.loads((root/'tests/fixtures'/name).read_text())
  with tempfile.TemporaryDirectory() as directory:result=run(pack,directory,{'rows':[]})
  self.assertEqual(result['summary']['C']['total'],total)
  for row in result['rows']:
   with self.subTest(case=row['id']):self.assertTrue(row['planning_correct'],row['grade'])
  self.assertTrue(result['integrity']['passed'])
 def test_twenty_eight_development_questions_without_model(self):self.evaluate('question-planning-gold.json',28)
 def test_eight_separate_transfer_questions_without_model(self):self.evaluate('question-planning-transfer.json',8)
