"""Real Tk controls, guarded backend and durable original-reading state."""
import os,subprocess,sys,unittest
from pathlib import Path

class ResourceDesktopTests(unittest.TestCase):
    def test_native_library_controls_complete_text_and_durable_reopen(self):
        if not os.environ.get('DISPLAY'):self.skipTest('No local X11 display; actual Library controls unverified.')
        script=r'''
import argparse,json,socket,tempfile,time
from pathlib import Path
from vector_core.desktop import bootstrap,Desktop
with tempfile.TemporaryDirectory() as folder:
 args=argparse.Namespace(data_dir=str(Path(folder)/'data'),choose_data=False,choose_models=False,models_directory=None,managed=False,no_inference=True,runtime_profile=None)
 root,client=bootstrap(args);app=Desktop(root,client);lib=app.library;errors=[];app.dialog.showerror=lambda *a,**k:errors.append(a);app.simple.askstring=lambda *a,**k:'Owner bookmark'
 def wait():
  end=time.monotonic()+30
  while time.monotonic()<end:
   root.update();time.sleep(.02)
   if not client.pending and not lib.queue and lib.timer is None and lib.save_timer is None:break
  assert not client.pending and not lib.queue,'Library operation timed out'
  assert not errors,errors
 wait();app.call('ingest',{'text':'CHAPTER I\n'+'Complete preserved original line.\n'*1100+'\nCHAPTER II\nNeedle at the end.','name':'GUI original.txt'});wait();event=app.last_response['result']['event_id']
 app.shell.nav['Library'].invoke();wait();assert lib.listing.get_children()
 lib.query.insert(0,'GUI original');lib.search_button.invoke();wait();lib.listing.selection_set('0');lib.open_button.invoke();wait();assert lib.kind=='text' and len(lib.text.get('1.0','end-1c'))>8000
 lib.next_button.invoke();wait();assert lib.offset==16000
 lib.bookmark();wait();lib.back_button.invoke();wait();lib.listing.selection_set('0');lib.open_button.invoke();wait();assert lib.offset==16000
 lib.find_entry.insert(0,'Needle');lib.find_button.invoke();wait();assert lib.offset>16000 and lib.text.get('1.0','end-1c').startswith('Needle')
 app.call('resource_bookmarks',{'id':event},lambda r:None);wait();assert len(app.last_response['result']['items'])==1
 root.geometry('820x600');root.update()
 for w in (lib.back_button,lib.next_button,lib.find_button):assert w.winfo_ismapped() and w.winfo_rootx()+w.winfo_width()<=root.winfo_rootx()+root.winfo_width()
 for family in (socket.AF_INET,socket.AF_INET6,socket.AF_UNIX):
  try:s=socket.socket(family,socket.SOCK_STREAM)
  except PermissionError:pass
  else:s.close();raise AssertionError('Library allowed network access')
 app.close()
print('native-library-controls-passed')
'''
        env={**os.environ,'PYTHONPATH':str(Path(__file__).resolve().parents[1]/'src'),'PYTHONDONTWRITEBYTECODE':'1'}
        result=subprocess.run([sys.executable,'-B','-c',script],env=env,capture_output=True,text=True,timeout=120)
        self.assertEqual(result.returncode,0,result.stderr+'\n'+result.stdout);self.assertIn('native-library-controls-passed',result.stdout)
    def test_library_startup_is_explicitly_model_independent(self):
        from types import SimpleNamespace
        from vector_core.desktop import configure_startup
        args=SimpleNamespace(library=True,no_inference=False,models_directory=None,managed=False,runtime_profile=None)
        configure_startup(args);self.assertTrue(args.no_inference);self.assertIsNone(args.runtime_profile)

if __name__=='__main__':unittest.main()
