"""Real offline production service acceptance; fixtures are never substituted."""
import argparse,json,os,re,sys,time
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--runtime-profile',required=True);p.add_argument('--output',required=True);p.add_argument('--source',required=True);p.add_argument('--context',type=int,default=2048);p.add_argument('--modes',nargs='+',default=['a','b','both'],choices=['a','b','both']);args=p.parse_args()
sys.path.insert(0,args.source)
from vector_core.worker_launcher import desktop_runtime
from vector_core.inference import GenerationConfig
from dataclasses import asdict
report={'simulated':False,'cases':[],'started':time.time(),'initial_meminfo':Path('/proc/meminfo').read_text(),'initial_pressure':Path('/proc/pressure/memory').read_text(),'initial_vmstat':Path('/proc/vmstat').read_text()};transport=None
out=Path(args.output);out.mkdir(mode=0o700,parents=True,exist_ok=False)
try:
 transport=desktop_runtime(args.runtime_profile)
 if transport is None:raise RuntimeError('No explicit qualified runtime profile available')
 report['isolation']=transport.report
 from vector_core.security import activate
 report['policy']=activate(pipe_fds=transport.retained_fds)
 from vector_core.memory import Memory
 from vector_core.config import Config
 from vector_core.service import Application
 with Memory(Config.load(data_dir=str(out/'data'))) as memory:
  app=Application(memory,transport);app.policy=report['policy'];report['catalog']=app.handle('model_modes',{})
  settings=report['catalog']['settings'];settings['generation']=asdict(GenerationConfig('',args.context,192,300))
  question='Every red object is metal. No metal object floats. Object K is red. Does K float? Give one short answer with any uncertainty.'
  for mode in args.modes:
   if not transport.qualified:
    report['cases'].append({'mode':mode,'status':'NOT RUN','reason':'Previous stage closed the worker; no unqualified fallback.'});continue
   app.handle('new_conversation',{});app.handle('model_mode_set',{'mode':mode,'settings':settings});stage=[]
   def progress(value):
    snapshot={'progress':value,'processes':[]}
    try:
     for pid in (Path(transport.report['cgroup'])/'cgroup.procs').read_text().split():
      try:
       command=(Path('/proc')/pid/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')
       snapshot['processes'].append({'pid':int(pid),'command':command})
      except OSError:pass
    except OSError:pass
    stage.append(snapshot);print(json.dumps(snapshot),flush=True)
   app.model_controller.progress=progress
   row={'mode':mode,'question':question,'context':args.context,'progress':stage,'expected':'Under the given premises, K does not float. Model agreement is not verification.'};tick=time.monotonic()
   try:
    response=app.handle('ask',{'question':question});row['response']=response
    if response.get('model_run_ref'):row['run']=app.handle('model_run',{'id':response['model_run_ref']})
    text=response['outcome'].get('model_text','') or ''
    row['pipeline_complete']=response.get('model_run',{}).get('status')=='complete'
    row['lexical_correctness_screen']=bool(row['pipeline_complete'] and re.search(r"(?:does not|doesn't|cannot|can't|will not|won't|not)\s+float",text,re.I))
    row['manual_semantic_review_required']=True
    row['status']='completed' if row['pipeline_complete'] else 'FAILED/CLOSED'
    assert response['outcome']['status']!='simulated-test-response','Real acceptance refuses all simulated outputs'
   except Exception as error:row.update(status='FAILED/CLOSED',error=repr(error),pipeline_complete=False,objective_correct=False)
   row['seconds']=time.monotonic()-tick;report['cases'].append(row);(out/'result.json').write_text(json.dumps(report,indent=2));print(json.dumps({'mode':mode,'status':row['status'],'lexical_correctness_screen':row.get('lexical_correctness_screen'),'seconds':row['seconds']}),flush=True)
except Exception as error:report['blocker']=repr(error)
finally:
 if transport:
  group=Path(transport.report['cgroup']);transport.close();report['worker_closed']=True;report['worker_returncode']=transport.process.poll()
  deadline=time.monotonic()+5
  while group.exists() and (group/'pids.current').read_text().strip()!='0' and time.monotonic()<deadline:time.sleep(.1)
  report['scope_cleanup_verified']=not group.exists() or (group/'pids.current').read_text().strip()=='0'
 report['finished']=time.time();report['final_meminfo']=Path('/proc/meminfo').read_text();report['final_pressure']=Path('/proc/pressure/memory').read_text();(out/'result.json').write_text(json.dumps(report,indent=2))
 print(json.dumps({'output':str(out),'blocker':report.get('blocker'),'real_modes_complete':[c['mode'] for c in report['cases'] if c.get('pipeline_complete')]}),flush=True)

# A successful diagnostic run is not automatically successful model acceptance.
complete=len(report['cases'])==len(args.modes) and all(c.get('pipeline_complete') and c.get('lexical_correctness_screen') for c in report['cases'])
raise SystemExit(2 if report.get('blocker') else 0 if complete else 1)
