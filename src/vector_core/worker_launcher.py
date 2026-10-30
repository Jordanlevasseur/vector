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
        if self.process.poll() is None:
            self.process.terminate()
            try:self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:self.process.kill();self.process.wait(timeout=3)
        for stream in (self.process.stdin,self.process.stdout):stream.close()
        if getattr(self,'temporary',None):self.temporary.cleanup();self.temporary=None
    def request(self,payload,timeout,cancellation=None):
        if not self.qualified:raise InferenceError('Worker is closed/unqualified.')
        frame=json.dumps(payload,allow_nan=False).encode()+b'\n'
        if len(frame)>MAX_FRAME:raise InferenceError('Inference request too large.')
        end=time.monotonic()+timeout
        try:
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
                    if not chunk:raise InferenceError('Inference worker crashed or closed its channel.')
                    self.buffer+=chunk
                    if len(self.buffer)>MAX_FRAME:raise InferenceError('Excessive worker response.')
            raw,self.buffer=self.buffer.split(b'\n',1)
            from vector_core.portable import unique
            response=json.loads(raw,object_pairs_hook=unique)
            if not isinstance(response,dict) or set(response)!={'ok','result'}:raise InferenceError('Malformed worker response.')
            if response['ok'] is not True:
                result=response['result'];error=InferenceError(str(result.get('error'))[:1000] if isinstance(result,dict) else str(result)[:1000])
                error.raw_generation=result.get('partial') if isinstance(result,dict) else None
                raise error
            return response['result']
        except (OSError,ValueError,InferenceError) as error:
            self.close()
            if isinstance(error,InferenceError):raise
            raise InferenceError('Worker communication failed: '+str(error)) from error
    def _check(self,end,cancellation):
        if cancellation and cancellation.cancelled:raise InferenceError('Cancelled; isolated worker terminated.')
        if time.monotonic()>end:raise InferenceError('Inference timeout; isolated worker terminated.')
        if self.process.poll() is not None:raise InferenceError('Inference worker crashed.')


