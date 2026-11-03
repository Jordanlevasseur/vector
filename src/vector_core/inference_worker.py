"""Private-namespace Ollama broker. Only fixed generation/discovery API calls."""
import ctypes
import errno
import http.client
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
import time
from vector_core.inference import GenerationConfig,ANSWER_SCHEMA,CLAIM_SCHEMA,FINDING_NOTES_SCHEMA,COLLABORATION_SCHEMA
from vector_core.portable import unique

MAX_FRAME=1024*1024


def configure_cpu_memory():
    """Avoid synchronous huge-page compaction in this worker and its children.

    PR_SET_THP_DISABLE is inherited across fork/exec. This is a process-local
    allocation policy, not a change to the host's transparent-hugepage settings.
    """
    libc=ctypes.CDLL('libc.so.6',use_errno=True)
    if libc.prctl(41,1,0,0,0) or libc.prctl(42,0,0,0,0)!=1:
        raise RuntimeError('Per-worker transparent huge-page disable failed.')


def generation_payload(config,prompt,response_kind):
    """Bound CPU prefill workspace as well as context; never shorten the prompt.

    Ollama otherwise chooses its own prefill batch and may copy all weights into
    anonymous RAM. A small batch and read-only mapping trade speed for memory
    headroom. Kernel limits and host-pressure monitoring remain mandatory.
    """
    return {'model':config.model,'prompt':prompt,'stream':False,
            'format':{'answer-v1':ANSWER_SCHEMA,'claims-v1':CLAIM_SCHEMA,
                      'finding-notes-v1':FINDING_NOTES_SCHEMA,
                      'collaboration-v1':COLLABORATION_SCHEMA,
                      'proposal-text-v1':None}.get(response_kind,'json'),
            'keep_alive':0,'options':{'num_ctx':config.context_tokens,
                'num_predict':config.output_tokens,'temperature':config.temperature,
                'seed':config.seed,'num_thread':2,'num_batch':32,'use_mmap':True}}


def restrict():
    libc=ctypes.CDLL('libc.so.6',use_errno=True);lib=ctypes.CDLL('libseccomp.so.2',use_errno=True)
    lib.seccomp_init.argtypes=[ctypes.c_uint32];lib.seccomp_init.restype=ctypes.c_void_p
    lib.seccomp_syscall_resolve_name.argtypes=[ctypes.c_char_p];lib.seccomp_syscall_resolve_name.restype=ctypes.c_int
    class Compare(ctypes.Structure):_fields_=[('arg',ctypes.c_uint),('op',ctypes.c_uint),('a',ctypes.c_uint64),('b',ctypes.c_uint64)]
    lib.seccomp_rule_add_array.argtypes=[ctypes.c_void_p,ctypes.c_uint32,ctypes.c_int,ctypes.c_uint,ctypes.POINTER(Compare)]
    lib.seccomp_load.argtypes=[ctypes.c_void_p];lib.seccomp_release.argtypes=[ctypes.c_void_p]
    if libc.prctl(38,1,0,0,0):raise RuntimeError('Worker no_new_privs failed.')
    ctx=lib.seccomp_init(0x7fff0000)
    if not ctx:raise RuntimeError('Worker filter allocation failed.')
    try:
        for name in ('socketpair','ptrace','process_vm_writev','process_vm_readv','pidfd_getfd','bpf','unshare','setns','mount','umount2','io_uring_setup','io_uring_enter','io_uring_register'):
            number=lib.seccomp_syscall_resolve_name(name.encode())
            if number<0 or lib.seccomp_rule_add_array(ctx,0x50000|errno.EPERM,number,0,None):raise RuntimeError('Worker filter rule failed: '+name)
        comparison=Compare(0,1,socket.AF_INET,0)  # SCMP_CMP_NE: private IPv4 only.
        if lib.seccomp_rule_add_array(ctx,0x50000|errno.EPERM,lib.seccomp_syscall_resolve_name(b'socket'),1,ctypes.byref(comparison)) or lib.seccomp_load(ctx):
            raise RuntimeError('Worker socket filter failed.')
    finally:lib.seccomp_release(ctx)
    if libc.prctl(39,0,0,0,0)!=1:raise RuntimeError('Worker no_new_privs not confirmed.')


