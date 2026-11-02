"""One bounded actual 0.5B proposal through the planner; no fixture answers.

Run on the qualified Lenovo only, after other heavy workloads have stopped.
Exits with recorded blocking evidence rather than relaxing resource/isolation gates.
"""
import argparse,json,os,subprocess,threading,time
from dataclasses import asdict
from pathlib import Path
from vector_core.worker_launcher import launch
from vector_core.inference import GenerationConfig,Cancellation,OllamaAdapter
from vector_core.config import Config
from vector_core.memory import Memory
from vector_core.service import Application
from vector_core.investigation import Budget
from vector_core.planner import Planner

MODEL='qwen2.5-coder:0.5b'
QUESTION='Why might a small fan vibrate intermittently? Propose two competing explanations and one measurement that could distinguish them. State what remains uncertain.'


def main():
 p=argparse.ArgumentParser();p.add_argument('--directory',required=True);p.add_argument('--models-directory',required=True);a=p.parse_args()
 out=Path(a.directory).absolute();out.mkdir(mode=0o700,parents=True,exist_ok=False)
 start=time.monotonic();stop=threading.Event();go=threading.Event();ready=threading.Event();cancel=Cancellation();samples=[];transport=None;cg=None;monitor=None;memory=None;recording=None;stage='baseline'
 config=GenerationConfig(MODEL,2048,96,60,0,0).validate()
 report={'model':MODEL,'simulated':False,'configuration':asdict(config),'question':QUESTION,'methodology':'One actual unverified proposal, no retries, no golden answer in prompt. Semantic originality/correctness is not established by format acceptance. No production data or preference changes.','stopping_conditions':{'reserve_mib':512,'phase_swapout_mib':32,'full_psi_avg10_percent':10,'pressure_seconds':5,'worker_swap_bytes':0,'oom_kill':0},'results':[]}
 def sample():
  m={l.split(':')[0]:int(l.split()[1])*1024 for l in Path('/proc/meminfo').read_text().splitlines() if len(l.split())==3 and l.split()[2]=='kB'}
  vm={k:int(v) for k,v in (l.split() for l in Path('/proc/vmstat').read_text().splitlines())}
  psi={l.split()[0]:{k:float(v) for k,v in (x.split('=') for x in l.split()[1:])} for l in Path('/proc/pressure/memory').read_text().splitlines()}
  r={'elapsed':time.monotonic()-start,'stage':stage,'mem':{k:m[k] for k in ('MemTotal','MemAvailable','SwapTotal','SwapFree')},'vmstat':{k:vm[k] for k in ('pswpin','pswpout','pgmajfault','oom_kill')},'memory_psi':psi,'cpu_times':list(map(int,Path('/proc/stat').read_text().splitlines()[0].split()[1:9])),'processes':[]}
  if cg is not None:
   for name in ('memory.current','memory.peak','memory.swap.current','memory.events','pids.current'):
    try:r[name]=(cg/name).read_text().strip()
    except FileNotFoundError:
     if transport and transport.qualified:raise
   try:pids=(cg/'cgroup.procs').read_text().split()
   except FileNotFoundError:pids=[]
   for pid in pids:
    try:
     s=dict(l.split(':',1) for l in (Path('/proc')/pid/'status').read_text().splitlines() if ':' in l)
     r['processes'].append({'pid':int(pid),'name':s.get('Name','').strip(),'rss_bytes':int(s.get('VmRSS','0 kB').split()[0])*1024,'swap_bytes':int(s.get('VmSwap','0 kB').split()[0])*1024})
    except FileNotFoundError:pass
  return r
 def persist():(out/'result.json').write_text(json.dumps(report,indent=2))
 def watch():
  go.wait()
  pressure_since=None;initial=samples[-1]
  with (out/'resources.ndjson').open('a') as log:
   while not stop.is_set():
    try:
     r=sample();reason=None
     if r['mem']['MemAvailable']<512*1048576:reason='Available RAM reserve below512MiB'
     if r['vmstat']['oom_kill']>initial['vmstat']['oom_kill']:reason='Host OOM kill'
     if (r['vmstat']['pswpout']-initial['vmstat']['pswpout'])*os.sysconf('SC_PAGE_SIZE')>32*1048576:reason='Host phase swap-out exceeded32MiB'
     if int(r.get('memory.swap.current','0')):reason='Worker swap observed'
     if any(l.split()[0]=='oom_kill' and int(l.split()[1]) for l in r.get('memory.events','').splitlines()):reason='Trial cgroup OOM kill'
     pressure_since=(pressure_since or time.monotonic()) if r['memory_psi']['full']['avg10']>10 else None
     if pressure_since and time.monotonic()-pressure_since>5:reason='Host full-memory PSI above10percent for5seconds'
     if reason:r['stop_reason']=reason;cancel.cancel()
     samples.append(r);log.write(json.dumps(r)+'\n');log.flush();ready.set()
    except Exception as e:
     report.setdefault('monitor_errors',[]).append(repr(e));cancel.cancel();ready.set()
    stop.wait(.5)
 try:
  with (out/'resources.ndjson').open('x') as log:
   until=time.monotonic()+10
   while time.monotonic()<until:
    r=sample();samples.append(r);log.write(json.dumps(r)+'\n');log.flush();time.sleep(.5)
  report['baseline_samples']=list(samples)
  if any(r['mem']['MemAvailable']<(768+512)*1048576 or r['memory_psi']['full']['avg10']>5 for r in samples) or samples[-1]['vmstat']['oom_kill']>samples[0]['vmstat']['oom_kill'] or (samples[-1]['vmstat']['pswpout']-samples[0]['vmstat']['pswpout'])*os.sysconf('SC_PAGE_SIZE')>4*1048576:raise RuntimeError('RESOURCE_BLOCKED: no conservative baseline headroom.')
  stage='launch';transport=launch(Path(a.models_directory),memory_bytes=768*1048576,tasks=64);cg=Path(transport.report['cgroup'])
  env={'PATH':'/usr/bin:/bin','HOME':str(Path.home()),'XDG_RUNTIME_DIR':'/run/user/'+str(os.getuid()),'DBUS_SESSION_BUS_ADDRESS':'unix:path=/run/user/'+str(os.getuid())+'/bus'}
  subprocess.run(['/usr/bin/systemctl','--user','set-property','--runtime',transport.report['unit']+'.scope','MemorySwapMax=0'],env=env,check=True,timeout=5)
  assert (cg/'memory.swap.max').read_text().strip()=='0'
  report['isolation']={**transport.report,'memory_swap_max':0}
  monitor=threading.Thread(target=watch,name='planning-resource-monitor');monitor.start()
  from vector_core.security import activate
  report['policy']=activate(pipe_fds=transport.retained_fds);go.set()
  if not ready.wait(3) or cancel.cancelled:raise RuntimeError('Resource monitor unavailable or baseline unstable.')
  class Recording:
   def __init__(self,inner):self.inner=inner;self.raw=None;self.prompts=[]
   @property
   def qualified(self):return self.inner.qualified
   @property
   def runtime_version(self):return self.inner.runtime_version
   def request(self,payload,timeout,cancellation=None):
    if payload.get('operation')=='generate':self.prompts.append(payload['prompt'])
    result=self.inner.request(payload,timeout,cancellation)
    if payload.get('operation')=='generate':self.raw=result
    return result
  recording=Recording(transport)
  memory=Memory(Config.load(data_dir=str(out/'data')));app=Application(memory,transport);app.generation=config;app.adapter=OllamaAdapter(recording)
  report['discovery']=app.adapter.discover()
  if MODEL not in [m['name'] for m in report['discovery']['models']]:raise RuntimeError('Installed0.5B absent from qualified worker.')
  stage='model-disabled-question';turn=app.handle('ask',{'question':QUESTION,'planning':True});report['before_exploration']=turn['planning']
  assert not turn['planning']['completion']['findings_complete']
  state=turn['planning']['state'];planner=Planner(memory,app.adapter,config);state=planner.explore(state['id'],state['revision'],approved=True)
  app.prepare_inference();stage='actual-proposal';tick=time.monotonic()
  result=planner.run(state['id'],budget=Budget(4,1,65),approved=True,cancellation=cancel)
  report['results'].append({'seconds':time.monotonic()-tick,'view':result})
  good,feedback=planner.inv._results(state['id']);report['feedback']=feedback;report['generations']=[r['generation'] for r in good.values() if 'generation' in r];report['proposal_accepted_as_unverified']=bool(report['generations'])
  for generation in report['generations']:
   assert generation['simulated'] is False
   metrics=generation['metrics'];generation['tokens_per_second']=metrics.get('eval_count',0)*1e9/metrics['eval_duration'] if metrics.get('eval_duration') else None
  stage='unload';time.sleep(3)
 except (Exception,KeyboardInterrupt) as e:
  report['error']=repr(e);report['raw_generation_on_error']=getattr(e,'raw_generation',None);cancel.cancel()
 finally:
  go.set()
  if recording:
   report['prompts']=recording.prompts;report['raw_api_result']=recording.raw;report['actual_model_calls']=len(recording.prompts)
   if recording.raw:
    r=recording.raw;report['load_seconds']=r.get('load_duration',0)/1e9;report['tokens_per_second']=r.get('eval_count',0)*1e9/r['eval_duration'] if r.get('eval_duration') else None
  if memory:memory.close()
  if transport:
   try:report['before_close']=sample()
   except Exception as e:report['before_close_error']=repr(e)
   stage='closing-worker';transport.close();report['worker_closed']=not transport.qualified
  stage='after-worker-close';time.sleep(3);stop.set()
  if monitor:monitor.join(timeout=3)
  samples.append(sample());report['after_close']=samples[-1];report['cancelled']=cancel.cancelled;report['stop_reasons']=sorted({r['stop_reason'] for r in samples if 'stop_reason' in r});report['cgroup_exists_after_close']=cg.exists() if cg else None
  report['summary']={'seconds':time.monotonic()-start,'peak_host_used_ram_bytes':max(r['mem']['MemTotal']-r['mem']['MemAvailable'] for r in samples),'peak_host_swap_bytes':max(r['mem']['SwapTotal']-r['mem']['SwapFree'] for r in samples),'peak_worker_memory_bytes':max(int(r.get('memory.peak','0')) for r in samples),'host_swapout_bytes':(samples[-1]['vmstat']['pswpout']-samples[0]['vmstat']['pswpout'])*os.sysconf('SC_PAGE_SIZE'),'oom_kills':samples[-1]['vmstat']['oom_kill']-samples[0]['vmstat']['oom_kill']}
  persist();print(json.dumps({k:report.get(k) for k in ('summary','error','cancelled','stop_reasons','proposal_accepted_as_unverified','worker_closed','cgroup_exists_after_close')},indent=2))
if __name__=='__main__':main()
