"""Actual native presentation, preserved backend work and unchanged offline guards."""
import json,os,subprocess,sys,unittest
from pathlib import Path

class DesktopStage1Tests(unittest.TestCase):
 def run_gui(self,body):
  if not os.environ.get('DISPLAY'):self.skipTest('Local display unavailable; redesigned UI runtime not verified.')
  setup='''
import argparse,json,time,tempfile,socket
from pathlib import Path
from vector_core.desktop import bootstrap,Desktop
from vector_core.desktop_shell import PRIMARY,SECONDARY
with tempfile.TemporaryDirectory() as folder:
 args=argparse.Namespace(data_dir=str(Path(folder)/'data'),choose_data=False,choose_models=False,models_directory=None,managed=False)
 root,client=bootstrap(args);app=Desktop(root,client);errors=[];app.dialog.showerror=lambda *a,**k:errors.append(a);s=app.shell
 def wait():
  end=time.monotonic()+30
  while client.pending and time.monotonic()<end:root.update();time.sleep(.01)
  root.update();assert not client.pending,'Bounded UI request timed out'
 wait()
'''
  script=setup+'\n'.join(' '+line for line in body.splitlines())+"\n assert not errors,errors\n app.close();print(json.dumps({'passed':True}))\n"
  env={**os.environ,'PYTHONPATH':str(Path(__file__).resolve().parents[1]/'src'),'PYTHONDONTWRITEBYTECODE':'1'}
  r=subprocess.run([sys.executable,'-B','-c',script],env=env,capture_output=True,text=True,timeout=100);self.assertEqual(r.returncode,0,r.stderr);self.assertTrue(json.loads(r.stdout)['passed'])
 def test_menu_keyboard_drafts_layout_animation_and_network_denial(self):
  self.run_gui(r'''
assert PRIMARY==('Home / Chat','Projects','History') and set(SECONDARY)=={'Library','Knowledge','Memory','Investigations','Settings','Advanced'}
assert s.hamburger.cget('text')=='☰' and not s.menu_open and not s.menu.winfo_ismapped()
assert app.planning_enabled.get() is False and app.semantic_enabled.get() is False
assert app.mode_catalog['available'] is False and 'runtime stopped' in s.model_state.get().lower()
assert all(w.winfo_class()!='TNotebook' for w in root.winfo_children())
app.question.insert(0,'An unsent\nmultiline draft');draft=app.question.get()
s.toggle_menu();root.update();assert s.menu.winfo_ismapped();s.menu_focus(1);s.hide_menu();assert not s.menu_open
s.toggle_menu();root.focus_force();root.update();s.menu.event_generate('<Escape>');root.update();assert not s.menu_open
for name in (*PRIMARY,*SECONDARY):
 s.navigate(name);wait();assert app.question.get()==draft;assert not s.menu_open
assert s.core.timer is None
s.navigate('Home / Chat');root.update();assert s.core.timer is not None
s.core.state(motion=False);assert s.core.timer is None
s.core.state(motion=True);assert s.core.timer is not None
root.geometry('820x600');root.update();assert app.question.winfo_ismapped();assert app.question.winfo_rooty()+app.question.winfo_height()<root.winfo_rooty()+root.winfo_height()
for family in (socket.AF_INET,socket.AF_INET6,socket.AF_UNIX):
 try:socket.socket(family,socket.SOCK_STREAM)
 except PermissionError:pass
 else:raise AssertionError('Redesign weakened network denial')
app.client.process.terminate();app.client.process.wait(timeout=5);app.poll();assert not s.core.busy and s.core.timer is None;assert 'unavailable' in app.status.get().lower()
''')
 def test_scroll_retains_reading_position_and_fixed_multiline_command(self):
  self.run_gui(r'''
for i in range(200):app.show_chat('Scroll fixture line '+str(i)+'\nReadable evidence remains visible.')
root.update();assert s.core.compact
app.chat.yview_moveto(.2);root.update();position=app.chat.index('@0,0');assert not s.follow
bar_y=app.question.winfo_rooty();app.show_chat('New scroll fixture line');root.update();assert app.chat.index('@0,0')==position
assert s.latest.winfo_ismapped();assert app.question.winfo_rooty()==bar_y
s.to_latest();root.update();assert app.chat.yview()[1]>.995
app.question.insert(0,'first');app.question.mark_set('insert','end-1c');app.question.focus_force();root.update();app.question.event_generate('<Shift-Return>');root.update();app.question.insert('insert','second');assert app.question.get()=='first\nsecond'
s.navigate('Projects');wait();s.navigate('Home / Chat');assert app.question.get()=='first\nsecond'
''')
 def test_actual_project_history_investigation_and_reduced_motion(self):
  self.run_gui(r'''
s.navigate('Projects');wait();app.project_name.insert(0,'UI acceptance project');app.create_project();wait();project=app.active_project;assert project
app.item_title.insert(0,'Preserved objective');app.item_body.insert('1.0','Investigate using evidence.');app.save_item();wait();app.project_items();wait();assert app.project_item_list.size()==1
s.navigate('Home / Chat');app.planning_enabled.set(True);app.question.insert(0,'Calculate 7 * 9.');app.question.focus_force();root.update();app.question.event_generate('<Return>');wait();record=app.last_response['result'];assert record['planning']['answer']['findings'][0]['values'][0]['value']=='63'
s.navigate('History');wait();assert s.history_rows[0]['conversation_id']==record['conversation_id'];assert s.history_rows[0]['created']==record['created'];assert s.history_rows[0]['id']==record['id']
s.history_list.selection_set('0');s.open_history();wait();assert s.current=='Home / Chat';assert '63' in app.chat.get('1.0','end')
s.navigate('Investigations');wait();assert s.investigations;s.investigation_list.selection_set(0);s.control_investigation('pause');wait();assert s.investigations[0]['status']=='paused';s.investigation_list.selection_set(0);s.control_investigation('resume');wait();assert s.investigations[0]['status']=='complete';s.investigation_list.selection_set(0);s.open_planned();wait();assert app.active_planning['planning']['id']==record['planning']['id']
s.toggle_options();root.update();assert s.options.winfo_ismapped();s.more_history.invoke();wait();assert 'items' in app.last_response['result']
s.navigate('Settings');s.reduced.set(True);s.core.state(motion=not s.reduced.get());s.navigate('Home / Chat');assert s.core.timer is None
''')

class AppearancePersistenceTests(unittest.TestCase):
 def test_strict_preference_survives_restart_restore_without_changing_model(self):
  import tempfile
  from vector_core.config import Config
  from vector_core.memory import Memory
  from vector_core.service import Application
  from vector_core.portable import export_vector,restore_vector
  from vector_core.persistence import put
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);config=Config.load(data_dir=str(root/'data'))
   with Memory(config) as memory:
    app=Application(memory);before=app.generation;self.assertIsNone(app.handle('health',{})['appearance']);app.handle('appearance_set',{'reduced_motion':True});self.assertEqual(app.generation,before)
    for p in ({'reduced_motion':1},{'reduced_motion':False,'model':'other'},{}):
     with self.assertRaises(ValueError):app.handle('appearance_set',p)
    with self.assertRaises(ValueError):put(memory,'preferences','appearance',{'reduced_motion':'false'})
    export_vector(memory,root/'archive')
   target=Config.load(data_dir=str(root/'restored'));restore_vector(target,root/'archive')
   for cfg in (config,target):
    with Memory(cfg) as memory:self.assertTrue(Application(memory).handle('health',{})['appearance']['reduced_motion']);self.assertIsNone(Application(memory).preference('generation'))