def launch(models_directory,*,memory_bytes=768*1024*1024,tasks=64):
    """Called only by trusted startup before the main strict filter. Fail closed."""
    model_root=safe_path(models_directory)
    if not model_root.is_dir() or not all((model_root/name).is_dir() for name in ('blobs','manifests')):raise InferenceError('Explicit model directory must contain blobs and manifests.')
    from vector_core.models import validate_layout
    validate_layout(model_root)
    if type(memory_bytes) is not int or not 256*1024*1024<=memory_bytes<=2*1024**3 or type(tasks) is not int or not 16<=tasks<=128:
        raise InferenceError('Invalid worker resource limits.')
    available=int(next(line.split()[1] for line in Path('/proc/meminfo').read_text().splitlines() if line.startswith('MemAvailable:')))*1024
    if available<memory_bytes+384*1024*1024:raise InferenceError('RESOURCE_BLOCKED: insufficient available RAM plus 384 MiB host reserve.')
    executables={}
    for executable in ('bwrap','systemd-run','systemctl','ollama'):
        located=shutil.which(executable)
        if not located:raise InferenceError('Required offline runtime unavailable: '+executable)
        path=Path(located).resolve()
        if not str(path).startswith(('/usr/bin/','/usr/local/bin/')) or path.stat().st_uid!=0 or path.stat().st_mode&0o022:
            raise InferenceError('Untrusted installed executable: '+executable)
        executables[executable]=str(path)
    binary=Path(executables['ollama'])
    runtime_directory='/run/user/'+str(os.getuid())
    local_environment={'PATH':'/usr/bin:/bin','HOME':str(Path.home()),'XDG_RUNTIME_DIR':runtime_directory,
                       'DBUS_SESSION_BUS_ADDRESS':'unix:path='+runtime_directory+'/bus','LC_ALL':'C.UTF-8'}
    unit='vector-inference-'+uuid4().hex
    package=Path(__file__).resolve().parent
    command=[executables['systemd-run'],'--user','--scope','--quiet','--unit='+unit,'--property=MemoryMax='+str(memory_bytes),
             '--property=TasksMax='+str(tasks),'--property=CPUQuota=100%',
             executables['bwrap'],'--unshare-all','--unshare-user','--disable-userns','--assert-userns-disabled','--die-with-parent','--new-session',
             '--cap-drop','ALL','--clearenv','--setenv','PATH','/usr/bin:/runtime','--setenv','HOME','/tmp/home',
             '--setenv','OLLAMA_HOST','127.0.0.1:11434','--setenv','OLLAMA_MODELS','/models','--setenv','OLLAMA_NUM_PARALLEL','1',
             '--setenv','OLLAMA_MAX_LOADED_MODELS','1','--setenv','OLLAMA_LLM_LIBRARY','cpu','--setenv','OLLAMA_VULKAN','false','--setenv','CUDA_VISIBLE_DEVICES','-1','--setenv','HIP_VISIBLE_DEVICES','-1','--setenv','ROCR_VISIBLE_DEVICES','-1','--setenv','GGML_VK_VISIBLE_DEVICES','-1','--setenv','GOMAXPROCS','2','--setenv','OMP_NUM_THREADS','2','--setenv','OPENBLAS_NUM_THREADS','2','--setenv','OLLAMA_NO_CLOUD','1','--setenv','OLLAMA_NOPRUNE','1','--setenv','OLLAMA_NOHISTORY','1','--setenv','OLLAMA_MAX_QUEUE','1','--setenv','OLLAMA_LOAD_TIMEOUT','120s',
             '--ro-bind','/usr','/usr','--ro-bind','/lib','/lib','--ro-bind','/lib64','/lib64','--proc','/proc','--dev','/dev',
             '--size','67108864','--tmpfs','/tmp','--dir','/tmp/home','--setenv','VECTOR_OLLAMA_BINARY',str(binary),
             '--size','67108864','--tmpfs','/models','--ro-bind',str(model_root/'blobs'),'/models/blobs',
             '--ro-bind',str(model_root/'manifests'),'/models/manifests','--dir','/models/manifests-v2',
             '--ro-bind',str(package),'/application/vector_core',
             '--setenv','PYTHONPATH','/application','--chdir','/tmp','/usr/bin/python3','-m','vector_core.inference_worker']
    if (model_root/'manifests-v2').is_dir():
        at=command.index('--chdir');command[at:at]=['--ro-bind',str(model_root/'manifests-v2'),'/models/manifests-v2']
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
    transport.qualified=True  # Private object; not returned until independent parent checks finish.
    try:
        report=transport.request({'operation':'qualify'},15)
        host_net=str(Path('/proc/self/ns/net').readlink())
        if (not isinstance(report,dict) or report.get('network_namespace')==host_net or report.get('routes') is not False
            or report.get('external_denied') is not True or report.get('nested_userns_denied') is not True
            or report.get('host_home_absent') is not True or report.get('model_blobs_readonly') is not True
            or report.get('shared_model_home_hidden') is not True or report.get('cpu_only') is not True):
            raise InferenceError('Worker namespace/egress qualification failed.')
        details=subprocess.run([executables['systemctl'],'--user','show',unit+'.scope','--property=ControlGroup','--property=MemoryMax','--property=TasksMax'],
                               capture_output=True,text=True,timeout=5,check=True,env=local_environment)
        properties=dict(line.split('=',1) for line in details.stdout.splitlines() if '=' in line)
        cgroup=Path('/sys/fs/cgroup')/properties['ControlGroup'].lstrip('/')
        if int((cgroup/'memory.max').read_text())!=memory_bytes or int((cgroup/'pids.max').read_text())!=tasks:
            raise InferenceError('Per-worker memory/pids controls were not enforced.')
        quota,period=(cgroup/'cpu.max').read_text().split()
        if quota=='max' or int(quota)>int(period):raise InferenceError('Per-worker CPU quota was not enforced.')
        report.update(cpu_max=(cgroup/'cpu.max').read_text().strip(),memory_max=memory_bytes,pids_max=tasks,cgroup=str(cgroup),unit=unit)
        transport.report=report;transport.runtime_version=report['runtime_version'];transport.model_directory=model_root
        return transport
    except Exception as error:
        diagnostic.seek(0);details=diagnostic.read(4096).decode('utf-8','replace')
        transport.close()
        raise InferenceError(str(error)+((': '+details) if details else '')) from error
    finally:diagnostic.close()


def launch_managed(**limits):
    temporary=tempfile.TemporaryDirectory(prefix='vector_managed_runtime_')
    root=Path(temporary.name)
    for name in ('blobs','manifests','manifests-v2'):(root/name).mkdir(mode=0o700)
    try:transport=launch(root,**limits)
    except Exception:temporary.cleanup();raise
    transport.temporary=temporary;transport.model_directory=root;transport.managed=True
    return transport
