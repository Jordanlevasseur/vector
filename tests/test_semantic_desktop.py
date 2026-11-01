"""Actual opt-in desktop path, never a replacement model or simulated success."""
import json,os,subprocess,sys,unittest
from pathlib import Path

class SemanticDesktopTests(unittest.TestCase):
 def test_real_desktop_opt_in_and_new_session_default(self):
  if not os.environ.get('DISPLAY'):self.skipTest('No local display: connected-evidence GUI path not verified.')
  script=r'''
import argparse,json,tempfile,time
from pathlib import Path
from vector_core.desktop import bootstrap,Desktop
with tempfile.TemporaryDirectory() as directory:
 args=argparse.Namespace(data_dir=str(Path(directory)/'data'),choose_data=False,choose_models=False,models_directory=None,managed=False)
 root,client=bootstrap(args);app=Desktop(root,client);errors=[];app.dialog.showerror=lambda *a,**k:errors.append(a)
 def wait():
  end=time.monotonic()+15
  while client.pending and time.monotonic()<end:root.update();time.sleep(.02)
  assert not client.pending,'Desktop semantic request exceeded bounded wait'
 wait();assert app.semantic_enabled.get() is False
 app.call('learn',{'text':'Gauge N | reading | 8','scope':'fixture','exclusive':True});wait()
 event=app.last_response['result']['event']['event_id']
 app.call('claims',{'event_id':event});wait();claim=app.last_response['result']['items'][0]
 app.call('semantic_qualify',{'claim_id':claim['id'],'approved':True,'spec':{'sense':'equipment','status':'reviewed','epistemic':'source-assertion','polarity':'affirmed','reason':'Explicit fictional GUI acceptance fixture.'}});wait()
 app.semantic_enabled.set(True);app.question.insert(0,'Gauge N');app.send_chat();wait()
 record=app.last_response['result'];assert record['outcome']['status']=='evidence-only',record;assert record['context']['context']['semantic']['assertions'],record;assert not errors,errors
 app.call('semantic_answer',{'question':'Reading and missing mass','requests':[{'kind':'lookup','selector':{'subject':'Gauge N','sense':'equipment','predicate':'reading','scope':'fixture'}},{'kind':'lookup','selector':{'subject':'Gauge N','sense':'equipment','predicate':'mass','scope':'fixture'}}],'approved':True});wait()
 checked=app.last_response['result'];assert checked['answer']['summary']['partial'],checked
 app.checked_answer({'answer':checked['answer'],'notices':[]});assert 'Source reports:' in app.chat.get('1.0','end');assert 'Unknown or not completed' in app.chat.get('1.0','end')
 app.checked_results();wait();assert app.last_response['result']['items'];assert not errors,errors
 app.close();print(json.dumps({'passed':True,'default_disabled':True,'actual_connected_context':True}))
'''
  env={**os.environ,'PYTHONPATH':str(Path(__file__).resolve().parents[1]/'src'),'PYTHONDONTWRITEBYTECODE':'1'}
  child=subprocess.run([sys.executable,'-B','-c',script],env=env,capture_output=True,text=True,timeout=60)
  self.assertEqual(child.returncode,0,child.stderr);self.assertTrue(json.loads(child.stdout)['passed'])
