import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from vector_core.config import Config
from vector_core.memory import Memory,Submission
from vector_core.maintenance import backup,restore

ROOT=Path(__file__).resolve().parents[1]
ENV={**os.environ,'PYTHONPATH':str(ROOT/'src'),'PYTHONDONTWRITEBYTECODE':'1'}

class MemoryTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.base=Path(self.temp.name);self.config=Config.load(data_dir=str(self.base/'data'))
        self.memory=Memory(self.config);self.addCleanup(self.memory.close)

    def test_duplicate_bytes_are_distinct_durable_events(self):
        raw=b'Complete original\x00\xff\r\n'
        one=self.memory.ingest(Submission(raw,'first','application/octet-stream'))
        two=self.memory.ingest(Submission(raw,'second','application/octet-stream'))
        self.assertNotEqual(one['event_id'],two['event_id'])
        self.assertEqual(one['sha256'],two['sha256'])
        self.assertEqual(self.memory.db.execute('SELECT count(*) FROM blobs').fetchone()[0],1)
        with Memory(self.config) as reopened:
            for event in (one,two): self.assertEqual(reopened.original(event['event_id']),raw)
            self.assertTrue(reopened.verify()['passed'])

    def test_revisions_preserve_original_source_and_each_filename(self):
        one=self.memory.ingest(Submission(b'version one','original.txt'))
        two=self.memory.ingest(Submission(b'version two','revision.txt',parent_id=one['event_id']))
        self.assertEqual(one['source_id'],two['source_id'])
        self.assertEqual(self.memory.original(one['event_id']),b'version one')
        event=self.memory.event(two['event_id'])
        self.assertEqual(event['parent_id'],one['event_id'])
        self.assertEqual(event['submission_name'],'revision.txt')

    def test_failed_batch_rolls_back_all_originals_events_and_audit(self):
        with self.assertRaises(ValueError): self.memory.ingest_batch([
            Submission(b'first','first'),Submission(b'second','second',source_id='absent')])
        for table in ('blobs','sources','events','texts','audit'):
            self.assertEqual(self.memory.db.execute('SELECT count(*) FROM '+table).fetchone()[0],0)

    def test_originals_and_history_cannot_be_updated_or_deleted(self):
        self.memory.ingest(Submission(b'keep','keep'))
        for table in ('blobs','sources','events','audit'):
            with self.assertRaises(sqlite3.IntegrityError): self.memory.db.execute('DELETE FROM '+table)
        with self.assertRaises(sqlite3.IntegrityError): self.memory.db.execute("UPDATE blobs SET body=X'00'")

    def test_invalid_extraction_and_metadata_never_discard_original(self):
        record=self.memory.ingest(Submission(b'\xff','invalid.txt',metadata={'provided_by':'user','nested':[1,True]}))
        self.assertEqual(record['extraction_status'],'invalid-utf8-preserved')
        self.assertEqual(self.memory.original(record['event_id']),b'\xff')
        self.assertEqual(self.memory.event(record['event_id'])['metadata']['nested'],[1,True])

    def test_corruption_detected_not_silently_reused(self):
        record=self.memory.ingest(Submission(b'abc','first'))
        self.memory.db.execute('DROP TRIGGER blobs_no_update')
        self.memory.db.execute("UPDATE blobs SET body=X'646566'")
        self.assertFalse(self.memory.verify()['passed'])
        with self.assertRaises(ValueError): self.memory.original(record['event_id'])
        with self.assertRaises(ValueError): self.memory.ingest(Submission(b'abc','again'))

    def test_non_overwriting_restore_recovers_exact_bytes(self):
        record=self.memory.ingest(Submission(b'faithful\r\n\x00','source'))
        saved=backup(self.memory.db,self.config.data_dir)
        target=Config.load(data_dir=str(self.base/'restored'))
        self.assertTrue(restore(target,saved['directory'])['restored'])
        with Memory(target) as reopened:self.assertEqual(reopened.original(record['event_id']),b'faithful\r\n\x00')
        with self.assertRaises(FileExistsError): restore(self.config,saved['directory'])

    def test_corrupt_backup_quarantines_new_target(self):
        self.memory.ingest(Submission(b'original','source'))
        saved=backup(self.memory.db,self.config.data_dir)
        with (Path(saved['directory'])/'archive.sqlite3').open('ab') as output:output.write(b'corrupt')
        target=Config.load(data_dir=str(self.base/'quarantined'))
        with self.assertRaises(ValueError): restore(target,saved['directory'])
        with self.assertRaises(ValueError): Memory(target)
        self.assertTrue(self.memory.verify()['passed'])

    def test_source_limits_and_revision_mismatch_fail_before_acknowledgement(self):
        with self.assertRaises(ValueError):self.memory.ingest(Submission(b'x'*(self.config.max_source_bytes+1),'large'))
        one=self.memory.ingest(Submission(b'a','one'))
        two=self.memory.ingest(Submission(b'b','two'))
        with self.assertRaises(ValueError):self.memory.ingest(Submission(b'c','bad',source_id=two['source_id'],parent_id=one['event_id']))
        self.assertEqual(self.memory.verify()['events'],2)

    def test_real_process_crashes_before_and_after_commit(self):
        path=str(self.config.data_dir)
        uncommitted='''import os
from vector_core.config import Config
from vector_core.memory import Memory
m=Memory(Config.load(data_dir=PATH))
m.db.execute('BEGIN IMMEDIATE')
m.db.execute("INSERT INTO blobs VALUES ('uncommitted',X'78',1)")
os._exit(17)
'''.replace('PATH',repr(path))
        run=subprocess.run([sys.executable,'-c',uncommitted],env=ENV,timeout=20)
        self.assertEqual(run.returncode,17)
        self.assertEqual(self.memory.verify()['events'],0)
        self.assertEqual(self.memory.db.execute('SELECT count(*) FROM blobs').fetchone()[0],0)
        marker=self.base/'committed-id'
        committed='''import os
from pathlib import Path
from vector_core.config import Config
from vector_core.memory import Memory,Submission
m=Memory(Config.load(data_dir=PATH))
r=m.ingest(Submission(b'committed-original','crash-source'))
with open(MARKER,'w') as f:f.write(r['event_id']);f.flush();os.fsync(f.fileno())
os._exit(18)
'''.replace('PATH',repr(path)).replace('MARKER',repr(str(marker)))
        run=subprocess.run([sys.executable,'-c',committed],env=ENV,timeout=20)
        self.assertEqual(run.returncode,18)
        with Memory(self.config) as reopened:
            self.assertEqual(reopened.original(marker.read_text()),b'committed-original')
            self.assertTrue(reopened.verify()['passed'])