def local_api(path,payload=None,timeout=10):
    connection=http.client.HTTPConnection('127.0.0.1',11434,timeout=timeout)
    try:
        body=json.dumps(payload,allow_nan=False) if payload is not None else None
        connection.request('POST' if payload is not None else 'GET',path,body,{'Content-Type':'application/json'})
        response=connection.getresponse();raw=response.read(MAX_FRAME+1)
        if response.status!=200 or len(raw)>MAX_FRAME:raise ValueError('Local runtime response error or output limit: '+str(response.status)+' '+raw[:800].decode('utf-8','replace'))
        result=json.loads(raw,object_pairs_hook=unique)
        if not isinstance(result,dict):raise ValueError('Local runtime returned a non-object.')
        return result
    finally:connection.close()


class GenerationFailure(ValueError):
    def __init__(self,message,partial):super().__init__(message);self.partial=partial


def stream_generation(payload,timeout):
    connection=http.client.HTTPConnection('127.0.0.1',11434,timeout=timeout)
    end=time.monotonic()+timeout;parts=[];size=0;thinking_bytes=0
    try:
        payload=dict(payload,stream=True)
        if payload.get('format') is None:payload.pop('format',None)
        connection.request('POST','/api/generate',json.dumps(payload),{'Content-Type':'application/json'})
        response=connection.getresponse()
        if response.status!=200:raise GenerationFailure('Local generation HTTP '+str(response.status)+': '+response.read(1000).decode('utf-8','replace'),'')
        while True:
            remaining=end-time.monotonic()
            if remaining<=0:raise GenerationFailure('Generation deadline reached.',''.join(parts))
            if connection.sock:connection.sock.settimeout(remaining)
            raw=response.readline(65537)
            if not raw:raise GenerationFailure('Runtime ended before completion.',''.join(parts))
            if len(raw)>65536:raise GenerationFailure('Excessive runtime chunk.',''.join(parts))
            chunk=json.loads(raw,object_pairs_hook=unique)
            if not isinstance(chunk,dict) or not isinstance(chunk.get('response',''),str):raise GenerationFailure('Malformed generation chunk.',''.join(parts))
            if not isinstance(chunk.get('thinking',''),str):raise GenerationFailure('Malformed thinking metadata.',''.join(parts))
            thinking_bytes+=len(chunk.get('thinking','').encode())
            fragment=chunk.get('response','');size+=len(fragment.encode())
            if size>min(MAX_FRAME,payload['options']['num_predict']*64):raise GenerationFailure('Generation output budget exceeded.',''.join(parts))
            parts.append(fragment)
            if chunk.get('error'):raise GenerationFailure(str(chunk['error'])[:500],''.join(parts))
            if chunk.get('done') is True:
                chunk.pop('thinking',None)  # Keep measurements, never hidden reasoning text.
                chunk['thinking_bytes']=thinking_bytes
                chunk['response']=''.join(parts);return chunk
    except (OSError,ValueError) as error:
        if isinstance(error,GenerationFailure):raise
        raise GenerationFailure(str(error),''.join(parts)) from error
    finally:connection.close()


