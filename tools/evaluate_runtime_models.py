"""Bounded real-host evaluation. No downloads, mocks, default changes or shared daemon.

Run with PYTHONPATH pointing at the source/package being qualified. Each output
directory is new. Safety limits are enforced by the normal qualified transport.
The independent expected answers below are report criteria, never model input.
"""
import argparse
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import threading
import time

from vector_core.inference import GenerationConfig,OllamaAdapter
from vector_core.worker_launcher import launch

TASKS={
 'logic':('Every red object is metal. No metal object floats. Object K is red. Does K float? Give one short answer with any uncertainty.', 'K does not float under the given premises.'),
 'engineering':('An ideal 18 V DC supply is connected across a 9 ohm resistor. What current flows and what power is dissipated? State the ideal assumptions.', '2 A; 36 W; ideal supply and resistor/Ohm law assumptions.'),
 'uncertainty':('A sealed box contains an unknown object. What is its mass? Explain what information is missing.', 'Cannot determine mass from this information; measurement or additional data needed.'),
 'greeting':('Write one short welcoming sentence for a new project.', 'A coherent welcoming sentence without a contradictory refusal.'),
 'hi':('Hi','A coherent short greeting; no schema copy, empty reply or unrelated refusal.'),
 'conversation':('How are you?','A relevant conversational answer without invented provider identity or human experiences.'),
 'arithmetic':('What is 2 + 2?','The actual model answer is4; independently computed values are reported separately.'),
 'alaska':('What is the capital of Alaska?','Juneau, not Anchorage; check the actual statement, not a keyword alone.'),
 'engine':('Explain how a gasoline engine works.','Coherent fuel/air, ignition and conversion to mechanical motion; do not confuse gasoline spark ignition with diesel-only ignition.'),
 'pressure':('What is the difference between force and pressure?','Pressure is force per area; force in newtons, pressure in pascals where units are given.'),
 'clarification':('Give me three ways to solve this problem.','Without a supplied problem, asks for the problem or explains the missing information; does not invent one.'),
 'multi-math':('Calculate (13 + 7) * 2, then divide the result by 8.','5; correct operations and any explanation consistent.'),
 'deduction':('Every flimp is ceramic. No ceramic item is flexible. Nara is a flimp. Under these premises, is Nara flexible?','Nara is not flexible, conditionally on the supplied premises; archive evidence is not necessary.'),
 'contradiction':('A report says all nine lamps are off and exactly three of those same lamps are on at the same instant. Can both statements be true? Explain briefly.','No under the same set/time and ordinary binary on/off meaning; do not invent a different set or time.'),
 'planning':('Design a practical test to distinguish a biased temperature sensor from a gain error. Give measurements, competing predictions and a limitation.','Two or more known references; constant additive error versus changing error, with measurement/reference limitations; coherence and feasibility need semantic review.'),
 'alternatives':('A gravity-fed rain gauge must work without mains power. Propose three distinct feasible ways to detect a full reservoir and compare a failure mode for each.','Three distinct approaches respecting the power constraint, with plausible tradeoffs. Do not claim universal novelty or discovery.'),
 'continuity-set':('My calibration token is cobalt and my project is a low-cost rain gauge.','Relevant acknowledgment; retain the exact user information as conversational context, not an established external fact.'),
 'continuity-get':('Which calibration token and project did I mention?','cobalt and low-cost rain gauge, when run after continuity-set with --continue-conversation.'),
 'revision-initial':('A 12 V DC supply feeds a 6 ohm resistor. Find current and power.','2A and24W for an ideal steady resistor. Record initial correctness independently.'),
 'revision-check':('Check your calculation using I=V/R and P=V*I. If your earlier answer is wrong, revise it and explain the correction.','2A and24W; acknowledge a genuine earlier mistake. Run after revision-initial with --continue-conversation; do not merge initial/corrected scores.'),
}
SUITES={'basic':['hi','conversation','arithmetic','alaska','engine','pressure','clarification'],
        'reasoning':['multi-math','deduction','contradiction','engineering','uncertainty','planning','alternatives'],
        'continuity':['continuity-set','continuity-get'],
        'revision':['revision-initial','revision-check']}
NAMES={'a':'qwen2.5-coder:0.5b','b':'vector-qwen35-local:2b-q4_k_m'}


