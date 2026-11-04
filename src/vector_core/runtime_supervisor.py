"""Offline, fixed-command runtime control. Never accepts paths or commands over RPC.

A small, data-blind service retains the user-manager connection. The desktop
retains pipes only. Each inference service has its own fully qualified namespace
and cgroup, and is BindsTo this controller for crash cleanup.
"""
import json
import os
from pathlib import Path
import select
import signal
import subprocess
import sys
import time
from uuid import uuid4
from vector_core.inference import InferenceError
from vector_core.portable import unique
from vector_core.worker_launcher import MAX_FRAME


def encode(value):
    raw=json.dumps(value,allow_nan=False).encode()+b'\n'
    if len(raw)>MAX_FRAME:raise InferenceError('Runtime control frame exceeds1MiB.')
    return raw

class SupervisorProxy:
    """Retained pipe capability; closing a failed worker leaves restart available."""
    qualified=False
    managed=False
    def __init__(self,process,unit,roots):
        self.process=process;self.unit=unit;self.model_directories=tuple(Path(p) for p in roots);self.model_directory=self.model_directories[0] if roots else None
        self.report={};self.runtime_version='not-started';self.buffer=b'';self.serial=0;self.abandoned=None;self.last_plan=None
    @property
    def retained_fds(self):return (self.process.stdin.fileno(),self.process.stdout.fileno())+((self.process.stderr.fileno(),) if self.process.stderr is not None else ())
    def diagnostic(self):
        stream=self.process.stderr
        if stream is None:return ''
        chunks=[];size=0
        while size<65536 and select.select([stream],[],[],0)[0]:
            part=os.read(stream.fileno(),min(4096,65536-size))
            if not part:break
            chunks.append(part);size+=len(part)
        return b''.join(chunks)[-8000:].decode('utf-8','replace')
    def _write(self,value):
        frame=encode(value);fd=self.process.stdin.fileno();os.set_blocking(fd,False);sent=0;end=time.monotonic()+5
        # SIGUSR1 may interrupt the wait, never half of a JSON frame.
        old=signal.pthread_sigmask(signal.SIG_BLOCK,{signal.SIGUSR1})
        try:
            while sent<len(frame):
                if self.process.poll() is not None or time.monotonic()>end:
                    self.qualified=False
                    raise InferenceError('Runtime controller write failed; exit='+str(self.process.poll())+'; '+self.diagnostic(),code='SUPERVISOR_CLOSED',stage='runtime-control')
                if select.select([], [fd], [], .05)[1]:
                    try:sent+=os.write(fd,frame[sent:])
                    except BlockingIOError:pass
        finally:signal.pthread_sigmask(signal.SIG_SETMASK,old)
    def _read(self,expected,timeout,cancellation=None):
        end=time.monotonic()+timeout
        while b'\n' not in self.buffer:
            if cancellation and cancellation.cancelled:raise InferenceError('Cancelled.',code='CANCELLED')
            if time.monotonic()>end:raise InferenceError('Runtime control deadline reached.',code='INFERENCE_TIMEOUT',stage='runtime-control')
            if select.select([self.process.stdout],[],[],.05)[0]:
                chunk=os.read(self.process.stdout.fileno(),65536)
                if not chunk:
                    self.qualified=False
                    raise InferenceError('Protected runtime controller exited; exit='+str(self.process.poll())+'; '+self.diagnostic(),code='SUPERVISOR_CLOSED',stage='runtime-control')
                self.buffer+=chunk
                if len(self.buffer)>MAX_FRAME:raise InferenceError('Excessive runtime control response.')
        raw,self.buffer=self.buffer.split(b'\n',1);reply=json.loads(raw,object_pairs_hook=unique)
        if not isinstance(reply,dict) or set(reply)!={'id','ok','result'} or reply['id']!=expected or type(reply['ok']) is not bool:raise InferenceError('Runtime control protocol mismatch.')
        self.reply_received=True
        if not reply['ok']:
            result=reply['result'];error=InferenceError(result['error'],code=result.get('code','INFERENCE_FAILED'),stage=result.get('stage','runtime-control'))
            for field in ('resources','raw_generation'):setattr(error,field,result.get(field))
            self.qualified=False;raise error
        return reply['result']
    def call(self,payload,timeout=90,cancellation=None):
        if self.abandoned is not None:
            abandoned=self.abandoned;self.abandoned=None
            try:self._read(abandoned,20)
            except InferenceError as error:
                if error.code in {'SUPERVISOR_CLOSED','INFERENCE_TIMEOUT'}:raise
        self.serial+=1;request_id=self.serial
        self.reply_received=False
        self._write({'id':request_id,'payload':payload})
        try:return self._read(request_id,timeout,cancellation)
        except BaseException:
            # Cancellation is an inert protocol message, not a signal/command.
            # Drain the abandoned reply before a subsequent request.
            if not self.reply_received:
                if self.process.poll() is None:
                    self.abandoned=request_id
                    try:self._write({'id':request_id,'payload':{'operation':'cancel'}})
                    except (OSError,InferenceError):self.qualified=False
                else:self.qualified=False;self.abandoned=None
            raise
    def ensure(self,plan):
        self.qualified=False
        result=self.call({'operation':'start','plan':plan},150)
        self.report=result['report'];self.runtime_version=self.report['runtime_version'];self.last_plan=plan;self.qualified=True
        return result
    def request(self,payload,timeout,cancellation=None):
        if not self.qualified:raise InferenceError('Protected worker not started.',code='WORKER_CLOSED')
        return self.call({'operation':'worker','request':payload},timeout+10,cancellation)
    def close(self):
        self.qualified=False
        if self.process.poll() is None:self.call({'operation':'stop'},30)
    def shutdown(self):
        try:self.close()
        finally:
            self.qualified=False
            self.process.stdin.close()
            try:self.process.wait(timeout=15)
            except subprocess.TimeoutExpired:self.process.terminate();self.process.wait(timeout=5)
            self.process.stdout.close()
            if self.process.stderr is not None:self.process.stderr.close()


