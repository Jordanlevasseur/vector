"""Controlled context/tool benchmark; actual model timings are separate evidence."""
import json
from pathlib import Path
import resource
import sqlite3
import statistics
import tempfile
import time


def run():
    from vector_core.config import Config
    from vector_core.memory import Memory,Submission
    from vector_core.context import build_context
    from vector_core.retrieval import search
    from vector_core.tools import compute
    with tempfile.TemporaryDirectory(prefix='vector_context_benchmark_') as directory:
        config=Config.load(data_dir=str(Path(directory)/'data'))
        with Memory(config) as memory:
            ids=[];tick=time.perf_counter()
            for event in memory.ingest_iter(Submission(f'Station {i:04d} pressure is {1000+i} Pa.'.encode(),f'station-{i:04d}') for i in range(1000)):ids.append(event['event_id'])
            ingest=time.perf_counter()-tick
            retrieval=[];context=[];correct=0;cpu=time.process_time()
            for i in range(0,1000,10):
                question=f'Station {i:04d} pressure'
                tick=time.perf_counter();search(memory,question,limit=8);retrieval.append((time.perf_counter()-tick)*1000)
                tick=time.perf_counter();built=build_context(memory,question,budget_bytes=8192);context.append((time.perf_counter()-tick)*1000)
                correct+=bool(built['context']['sources'] and built['context']['sources'][0]['event_id']==ids[i])
            cpu=time.process_time()-cpu;tick=time.perf_counter()
            for _ in range(1000):assert compute('arithmetic',{'expression':'2*(3+4)'})['value']=='14'
            tools=time.perf_counter()-tick
            memory.db.execute('PRAGMA wal_checkpoint(TRUNCATE)')
            try:index_bytes=memory.db.execute("SELECT coalesce(sum(pgsize),0) FROM dbstat WHERE name LIKE 'text_search%' ").fetchone()[0]
            except sqlite3.Error:index_bytes=None
            return {'passed':correct==100,'corpus_originals':1000,'literal_queries':100,'correct_top_context_source':correct,
                    'ingest_seconds':ingest,'retrieval_median_ms':statistics.median(retrieval),'retrieval_p95_ms':sorted(retrieval)[95],
                    'context_median_ms':statistics.median(context),'context_p95_ms':sorted(context)[95],'retrieval_context_cpu_seconds':cpu,
                    'pure_arithmetic_1000_calls_seconds':tools,'database_bytes':(config.data_dir/'vector.sqlite3').stat().st_size,
                    'fts_page_bytes':index_bytes,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                    'scope':'Warm synthetic literal retrieval/context. No semantic reasoning or inference performance claim. Pure tool timing excludes durable audit.'}


def main():
    from vector_core.security import activate
    activate();report=run();print(json.dumps(report,indent=2));return 0 if report['passed'] else 1

if __name__=='__main__':raise SystemExit(main())
