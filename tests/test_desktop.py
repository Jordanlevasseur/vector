import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ENV={**os.environ,'PYTHONPATH':str(Path(__file__).resolve().parents[1]/'src'),'PYTHONDONTWRITEBYTECODE':'1'}

class DesktopTests(unittest.TestCase):
    def test_guarded_backend_actual_workflows_and_restart(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);data=root/'data'
            def session(commands):
                process=subprocess.Popen([sys.executable,'-m','vector_core.desktop_worker','--data-dir',str(data)],env=ENV,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
                responses=[]
                try:
                    for index,(operation,parameters) in enumerate(commands):
                        process.stdin.write(json.dumps({'id':str(index),'operation':operation,'parameters':parameters})+'\n');process.stdin.flush()
                        response=json.loads(process.stdout.readline());self.assertEqual(response['id'],str(index));responses.append(response)
                finally:
                    process.stdin.close();process.wait(timeout=15);errors=process.stderr.read();process.stdout.close();process.stderr.close()
                self.assertEqual(process.returncode,0,errors);return responses
            first=session([('health',{}),('project_create',{'name':'Restart project'}),('ingest',{'text':'Rotor speed is 30 rpm.'}),('ask',{'question':'Rotor speed'}),('tool',{'name':'arithmetic','parameters':{'expression':'2+2'}}),('shell',{'command':'id'}),('backup',{'directory':str(root/'backup')})])
            self.assertTrue(first[3]['ok']);self.assertEqual(first[3]['result']['outcome']['status'],'evidence-only')
            self.assertFalse(first[4]['ok']);self.assertFalse(first[5]['ok']);self.assertTrue(first[6]['ok'])
            restored=session([('history',{}),('verify',{}),('verify_backup',{'directory':str(root/'backup')}),('restore',{'directory':str(root/'backup'),'destination':str(root/'restored')})])
            self.assertEqual(restored[0]['result']['items'][0]['question'],'Rotor speed');self.assertTrue(restored[3]['result']['restored'])
    def test_actual_gui_and_narrow_display_profile(self):
        if not os.environ.get('DISPLAY'):self.skipTest('No local display; actual desktop startup not verified.')
        script=r'''
import argparse,json,tempfile,time,socket
from pathlib import Path
from vector_core.desktop import bootstrap,Desktop
with tempfile.TemporaryDirectory() as folder:
 args=argparse.Namespace(data_dir=str(Path(folder)/'data'),choose_data=False,choose_models=False,models_directory=None,managed=False)
 root,client=bootstrap(args);app=Desktop(root,client)
 errors=[];app.dialog.showerror=lambda *a,**k:errors.append(a)
 def wait():
  end=time.monotonic()+15
  while client.pending and time.monotonic()<end:root.update();time.sleep(.02)
  assert not client.pending,'GUI request timed out'
 wait()
 assert len(app.tabs)==6
 for family in (socket.AF_INET,socket.AF_INET6,socket.AF_UNIX):
  try:socket.socket(family,socket.SOCK_STREAM)
  except PermissionError:pass
  else:raise AssertionError('Frontend socket allowed')
 app.call('ingest',{'text':'Pump speed is 20 rpm.'});wait()
 app.question.insert(0,'Pump speed');app.send_chat();wait()
 assert app.last_response['result']['outcome']['status']=='evidence-only'
 app.run_tool();wait();assert app.last_response['result']['result']['value']=='4'
 assert not errors,errors
 app.close();print(json.dumps({'passed':True,'tabs':6,'frontend_socket_denial':True}))
'''
        child=subprocess.run([sys.executable,'-c',script],env=ENV,capture_output=True,text=True,timeout=45)
        self.assertEqual(child.returncode,0,child.stderr);self.assertTrue(json.loads(child.stdout)['passed'])

class DesktopStartupTests(unittest.TestCase):
    def test_invalid_data_location_reports_actionable_startup_error(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'file';path.write_text('unrelated file')
            child=subprocess.run([sys.executable,'-m','vector_core.desktop_worker','--data-dir',str(path)],input='',env=ENV,capture_output=True,text=True,timeout=10)
            self.assertEqual(child.returncode,1)
            result=json.loads(child.stdout);self.assertTrue(result['initialization_error']);self.assertTrue(result['result'])
