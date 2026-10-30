"""One real, isolated, independently checked local-model acceptance trial.

Run separate invocations for independent workers. No simulated inference is used.
"""
import argparse
from dataclasses import asdict
import json
from pathlib import Path
import tempfile
import time


def main(argv=None):
    parser=argparse.ArgumentParser()
    parser.add_argument('--models-directory',required=True);parser.add_argument('--model',required=True)
    parser.add_argument('--timeout',type=float,default=240);parser.add_argument('--roundtrip',action='store_true')
    args=parser.parse_args(argv)
    from vector_core.inference import GenerationConfig
    config=GenerationConfig(args.model,4096,512,args.timeout).validate()
    from vector_core.worker_launcher import launch,launch_managed
    report={'simulated':False,'configuration':asdict(config),'task':'two-source verbatim attribution; not general reasoning',
            'passed':False,'roundtrip_requested':args.roundtrip}
    transport=None;tick=time.perf_counter()
    try:
        transport=launch_managed() if args.roundtrip else launch(args.models_directory)
        from vector_core.security import activate
        policy=activate(pipe_fds=transport.retained_fds)
        report['core_network_denial']=policy['network_denied'];report['worker_isolation']=transport.report
        from vector_core.config import Config
        from vector_core.memory import Memory
        from vector_core.service import Application
        from vector_core.assistant import ask
        from vector_core.portable import export_vector,restore_vector
        with tempfile.TemporaryDirectory(prefix='vector_real_qualification_') as directory:
            root=Path(directory);source=Config.load(data_dir=str(root/'data'))
            expected={}
            with Memory(source) as memory:
                if args.roundtrip:
                    from vector_core.models import import_model
                    start=time.perf_counter()
                    report['managed_import']=import_model(memory,args.models_directory,args.model,transport.runtime_version)
                    report['managed_import_seconds']=time.perf_counter()-start
                app=Application(memory,transport)
                for name,text in [('pump-a','Pump A has a flow of 12 L/s.'),('pump-b','Pump B has a flow of 8 L/s.')]:
                    event=app.handle('ingest',{'text':text,'name':name});expected[event['event_id']]=text
                if args.roundtrip:
                    start=time.perf_counter();report['export']=export_vector(memory,root/'archive');report['export_seconds']=time.perf_counter()-start
            if args.roundtrip:
                source=Config.load(data_dir=str(root/'restored'));start=time.perf_counter()
                report['restore']=restore_vector(source,root/'archive');report['restore_seconds']=time.perf_counter()-start
            with Memory(source) as memory:
                for identity,text in expected.items():
                    if memory.original(identity)!=text.encode():raise ValueError('Independent original-byte expectation failed.')
                app=Application(memory,transport)
                app.handle('select_model',{'configuration':asdict(config),'authorize_external':True})
                if not args.roundtrip:
                    try:export_vector(memory,root/'must-not-be-complete')
                    except ValueError as error:report['external_export_rejection']=str(error)
                    else:raise ValueError('External required model assets were incorrectly omitted from complete export.')
                result=ask(memory,'Quote the documented flow rate of each of Pump A and Pump B verbatim, with its exact original source citation.',
                           adapter=app.adapter,config=config,max_attempts=1)
                report['interaction']=result
                outcome=result['outcome'];answer=outcome['answer'];matched=set()
                if answer and not answer['insufficient']:
                    for statement in answer['statements']:
                        if statement['kind']!='source':continue
                        for citation in statement['citations']:
                            identity=citation['event_id']
                            if identity in expected and statement['text']==expected[identity] and citation['quote']==expected[identity]:matched.add(identity)
                report['independent_check']={'expected_full_original_quotes':expected,'matched_event_ids':sorted(matched),
                    'required_statements':2,'actual_statements':len(answer['statements']) if answer else 0}
                report['passed']=bool(answer and outcome['status']=='model-inference-unverified' and matched==set(expected) and len(answer['statements'])==2)
    except Exception as error:report['error']=str(error)
    finally:
        if transport:transport.close()
        report['elapsed_seconds']=time.perf_counter()-tick
        print(json.dumps(report,ensure_ascii=False,indent=2),flush=True)
    return 0 if report['passed'] else 1

if __name__=='__main__':raise SystemExit(main())
