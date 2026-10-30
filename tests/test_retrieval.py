from pathlib import Path
import tempfile
import unittest
from vector_core.config import Config
from vector_core.memory import Memory,Submission
from vector_core.retrieval import search,rebuild

class RetrievalTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.memory=Memory(Config.load(data_dir=str(Path(self.temp.name)/'data')))
        self.addCleanup(self.memory.close)
        self.one=self.memory.ingest(Submission('Pressure sensor measures 42 pascals. Café.'.encode(),'sensor',metadata={'project':'lab','checked':True,'count':1}))
        self.two=self.memory.ingest(Submission(b'Thermal sensor measures 17 kelvin.','thermal',metadata={'project':'other','checked':1}))

    def test_incremental_results_have_exact_source_attribution(self):
        results=search(self.memory,'pressure 42')
        self.assertEqual(len(results),1)
        self.assertEqual(results[0]['event_id'],self.one['event_id'])
        self.assertEqual(results[0]['source_id'],self.one['source_id'])
        self.assertEqual(results[0]['sha256'],self.one['sha256'])
        self.assertIn('42 pascals',results[0]['excerpt'])
        self.assertEqual(search(self.memory,'CAFÉ')[0]['event_id'],self.one['event_id'])

    def test_source_time_and_typed_metadata_filters(self):
        self.assertEqual(search(self.memory,'sensor',source_id=self.one['source_id'])[0]['event_id'],self.one['event_id'])
        self.assertEqual(len(search(self.memory,'sensor',metadata={'checked':True})),1)
        self.assertEqual(search(self.memory,'sensor',metadata={'checked':1})[0]['event_id'],self.two['event_id'])
        self.assertEqual(len(search(self.memory,'',metadata={'project':'lab'})),1)
        self.assertEqual(search(self.memory,'sensor',since='2999-01-01T00:00:00+00:00'),[])
        with self.assertRaises(ValueError):search(self.memory,'sensor',since='2020-01-01')
        with self.assertRaises(ValueError):search(self.memory,'sensor',since='2030-01-01T00:00:00Z',until='2020-01-01T00:00:00Z')

    def test_malformed_queries_are_literal_data_not_fts_or_sql_programs(self):
        for query in ('" OR *',"sensor'; DROP TABLE events; --",'NEAR(sensor,42)',':{}[]'):
            result=search(self.memory,query,metadata={'project':'lab'})
            self.assertIsInstance(result,list)
        self.assertEqual(self.memory.verify()['events'],2)
        for query in ('', 'x'*513, ' '.join(['x']*17)):
            with self.assertRaises(ValueError):search(self.memory,query)
        with self.assertRaises(ValueError):search(self.memory,'sensor',limit=1000)

    def test_rebuild_discards_corrupt_derived_text_and_keeps_originals(self):
        original=self.memory.original(self.one['event_id'])
        self.memory.db.execute("UPDATE texts SET text='corrupt derived text'")
        with self.assertRaises(ValueError):search(self.memory,'pressure')
        rebuild(self.memory)
        self.assertEqual(search(self.memory,'pressure')[0]['event_id'],self.one['event_id'])
        self.assertEqual(self.memory.original(self.one['event_id']),original)
        self.assertTrue(self.memory.verify()['passed'])

    def test_binary_and_failed_batch_are_not_indexed(self):
        self.memory.ingest(Submission(b'pressure 42','binary','application/octet-stream'))
        with self.assertRaises(ValueError):self.memory.ingest_batch([
            Submission(b'uncommitted searchable phrase','first'),Submission(b'bad','second',source_id='absent')])
        self.assertEqual(search(self.memory,'uncommitted'),[])
        self.assertEqual(len(search(self.memory,'pressure')),1)

    def test_corrupt_original_blocks_rebuild_without_partial_index_commit(self):
        self.memory.db.execute('DROP TRIGGER blobs_no_update')
        self.memory.db.execute('UPDATE blobs SET body=zeroblob(byte_count) WHERE sha256=?',(self.one['sha256'],))
        with self.assertRaises(ValueError):rebuild(self.memory)
        self.assertEqual(len(search(self.memory,'thermal')),1)
