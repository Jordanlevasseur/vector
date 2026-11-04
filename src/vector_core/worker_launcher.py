"""Fixed-command isolated Ollama launcher; no shared daemon or remote endpoint."""
import json
import os
from pathlib import Path
import select
import shutil
import signal
import stat
import subprocess
import sys
import time
import tempfile
from uuid import uuid4
from vector_core.inference import InferenceError
from vector_core.storage import safe_path

MAX_FRAME=1024*1024

class WorkerTransport:
    qualified=False
    def __init__(self,process,report):
        self.process=process;self.report=report;self.qualified=True;self.buffer=b''
        self.runtime_version=report['runtime_version']
    @property
    def retained_fds(self):return (self.process.stdin.fileno(),self.process.stdout.fileno())
    def close(self):
        self.qualified=False
        if getattr(self,'service_unit',None):
            # The service belongs to the user manager, not to the pipe client.
            # Terminate its entire cgroup and verify cleanup before reuse.
            stopped=subprocess.run(['/usr/bin/systemctl','--user','stop',self.service_unit],capture_output=True,timeout=10,env=self.service_environment)
            if stopped.returncode and 'not loaded' not in stopped.stderr.decode('utf-8','replace') and 'not found' not in stopped.stderr.decode('utf-8','replace'):raise InferenceError('Worker service stop failed; cleanup unverified.',code='RUNNER_CLEANUP_FAILED')
            cg=Path(self.report.get('cgroup','/nonexistent'))
            if cg.exists() and (cg/'cgroup.events').exists() and 'populated 1' in (cg/'cgroup.events').read_text():
                subprocess.run(['/usr/bin/systemctl','--user','kill','--signal=KILL',self.service_unit],capture_output=True,timeout=5,env=self.service_environment)
                if cg.exists() and 'populated 1' in (cg/'cgroup.events').read_text():raise InferenceError('Worker service cleanup could not be verified; restart refused.',code='RUNNER_CLEANUP_FAILED')
            self.service_unit=None
        if self.process.poll() is None:
            self.process.terminate()
            try:self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:self.process.kill();self.process.wait(timeout=3)
        for stream in (self.process.stdin,self.process.stdout):stream.close()
        if getattr(self,'temporary',None):self.temporary.cleanup();self.temporary=None
    def request(self,payload,timeout,cancellation=None):
        if not self.qualified:raise InferenceError('Worker is closed/unqualified. Restart VECTOR to qualify a new isolated worker; saved conversation work remains available.',code='WORKER_CLOSED',stage='availability')
        frame=json.dumps(payload,allow_nan=False).encode()+b'\n'
        if len(frame)>MAX_FRAME:raise InferenceError('Inference request too large.')
        end=time.monotonic()+timeout
        self.resource_watch=None
        try:
            if payload.get('operation')=='generate' and self.report.get('cgroup'):
                try:
                    vm=dict(line.split() for line in Path('/proc/vmstat').read_text().splitlines())
                    self.resource_watch={'next':0,'pressure_since':None,'swap_out_initial':int(vm['pswpout']),'oom_initial':int(vm['oom_kill']),'samples':0,'peak_memory_bytes':0,'peak_swap_bytes':0,'max_full_pressure':0,'minimum_host_available':2**63}
                except (OSError,ValueError,KeyError) as error:
                    raise InferenceError('RESOURCE_BLOCKED: memory monitor failed closed: '+str(error)) from error
            # Bounded requests are small; nonblocking pipe writes avoid a wedged worker.
            fd=self.process.stdin.fileno();os.set_blocking(fd,False);sent=0
            while sent<len(frame):
                self._check(end,cancellation)
                if select.select([], [fd], [], .05)[1]:
                    try:sent+=os.write(fd,frame[sent:])
                    except BlockingIOError:pass
            while b'\n' not in self.buffer:
                self._check(end,cancellation)
                if select.select([self.process.stdout],[],[],.05)[0]:
                    chunk=os.read(self.process.stdout.fileno(),65536)
                    if not chunk:raise InferenceError('Inference worker crashed or closed its channel.',code='WORKER_CRASH',stage='runtime-transport')
                    self.buffer+=chunk
                    if len(self.buffer)>MAX_FRAME:raise InferenceError('Excessive worker response.')
            raw,self.buffer=self.buffer.split(b'\n',1)
            from vector_core.portable import unique
            response=json.loads(raw,object_pairs_hook=unique)
            if not isinstance(response,dict) or set(response)!={'ok','result'}:raise InferenceError('Malformed worker response.')
            if response['ok'] is not True:
                result=response['result'];error=InferenceError(str(result.get('error'))[:1000] if isinstance(result,dict) else str(result)[:1000])
                if isinstance(result,dict):
                    error.stage=result.get('stage','inference')
                    error.code={'model-discovery':'MODEL_DISCOVERY_FAILED','model-metadata':'MODEL_METADATA_FAILED','model-generation':'MODEL_GENERATION_FAILED','runner-cleanup':'RUNNER_CLEANUP_FAILED','prompt-preparation':'CONTEXT_BUDGET'}.get(error.stage,'INFERENCE_FAILED')
                error.raw_generation=result.get('partial') if isinstance(result,dict) else None
                raise error
            result=response['result']
            if self.resource_watch and isinstance(result,dict):
                result['resources']={k:v for k,v in self.resource_watch.items() if k not in {'next','pressure_since'}}
            return result
        except (OSError,ValueError,InferenceError) as error:
            # Retain the last bounded observation for runtime errors, timeouts
            # and crashes too: a missing answer alone cannot diagnose pressure.
            failure=error if isinstance(error,InferenceError) else InferenceError('Worker communication failed: '+str(error))
            if self.report.get('cgroup'):
                try:
                    final_events={k:int(v) for k,v in (line.split() for line in (Path(self.report['cgroup'])/'memory.events').read_text().splitlines())}
                    if self.resource_watch:self.resource_watch['final_cgroup_memory_events']=final_events
                    if final_events.get('oom_kill',0):
                        failure=InferenceError('Kernel cgroup memory kill: memory.events oom_kill='+str(final_events['oom_kill'])+', MemoryMax='+str(self.report.get('memory_max'))+' bytes. No accuracy evaluation caused this failure.',code='KERNEL_MEMORY_LIMIT',stage='model-loading-or-inference')
                except (OSError,ValueError):pass
            failure.operation=payload.get('operation')
            if failure.code=='INFERENCE_TIMEOUT':failure.stage='model-discovery' if payload.get('operation')=='discover' else 'model-execution'
            if self.resource_watch:
                failure.resources={k:v for k,v in self.resource_watch.items() if k not in {'next','pressure_since'}}
            self.close()
            if failure is error:raise
            raise failure from error
    def _check(self,end,cancellation):
        if getattr(self,'extra_check',None):self.extra_check()
        if cancellation and cancellation.cancelled:raise InferenceError('Cancelled; isolated worker terminated.')
        if time.monotonic()>end:raise InferenceError('Inference timeout; isolated worker terminated.',code='INFERENCE_TIMEOUT',stage='transport')
        if self.process.poll() is not None:raise InferenceError('Inference worker crashed.',code='WORKER_CRASH',stage='runtime-transport')
        watch=getattr(self,'resource_watch',None)
        if watch and time.monotonic()>=watch['next']:
            watch['next']=time.monotonic()+.5
            try:
                available=int(next(l.split()[1] for l in Path('/proc/meminfo').read_text().splitlines() if l.startswith('MemAvailable:')))*1024
                vm=dict(line.split() for line in Path('/proc/vmstat').read_text().splitlines())
                pressure=float(next(l for l in Path('/proc/pressure/memory').read_text().splitlines() if l.startswith('full ')).split()[1].split('=')[1])
                cg=Path(self.report['cgroup']);used=int((cg/'memory.current').read_text());swap=int((cg/'memory.swap.current').read_text())
                events=dict(line.split() for line in (cg/'memory.events').read_text().splitlines())
                statistics=dict(line.split() for line in (cg/'memory.stat').read_text().splitlines())
                # Fixed keys bound persistent evidence and distinguish anonymous
                # allocation from file-cache reclaim/refaults at the kernel cap.
                events={key:int(events[key]) for key in ('max','oom','oom_kill')}
                statistics={key:int(statistics[key]) for key in ('anon','file','pgmajfault','workingset_refault_file')}
                watch.update(samples=watch['samples']+1,peak_memory_bytes=max(used,watch['peak_memory_bytes']),peak_swap_bytes=max(swap,watch['peak_swap_bytes']),max_full_pressure=max(pressure,watch['max_full_pressure']),minimum_host_available=min(available,watch['minimum_host_available']),host_swap_out_bytes=(int(vm['pswpout'])-watch['swap_out_initial'])*os.sysconf('SC_PAGE_SIZE'),current_host_available_bytes=available,current_full_pressure=pressure,current_memory_bytes=used,current_swap_bytes=swap,cgroup_memory_events=events,cgroup_memory_stat=statistics)
                watch['pressure_since']=(watch['pressure_since'] or time.monotonic()) if pressure>30 else None
                violations=[]
                advisory=[]
                if available<384*1024*1024:violations.append('host available RAM below384MiB ('+str(available)+' bytes)')
                if swap:violations.append('worker swap is nonzero ('+str(swap)+' bytes)')
                if int(vm['oom_kill'])>watch['oom_initial']:violations.append('host OOM-kill counter increased')
                if watch['host_swap_out_bytes']>128*1024*1024:advisory.append('host swap-out exceeded128MiB ('+str(watch['host_swap_out_bytes'])+' bytes)')
                if watch['pressure_since'] and time.monotonic()-watch['pressure_since']>15:advisory.append('full-memory PSI above30percent for15seconds (avg10='+str(pressure)+')')
                if self.report.get('experimental_memory') is True:
                    if advisory:watch['experimental_advisories']=advisory
                else:violations.extend(advisory)
                if violations:
                    error=InferenceError('RESOURCE_BLOCKED: '+'; '.join(violations),code='RESOURCE_LIMIT',stage='resource-protection');error.resources={k:v for k,v in watch.items() if k not in {'next','pressure_since'}};raise error
            except (OSError,ValueError,StopIteration,KeyError) as error:raise InferenceError('RESOURCE_BLOCKED: memory monitor failed closed: '+str(error),code='RESOURCE_MONITOR_FAILED',stage='resource-protection') from error


