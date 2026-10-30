"""Controlled 10k lexical/provenance benchmark; no semantic reasoning claim."""
import json
from pathlib import Path
import resource
import shutil
import statistics
import tempfile
import time


def run():
    from vector_core.config import Config
    from vector_core.memory import Memory,Submission
    from vector_core.retrieval import search,rebuild
    available=int(next(line.split()[1] for line in Path('/proc/meminfo').read_text().splitlines()
                       if line.startswith('MemAvailable:')))*1024
    if available<256*1024*1024 or shutil.disk_usage('/tmp').free<128*1024*1024:
        return {'passed':False,'status':'RESOURCE_BLOCKED','reason':'10k benchmark requires 256 MiB available RAM and 128 MiB free disk.'}
    with tempfile.TemporaryDirectory(prefix='vector_10k_') as folder:
        config=Config.load(data_dir=str(Path(folder)/'data'))
        with Memory(config) as memory:
            count=10000
            records=[]
            started=time.perf_counter()
            for start in range(0,count,64):
                batch=[Submission(f'Station {i:05d} records pressure {1000+i} pascals. Run {i%23}.'.encode(),
                                  f'station-{i:05d}',metadata={'station':i,'run':i%23})
                       for i in range(start,min(start+64,count))]
                records.extend(memory.ingest_batch(batch))
            ingestion=time.perf_counter()-started
            lexical=[];exact=[];correct=0;attributed=0;reconstructed=0
            cpu_start=time.process_time()
            for i,event in enumerate(records):
                expected=f'Station {i:05d} records pressure {1000+i} pascals. Run {i%23}.'.encode()
                tick=time.perf_counter_ns()
                original=memory.original(event['event_id'])
                exact.append((time.perf_counter_ns()-tick)/1e6)
                reconstructed+=original==expected
                tick=time.perf_counter_ns()
                result=search(memory,f'station {i:05d} pressure',limit=3)
                lexical.append((time.perf_counter_ns()-tick)/1e6)
                correct+=bool(result and result[0]['event_id']==event['event_id'])
                attributed+=bool(result and result[0]['source_id']==event['source_id'] and result[0]['sha256']==event['sha256'])
            cpu=time.process_time()-cpu_start
            tick=time.perf_counter();rebuild(memory);rebuild_seconds=time.perf_counter()-tick
            verified=memory.verify()
            memory.db.execute('PRAGMA wal_checkpoint(TRUNCATE)')
            footprint=sum(p.stat().st_size for p in config.data_dir.glob('vector.sqlite3*'))
            report={'passed':correct==count and attributed==count and reconstructed==count and verified['passed'],
                'workload':'10k distinct synthetic station facts, one ID-bearing literal lexical query each; not general fact QA or semantic recall',
                'records':count,'lexical_top1_fraction':correct/count,'source_attribution_fraction':attributed/count,
                'byte_reconstruction_fraction':reconstructed/count,'ingest_seconds':ingestion,
                'ingest_events_per_second':count/ingestion,'rebuild_seconds':rebuild_seconds,
                'lookup_median_ms':statistics.median(exact),'lookup_p95_ms':sorted(exact)[int(count*.95)],
                'lexical_median_ms':statistics.median(lexical),'lexical_p95_ms':sorted(lexical)[int(count*.95)],
                'query_cpu_seconds':cpu,'database_bytes_including_indexes':footprint,
                'process_peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                'index_size_separate':'not separately measured (shared SQLite file)',
                'model_inference':'not run','cache_condition':'warm after ingestion; no cold-cache guarantee',
                'original_integrity':verified}
            return report


def main():
    from vector_core.security import activate
    activate()
    report=run()
    print(json.dumps(report,indent=2))
    return 0 if report['passed'] else 1

if __name__=='__main__':raise SystemExit(main())