def main():
    if {line.split(':')[0].strip() for line in Path('/proc/net/dev').read_text().splitlines()[2:]}!={'lo'}:
        raise RuntimeError('Private network namespace is not loopback-only.')
    configure_cpu_memory()
    restrict()
    import resource
    resource.setrlimit(resource.RLIMIT_FSIZE,(16*1024*1024,16*1024*1024))
    import tempfile
    runtime_log=tempfile.TemporaryFile()
    daemon=subprocess.Popen([os.environ['VECTOR_OLLAMA_BINARY'],'serve'],stdin=subprocess.DEVNULL,stdout=runtime_log,stderr=runtime_log)
    version=None
    try:
        startup_deadline=time.monotonic()+8
        while time.monotonic()<startup_deadline:
            if daemon.poll() is not None:break
            try:version=local_api('/api/version',timeout=.25)['version'];break
            except (OSError,ValueError):time.sleep(.05)
        if not isinstance(version,str):
            runtime_log.seek(0,2);length=runtime_log.tell();runtime_log.seek(max(0,length-2000))
            raise RuntimeError('Private Ollama startup failed/deadline reached: '+runtime_log.read(2000).decode('utf-8','replace'))
        for raw in iter(lambda:sys.stdin.buffer.readline(MAX_FRAME+1),b''):
            if len(raw)>MAX_FRAME or not raw.endswith(b'\n'):raise RuntimeError('Invalid request frame.')
            try:
                request=json.loads(raw,object_pairs_hook=unique)
                operation=request.get('operation')
                if operation=='qualify':
                    denied=False
                    with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as probe:
                        probe.settimeout(.2)
                        try:probe.connect(('192.0.2.1',9))
                        except OSError as error:denied=error.errno in (errno.ENETUNREACH,errno.EHOSTUNREACH,errno.EPERM)
                    try:socket.socket(socket.AF_UNIX);raise RuntimeError('Worker Unix socket unexpectedly permitted.')
                    except PermissionError:pass
                    libc=ctypes.CDLL('libc.so.6',use_errno=True)
                    nested=libc.unshare(0x10000000)!=0 and ctypes.get_errno()==errno.EPERM
                    result={'network_namespace':str(Path('/proc/self/ns/net').readlink()),
                            'routes':bool(Path('/proc/net/route').read_text().splitlines()[1:]),'external_denied':denied,
                            'nested_userns_denied':nested,'runtime_version':version,
                            'host_home_absent':not Path('/home/mint').exists(),
                            'shared_model_home_hidden':not Path('/usr/share/ollama/.ollama').exists(),
                            'cpu_only':os.environ.get('OLLAMA_LLM_LIBRARY')=='cpu' and os.environ.get('CUDA_VISIBLE_DEVICES')=='-1',
                            'transparent_hugepages_disabled':libc.prctl(42,0,0,0,0)==1,
                            'model_blobs_readonly':bool(os.statvfs('/models/blobs').f_flag & os.ST_RDONLY)}
                elif operation=='resource_probe':
                    children=[];exhausted=False
                    try:
                        for _ in range(256):
                            try:pid=os.fork()
                            except OSError as error:
                                exhausted=error.errno==errno.EAGAIN;break
                            if pid==0:
                                time.sleep(10);os._exit(0)
                            children.append(pid)
                    finally:
                        import signal
                        for pid in children:
                            try:os.kill(pid,signal.SIGKILL)
                            except ProcessLookupError:pass
                        for pid in children:os.waitpid(pid,0)
                    result={'pids_exhaustion_denied':exhausted,'children_cleaned':len(children)}
                elif operation=='discover':
                    result=local_api('/api/tags');result['available']=True;result['runtime_version']=version
                elif operation=='generate':
                    config=GenerationConfig(**request['config']).validate()
                    if not re.fullmatch(r'[A-Za-z0-9_.:/-]{1,200}',config.model) or '..' in config.model:raise ValueError('Invalid selected model.')
                    models=local_api('/api/tags').get('models',[])
                    selected=next((model for model in models if model.get('name')==config.model),None)
                    if selected is None:raise ValueError('Selected local model unavailable; no pull/download is allowed.')
                    metadata=local_api('/api/show',{'model':config.model})
                    limits=[value for key,value in metadata.get('model_info',{}).items() if key.endswith('.context_length') and type(value) is int]
                    if not limits or config.context_tokens>min(limits):raise ValueError('Actual model context capacity is unknown or insufficient.')
                    prompt=request['prompt']
                    if not isinstance(prompt,str) or len(prompt.encode())>config.prompt_bytes:raise ValueError('Prompt byte budget exceeded.')
                    response_kind=request.get('response_kind')
                    if response_kind not in (None,'answer-v1','claims-v1','finding-notes-v1','proposal-text-v1','collaboration-v1'):raise ValueError('Unknown structured response format.')
                    if local_api('/api/ps').get('models'):raise ValueError('A prior runner remains loaded; sequential inference refused.')
                    payload=generation_payload(config,prompt,response_kind)
                    result=stream_generation(payload,max(.05,config.timeout_seconds-1))
                    result['execution_options']=payload['options']
                    result['model_digest']=selected.get('digest','unknown')
                    unload_deadline=time.monotonic()+5
                    while local_api('/api/ps').get('models'):
                        if time.monotonic()>unload_deadline:raise ValueError('Runner did not unload after generation; sequential continuation refused.')
                        time.sleep(.05)
                    result['runner_unloaded']=True
                else:raise ValueError('Unauthorized worker operation.')
                response={'ok':True,'result':result}
            except (ValueError,KeyError,TypeError,OSError) as error:
                runtime_log.seek(0,2);length=runtime_log.tell();runtime_log.seek(max(0,length-700))
                diagnostic=runtime_log.read(700).decode('utf-8','replace')
                response={'ok':False,'result':{'error':str(error)[:250]+'; private runtime log tail: '+diagnostic,
                          'partial':getattr(error,'partial',None),'simulated':False}}
            encoded=json.dumps(response,allow_nan=False).encode()
            if len(encoded)>MAX_FRAME:encoded=b'{"ok":false,"result":"Excessive output"}'
            sys.stdout.buffer.write(encoded+b'\n');sys.stdout.buffer.flush()
    finally:
        daemon.terminate()
        try:daemon.wait(timeout=2)
        except subprocess.TimeoutExpired:daemon.kill();daemon.wait()
        runtime_log.close()

if __name__=='__main__':main()