def launch(models_directory,*,memory_bytes=768*1024*1024,tasks=64,additional_model_directories=(),experimental=False,service_mode=False,supervisor_unit=None,selected_models=None,host_network_namespace=None,source_package=None,cpu_threads=2,cpu_quota_percent=100,extra_check=None,trusted_executables=None):
    """Called only by trusted startup before the main strict filter. Fail closed."""
    model_root=safe_path(models_directory)
    if not model_root.is_dir() or not all((model_root/name).is_dir() for name in ('blobs','manifests')):raise InferenceError('Explicit model directory must contain blobs and manifests.')
    from vector_core.models import validate_layout
    validate_layout(model_root)
    if not isinstance(additional_model_directories,(list,tuple)) or len(additional_model_directories)>7:raise InferenceError('Select at most eight explicit local stores.')
    model_roots=tuple(dict.fromkeys([model_root,*[validate_layout(p) for p in additional_model_directories]]))
    if type(memory_bytes) is not int or not 256*1024*1024<=memory_bytes<=(1024**4 if service_mode else 2*1024**3) or type(tasks) is not int or not 16<=tasks<=128:
        raise InferenceError('Invalid worker resource limits.')
    if type(cpu_threads) is not int or not 1<=cpu_threads<=8 or type(cpu_quota_percent) is not int or not 1<=cpu_quota_percent<=65536:raise InferenceError('Invalid CPU resource limits.')
    if type(experimental) is not bool:raise InferenceError('Experimental memory selection must be a boolean.')
    available=int(next(line.split()[1] for line in Path('/proc/meminfo').read_text().splitlines() if line.startswith('MemAvailable:')))*1024
    if available<384*1024*1024 or not experimental and available<memory_bytes+384*1024*1024:raise InferenceError('RESOURCE_BLOCKED: insufficient available RAM plus 384 MiB host reserve.')
    executables={}
    for executable in ('bwrap','systemd-run','systemctl','ollama'):
        located=trusted_executables.get(executable,{}).get('path') if trusted_executables is not None else shutil.which(executable)
        if not located:raise InferenceError('Required offline runtime unavailable: '+executable)
        path=Path(located).resolve()
        if trusted_executables is None:
            if not str(path).startswith(('/usr/bin/','/usr/local/bin/')) or path.stat().st_uid!=0 or path.stat().st_mode&0o022:
                raise InferenceError('Untrusted installed executable: '+executable)
        else:
            # The outer controller user namespace cannot represent host root.
            # Verify the host-root-owned executable fingerprint captured before
            # entry; never accept this mapping over the desktop/model RPC.
            import hashlib
            expected=trusted_executables.get(executable,{})
            digest=hashlib.sha256()
            with path.open('rb') as source:
                while chunk:=source.read(1024*1024):digest.update(chunk)
            if expected!={'path':str(path),'sha256':digest.hexdigest()} or path.stat().st_mode&0o022:raise InferenceError('Trusted startup executable changed: '+executable)
        executables[executable]=str(path)
    binary=Path(executables['ollama'])
    runtime_directory='/run/user/'+str(os.getuid())
    local_environment={'PATH':'/usr/bin:/bin','HOME':str(Path.home()),'XDG_RUNTIME_DIR':runtime_directory,
                       'DBUS_SESSION_BUS_ADDRESS':'unix:path='+runtime_directory+'/bus','LC_ALL':'C.UTF-8','SYSTEMD_IGNORE_CHROOT':'1'}
    unit='vector-inference-'+uuid4().hex
    package=Path(source_package) if source_package else Path(__file__).resolve().parent
    command=[executables['systemd-run'],'--user','--scope','--quiet','--unit='+unit,'--property=MemoryMax='+str(memory_bytes),
             '--property=TasksMax='+str(tasks),'--property=CPUQuota='+str(cpu_quota_percent)+'%','--property=MemorySwapMax=0',
             executables['bwrap'],'--unshare-all','--unshare-user','--disable-userns','--assert-userns-disabled','--die-with-parent','--new-session',
             '--cap-drop','ALL','--clearenv','--setenv','PATH','/usr/bin:/runtime','--setenv','HOME','/tmp/home',
             '--setenv','OLLAMA_HOST','127.0.0.1:11434','--setenv','OLLAMA_MODELS','/models','--setenv','OLLAMA_NUM_PARALLEL','1',
             '--setenv','OLLAMA_MAX_LOADED_MODELS','1','--setenv','OLLAMA_LLM_LIBRARY','cpu','--setenv','OLLAMA_VULKAN','false','--setenv','CUDA_VISIBLE_DEVICES','-1','--setenv','HIP_VISIBLE_DEVICES','-1','--setenv','ROCR_VISIBLE_DEVICES','-1','--setenv','GGML_VK_VISIBLE_DEVICES','-1','--setenv','GOMAXPROCS',str(cpu_threads),'--setenv','OMP_NUM_THREADS',str(cpu_threads),'--setenv','OPENBLAS_NUM_THREADS',str(cpu_threads),'--setenv','VECTOR_CPU_THREADS',str(cpu_threads),'--setenv','OLLAMA_NO_CLOUD','1','--setenv','OLLAMA_NOPRUNE','1','--setenv','OLLAMA_NOHISTORY','1','--setenv','OLLAMA_MAX_QUEUE','1','--setenv','OLLAMA_LOAD_TIMEOUT','120s',
             '--ro-bind','/usr','/usr','--ro-bind','/lib','/lib','--ro-bind','/lib64','/lib64','--proc','/proc','--dev','/dev',
             '--size','67108864','--tmpfs','/tmp','--dir','/tmp/home','--setenv','VECTOR_OLLAMA_BINARY',str(binary),
             '--size','67108864','--tmpfs','/models','--ro-bind',str(model_root/'blobs'),'/models/blobs',
             '--ro-bind',str(model_root/'manifests'),'/models/manifests','--dir','/models/manifests-v2',
             '--ro-bind',str(package),'/application/vector_core',
             '--setenv','PYTHONPATH','/application','--chdir','/tmp','/usr/bin/python3','-m','vector_core.inference_worker']
    if service_mode:
        command.remove('--scope');command[2:2]=['--pipe','--wait','--collect']
        if not isinstance(supervisor_unit,str) or not __import__('re').fullmatch(r'vector-supervisor-[a-f0-9]{32}\.service',supervisor_unit):raise InferenceError('Fixed supervisor unit required.')
        at=command.index(executables['bwrap']);command[at:at]=['--property=BindsTo='+supervisor_unit,'--property=After='+supervisor_unit,'--property=KillMode=control-group','--property=TimeoutStopSec=5']
    if experimental:command[command.index('OLLAMA_LOAD_TIMEOUT')+1]='240s'
    if (model_root/'manifests-v2').is_dir():
        at=command.index('--chdir');command[at:at]=['--ro-bind',str(model_root/'manifests-v2'),'/models/manifests-v2']
    if len(model_roots)>1 or selected_models is not None:
        # Compose local stores inside the private tmpfs namespace. No copied
        # weights, host symlinks, shared daemon, or writable source mounts.
        from vector_core.models import runtime_files
        mounts=runtime_files(model_roots,selected_models)
        for source,target in ((str(model_root/'blobs'),'/models/blobs'),(str(model_root/'manifests'),'/models/manifests'),(str(model_root/'manifests-v2'),'/models/manifests-v2')):
            for i in range(len(command)-2,-1,-1):
                if command[i:i+3]==['--ro-bind',source,target]:del command[i:i+3]
        at=command.index('--chdir');bindings=['--size','67108864','--tmpfs','/models/blobs','--size','67108864','--tmpfs','/models/manifests']
        for relative,item in sorted(mounts.items()):bindings+=['--ro-bind',str(item['path']),'/models/'+relative]
        bindings+=['--remount-ro','/models/blobs','--remount-ro','/models/manifests']
        command[at:at]=bindings
    # The Ollama runner library directory is installation data, never arbitrary selected code.
    libraries=Path('/usr/local/lib/ollama')
    if libraries.is_dir():
        at=command.index('--proc');command[at:at]=['--ro-bind',str(libraries),'/usr/local/lib/ollama']
    for hidden in (Path('/usr/share/ollama'),libraries/'cuda_v12',libraries/'cuda_v13',libraries/'vulkan'):
        if hidden.is_dir():
            at=command.index('--proc');command[at:at]=['--size','4096','--tmpfs',str(hidden)]
    diagnostic=tempfile.TemporaryFile()
    process=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=diagnostic,bufsize=0,start_new_session=True,env=local_environment)
    transport=WorkerTransport(process,{'runtime_version':'unqualified'})
    if service_mode:transport.service_unit=unit+'.service';transport.service_environment=local_environment
    transport.extra_check=extra_check
    transport.qualified=True  # Private object; not returned until independent parent checks finish.
    try:
        report=transport.request({'operation':'qualify'},75)
        host_net=host_network_namespace or str(Path('/proc/self/ns/net').readlink())
        if (not isinstance(report,dict) or report.get('network_namespace')==host_net or report.get('routes') is not False
            or report.get('external_denied') is not True or report.get('nested_userns_denied') is not True
            or report.get('host_home_absent') is not True or report.get('model_blobs_readonly') is not True
            or report.get('shared_model_home_hidden') is not True or report.get('cpu_only') is not True
            or report.get('transparent_hugepages_disabled') is not True):
            raise InferenceError('Worker namespace/egress qualification failed.')
        details=subprocess.run([executables['systemctl'],'--user','show',unit+('.service' if service_mode else '.scope'),'--property=ControlGroup','--property=MemoryMax','--property=TasksMax'],
                               capture_output=True,text=True,timeout=5,check=True,env=local_environment)
        properties=dict(line.split('=',1) for line in details.stdout.splitlines() if '=' in line)
        if not properties.get('ControlGroup'):raise InferenceError('User manager did not report an enforced worker cgroup: '+details.stdout[:500]+' '+details.stderr[:500])
        cgroup=Path('/sys/fs/cgroup')/properties['ControlGroup'].lstrip('/')
        if int((cgroup/'memory.max').read_text())!=memory_bytes or int((cgroup/'pids.max').read_text())!=tasks:
            raise InferenceError('Per-worker memory/pids controls were not enforced.')
        if int((cgroup/'memory.swap.max').read_text())!=0:raise InferenceError('Zero worker swap was not enforced.')
        quota,period=(cgroup/'cpu.max').read_text().split()
        if quota=='max' or int(quota)*100>int(period)*cpu_quota_percent:raise InferenceError('Per-worker CPU quota was not enforced.')
        report.update(cpu_threads=cpu_threads,supervisor_bound=service_mode,cpu_max=(cgroup/'cpu.max').read_text().strip(),memory_max=memory_bytes,memory_swap_max=0,pids_max=tasks,cgroup=str(cgroup),unit=unit)
        report['experimental_memory']=experimental
        if experimental:report['resource_notice']='Experimental memory: estimates, sustained PSI and host swap-out are advisory. Crashes/resource exhaustion are possible. Kernel memory, zero-worker-swap, CPU/pids, isolation, host reserve and OOM stops remain enforced.'
        transport.report=report;transport.runtime_version=report['runtime_version'];transport.model_directory=model_root
        transport.model_directories=model_roots
        return transport
    except Exception as error:
        diagnostic.seek(0);details=diagnostic.read(4096).decode('utf-8','replace')
        transport.close()
        raise InferenceError(str(error)+((': '+details) if details else ''),code=getattr(error,'code','QUALIFICATION_FAILED'),stage=getattr(error,'stage','runtime-qualification')) from error
    finally:diagnostic.close()


