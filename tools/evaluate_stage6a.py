"""Small real-model system comparison; expectations never enter model input.

Use a NEW work directory. Run baseline and adaptive separately under the same
qualified local model. This is not a model-only architecture ablation or a claim
of originality. No simulation is available in this harness.
"""
import argparse,json,time
from pathlib import Path
from decimal import Decimal,InvalidOperation
from dataclasses import asdict

def main():
    p=argparse.ArgumentParser();p.add_argument('--mode',choices=['baseline','adaptive'],required=True);p.add_argument('--models-directory',required=True);p.add_argument('--model',default='qwen2.5-coder:0.5b');p.add_argument('--tasks',required=True);p.add_argument('--work-directory',required=True);args=p.parse_args()
    from vector_core.worker_launcher import launch
    from vector_core.inference import GenerationConfig
    report={'mode':args.mode,'simulated':False,'passed':False,'results':[]};transport=None;start=time.monotonic()
    try:
        root=Path(args.work_directory)
        if root.exists():raise FileExistsError('Existing evaluation work must be preserved; choose a new path.')
        root.mkdir(parents=True,mode=0o700);tasks=json.loads(Path(args.tasks).read_text())
        transport=launch(args.models_directory)
        from vector_core.security import activate
        report['policy']=activate(pipe_fds=transport.retained_fds);report['isolation']=transport.report
        from vector_core.config import Config
        from vector_core.memory import Memory,Submission
        from vector_core.service import Application
        from vector_core.assistant import ask
        from vector_core.investigation import Investigations,Budget
        configuration=GenerationConfig(args.model,4096,384,120);report['configuration']=asdict(configuration)
        for task in tasks:
            tick=time.monotonic();row={'id':task['id'],'category':task['category'],'goal':task['goal'],'objective_passed':None}
            with Memory(Config.load(data_dir=str(root/task['id']))) as memory:
                app=Application(memory,transport);app.handle('select_model',{'configuration':asdict(configuration),'authorize_external':True})
                events=[]
                for index,source in enumerate(task['sources']):events.append(memory.ingest(Submission(source.encode(),'independent pilot '+str(index)))['event_id'])
                if args.mode=='baseline':
                    interaction=ask(memory,task['goal'],adapter=app.adapter,config=configuration,max_attempts=1);row['interaction']=interaction;answer=interaction['outcome']['answer'];row['valid_structure']=bool(answer);row['texts']=[s['text'] for s in answer['statements']] if answer else [];row['citations']=[c for s in answer['statements'] for c in s['citations']] if answer else []
                else:
                    inv=Investigations(memory,app.adapter,configuration);state=inv.create(task['goal'],explore=task['category']=='creative',approved=True);row['interaction']=inv.run(state['id'],budget=Budget(2,1,150),approved=True);row['history']=inv.history(state['id'])
                    proposals=[e['result'] for e in row['history']['items'] if e['status']=='ok' and 'generation' in e['result']];row['valid_structure']=bool(proposals);row['texts']=[x['answer'] for x in proposals];row['citations']=[c for x in proposals for c in x['citations']]
                if task['category'] in ('arithmetic','logic'):
                    try:row['objective_passed']=bool(row['texts']) and Decimal(row['texts'][-1].strip())==Decimal(task['expected'])
                    except InvalidOperation:row['objective_passed']=False
                elif task['category']=='reconciliation':row['objective_passed']=set(c['event_id'] for c in row['citations'])==set(events);row['rubric_scope']='Both conflicting source attributions only; not semantic entailment or scientific truth.'
                else:row['rubric_scope']='No originality/feasibility pass is assigned. Independent domain review remains required.'
                row['expected']=task.get('expected');row['source_events']=events;row['seconds']=time.monotonic()-tick
            report['results'].append(row)
            with (root/'progress.ndjson').open('a') as f:f.write(json.dumps({'task':row['id'],'valid_structure':row['valid_structure'],'objective_passed':row['objective_passed'],'seconds':row['seconds']})+'\n')
        scored=[r for r in report['results'] if r['objective_passed'] is not None];report['objective_hits']=sum(r['objective_passed'] for r in scored);report['objective_denominator']=len(scored);report['passed']=bool(scored) and all(r['objective_passed'] for r in scored)
    except Exception as e:report['error']=repr(e)
    finally:
        if transport:transport.close()
        report['seconds']=time.monotonic()-start;print(json.dumps(report,indent=2))
    return 0 if report['passed'] else 1

if __name__=='__main__':raise SystemExit(main())
