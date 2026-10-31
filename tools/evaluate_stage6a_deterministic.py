"""Independent small numeric/constraint pilot, not real-model intelligence."""
import argparse,json,random,time,resource
from decimal import Decimal,localcontext
from fractions import Fraction
from pathlib import Path

def main():
    p=argparse.ArgumentParser();p.add_argument('--work-directory',required=True);p.add_argument('--seed',type=int,required=True);args=p.parse_args();root=Path(args.work_directory)
    if root.exists():raise FileExistsError('Use a new pilot directory.')
    root.mkdir(parents=True,mode=0o700)
    from vector_core.security import activate
    policy=activate()
    from vector_core.config import Config
    from vector_core.memory import Memory,Submission
    from vector_core.investigation import Investigations,Budget
    from vector_core.tools import compute
    from vector_core.knowledge import learn
    report={'policy':policy,'seed':args.seed,'model_calls':0,'simulated_model':False,'scope':'Deterministic tools/finite constraints and orchestration; no model or discovery qualification','arithmetic':[],'constraints':[]};rng=random.Random(args.seed);start=time.monotonic()
    def step(i,strategy,depends=(),**input):return {'id':i,'strategy':strategy,'depends':list(depends),'input':input}
    with Memory(Config.load(data_dir=str(root/'data'))) as memory:
        inv=Investigations(memory)
        for i in range(20):
            a,b,c,d=[rng.randint(2,51) for _ in range(4)];expected=Fraction(a*b+c,d)
            with localcontext() as ctx:ctx.prec=40;expected_decimal=Decimal(expected.numerator)/Decimal(expected.denominator)
            tick=time.perf_counter();baseline=compute('arithmetic',{'expression':f'({a}*{b}+{c})/{d}'})['value'];baseline_seconds=time.perf_counter()-tick
            steps=[step('product','calculate',operation='arithmetic',parameters={'expression':f'{a}*{b}'}),step('combine','calculate',['product'],operation='arithmetic',parameters={'expression':f'(x+{c})/{d}'},bindings={'x':{'step':'product','field':'value','unit':'1'}})]
            tick=time.perf_counter();state=inv.create('Independent numeric pilot',steps,approved=True);key=state['id'];first=inv.run(key,budget=Budget(1,0,30),approved=True);assert first['state']['status']=='paused';state=first['state'];inv.control(key,'resume',state['revision'],approved=True);last=inv.run(key,budget=Budget(1,0,30),approved=True);actual=inv.history(key)['items'][-1]['result']['value'];assert last['state']['status']=='complete'
            report['arithmetic'].append({'parameters':[a,b,c,d],'expected_fraction':str(expected),'expected_40_digit_decimal':str(expected_decimal),'baseline':baseline,'adaptive':actual,'baseline_passed':Decimal(baseline)==expected_decimal,'adaptive_passed':Decimal(actual)==expected_decimal,'baseline_seconds':baseline_seconds,'adaptive_seconds_including_durable_checkpoint_resume':time.perf_counter()-tick})
        for case in range(6):
            target=rng.randint(-3,8);offset=0;found=[];key=None
            for chunk in range(10):
                task=step('chunk-'+str(chunk),'constraints',domains={'x':list(range(-3,4)),'y':list(range(6))},constraints=[{'left':'2*x+y','relation':'eq','right':str(target)},{'left':'x','relation':'ne','right':'y'}],offset=offset,assignments=7)
                if key is None:state=inv.create('Independent finite-domain pilot',[task],approved=True);key=state['id']
                else:state=inv.control(key,'redirect',inv.get(key)['revision'],steps=[task],approved=True)
                inv.run(key,approved=True);result=inv.history(key,after=0,limit=100)['items'][-1]['result'];found+=result['solutions'];offset=result['next_offset']
                if result['complete']:break
            expected=[{'x':x,'y':y} for x in range(-3,4) for y in range(6) if 2*x+y==target and x!=y];report['constraints'].append({'target':target,'expected':expected,'actual':found,'passed':found==expected and offset==42,'examined':offset})
        originals={}
        for value in ['11','29']:
            content='Sigma | capacity | '+value;event=learn(memory,Submission(content.encode(),'contradictory pilot'),'pilot',True)['event'];originals[event['event_id']]=content
        state=inv.create('Reconcile Sigma capacity',[step('compare','reconcile',query='Sigma capacity')],approved=True);inv.run(state['id'],approved=True);result=inv.history(state['id'])['items'][-1]['result'];report['reconciliation']={'conflicts_reported':len(result['context']['conflicts']),'originals_preserved':all(memory.original(k)==v.encode() for k,v in originals.items()),'scope':'Comparable explicit literal disagreement; not general semantic contradiction reasoning'}
        report['passed']=all(x['baseline_passed'] and x['adaptive_passed'] for x in report['arithmetic']) and all(x['passed'] for x in report['constraints']) and report['reconciliation']['conflicts_reported']>0 and report['reconciliation']['originals_preserved']
    report['seconds']=time.monotonic()-start;report['peak_rss_kib']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss;print(json.dumps(report,indent=2));return 0 if report['passed'] else 1

if __name__=='__main__':raise SystemExit(main())