def launch_managed(**limits):
    temporary=tempfile.TemporaryDirectory(prefix='vector_managed_runtime_')
    root=Path(temporary.name)
    for name in ('blobs','manifests','manifests-v2'):(root/name).mkdir(mode=0o700)
    try:transport=launch(root,**limits)
    except Exception:temporary.cleanup();raise
    transport.temporary=temporary;transport.model_directory=root;transport.managed=True
    return transport


def read_runtime_profile(path=None):
    """Small owner-controlled startup declaration, read before strict core policy.

    It contains paths and bounded limits only, never executable startup options.
    VECTOR data is still opened only after kernel network enforcement.
    """
    path=Path(path) if path else Path.home()/'.config/vector/local-inference.json'
    if not path.exists():return None
    if any(p.is_symlink() for p in (path,*path.parents)) or path.stat().st_uid!=os.getuid() or path.stat().st_mode&0o077 or path.parent.stat().st_uid!=os.getuid() or path.parent.stat().st_mode&0o022:raise InferenceError('Local inference startup declaration must be private, owned by this user and symlink-free.')
    from vector_core.intake import read_file
    from vector_core.portable import unique
    settings=json.loads(read_file(path,16384),object_pairs_hook=unique)
    if not isinstance(settings,dict) or set(settings)-{'model_directories','memory_bytes','tasks','experimental_memory'} or not {'model_directories','memory_bytes','tasks'}<=set(settings):raise InferenceError('Invalid local inference startup declaration.')
    roots=settings['model_directories']
    if not isinstance(roots,list) or not 1<=len(roots)<=8 or any(not isinstance(p,str) or not Path(p).is_absolute() for p in roots):raise InferenceError('Explicit absolute local model stores required.')
    if type(settings['memory_bytes']) is not int or not 256*1024*1024<=settings['memory_bytes']<=2*1024**3 or type(settings['tasks']) is not int or not 16<=settings['tasks']<=128 or type(settings.get('experimental_memory',False)) is not bool:raise InferenceError('Invalid fixed runtime limits.')
    return settings


