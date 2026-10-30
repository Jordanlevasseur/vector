import hashlib
from pathlib import Path
import tempfile
import unittest
from vector_core.config import Config
from vector_core.memory import Memory,Submission
from vector_core.portable import export_vector,restore_vector

class StreamingTests(unittest.TestCase):
    def test_large_original_streams_restores_and_exports_without_collection_cap(self):
        with tempfile.TemporaryDirectory() as folder:
            base=Path(folder);source=base/'large.bin'
            hasher=hashlib.sha256()
            with source.open('wb') as output:
                for i in range(24):
                    part=bytes([i])*1024*1024;output.write(part);hasher.update(part)
            with Memory(Config.load(data_dir=str(base/'data'))) as memory:
                one=memory.ingest_file(source)
                two=memory.ingest_file(source)
                self.assertNotEqual(one['event_id'],two['event_id'])
                self.assertEqual(one['sha256'],hasher.hexdigest())
                self.assertEqual(memory.event(one['event_id'])['byte_count'],24*1024*1024)
                self.assertEqual(memory.db.execute('SELECT count(*) FROM managed_objects').fetchone()[0],1)
                with self.assertRaisesRegex(ValueError,'Large original'):memory.original(one['event_id'])
                memory.export_original(one['event_id'],base/'exported.bin')
                export_vector(memory,base/'archive')
            restored=Config.load(data_dir=str(base/'different'))
            restore_vector(restored,base/'archive')
            with Memory(restored) as memory:
                digest=hashlib.sha256()
                for chunk in memory.original_chunks(one['event_id']):
                    self.assertLessEqual(len(chunk),1024*1024);digest.update(chunk)
                self.assertEqual(digest.hexdigest(),hasher.hexdigest())
                self.assertTrue(memory.verify()['passed'])
            self.assertEqual(source.read_bytes(),(base/'exported.bin').read_bytes())

    def test_cross_api_duplicate_originals_share_one_content_representation(self):
        with tempfile.TemporaryDirectory() as folder:
            base=Path(folder);file=base/'source';file.write_bytes(b'same source')
            with Memory(Config.load(data_dir=str(base/'data'))) as memory:
                one=memory.ingest_file(file,media_type='text/plain')
                two=memory.ingest(Submission(b'same source','second'))
                self.assertEqual(memory.original(one['event_id']),memory.original(two['event_id']))
                self.assertEqual(memory.db.execute('SELECT count(*) FROM blobs').fetchone()[0],1)
            with Memory(Config.load(data_dir=str(base/'legacy-first'))) as memory:
                one=memory.ingest(Submission(b'same source','legacy'))
                two=memory.ingest_file(file)
                self.assertEqual(one['sha256'],two['sha256'])
                self.assertEqual(memory.db.execute('SELECT count(*) FROM managed_objects').fetchone()[0],0)

    def test_unbounded_input_iterator_has_bounded_durable_batches_and_pages(self):
        with tempfile.TemporaryDirectory() as folder:
            with Memory(Config.load(data_dir=str(Path(folder)/'data'))) as memory:
                count=sum(1 for _ in memory.ingest_iter(Submission(('record '+str(i)).encode(),str(i)) for i in range(1001)))
                self.assertEqual(count,1001)
                cursor='';seen=set()
                while True:
                    page=memory.event_page(cursor,limit=37)
                    if not page['items']:break
                    for item in page['items']:self.assertNotIn(item['id'],seen);seen.add(item['id'])
                    cursor=page['next_cursor']
                self.assertEqual(len(seen),1001)

    def test_more_than_one_hundred_claims_are_integrated_and_pageable(self):
        from vector_core.knowledge import Knowledge,learn
        with tempfile.TemporaryDirectory() as folder:
            with Memory(Config.load(data_dir=str(Path(folder)/'data'))) as memory:
                source='\n'.join('Sensor '+str(i)+' | state | online' for i in range(1201))
                result=learn(memory,Submission(source.encode(),'many claims'),'plant',True)
                self.assertEqual(result['knowledge']['claim_count'],1201)
                self.assertTrue(result['knowledge']['claim_ids_truncated'])
                knowledge=Knowledge(memory);cursor='';count=0
                while True:
                    page=knowledge.claim_page(event_id=result['event']['event_id'],after=cursor,limit=71)
                    if not page['items']:break
                    count+=len(page['items']);cursor=page['next_cursor']
                self.assertEqual(count,1201)
