"""Controlled long-term/project recall benchmark. No model inference or truth claim."""
import json
from pathlib import Path
import resource
import statistics
import tempfile
import time
from unittest.mock import patch

def run(count=5000,probes=100):
    from vector_core.security import activate
    policy=activate()
    from vector_core.config import Config
    from vector_core.memory import Memory,Submission
    from vector_core.projects import Projects
    from vector_core.memory_intelligence import recall
    from vector_core.context import build_context
    from vector_core.portable import export_vector,restore_vector
    with tempfile.TemporaryDirectory(prefix='vector_memory_benchmark_') as folder:
        root=Path(folder);expected={};latency=[];contexts=[];sizes=[];cpu=time.process_time()
        with Memory(Config.load(data_dir=str(root/'data'))) as memory:
            projects=[Projects(memory).create('Controlled project '+str(i)) for i in range(4)]
            before=memory.db.execute('PRAGMA page_count').fetchone()[0]*memory.db.execute('PRAGMA page_size').fetchone()[0]
            start=time.perf_counter()
            for offset in range(0,count,64):
                batch=[Submission(('Historical entry '+str(i)+'\n'+('archive preface '*50)+' specimen'+str(i)+' measured '+str(i+7)+' pascals.').encode(),'record-'+str(i)) for i in range(offset,min(count,offset+64))]
                with patch('vector_core.memory.now',return_value='2012-06-01T00:00:00.000000+00:00'):
                    events=memory.ingest_batch(batch)
                for i,event in enumerate(events,offset):expected[i]=event['event_id']
            ingest=time.perf_counter()-start
            start=time.perf_counter()
            # Every corpus source is linked. No application collection limit is involved.
            for project_index,project in enumerate(projects):
                chosen=[event_id for i,event_id in expected.items() if i%4==project_index]
                for offset in range(0,len(chosen),64):Projects(memory).link_many(project['id'],chosen[offset:offset+64],approved=True)
            association=time.perf_counter()-start
            hits=0;chronological=0;totalcontext=0;querycpu=time.process_time()
            for i in range(probes):
                number=i*count//probes;query='specimen'+str(number);tick=time.perf_counter()
                results=recall(memory,query,project_id=projects[number%4]['id'],view='project',until='2013-01-01T00:00:00+00:00')['items'];latency.append((time.perf_counter()-tick)*1000)
                hits+=bool(results and results[0]['event_id']==expected[number]);chronological+=bool(results and results[0]['occurred'].startswith('2012-06-01'))
                tick=time.perf_counter();context=build_context(memory,query,project_id=projects[number%4]['id'],budget_bytes=8192)
                contexts.append((time.perf_counter()-tick)*1000);sizes.append(context['bytes'])
                totalcontext+=bool(context['context']['sources'] and context['context']['sources'][0]['event_id']==expected[number] and query in context['context']['sources'][0]['quote'])
            querycpu=time.process_time()-querycpu
            queryplan=[r[3] for r in memory.db.execute("EXPLAIN QUERY PLAN SELECT rowid FROM persistent_records WHERE contract='project_sources' AND json_extract(payload,'$.project_id')=?",(projects[0]['id'],))]
            dbbytes=memory.db.execute('PRAGMA page_count').fetchone()[0]*memory.db.execute('PRAGMA page_size').fetchone()[0]
            ftsbytes=memory.db.execute("SELECT coalesce(sum(pgsize),0) FROM dbstat WHERE name LIKE 'text_search%'").fetchone()[0]
            start=time.perf_counter();exported=export_vector(memory,root/'archive');exporttime=time.perf_counter()-start
        start=time.perf_counter();target=Config.load(data_dir=str(root/'restored'));restored=restore_vector(target,root/'archive');restoretime=time.perf_counter()-start
        with Memory(target) as memory:
            exact=0
            for i in range(probes):
                number=i*count//probes
                expected_bytes=('Historical entry '+str(number)+'\n'+('archive preface '*50)+' specimen'+str(number)+' measured '+str(number+7)+' pascals.').encode()
                exact+=memory.original(expected[number])==expected_bytes
            links=memory.db.execute("SELECT count(*) FROM persistent_records WHERE contract='project_sources'").fetchone()[0]
        return {'passed':hits==probes and totalcontext==probes and chronological==probes and exact==probes and links==count,
                'originals':count,'projects':4,'associations':links,'independent_probes':probes,'top_recall_hits':hits,'chronological_hits':chronological,'late_file_context_hits':totalcontext,'restored_exact_probes':exact,
                'ingest_seconds':ingest,'association_seconds':association,'retrieval_median_ms':statistics.median(latency),'retrieval_p95_ms':sorted(latency)[int(.95*(len(latency)-1))],
                'context_median_ms':statistics.median(contexts),'context_p95_ms':sorted(contexts)[int(.95*(len(contexts)-1))],'context_max_bytes':max(sizes),'query_cpu_seconds':querycpu,
                'database_bytes':dbbytes,'database_growth_bytes':dbbytes-before,'fts_bytes':ftsbytes,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                'export_seconds':exporttime,'restore_seconds':restoretime,'restore_integrity':restored['integrity'],'project_query_plan':queryplan,'kernel_policy':policy['kernel_policy'],
                'scope':'Warm deterministic synthetic literal/chronological/project recall; 100 restored byte probes plus complete restore integrity. No neural/model or general semantic reasoning measurement.'}

def main():
    result=run();print(json.dumps(result,indent=2));return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