def save_runtime_options(path=None,*,memory_mib,experimental,acknowledged=False):
    path=Path(path) if path else Path.home()/'.config/vector/local-inference.json'
    settings=read_runtime_profile(path)
    if settings is None:raise InferenceError('No startup profile exists. Select an authorized local model folder first.')
    if type(memory_mib) is not int or not 256<=memory_mib<=2048 or type(experimental) is not bool:raise ValueError('Choose256–2048MiB and an explicit experimental boolean.')
    if experimental and acknowledged is not True:raise PermissionError('Acknowledge possible crashes and resource exhaustion before enabling experimental memory.')
    settings.update(memory_bytes=memory_mib*1024*1024,experimental_memory=experimental)
    from vector_core.intake import write_new_file
    temporary=path.with_name(path.name+'.'+uuid4().hex+'.tmp')
    try:
        write_new_file(temporary,(json.dumps(settings,indent=2)+'\n').encode());temporary.chmod(0o600);os.replace(temporary,path)
        from vector_core.maintenance import sync
        sync(path)
    finally:
        if temporary.exists():temporary.unlink()
    return {'saved':True,'restart_required':True,'settings':settings,'message':'Saved. Close and reopen VECTOR to qualify a new isolated runtime with these limits. Models, model selection and knowledge were not changed.'}


