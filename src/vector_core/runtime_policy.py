"""Local hardware observations and bounded AUTO recommendations, never permissions."""
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import shutil

MIB=1024*1024

def _pairs(path):
    return {line.split()[0].rstrip(':'):line.split()[1:] for line in Path(path).read_text().splitlines() if len(line.split())>=2}

def hardware(data_directory=None):
    """No commands, devices, sockets, model loading or persisted configuration."""
    mem=_pairs('/proc/meminfo');total=int(mem['MemTotal'][0])*1024;available=int(mem['MemAvailable'][0])*1024
    try:affinity=len(os.sched_getaffinity(0))
    except (AttributeError,OSError):affinity=os.cpu_count() or 1
    cpu=Path('/proc/cpuinfo').read_text();flags=next((line.split(':',1)[1].split() for line in cpu.splitlines() if line.startswith(('flags\t','Features\t'))),[])
    constraints=[];effective_cores=float(affinity);effective_available=available;effective_total=total;pids=None
    try:
        relative=next(line.split('::',1)[1] for line in Path('/proc/self/cgroup').read_text().splitlines() if line.startswith('0::'))
        group=Path('/sys/fs/cgroup')/relative.lstrip('/')
        if not group.is_relative_to('/sys/fs/cgroup'):raise ValueError('Invalid cgroup path.')
        for g in (group,*group.parents):
            if not g.is_relative_to('/sys/fs/cgroup'):continue
            limit='not-delegated';current=None;quota=['not-delegated'];value='not-delegated'
            if (g/'memory.max').exists():
                limit=(g/'memory.max').read_text().strip();current=int((g/'memory.current').read_text())
                if limit!='max':effective_total=min(effective_total,int(limit));effective_available=min(effective_available,max(0,int(limit)-current))
            if (g/'cpu.max').exists():
                quota=(g/'cpu.max').read_text().split()
                if quota[0]!='max':effective_cores=min(effective_cores,int(quota[0])/int(quota[1]))
            if (g/'pids.max').exists():
                value=(g/'pids.max').read_text().strip()
                if value!='max':pids=min(pids if pids is not None else int(value),int(value))
            constraints.append({'path':str(g),'memory_max':limit,'memory_current':current,'cpu_max':' '.join(quota),'pids_max':value,'missing_controller_rule':'A controller not delegated here inherits active ancestor constraints; every ancestor is inspected.'})
    except (OSError,ValueError,StopIteration) as error:
        # A known v2 hierarchy must be readable; never call unavailable limits unlimited.
        if Path('/sys/fs/cgroup/cgroup.controllers').exists():raise RuntimeError('Hardware cgroup inspection failed closed: '+str(error)) from error
    try:pressure={line.split()[0]:{k:float(v) for k,v in (part.split('=') for part in line.split()[1:] if not part.startswith('total='))} for line in Path('/proc/pressure/memory').read_text().splitlines()}
    except (OSError,ValueError):pressure={'status':'unavailable'}
    gpus=[]
    for card in sorted(Path('/sys/class/drm').glob('card[0-9]*')):
        if '-' in card.name:continue
        device=card/'device'
        try:
            if not (device/'vendor').is_file():continue
            vendor=(device/'vendor').read_text().strip();device_id=(device/'device').read_text().strip();vram=device/'mem_info_vram_total'
            gpus.append({'device':card.name,'vendor_id':vendor,'device_id':device_id,'vram_bytes':int(vram.read_text()) if vram.is_file() else None,'runtime_qualified':False,'reason':'Existing inference policy is CPU-only; no GPU device authorization/qualification exists.'})
        except (OSError,ValueError) as error:gpus.append({'device':card.name,'runtime_qualified':False,'reason':str(error)[:300]})
    root=Path(data_directory or Path.home());disk=shutil.disk_usage(root)
    static={'machine':platform.machine(),'physical_memory':total,'logical_cpus':os.cpu_count() or 1,'affinity_cpus':affinity,'cpu_flags':sorted(flags),'gpus':gpus,'effective_total':effective_total,'effective_cores':effective_cores}
    return {**static,'fingerprint':hashlib.sha256(json.dumps(static,sort_keys=True).encode()).hexdigest(),'available_memory':available,'effective_available':effective_available,'swap_total':int(mem.get('SwapTotal',['0'])[0])*1024,'swap_free':int(mem.get('SwapFree',['0'])[0])*1024,'pressure':pressure,'cgroup_constraints':constraints,'parent_pids_max':pids,'disk':{'total':disk.total,'free':disk.free},'execution_backend':'cpu','gpu_execution_qualified':False}

