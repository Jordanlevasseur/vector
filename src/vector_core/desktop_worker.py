"""Fixed RPC backend. Kernel offline policy precedes opening any VECTOR state."""
import argparse
import json
import signal
import sqlite3
import sys
from uuid import uuid4
from vector_core.memory import now

class Cancelled(RuntimeError):pass
busy=False

def cancel(signum,frame):
    if busy:raise Cancelled('Operation cancelled; committed originals remain. Interrupted transfers may need resume/recovery.')


def main():
    global busy
    parser=argparse.ArgumentParser();parser.add_argument('--data-dir');parser.add_argument('--models-directory');parser.add_argument('--managed',action='store_true');parser.add_argument('--runtime-profile')
    args=parser.parse_args();transport=None;startup_error=None
    signal.signal(signal.SIGUSR1,cancel)
    if args.models_directory or args.managed:
        busy=True
        try:
            from vector_core.worker_launcher import launch,launch_managed
            transport=launch_managed() if args.managed else launch(args.models_directory)
        except (RuntimeError,ValueError,OSError) as error:startup_error=str(error)
        finally:busy=False
    elif args.runtime_profile or args.data_dir is None:
        busy=True
        try:
            from vector_core.worker_launcher import desktop_runtime
            transport=desktop_runtime(args.runtime_profile)
        except (RuntimeError,ValueError,OSError) as error:startup_error=str(error)
        finally:busy=False
    from vector_core.security import activate
    policy=activate(pipe_fds=transport.retained_fds if transport else ())
    from vector_core.config import Config
    from vector_core.memory import Memory
    from vector_core.service import Application
    from vector_core.persistence import register,put
    from vector_core.portable import unique
    application=None
    try:
        application=Application(Memory(Config.load(data_dir=args.data_dir)),transport,startup_error);application.policy=policy
        signal.signal(signal.SIGUSR1,cancel)
        for raw in iter(lambda:sys.stdin.buffer.readline(65537),b''):
            if len(raw)>65536 or not raw.endswith(b'\n'):raise ValueError('Desktop request exceeds framing limit.')
            request_id=None;request={}
            try:
                request=json.loads(raw,object_pairs_hook=unique)
                if not isinstance(request,dict) or set(request)!={'id','operation','parameters'}:raise ValueError('Invalid desktop request.')
                request_id=request['id'];busy=True
                def progress(value):
                    sys.stdout.buffer.write(json.dumps({'id':request_id,'progress':value},allow_nan=False).encode()+b'\n');sys.stdout.buffer.flush()
                application.model_controller.progress=progress
                result=application.handle(request['operation'],request['parameters'])
                response={'id':request_id,'ok':True,'result':result}
            except (ValueError,KeyError,TypeError,RuntimeError,OSError,sqlite3.Error) as error:
                if isinstance(error,Cancelled) and transport:transport.close()
                response={'id':request_id,'ok':False,'result':str(error)[:2000]}
                # Error records use the same portable state, never a hidden side database.
                if application:
                    memory=application.memory
                    try:
                        if memory.db.execute("SELECT 1 FROM persistence_contracts WHERE name='application_events'").fetchone() is None:register(memory,'application_events','Desktop operational errors/cancellation')
                        put(memory,'application_events',uuid4().hex,{'time':now(),'request_id':request_id,'error':str(error)[:2000],
                            'operation':request.get('operation') if isinstance(request,dict) else None,
                            'parameters':request.get('parameters') if isinstance(request,dict) else None})
                    except (RuntimeError,OSError,ValueError,sqlite3.Error):pass
            finally:busy=False
            encoded=json.dumps(response,ensure_ascii=False,allow_nan=False).encode()
            if len(encoded)>1024*1024:encoded=json.dumps({'id':request_id,'ok':False,'result':'Response exceeds desktop page budget.'}).encode()
            sys.stdout.buffer.write(encoded+b'\n');sys.stdout.buffer.flush()
    finally:
        if transport:transport.close()
        if application:application.memory.close()

if __name__=='__main__':
    try:main()
    except (RuntimeError,ValueError,OSError,sqlite3.Error) as error:
        print(json.dumps({'id':None,'ok':False,'initialization_error':True,'result':str(error)[:2000]}),flush=True)
        raise SystemExit(1)
