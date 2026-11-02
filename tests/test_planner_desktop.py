"""Actual protected desktop question entry and saved-plan path, no neural fixture."""
import os,json,subprocess,sys,unittest
from pathlib import Path
class PlanningDesktopTests(unittest.TestCase):
 def test_real_question_entry_plan_and_saved_history(self):
  if not os.environ.get('DISPLAY'):self.skipTest('Local display unavailable; planner GUI not verified.')
  script=r'''
import argparse,json,tempfile,time
from pathlib import Path
from vector_core.desktop import bootstrap,Desktop
with tempfile.TemporaryDirectory() as t:
 args=argparse.Namespace(data_dir=str(Path(t)/'data'),choose_data=False,choose_models=False,models_directory=None,managed=False)
 root,client=bootstrap(args);app=Desktop(root,client);errors=[];app.dialog.showerror=lambda *a,**k:errors.append(a)
 def wait():
  end=time.monotonic()+25
  while client.pending and time.monotonic()<end:root.update();time.sleep(.02)
  assert not client.pending,'Bounded desktop planner wait exceeded'
 wait();assert app.planning_enabled.get() is False
 app.planning_enabled.set(True);app.question.insert(0,'Calculate (16 + 9) * 2.');app.send_chat();wait()
 result=app.last_response['result'];assert result['planning']['completion']['findings_complete'],result;assert '50' in app.chat.get('1.0','end');assert app.active_planning
 app.load_history();wait();assert app.last_response['result']['items'][-1]['planning']['answer'];assert not errors,errors
 app.close();print(json.dumps({'passed':True,'default_unchanged':True,'actual_no_model_chat':True,'history':True}))
'''
  root=Path(__file__).resolve().parents[1];env={**os.environ,'PYTHONPATH':str(root/'src'),'PYTHONDONTWRITEBYTECODE':'1'};r=subprocess.run([sys.executable,'-B','-c',script],capture_output=True,text=True,env=env,timeout=90);self.assertEqual(r.returncode,0,r.stderr);self.assertTrue(json.loads(r.stdout)['passed'])