def profile_limit(boot,proposed):
    selection=proposed.get('selection');experimental=proposed.get('experimental')
    if selection not in {'auto','manual'} or type(experimental) is not bool:raise ValueError('Explicit runtime selection/resource scope required.')
    if experimental and (selection!='manual' or boot.get('experimental_authorized') is not True):raise PermissionError('Experimental resource consent is scoped to explicit manual attempts only.')
    return boot.get('manual_limit') if selection=='manual' else None


def approved_stores(roots):
    """Quarantine an unavailable approved store; never broaden its grant."""
    from vector_core.models import validate_layout
    usable=[];unavailable=[]
    for root in roots:
        try:usable.append(str(validate_layout(root)))
        except (OSError,ValueError) as error:unavailable.append({'name':'Unavailable store: '+str(root),'root':str(root),'installed':False,'compatible':False,'unavailable_reason':str(error)[:1000]})
    return list(dict.fromkeys(usable)),unavailable


def create(*,profile=None,roots=None):
    """Only trusted startup calls this, before the core's mandatory filter."""
    from vector_core.worker_launcher import read_runtime_profile
    from vector_core.models import validate_layout
    from vector_core.runtime_policy import hardware
    settings=read_runtime_profile(profile) if roots is None else None
    roots,unavailable=approved_stores(roots if roots is not None else settings['model_directories'] if settings else [])
    if not roots:raise InferenceError('No approved local model store. Approve a specific local models directory once; no network access is needed.',code='MODEL_ROOT_AUTHORIZATION_REQUIRED')
    uid=str(os.getuid());bus='/run/user/'+uid+'/bus';unit='vector-supervisor-'+uuid4().hex;package=str(Path(__file__).resolve().parent)
    import hashlib,shutil
    executables={}
    for name in ('bwrap','systemd-run','systemctl','ollama'):
        located=shutil.which(name)
        if not located:raise InferenceError('Required installed runtime absent: '+name)
        p=Path(located).resolve()
        if not str(p).startswith(('/usr/bin/','/usr/local/bin/')) or p.stat().st_uid!=0 or p.stat().st_mode&0o022:raise InferenceError('Untrusted installed runtime: '+name)
        digest=hashlib.sha256()
        with p.open('rb') as f:
            while chunk:=f.read(1024*1024):digest.update(chunk)
        executables[name]={'path':str(p),'sha256':digest.hexdigest()}
    host=hardware();boot={'unavailable_stores':unavailable,'executables':executables,'roots':roots,'unit':unit+'.service','package':package,'host_network_namespace':str(Path('/proc/self/ns/net').readlink()),'experimental_authorized':bool(settings and settings.get('experimental_memory')),'manual_limit':settings['memory_bytes'] if settings else None,'tasks_limit':settings['tasks'] if settings else 64,'hardware':host}
    command=['/usr/bin/systemd-run','--user','--pipe','--wait','--collect','--quiet','--unit='+unit,'--property=MemoryMax=268435456','--property=MemorySwapMax=0','--property=TasksMax=32','--property=CPUQuota=100%','--property=KillMode=control-group','--property=TimeoutStopSec=5',
        '/usr/bin/bwrap','--unshare-user','--unshare-net','--unshare-ipc','--unshare-uts','--disable-userns','--assert-userns-disabled','--die-with-parent','--new-session','--cap-drop','ALL','--clearenv',
        '--ro-bind','/usr','/usr','--ro-bind','/lib','/lib','--ro-bind','/lib64','/lib64','--dev','/dev','--size','67108864','--tmpfs','/tmp','--dir','/tmp/home','--dir','/proc','--ro-bind','/sys/fs/cgroup','/sys/fs/cgroup','--ro-bind',bus,bus,'--ro-bind','/etc/machine-id','/etc/machine-id','--dir','/run/systemd/system',
        '--setenv','PATH','/usr/bin:/bin','--setenv','HOME','/tmp/home','--setenv','XDG_RUNTIME_DIR','/run/user/'+uid,'--setenv','DBUS_SESSION_BUS_ADDRESS','unix:path='+bus,'--setenv','LC_ALL','C.UTF-8','--setenv','PYTHONPATH',str(Path(package).parent),'--setenv','PYTHONDONTWRITEBYTECODE','1']
    for source in ('/proc/meminfo','/proc/vmstat','/proc/cpuinfo','/proc/pressure','/proc/self/cgroup','/proc/self/status','/proc/self/stat','/proc/self/uid_map','/proc/self/gid_map','/proc/sys/kernel/random/boot_id'):
        command+=['--ro-bind',source.replace('/proc/self/','/proc/'+str(os.getpid())+'/'),source]
    command+=['--ro-bind',package,package]
    for root in roots:command+=['--ro-bind',root,root]
    command+=['/usr/bin/python3','-B','-m','vector_core.runtime_supervisor',json.dumps(boot)]
    environment={'PATH':'/usr/bin:/bin','XDG_RUNTIME_DIR':'/run/user/'+uid,'DBUS_SESSION_BUS_ADDRESS':'unix:path='+bus}
    process=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,bufsize=0,start_new_session=True,env=environment)
    proxy=SupervisorProxy(process,unit+'.service',roots)
    try:proxy.boot=proxy.call({'operation':'status'},30)
    except BaseException:proxy.shutdown();raise
    return proxy


