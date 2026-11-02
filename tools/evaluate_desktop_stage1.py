"""Native desktop acceptance, screenshots and bounded idle measurements. Offline.

Supervisor captures the existing X11 window; VECTOR retains its unchanged
preconnected-display policy. No model, production data or external assets used.
"""
import argparse,json,os,subprocess,sys,time,struct
from pathlib import Path

GUI=r'''
import argparse,json,time,tempfile,resource
from pathlib import Path
from vector_core.desktop import bootstrap,Desktop
out=Path(__import__('sys').argv[1])
args=argparse.Namespace(data_dir=str(out/'fixture-data'),choose_data=False,choose_models=False,models_directory=None,managed=False)
root,client=bootstrap(args);app=Desktop(root,client);s=app.shell;errors=[];app.dialog.showerror=lambda *a,**k:errors.append(a)
def wait():
 end=time.monotonic()+30
 while client.pending and time.monotonic()<end:root.update();time.sleep(.01)
 root.update();assert not client.pending,'GUI operation exceeded timeout'
def capture(name):
 root.update();(out/(name+'.ready')).write_text(str(root.winfo_id()))
 end=time.monotonic()+15
 while not (out/(name+'.captured')).exists() and time.monotonic()<end:root.update();time.sleep(.02)
 assert (out/(name+'.captured')).exists(),'Screenshot capture timed out'
wait();root.geometry('1060x700');root.update();capture('01-home-idle')
s.toggle_menu();capture('02-menu-open');s.hide_menu()
s.navigate('Projects');wait();app.project_name.insert(0,'Observatory · UI acceptance');app.create_project();wait();app.item_title.insert(0,'Compare observations');app.item_body.insert('1.0','Preserve sources and identify what remains unknown.');app.save_item();wait();app.project_items();wait();capture('03-projects')
s.navigate('Home / Chat');app.planning_enabled.set(True);app.question.insert(0,'Calculate (13 + 7) * 2; then divide the result by 8.');app.send_chat();wait();assert '5' in app.chat.get('1.0','end');capture('04-checked-conversation')
s.navigate('History');wait();assert s.history_rows;capture('05-history')
s.navigate('Investigations');wait();assert s.investigations;capture('06-investigations')
s.navigate('Settings');capture('07-settings');s.navigate('Advanced');capture('08-advanced')
s.navigate('Home / Chat');root.geometry('820x600');root.update();capture('09-small-screen');root.geometry('1060x700');root.update()
# Synthetic display-only scroll content, explicitly not inference or saved knowledge.
for i in range(150):app.show_chat('SCROLL ACCEPTANCE FIXTURE '+str(i)+' — sources and uncertainty remain inspectable.')
root.update();app.chat.yview_moveto(.2);root.update();old=app.chat.index('@0,0');app.show_chat('New scroll fixture content');root.update();assert app.chat.index('@0,0')==old;capture('10-reading-history');s.to_latest()
latencies=[]
for i in range(30):
 tick=time.perf_counter();s.navigate(('Home / Chat','Projects','Settings')[i%3],load=False);root.update_idletasks();latencies.append(time.perf_counter()-tick)
s.navigate('Home / Chat',load=False);root.update();measurements=[]
def measure(reduced):
 s.core.state(motion=not reduced);cpu=time.process_time();wall=time.monotonic();frames=s.core.frames
 def done():
  elapsed=time.monotonic()-wall;measurements.append({'reduced_motion':reduced,'seconds':elapsed,'cpu_seconds':time.process_time()-cpu,'core_frames':s.core.frames-frames});root.quit()
 root.after(15000,done);root.mainloop()
measure(False);measure(True)
assert not errors,errors
r={'passed':True,'model_calls':0,'window':'1060x700 and820x600','idle':measurements,'navigation_seconds':latencies,'frontend_maxrss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'backend_pid':client.process.pid,'backend_rss_kib':int(next(l.split()[1] for l in Path('/proc',str(client.process.pid),'status').read_text().splitlines() if l.startswith('VmRSS:'))),'screenshots':10,'actual_project':app.active_project,'experimental_defaults_initially_disabled':True,'scroll_retained':True}
app.close();r['backend_exited']=client.process.poll() is not None;(out/'result.json').write_text(json.dumps(r,indent=2))
'''

def png_from_xwd(source,target):
 # XWD's native TrueColor image is decoded without an extra screenshot service.
 from PIL import Image
 data=source.read_bytes();h=struct.unpack('>25I',data[:100]);size,version,format_,depth,w,height,xoff,byteorder,unit,bitorder,pad,bpp,stride,visual,red,green,blue,bits,cmap,colors,*rest=h
 if version!=7 or format_!=2 or bpp not in (24,32) or visual not in (4,5):raise ValueError('Unsupported XWD display format; retain raw screenshot.')
 start=size+colors*12;raw=data[start:];rgb=bytearray(w*height*3)
 def component(value,mask):
  shift=(mask&-mask).bit_length()-1;maximum=mask>>shift;return ((value&mask)>>shift)*255//maximum
 for y in range(height):
  for x in range(w):
   p=int.from_bytes(raw[y*stride+x*(bpp//8):y*stride+(x+1)*(bpp//8)],'little' if byteorder==0 else 'big');i=(y*w+x)*3;rgb[i:i+3]=bytes(component(p,m) for m in (red,green,blue))
 Image.frombytes('RGB',(w,height),bytes(rgb)).save(target)

def main():
 p=argparse.ArgumentParser();p.add_argument('--directory',required=True);a=p.parse_args();out=Path(a.directory).absolute();out.mkdir(parents=True,exist_ok=False)
 root=Path(__file__).resolve().parents[1];env={**os.environ,'PYTHONPATH':str(root/'src'),'PYTHONDONTWRITEBYTECODE':'1'}
 with (out/'ui.log').open('x') as log:
  child=subprocess.Popen([sys.executable,'-B','-c',GUI,str(out)],env=env,stdout=log,stderr=subprocess.STDOUT)
  try:
   until=time.monotonic()+180;done=set()
   while child.poll() is None and time.monotonic()<until:
    for ready in out.glob('*.ready'):
     if ready.name in done:continue
     wid=ready.read_text().strip();assert wid.isdigit();raw=ready.with_suffix('.xwd');subprocess.run(['/usr/bin/xwd','-silent','-id',wid,'-out',str(raw)],check=True,timeout=10);png_from_xwd(raw,ready.with_suffix('.png'));ready.with_suffix('.captured').write_text('Captured actual window');done.add(ready.name)
    time.sleep(.05)
   if child.poll() is None:raise TimeoutError('Bounded visual/performance acceptance exceeded180s')
   assert child.returncode==0,(out/'ui.log').read_text()
  finally:
   if child.poll() is None:child.terminate();child.wait(timeout=5)
 r=json.loads((out/'result.json').read_text());print(json.dumps(r,indent=2))
if __name__=='__main__':main()
