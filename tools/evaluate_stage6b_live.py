"""Controlled actual 0.5B A/B/C run; never substitutes simulated answers."""
import argparse,json,os,subprocess,sys,threading,time
from dataclasses import asdict
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from evaluate_stage6b import read_corpus,load_fixture,grade_model,grade_core,grade_retrieval
from vector_core.worker_launcher import launch
from vector_core.inference import Cancellation,GenerationConfig,OllamaAdapter
from vector_core.config import Config
from vector_core.memory import Memory,canonical
from vector_core.investigation import Investigations,Budget,INSTRUCTIONS,candidate
from vector_core.context import build_context
p=argparse.ArgumentParser();p.add_argument('--corpus',required=True);p.add_argument('--directory',required=True);p.add_argument('--models-directory',required=True);p.add_argument('--case');p.add_argument('--mode',choices=['A','B','C','D']);p.add_argument('--include-unseen',action='store_true');p.add_argument('--unseen-only',action='store_true');p.add_argument('--compare-checked',action='store_true');a=p.parse_args()
if a.unseen_only and not a.include_unseen:p.error('--unseen-only requires --include-unseen')
if a.compare_checked and a.mode:p.error('Choose --compare-checked or --mode, not both')
work=Path(a.directory).absolute();work.mkdir(parents=True,mode=0o700)
MODEL='qwen2.5-coder:0.5b';MEMORY=768*1048576
STORE=Path(a.models_directory)
config=GenerationConfig(MODEL,8192,512,300,0,0).validate()
start=time.monotonic();stop=threading.Event();go=threading.Event();monitor_ready=threading.Event();cancel=Cancellation();cg=None;transport=None;monitor=None;rows=[];lock=threading.Lock();stage='baseline'
report={'implementation_sha256':{p.name:__import__('hashlib').sha256(p.read_bytes()).hexdigest() for p in (Path(__import__('vector_core').__file__).parent).glob('*.py')},'model':MODEL,'simulated':False,'configuration':asdict(config),'evidence_budget_bytes':3500,'results':[], 'methodology':{'A':'Model with independent direct passage context only; no derived claims/controller/tool results.', 'B':'Existing investigation retrieve/generate; semantic disabled.', 'C':'Existing investigation with semantic retrieve, grounded source/tool verification, and model generate. Core and narration scored separately.', 'common':'Same structured task specification and question; no gold answer or gold source selection enters prompts. Old direct retrieval supplies A passages. Strict existing candidate/citation/adapter guards; one attempt per cell.'}}
def values(raw):return {k:int(v) for k,v in (line.split() for line in raw.splitlines())}
def mem(raw):return {l.split(':',1)[0]:int(l.split()[1])*1024 for l in raw.splitlines() if len(l.split())==3 and l.split()[2]=='kB'}
def pressure(raw):return {line.split()[0]:{p.split('=')[0]:float(p.split('=')[1]) for p in line.split()[1:]} for line in raw.splitlines()}
def sample():
 m=Path('/proc/meminfo').read_text();vm=values(Path('/proc/vmstat').read_text());cpu=list(map(int,Path('/proc/stat').read_text().splitlines()[0].split()[1:9]))
 row={'elapsed':time.monotonic()-start,'stage':stage,'mem':{k:v for k,v in mem(m).items() if k in ('MemTotal','MemAvailable','MemFree','SwapTotal','SwapFree','Cached','SReclaimable')},'vmstat':{k:vm[k] for k in ('pswpin','pswpout','pgmajfault','oom_kill')},'memory_psi':pressure(Path('/proc/pressure/memory').read_text()),'cpu_times':cpu,'loadavg':Path('/proc/loadavg').read_text().strip(),'processes':[]}
 if cg is not None:
  for name in ('memory.current','memory.peak','memory.swap.current','memory.events','memory.stat','pids.current','cpu.stat'):
   try:row[name]=(cg/name).read_text().strip()
   except OSError:
    if transport and transport.qualified and transport.process.poll() is None:raise
  try:pids=(cg/'cgroup.procs').read_text().split()
  except OSError:pids=[]
  for pid in pids:
   try:
    root=Path('/proc')/pid;s=dict(l.split(':',1) for l in (root/'status').read_text().splitlines() if ':' in l);cmd=(root/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')
    row['processes'].append({'pid':int(pid),'name':s.get('Name','').strip(),'rss_bytes':int(s.get('VmRSS','0 kB').split()[0])*1024,'swap_bytes':int(s.get('VmSwap','0 kB').split()[0])*1024,'threads':int(s.get('Threads','0')),'runner':s.get('Name','').strip() in ('llama-server','ollama_llama_se') or ' runner ' in ' '+cmd+' ' or 'ollama_llama_server' in cmd,'command':cmd[:400]})
   except (OSError,ValueError):pass
 return row
def watch():
 go.wait()
 with lock:initial=rows[0] if rows else None
 pressure_since=None
 with (work/'resources.ndjson').open('a') as log:
  while not stop.is_set():
   try:
    row=sample()
    if initial is None:initial=row
    reason=None
    if row['mem']['MemAvailable']<384*1048576:reason='Host available memory reserve below384MiB'
    if row['vmstat']['oom_kill']>initial['vmstat']['oom_kill']:reason='Host OOM kill observed'
    if (row['vmstat']['pswpout']-initial['vmstat']['pswpout'])*os.sysconf('SC_PAGE_SIZE')>128*1048576:reason='Host swap-out exceeded128MiB in this phase'
    if int(row.get('memory.swap.current','0'))>0:reason='Worker used swap despite verified zero-swap limit'
    if any(l.split()[0]=='oom_kill' and int(l.split()[1]) for l in row.get('memory.events','').splitlines()):reason='Trial cgroup OOM kill'
    full=row['memory_psi']['full']['avg10'];pressure_since=(pressure_since or time.monotonic()) if full>30 else None
    if pressure_since and time.monotonic()-pressure_since>15:reason='Host full-memory PSI above30percent for15seconds'
    if reason:row['stop_reason']=reason;cancel.cancel()
    with lock:rows.append(row)
    log.write(json.dumps(row)+'\n');log.flush();monitor_ready.set()
   except Exception as e:
    cancel.cancel();report.setdefault('monitor_errors',[]).append(repr(e));monitor_ready.set()
    try:log.write(json.dumps({'monitor_error':repr(e)})+'\n');log.flush()
    except OSError:pass
   stop.wait(.5)

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

def persist():
 (work/'result.json').write_text(json.dumps(report,indent=2))

def run_cell(mode,case,mapping):
 global stage,memory
 if cancel.cancelled or not transport.qualified or not monitor.is_alive():raise RuntimeError('Resource monitoring or isolated worker unavailable.')
 stage=mode+':'+case['id'];recording.raw=None;recording.prompts=[];tick=time.monotonic()
 row={'mode':mode,'id':case['id'],'category':case['category'],'model_attempted':False,'model_grade':grade_model(memory,case,None,mapping)};report['results'].append(row)
 print('START',stage,flush=True)
 inv=None;state=None
 goal=case['question']+'\nExplicit task specification (not an answer): '+canonical(case['request'])+'\nFor a missing/disputed answer use the short answer insufficient/disputed. Otherwise give the bare requested value in answer; quantities use the requested unit. Cite source spans supporting the answer.'
 try:
  if mode=='A':
   built=build_context(memory,case['question'],budget_bytes=3500)
   context={k:v for k,v in built['context'].items() if k in ('question','sources','truncated','policy')}
   row['retrieval']=grade_retrieval(memory,case,context,mapping,corpus)
   prompt=INSTRUCTIONS+canonical({'goal':goal,'strategy':'generate','request':'','context':context,'prior':[],'feedback':''})
   row['prompt_bytes']=len(prompt.encode());result=adapter.generate(prompt,config,cancel);row['generation']=result
   checked=candidate(memory,result['text'],context);row['candidate']=checked;row['model_grade']=grade_model(memory,case,checked,mapping)
  elif mode=='D':
   from evaluate_stage6c import grade
   steps=[{'id':'grounded','strategy':'grounded','depends':[],'input':{'request':case['request']}},
          {'id':'answer','strategy':'compose','depends':['grounded'],'input':{}},
          {'id':'commentary','strategy':'explain','depends':['answer'],'input':{}}]
   inv=Investigations(memory,adapter,config);state=inv.create(case['question'],steps,approved=True)
   execution=inv.run(state['id'],budget=Budget(3,1,360),cancellation=cancel,approved=True);results,feedback=inv._results(state['id'])
   row.update(execution=execution,feedback=feedback,investigation_id=state['id']);row.pop('model_grade')
   if 'answer' in results:row['checked_answer']=results['answer'];row['user_facing_grade']=grade(memory,case,results['answer'],mapping)
   row['neural_protocol_grade']={'accepted':bool(results.get('commentary')),'entailment_verified':False,'role':'Optional unverified commentary/order only, not a model-generated answer score.'}
   if 'commentary' in results:row['commentary']=results['commentary']
   row['core_grade']=grade_core(memory,case,results['grounded'],mapping);row['grounded_result']=results['grounded']
  else:
   step={'id':'evidence','strategy':'retrieve','depends':[],'input':{'query':case['question'],'evidence_budget':3500,'semantic':mode=='C'}}
   if mode=='C' and case['request']['kind']=='lookup':step['input']['selector']=case['request']['selector']
   steps=[step]
   if mode=='C':steps.append({'id':'grounded','strategy':'grounded','depends':['evidence'],'input':{'request':case['request']}})
   steps.append({'id':'candidate','strategy':'generate','depends':['evidence']+(['grounded'] if mode=='C' else []),'input':{}})
   inv=Investigations(memory,adapter,config);state=inv.create(goal,steps,approved=True)
   if case.get('continuation'):
    first=inv.run(state['id'],budget=Budget(1,0,60),approved=True)
    if first['state']['status']!='paused':raise RuntimeError('Continuation did not pause at evidence checkpoint.')
    cfg=memory.config;memory.close();memory=Memory(cfg);inv=Investigations(memory,adapter,config);s=inv.get(state['id']);inv.control(s['id'],'resume',s['revision'],approved=True);row['continued_after_reopen']=True
   execution=inv.run(state['id'],budget=Budget(4,1,360),cancellation=cancel,approved=True);results,feedback=inv._results(state['id']);row['execution']=execution;row['feedback']=feedback;row['investigation_id']=state['id']
   ctx=results.get('evidence',{}).get('context',{'sources':[]});row['retrieval']=grade_retrieval(memory,case,ctx,mapping,corpus)
   if 'grounded' in results:row['core_grade']=grade_core(memory,case,results['grounded'],mapping);row['grounded_result']=results['grounded']
   if 'candidate' in results:row['candidate']=results['candidate'];row['model_grade']=grade_model(memory,case,results['candidate'],mapping)
 except (Exception,KeyboardInterrupt) as e:
  row['error']=repr(e);row['raw_generation_on_error']=getattr(e,'raw_generation',None)
  if isinstance(e,KeyboardInterrupt):cancel.cancel()
 row['seconds']=time.monotonic()-tick;row['model_attempted']=bool(recording.prompts);row['prompts']=recording.prompts;row['raw_api_result']=recording.raw
 if recording.raw:
  r=recording.raw;row['load_seconds']=r.get('load_duration',0)/1e9;row['tokens_per_second']=r.get('eval_count',0)*1e9/r['eval_duration'] if r.get('eval_duration') else None
 stage='unload:'+mode+':'+case['id'];until=time.monotonic()+30
 while time.monotonic()<until and not cancel.cancelled:
  with lock:latest=rows[-1] if rows else {}
  if not any(p['runner'] for p in latest.get('processes',[])) and time.monotonic()-tick-row['seconds']>=3:break
  time.sleep(.5)
 row['runner_unloaded']=not any(p['runner'] for p in latest.get('processes',[]));row['post_unload_sample']=latest
 persist();print('DONE',json.dumps({k:row.get(k) for k in ('mode','id','seconds','model_attempted','error','feedback','model_grade','core_grade','user_facing_grade','neural_protocol_grade','tokens_per_second','runner_unloaded')}),flush=True)
 if not row['runner_unloaded']:cancel.cancel();raise RuntimeError('Runner did not unload within bounded recovery window.')

memory=None
try:
 corpus=read_corpus(a.corpus)
 if a.include_unseen:
  unseen=json.loads((Path(__file__).resolve().parents[1]/'tests/fixtures/stage6c-unseen.json').read_text())
  from evaluate_stage6c import merge_corpora
  corpus=merge_corpora(corpus,unseen)
  report['merged_corpus_sha256']=__import__('hashlib').sha256(canonical(corpus).encode()).hexdigest()
  report['unseen_corpus_sha256']=__import__('hashlib').sha256((Path(__file__).resolve().parents[1]/'tests/fixtures/stage6c-unseen.json').read_bytes()).hexdigest()
 report['methodology']['D']='Stage6C independent composition, then one optional model contribution. User-facing correctness and unverified neural protocol acceptance are scored separately; this is not a new neural reasoning score.'
 print('BASELINE 15 seconds',flush=True)
 with (work/'resources.ndjson').open('x') as log:
  until=time.monotonic()+15
  while time.monotonic()<until:
   row=sample();rows.append(row);log.write(json.dumps(row)+'\n');log.flush();time.sleep(.5)
 report['baseline_samples']=list(rows);report['corpus_sha256']=__import__('hashlib').sha256(Path(a.corpus).read_bytes()).hexdigest()
 if any(r['mem']['MemAvailable']<MEMORY+384*1048576 or r['memory_psi']['full']['avg10']>5 for r in rows[-20:]) or rows[-1]['vmstat']['oom_kill']>rows[0]['vmstat']['oom_kill'] or (rows[-1]['vmstat']['pswpout']-rows[0]['vmstat']['pswpout'])*4096>4*1048576:raise RuntimeError('RESOURCE_BLOCKED: no conservative baseline headroom.')
 stage='launch';transport=launch(STORE,memory_bytes=MEMORY,tasks=64);cg=Path(transport.report['cgroup'])
 env={'PATH':'/usr/bin:/bin','HOME':str(Path.home()),'XDG_RUNTIME_DIR':'/run/user/'+str(os.getuid()),'DBUS_SESSION_BUS_ADDRESS':'unix:path=/run/user/'+str(os.getuid())+'/bus'}
 subprocess.run(['/usr/bin/systemctl','--user','set-property','--runtime',transport.report['unit']+'.scope','MemorySwapMax=0'],env=env,check=True,timeout=5)
 assert (cg/'memory.swap.max').read_text().strip()=='0';report['isolation']={**transport.report,'memory_swap_max':0}
 monitor=threading.Thread(target=watch,name='resource-monitor');monitor.start()
 from vector_core.security import activate
 report['policy']=activate(pipe_fds=transport.retained_fds);go.set()
 if not monitor_ready.wait(3) or cancel.cancelled or not monitor.is_alive():raise RuntimeError('Resource monitor did not become healthy.')
 recording=Recording(transport);adapter=OllamaAdapter(recording);report['discovery']=adapter.discover()
 if MODEL not in [m['name'] for m in report['discovery']['models']]:raise RuntimeError('Expected installed0.5B absent from isolated discovery.')
 memory=Memory(Config.load(data_dir=str(work/'data')));mapping=load_fixture(memory,corpus)
 # Rotate order by case to avoid always favoring a warmer/cooler mode.
 for index,case in enumerate(c for c in corpus['cases'] if c['live']):
  if a.case and case['id']!=a.case:continue
  if a.unseen_only and not case['id'].startswith('U'):continue
  modes=[a.mode] if a.mode else ['A','C','D'] if a.compare_checked else ['A','B','C'];modes=modes[index%len(modes):]+modes[:index%len(modes)]
  for mode in modes:
   if cancel.cancelled:break
   run_cell(mode,case,mapping)
  if cancel.cancelled:break
 report['fixture_integrity']=memory.verify()
except (Exception,KeyboardInterrupt) as e:report['error']=repr(e);print('ERROR',repr(e),flush=True)
finally:
 go.set()
 if memory:memory.close()
 if transport:
  try:report['final_worker_sample']=sample()
  except Exception as e:report['final_sample_error']=repr(e)
  stage='closing-worker';transport.close();report['worker_closed']=not transport.qualified
 stage='after-worker-close';until=time.monotonic()+10
 while time.monotonic()<until:time.sleep(.5)
 stop.set()
 if monitor:monitor.join(timeout=3)
 report['seconds']=time.monotonic()-start;report['cancelled']=cancel.cancelled
 with lock:report['stop_reasons']=sorted({r['stop_reason'] for r in rows if 'stop_reason' in r});report['after_close_samples']=[r for r in rows if r['stage']=='after-worker-close']
 report['cgroup_exists_after_close']=cg.exists() if cg else None
 persist();print('COMPLETE',json.dumps({k:report.get(k) for k in ('error','cancelled','stop_reasons','seconds','worker_closed','cgroup_exists_after_close')}),flush=True)
