"""Measured 50,000-event portability workload; no general intelligence claim."""
import json
from pathlib import Path
import resource
import shutil
import tempfile
import time


def run():
    from vector_core.config import Config
    from vector_core.memory import Memory,Submission
    from vector_core.portable import export_vector,restore_vector
    from vector_core.retrieval import search
    count=50000
    if shutil.disk_usage('/tmp').free<1024**3:
        return {'passed':False,'status':'RESOURCE_BLOCKED','reason':'Requires 1 GiB free temporary storage including safety reserve.'}
    with tempfile.TemporaryDirectory(prefix='vector_50k_') as directory:
        root=Path(directory)
        source=Config.load(data_dir=str(root/'data'))
        text=lambda i:f'Portable station {i:06d} pressure {1000+i} pascals.'.encode()
        started=time.perf_counter()
        with Memory(source) as memory:
            acknowledged=0
            for receipt in memory.ingest_iter(Submission(text(i),f'station-{i:06d}') for i in range(count)):
                acknowledged+=1
            ingest_seconds=time.perf_counter()-started
            tick=time.perf_counter();exported=export_vector(memory,root/'archive');export_seconds=time.perf_counter()-tick
            first_bytes=sum(p.stat().st_size for p in (root/'archive').rglob('*') if p.is_file())
            tick=time.perf_counter();increment=export_vector(memory,root/'archive');increment_seconds=time.perf_counter()-tick
            after_bytes=sum(p.stat().st_size for p in (root/'archive').rglob('*') if p.is_file())
            memory.db.execute('PRAGMA wal_checkpoint(TRUNCATE)')
            database_bytes=(source.data_dir/'vector.sqlite3').stat().st_size
        restored_config=Config.load(data_dir=str(root/'restored'))
        tick=time.perf_counter();restoration=restore_vector(restored_config,root/'archive');restore_seconds=time.perf_counter()-tick
        with Memory(restored_config) as memory:
            tick=time.perf_counter();verified=memory.verify();verify_seconds=time.perf_counter()-tick
            correct=0;cursor='';retrieved=0
            while True:
                page=memory.event_page(cursor,1000)
                if not page['items']:break
                for event in page['items']:
                    index=int(event['submission_name'].split('-')[1])
                    correct+=memory.original(event['id'])==text(index)
                cursor=page['next_cursor']
            for i in range(0,count,500):
                results=search(memory,f'station {i:06d} pressure',limit=1)
                retrieved+=bool(results and results[0]['name']==f'station-{i:06d}')
        return {'passed':acknowledged==count and correct==count and verified['passed'] and retrieved==100 and increment['new_blocks']==0,
                'workload':'50,000 distinct short synthetic originals, full byte reconstruction and integrity, 100 literal lexical probes; warm cache',
                'events':count,'acknowledged':acknowledged,'byte_identical_originals':correct,'lexical_probes_correct':retrieved,
                'ingest_seconds':ingest_seconds,'export_seconds':export_seconds,'increment_seconds':increment_seconds,
                'restore_seconds':restore_seconds,'verify_seconds':verify_seconds,'database_bytes':database_bytes,
                'first_repository_bytes':first_bytes,'unchanged_incremental_bytes':after_bytes-first_bytes,
                'incremental_new_blocks':increment['new_blocks'],'incremental_reused_blocks':increment['reused_blocks'],
                'logical_export_bytes':exported['file_bytes'],'peak_process_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                'restoration_integrity':restoration['integrity'],'verification':verified,
                'limitations':'No million-record, cold-cache, real-model, multi-volume or desktop-GUI qualification.'}


def main():
    from vector_core.security import activate
    activate()
    report=run();print(json.dumps(report,indent=2));return 0 if report['passed'] else 1

if __name__=='__main__':raise SystemExit(main())