def memory_estimate(model,context=2048,observations=()):
    """A recommendation, not an availability gate for explicit manual attempts."""
    weights=model.get('weight_bytes',model.get('size',0));weights=weights if type(weights) is int and weights>=0 else 0
    info=model.get('model_info') or {};architecture=info.get('general.architecture') or (model.get('details') or {}).get('family') or ''
    layers=info.get(architecture+'.block_count');embedding=info.get(architecture+'.embedding_length');heads=info.get(architecture+'.attention.head_count');kv_heads=info.get(architecture+'.attention.head_count_kv')
    if all(type(v) is int and v>0 for v in (layers,embedding,heads,kv_heads)):
        kv=layers*(embedding//heads)*kv_heads*2*2*context
        kv=min(kv,1024**4)
    else:kv=64*MIB+context*32768
    estimate=weights+192*MIB+kv+64*MIB
    used=[]
    for row in observations:
        if row.get('model_digest')!=model.get('digest') or row.get('simulated') is not False or not row.get('inference_completed'):continue
        if type(row.get('peak_memory_bytes')) is not int or row['peak_memory_bytes']<=0:continue
        # Warm/shared page cache can make measured charge smaller than weights.
        measured=int(row['peak_memory_bytes']*1.15)+64*MIB
        if type(row.get('context_tokens')) is int and context>row['context_tokens']:measured+=max(0,context-row['context_tokens'])*32768
        estimate=max(estimate,measured);used.append(row.get('id'))
    return {'estimated_bytes':math.ceil(estimate/MIB)*MIB,'weight_bytes':weights,'kv_estimate':kv,'basis':'Verified local descriptor + runtime/generation allowance + KV estimate; measured peaks only raise the floor. Recommendations are not kernel limits.','observations_used':used}

def rank_models(models,observations=(),task='chat'):
    """Functional evidence and relevant capabilities precede size as a tie-break."""
    def rank(m):
        matching=[o for o in observations if o.get('model_digest')==m.get('digest') and o.get('simulated') is False and o.get('inference_completed')]
        owner=m.get('owner_priority',0);owner=owner if type(owner) is int and -100<=owner<=100 else 0
        relevant=task in m.get('verified_tasks',[]) or (task=='tools' and 'tools' in m.get('capabilities',[]))
        return (owner,bool(relevant),m.get('capability_priority',0),m.get('parameter_count') or 0,bool(matching),bool(m.get('runtime_inspected')),m.get('weight_bytes') or 0,m.get('name',''))
    return sorted(models,key=rank,reverse=True)

def plan(models,host,*,context_required=2048,output_tokens=192,observations=(),exclude=(),manual_names=None,experimental=False,manual_limit=None):
    """Return an explicit selection/resource plan. This grants no model-root access."""
    if type(context_required) is not int or not 512<=context_required<=32768:raise ValueError('Full required context must fit the existing trusted 512–32768 token protocol.')
    if type(experimental) is not bool:raise ValueError('Explicit experimental flag required.')
    reserve=max(384*MIB,min(1024*MIB,host['effective_total']//10));headroom=16*MIB
    cap=min(host['effective_total']-reserve,host['effective_available']-reserve-headroom)
    if manual_limit is not None:
        if type(manual_limit) is not int or manual_limit<256*MIB:raise ValueError('Invalid explicit resource ceiling.')
        if experimental and manual_names:cap=min(manual_limit,host['effective_total']-reserve)
        else:cap=min(cap,manual_limit)
    cap=max(0,cap//MIB*MIB)
    if cap<256*MIB:raise RuntimeError('RESOURCE_BLOCKED: less than 256 MiB remains after the mandatory host reserve.')
    cores=max(.01,float(host['effective_cores']));threads=max(1,min(8,int(math.ceil(cores))))
    tasks=min(128,max(64,threads*8))
    if host.get('parent_pids_max') is not None and host['parent_pids_max']<tasks+8:tasks=host['parent_pids_max']-8
    if tasks<16:raise RuntimeError('RESOURCE_BLOCKED: parent process limit cannot safely contain a protected inference worker.')
    candidates=[];rejected=[];requested=set(manual_names or ())
    for model in rank_models(models,observations):
        reason=model.get('unavailable_reason')
        if model.get('name') in exclude:reason='Already attempted for this request; bounded AUTO fallback excludes repeats.'
        if model.get('compatible') is False:reason=reason or 'Installed model is incompatible with this runtime/backend.'
        limit=model.get('context_length')
        if type(limit) is int and limit<context_required:reason='Model context is smaller than the complete required prompt budget.'
        estimate=memory_estimate(model,context_required,observations)
        if reason:rejected.append({'name':model['name'],'reason':reason});continue
        if estimate['estimated_bytes']>cap and model['name'] not in requested:
            rejected.append({'name':model['name'],'reason':'Conservative memory recommendation exceeds the safe automatic budget. Manual selection remains possible within enforced limits.','estimate':estimate});continue
        candidates.append((model,estimate))
    if requested:
        selected=[row for row in candidates if row[0]['name'] in requested]
        if {row[0]['name'] for row in selected}!=requested:raise RuntimeError('Selected exact model is unavailable or incompatible; no automatic substitution: '+json.dumps(rejected))
    elif candidates:selected=candidates[:1]
    else:raise RuntimeError('No viable AUTO candidate: '+json.dumps(rejected))
    # The registry/plan accepts more than two participants; the existing desktop
    # collaboration executor currently consumes A/B sequentially. No unqualified
    # parallel/GPU execution is silently enabled by this recommendation.
    return {'version':1,'selection':'manual' if requested else 'auto','models':[m['name'] for m,e in selected],'participants':[{'model':m['name'],'digest':m.get('digest'),'estimate':e} for m,e in selected],'execution':'sequential','memory_bytes':cap,'host_reserve_bytes':reserve,'tasks':tasks,'cpu_threads':threads,'cpu_quota_percent':max(1,int(cores*100)),'context_tokens':context_required,'output_tokens':min(output_tokens,context_required//2),'experimental':experimental,'hardware_fingerprint':host['fingerprint'],'rejected':rejected,'reason':'Best-ranked installed candidate within the protected CPU budget; actual runtime compatibility remains a launch/inference gate. Accuracy scores never block inference.','gpu_enabled':False}