def desktop_runtime(path=None):
    settings=read_runtime_profile(path)
    if settings is None:return None
    roots=settings['model_directories']
    if settings.get('experimental_memory') is True:return launch(roots[0],additional_model_directories=roots[1:],memory_bytes=settings['memory_bytes'],tasks=settings['tasks'],experimental=True)
    try:return launch(roots[0],additional_model_directories=roots[1:],memory_bytes=settings['memory_bytes'],tasks=settings['tasks'])
    except InferenceError as error:
        if 'RESOURCE_BLOCKED' not in str(error) or type(settings['memory_bytes']) is not int or settings['memory_bytes']<=768*1024*1024:raise
        # Preserve the exact startup reserve and every kernel/live monitor rule.
        # A fixed768MiB fallback needlessly discarded safe available capacity.
        # Select only a SMALLER ceiling, with16MiB extra race/reclaim headroom.
        available=int(next(line.split()[1] for line in Path('/proc/meminfo').read_text().splitlines() if line.startswith('MemAvailable:')))*1024
        ceiling=min(settings['memory_bytes']-1024*1024,available-(384+16)*1024*1024)
        ceiling=ceiling//(1024*1024)*(1024*1024)
        if ceiling<256*1024*1024:raise
        transport=launch(roots[0],additional_model_directories=roots[1:],memory_bytes=ceiling,tasks=settings['tasks'])
        transport.report['requested_memory_max']=settings['memory_bytes'];transport.report['resource_notice']='Larger startup profile blocked: '+str(error)+'. A smaller '+str(ceiling//(1024*1024))+'MiB ceiling is active with the host reserve preserved; oversized models remain unavailable.'
        return transport