def main(boot):
    from vector_core.inference_worker import restrict
    from vector_core.models import local_inventory
    from vector_core.runtime_policy import hardware,plan as make_plan
    from vector_core.worker_launcher import launch
    import socket
    restrict(socket_family=socket.AF_UNIX)
    for family in (socket.AF_INET,socket.AF_INET6):
        try:handle=socket.socket(family,socket.SOCK_STREAM)
        except PermissionError:pass
        else:handle.close();raise RuntimeError('Controller IP socket denial failed.')
    # No host PID traversal or original/user-data mounts exist in this service.
    if Path('/proc/1/root').exists():raise RuntimeError('Controller host-process view exposed; startup refused.')
    worker=None;buffer=b'';cancelled=False;closed=False
    inventory=local_inventory(boot['roots'])+boot.get('unavailable_stores',[]);known={m['name']:m for m in inventory}
    def check_control():
        nonlocal buffer,cancelled,closed
        if select.select([sys.stdin.buffer],[],[],0)[0]:
            chunk=os.read(0,65536)
            if not chunk:closed=True
            buffer+=chunk
            if len(buffer)>MAX_FRAME:raise InferenceError('Excessive controller input.')
            while b'\n' in buffer:
                raw,buffer=buffer.split(b'\n',1);value=json.loads(raw,object_pairs_hook=unique)
                if value.get('payload')!={'operation':'cancel'}:raise InferenceError('Only cancellation may interrupt a running control operation.')
                cancelled=True
        if closed or cancelled:raise InferenceError('Controller client disconnected or cancelled.',code='CANCELLED')
    def stop():
        nonlocal worker
        if worker:worker.close();worker=None
    try:
        while not closed:
            if b'\n' not in buffer:
                chunk=os.read(0,65536)
                if not chunk:break
                buffer+=chunk
                if len(buffer)>MAX_FRAME:raise ValueError('Controller frame too large.')
                continue
            raw,buffer=buffer.split(b'\n',1);request=json.loads(raw,object_pairs_hook=unique);request_id=request['id'];p=request['payload'];cancelled=False
            if p=={'operation':'cancel'}:continue
            try:
                operation=p.get('operation')
                if operation=='status':
                    result={'models':inventory,'hardware':boot['hardware'],'experimental_authorized':boot['experimental_authorized'],'manual_limit':boot['manual_limit'],'controller_offline':True,'ip_sockets_denied':True,'host_process_view_absent':True,'controller_unit':boot['unit']}
                elif operation=='stop':stop();result={'stopped':True,'cleanup_verified':True}
                elif operation=='start':
                    stop();proposed=p['plan']
                    if not isinstance(proposed,dict) or not proposed.get('models') or any(n not in known for n in proposed['models']):raise InferenceError('Only exact models in approved local stores can be started.')
                    manual_limit=profile_limit(boot,proposed)
                    host=hardware('/usr');host['fingerprint']=boot['hardware']['fingerprint']
                    # The captured /proc/self/cgroup is the original desktop's
                    # hierarchy, not the controller's deliberately small cgroup.
                    checked=make_plan(inventory,host,context_required=proposed['context_tokens'],output_tokens=proposed['output_tokens'],manual_names=proposed['models'],experimental=proposed.get('experimental',False),manual_limit=manual_limit)
                    checked['tasks']=min(checked['tasks'],boot['tasks_limit'])
                    if proposed.get('selection') not in {'auto','manual'}:raise InferenceError('Explicit runtime selection scope required.')
                    for field in ('memory_bytes','tasks','cpu_threads','cpu_quota_percent'):
                        if type(proposed[field]) is not int or proposed[field]>checked[field]:raise InferenceError('Requested runtime limit exceeds freshly checked host/profile allowance: '+field)
                    check_control()
                    worker=launch(boot['roots'][0],additional_model_directories=boot['roots'][1:],memory_bytes=proposed['memory_bytes'],tasks=proposed['tasks'],experimental=proposed.get('experimental',False),service_mode=True,supervisor_unit=boot['unit'],selected_models=proposed['models'],host_network_namespace=boot['host_network_namespace'],source_package=boot['package'],cpu_threads=proposed['cpu_threads'],cpu_quota_percent=proposed['cpu_quota_percent'],extra_check=check_control,trusted_executables=boot['executables'])
                    result={'report':worker.report,'cleanup_before_start_verified':True}
                elif operation=='worker':
                    if not worker or not worker.qualified:raise InferenceError('Worker unavailable; fresh qualification required.',code='WORKER_CLOSED')
                    payload=p['request']
                    if payload.get('operation') not in {'discover','inspect','generate','resource_probe'}:raise InferenceError('Unauthorized inference operation.')
                    if payload.get('operation')=='generate' and payload.get('config',{}).get('model') not in proposed['models']:raise InferenceError('Model outside the exact current runtime plan.')
                    timeout=payload.get('config',{}).get('timeout_seconds',60)
                    if not isinstance(timeout,(float,int)) or not 1<=timeout<=600:raise InferenceError('Invalid inference timeout.')
                    result=worker.request(payload,timeout+5)
                else:raise InferenceError('Unknown fixed runtime operation.')
                reply={'id':request_id,'ok':True,'result':result}
            except (RuntimeError,ValueError,OSError,KeyError,TypeError,subprocess.SubprocessError) as error:
                original_error=error
                try:stop()
                except (RuntimeError,OSError,subprocess.SubprocessError) as cleanup:
                    error=InferenceError(str(original_error)+'; cleanup unverified: '+str(cleanup),code='RUNNER_CLEANUP_FAILED',stage='worker-cleanup')
                    error.resources=getattr(original_error,'resources',None)
                reply={'id':request_id,'ok':False,'result':{'error':str(error)[:2000],'code':getattr(error,'code','RESOURCE_LIMIT' if str(error).startswith('RESOURCE_BLOCKED:') else 'RUNTIME_CONTROL_FAILED'),'stage':getattr(error,'stage','runtime-control'),'resources':getattr(error,'resources',None),'raw_generation':getattr(error,'raw_generation',None)}}
            old=signal.pthread_sigmask(signal.SIG_BLOCK,{signal.SIGUSR1})
            try:sys.stdout.buffer.write(encode(reply));sys.stdout.buffer.flush()
            finally:signal.pthread_sigmask(signal.SIG_SETMASK,old)
    finally:stop()

if __name__=='__main__':main(json.loads(sys.argv[1],object_pairs_hook=unique))