def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--store',action='append',required=True)
 p.add_argument('--output',required=True)
 p.add_argument('--memory-mib',type=int,default=1536)
 p.add_argument('--runtime-profile',help='Use the normal private desktop startup profile and its smaller-ceiling fallback; --memory-mib then does not select the ceiling.')
 p.add_argument('--context',type=int,default=1024)
 p.add_argument('--output-tokens',type=int,default=128)
 p.add_argument('--modes',nargs='+',choices=['a','b','both'],default=['b'])
 p.add_argument('--tasks',nargs='+',choices=list(TASKS),default=['logic'])
 p.add_argument('--suite',choices=list(SUITES),help='Predeclared response/reasoning criteria; real model outputs still require independent semantic review.')
 p.add_argument('--continue-conversation',action='store_true',help='Keep actual prior turns within each mode for continuity/revision tests; originals remain saved.')
 p.add_argument('--service',action='store_true')
 args=p.parse_args()
 if args.suite:
  args.tasks=SUITES[args.suite]
  args.service=True
 if 'both' in args.modes and not args.service:p.error('Both requires the actual application service.')
 config=GenerationConfig('',args.context,args.output_tokens,300).validate()
 out=Path(args.output);out.mkdir(parents=True,mode=0o700,exist_ok=False)
 report={'simulated':False,'arguments':vars(args),'configuration':asdict(config),'started':time.time(),'cases':[],
         'evaluation_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
         'exit_zero_means':'Protocol completion only; independent semantic review is required.'}
 transport=None;stop=threading.Event();ready=threading.Event();thread=None;tick=time.monotonic()
 def snapshot():
  row={'seconds':time.monotonic()-tick,'meminfo':Path('/proc/meminfo').read_text(),
       'vmstat':{k:int(v) for k,v in (l.split() for l in Path('/proc/vmstat').read_text().splitlines()) if k in {'pswpin','pswpout','oom_kill','pgmajfault','compact_stall','compact_fail','pgscan_direct','pgsteal_direct'} or k.startswith('allocstall_')},
       'pressure':Path('/proc/pressure/memory').read_text(),'io_pressure':Path('/proc/pressure/io').read_text(),'cpu':Path('/proc/stat').read_text().splitlines()[0],
       'processes':[]}
  if transport:
   group=Path(transport.report['cgroup'])
   for name in ('memory.current','memory.peak','memory.swap.current','memory.events','memory.stat','memory.pressure','cpu.stat','pids.current'):
    try:row[name]=(group/name).read_text()
    except FileNotFoundError:pass
   try:pids=(group/'cgroup.procs').read_text().split()
   except FileNotFoundError:pids=[]
   for pid in pids:
    try:
     proc=Path('/proc')/pid;s=dict(l.split(':',1) for l in (proc/'status').read_text().splitlines() if ':' in l)
     row['processes'].append({'pid':int(pid),'command':(proc/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')[:1000],
       'rss':int(s.get('VmRSS','0 kB').split()[0])*1024,'swap':int(s.get('VmSwap','0 kB').split()[0])*1024,'threads':int(s.get('Threads','0')),'thp_enabled':s.get('THP_enabled','unknown').strip()})
    except (FileNotFoundError,ProcessLookupError):pass
  return row
 def monitor():
  ready.wait()
  if stop.is_set():return
  try:
   with (out/'resources.ndjson').open('x') as log:
    while not stop.is_set():
     row=snapshot();log.write(json.dumps(row)+'\n');log.flush();stop.wait(.5)
  except Exception as e:
   report.setdefault('monitor_errors',[]).append(repr(e))
 def save():(out/'result.json').write_text(json.dumps(report,indent=2,default=str))
 try:
  report['initial']=snapshot()
  from vector_core.models import selected_files
  report['verified_assets']={}
  for mode in set(args.modes):
   for role in ('a','b') if mode=='both' else (mode,):
    if role in report['verified_assets']:continue
    for root in args.store:
     name,tag=NAMES[role].split(':')
     if (Path(root)/'manifests/registry.ollama.ai/library'/name/tag).is_file():
      report['verified_assets'][role]=selected_files(root,NAMES[role]);break
    else:raise RuntimeError('Required exact local model missing: '+NAMES[role])
  report['source_hashes']={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in Path(__import__('vector_core').__file__).parent.glob('*.py')}
  save()
  # A quiet baseline is an evaluation prerequisite, not a relaxed safety guard.
  stable=[];deadline=time.monotonic()+60
  while True:
   sample=snapshot();stable.append(sample);stable=[s for s in stable if sample['seconds']-s['seconds']<=10.5]
   available=int(next(l.split()[1] for l in sample['meminfo'].splitlines() if l.startswith('MemAvailable:')))*1024
   pressure=float(next(l for l in sample['pressure'].splitlines() if l.startswith('full ')).split()[1].split('=')[1])
   # Desktop startup selects/rechecks its safe ceiling using the normal owner
   # profile. A fixed benchmark ceiling must not preempt that same safe path.
   required=(256+384 if args.runtime_profile else args.memory_mib+384)*1048576
   if available<required or pressure>5:stable=[]
   if len(stable)>=20 and stable[-1]['seconds']-stable[0]['seconds']>=10:
    if (stable[-1]['vmstat']['pswpout']-stable[0]['vmstat']['pswpout'])*os.sysconf('SC_PAGE_SIZE')<4*1048576:break
   if time.monotonic()>=deadline:raise RuntimeError('RESOURCE_BLOCKED: no ten-second quiet baseline within60seconds at the startup reserve/ceiling and pressure requirements.')
   time.sleep(.5)
  report['quiet_baseline']=[stable[0],stable[-1]];save()
  if args.runtime_profile:
   from vector_core.worker_launcher import desktop_runtime
   transport=desktop_runtime(args.runtime_profile)
   if transport is None:raise RuntimeError('Explicit desktop runtime profile is unavailable.')
   if tuple(Path(p) for p in args.store)!=transport.model_directories:raise RuntimeError('Evaluation stores differ from the actually authorized desktop profile.')
  else:transport=launch(args.store[0],additional_model_directories=args.store[1:],memory_bytes=args.memory_mib*1048576,tasks=64)
  report['isolation']=transport.report
  # The core deliberately denies creation of processes/threads after activation.
  # Create the read-only sampler first; activation synchronizes all threads.
  thread=threading.Thread(target=monitor,daemon=True);thread.start()
  from vector_core.security import activate
  report['policy']=activate(pipe_fds=transport.retained_fds)
  ready.set()
  adapter=OllamaAdapter(transport)
  report['catalog']=adapter.discover()
  app=None;memory=None
  if args.service:
   from vector_core.memory import Memory
   from vector_core.config import Config
   from vector_core.service import Application
   memory=Memory(Config.load(data_dir=str(out/'data')));app=Application(memory,transport);app.policy=report['policy']
  try:
   for mode in args.modes:
    for task_index,task in enumerate(args.tasks):
     question,expected=TASKS[task];row={'mode':mode,'task':task,'question':question,'expected_independent_criterion':expected,'manual_semantic_review_required':True}
     if not transport.qualified:
      row.update(status='NOT RUN',reason='Worker closed after prior failure. No fallback.');report['cases'].append(row);continue
     started=time.monotonic();row['started_seconds']=started-tick
     try:
      if app:
       if not args.continue_conversation or task_index==0:app.handle('new_conversation',{})
       settings=app.model_controller.settings();settings['generation']=asdict(config)
       app.handle('model_mode_set',{'mode':mode,'settings':settings})
       app.model_controller.progress=lambda value:print(json.dumps(value),flush=True)
       response=app.handle('ask',{'question':question});row['response']=response
       if response.get('model_run_ref'):row['run']=app.handle('model_run',{'id':response['model_run_ref']})
       row['pipeline_complete']=response.get('model_run',{}).get('status')=='complete'
      else:
       # Same task and instructions for either real model. No expected answer supplied.
       prompt='Answer the task concisely. Return JSON with text, uncertainty (empty if none), issues and citations (empty without sources). Task: '+question
       from dataclasses import replace
       generated=adapter.generate(prompt,replace(config,model=NAMES[mode]),response_kind='collaboration-v1')
       row['generation']=generated  # Preserve rejected actual outputs as evidence too.
       from vector_core.model_routing import validate_output
       row['parsed']=validate_output(None,generated['text']);row['pipeline_complete']=True
      row['status']='completed' if row['pipeline_complete'] else 'FAILED/CLOSED'
     except Exception as error:
      row.update(status='FAILED/CLOSED',error=repr(error),pipeline_complete=False,partial=getattr(error,'raw_generation',None),resources_at_failure=getattr(error,'resources',None))
     row['seconds']=time.monotonic()-started;report['cases'].append(row);save()
     print(json.dumps({'mode':mode,'task':task,'status':row['status'],'seconds':row['seconds']}),flush=True)
  finally:
   if memory:memory.close()
 except Exception as error:report['blocker']=repr(error)
 finally:
  stop.set();ready.set()
  if thread and thread.ident is not None:thread.join(2)
  report['sampler_finished']=thread is not None and not thread.is_alive()
  if transport:
   group=Path(transport.report['cgroup']);transport.close()
   def empty():
    try:return (group/'pids.current').read_text().strip()=='0'
    except FileNotFoundError:return True
   deadline=time.monotonic()+5
   while not empty() and time.monotonic()<deadline:time.sleep(.1)
   report['scope_cleanup_verified']=empty()
  report['final']=snapshot();report['finished']=time.time();save()
 print(json.dumps({'output':str(out),'blocker':report.get('blocker')}),flush=True)
 return 2 if report.get('blocker') or report.get('monitor_errors') or not report.get('sampler_finished') else 0 if report['cases'] and all(c.get('pipeline_complete') for c in report['cases']) else 1


if __name__=='__main__':raise SystemExit(main())
