"""Host processes exercise offline CLI, abrupt exits, and actual SQLite-full rollback."""
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
from vector_core.portable import export_vector,restore_vector

ENV={**os.environ,'PYTHONPATH':str(Path(__file__).resolve().parents[1]/'src'),'PYTHONDONTWRITEBYTECODE':'1'}

class PortableAcceptanceTests(unittest.TestCase):
    def test_real_process_exits_during_export_and_restore_are_recoverable(self):
        with tempfile.TemporaryDirectory() as folder:
            base=Path(folder);config=Config.load(data_dir=str(base/'source'))
            with Memory(config) as memory:event=memory.ingest(Submission(b'crash recovery original','crash'))
            script='''
import os,sys
from vector_core.security import activate
activate()
from vector_core.config import Config
from vector_core.memory import Memory
from vector_core.portable import export_vector
with Memory(Config.load(data_dir=sys.argv[1])) as memory:
 def fault(stage):
  if stage=='after-publish':os._exit(73)
 export_vector(memory,sys.argv[2],fault=fault)
'''
            child=subprocess.run([sys.executable,'-c',script,str(config.data_dir),str(base/'archive')],env=ENV,capture_output=True,timeout=60)
            self.assertEqual(child.returncode,73,child.stderr)
            identifier=next((base/'archive'/'pending').iterdir()).name
            with Memory(config) as memory:self.assertTrue(export_vector(memory,base/'archive',resume=identifier)['complete'])
            script='''
import os,sys
from vector_core.security import activate
activate()
from vector_core.config import Config
from vector_core.portable import restore_vector

def fault(stage):
 if stage=='restore-block':os._exit(74)
restore_vector(Config.load(data_dir=sys.argv[1]),sys.argv[2],fault=fault)
'''
            target=Config.load(data_dir=str(base/'restored'))
            child=subprocess.run([sys.executable,'-c',script,str(target.data_dir),str(base/'archive')],env=ENV,capture_output=True,timeout=60)
            self.assertEqual(child.returncode,74,child.stderr)
            with self.assertRaisesRegex(ValueError,'quarantined'):Memory(target)
            self.assertTrue(restore_vector(target,base/'archive',resume=True)['activated'])
            with Memory(target) as restored:self.assertEqual(restored.original(event['event_id']),b'crash recovery original')

    def test_actual_cross_filesystem_export_and_restore(self):
        import shutil
        alternate=Path('/dev/shm')
        if not alternate.is_dir() or shutil.disk_usage(alternate).free<128*1024*1024:
            self.skipTest('No second local filesystem with 128 MiB free; cross-volume publication not verified.')
        with tempfile.TemporaryDirectory() as folder,tempfile.TemporaryDirectory(prefix='vector_portable_',dir=alternate) as other:
            base=Path(folder);repository=Path(other)/'archive'
            if base.stat().st_dev==Path(other).stat().st_dev:
                self.skipTest('Temporary locations share a filesystem; cross-volume publication not verified.')
            with Memory(Config.load(data_dir=str(base/'data'))) as memory:
                event=memory.ingest(Submission(b'cross-filesystem exact original','external SSD analogue'))
                self.assertTrue(export_vector(memory,repository)['complete'])
            target=Config.load(data_dir=str(base/'restored'))
            self.assertTrue(restore_vector(target,repository)['activated'])
            with Memory(target) as restored:self.assertEqual(restored.original(event['event_id']),b'cross-filesystem exact original')

    def test_actual_sqlite_full_rolls_back_without_losing_acknowledged_original(self):
        with tempfile.TemporaryDirectory() as folder:
            with Memory(Config.load(data_dir=str(Path(folder)/'data'))) as memory:
                first=memory.ingest(Submission(b'durable','first'))
                pages=memory.db.execute('PRAGMA page_count').fetchone()[0]
                memory.db.execute(f'PRAGMA max_page_count={pages+1}')
                with self.assertRaises(sqlite3.OperationalError) as error:
                    memory.ingest(Submission(os.urandom(1024*1024),'will not fit','application/octet-stream'))
                self.assertEqual(error.exception.sqlite_errorcode,sqlite3.SQLITE_FULL)
                self.assertEqual(memory.db.execute('SELECT count(*) FROM events').fetchone()[0],1)
                self.assertEqual(memory.original(first['event_id']),b'durable')
                self.assertTrue(memory.verify()['passed'])

    def test_guarded_cli_portability_and_network_denial_in_transfer_process(self):
        with tempfile.TemporaryDirectory() as folder:
            base=Path(folder)
            def cli(directory,*args):
                child=subprocess.run([sys.executable,'-m','vector_core','--data-dir',str(directory),*args],env=ENV,capture_output=True,text=True,timeout=60)
                self.assertEqual(child.returncode,0,child.stderr)
                return json.loads(child.stdout)
            event=cli(base/'data','add','--text','Exact offline state')
            cli(base/'data','export-vector',str(base/'archive'))
            self.assertTrue(cli(base/'unused','verify-export',str(base/'archive'))['actual_restoration'])
            cli(base/'restored','import-vector',str(base/'archive'))
            self.assertEqual(cli(base/'restored','show',event['event_id'])['sha256'],event['sha256'])
            script='''
import socket,sys
from vector_core.security import activate
activate()
from vector_core.portable import verify_export
assert verify_export(sys.argv[1])['verified']
for family in (socket.AF_INET,socket.AF_INET6,socket.AF_UNIX):
 try:socket.socket(family,socket.SOCK_STREAM)
 except PermissionError:pass
 else:raise AssertionError('Socket unexpectedly permitted')
'''
            child=subprocess.run([sys.executable,'-c',script,str(base/'archive')],env=ENV,capture_output=True,timeout=60)
            self.assertEqual(child.returncode,0,child.stderr)
