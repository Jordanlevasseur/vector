import errno
import json
import os
from pathlib import Path
import socket
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from vector_core.config import Config
from vector_core.database import connect
from vector_core.intake import read_file
from vector_core.maintenance import backup

ROOT=Path(__file__).resolve().parents[1]
ENV={**os.environ,'PYTHONPATH':str(ROOT/'src'),'PYTHONDONTWRITEBYTECODE':'1'}

class FoundationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base=Path(self.temp.name)
        self.config=Config.load(data_dir=str(self.base/'data'))

    def test_database_survives_restart_with_required_pragmas(self):
        db=connect(self.config)
        db.execute("INSERT INTO audit VALUES (1,'now','test','{}')")
        self.assertEqual(db.execute('PRAGMA synchronous').fetchone()[0],2)
        self.assertEqual(db.execute('PRAGMA journal_mode').fetchone()[0],'wal')
        db.close()
        db=connect(self.config)
        self.assertEqual(db.execute('SELECT action FROM audit').fetchone()[0],'test')
        with self.assertRaises(sqlite3.IntegrityError): db.execute('DELETE FROM audit')
        db.close()

    def test_nonempty_unrelated_directory_is_not_adopted(self):
        self.config.data_dir.mkdir(mode=0o700)
        keep=self.config.data_dir/'keep'
        keep.write_text('user data')
        with self.assertRaises(ValueError): connect(self.config)
        self.assertEqual(keep.read_text(),'user data')

    def test_unknown_future_migration_is_not_downgraded(self):
        db=connect(self.config);db.execute('PRAGMA user_version=999');db.close()
        with self.assertRaises(ValueError): connect(self.config)

    def test_symlink_and_helix_scopes_rejected(self):
        for path in ('/home/mint/VECTOR/helix/memory','/home/mint/VECTOR','relative'):
            with self.assertRaises(ValueError): Config.load(data_dir=path)
        with self.assertRaises(ValueError):Config(Path('/home/mint/VECTOR/helix/new-data')).initialize()
        link=self.base/'link';link.symlink_to(self.base,target_is_directory=True)
        with self.assertRaises(ValueError): Config.load(data_dir=str(link/'data'))

    def test_bounded_regular_file_reader(self):
        source=self.base/'source';source.write_bytes(b'raw\x00bytes')
        self.assertEqual(read_file(source,20),b'raw\x00bytes')
        with self.assertRaises(ValueError): read_file(source,2)
        link=self.base/'link';link.symlink_to(source)
        with self.assertRaises(OSError): read_file(link,20)
        fifo=self.base/'fifo';os.mkfifo(fifo)
        with self.assertRaises(ValueError): read_file(fifo,20)

    def test_unknown_config_cannot_disable_network_guard(self):
        path=self.base/'settings.toml';path.write_text('offline=false')
        with self.assertRaises(ValueError): Config.load(path)

    def test_consistent_backup_never_overwrites_previous_copy(self):
        db=connect(self.config)
        one=backup(db,self.config.data_dir);two=backup(db,self.config.data_dir)
        self.assertNotEqual(one['directory'],two['directory'])
        saved=sqlite3.connect(Path(one['directory'])/'archive.sqlite3')
        self.assertEqual(saved.execute('PRAGMA integrity_check').fetchone()[0],'ok')
        saved.close();db.close()

    def test_actual_cli_enforces_kernel_policy_before_database_use(self):
        run=subprocess.run([sys.executable,'-m','vector_core','--data-dir',str(self.config.data_dir),'health'],
            env={**ENV,'VECTOR_OFFLINE':'0'},capture_output=True,text=True,timeout=20)
        self.assertEqual(run.returncode,0,run.stderr)
        report=json.loads(run.stdout)
        self.assertTrue(all(report['policy']['network_denied'].values()))
        self.assertEqual(report['database_integrity'],'ok')
        self.assertFalse(report['model_available'])

    def test_missing_seccomp_fails_before_creating_data(self):
        code='from unittest.mock import patch; from vector_core.cli import main; '\
             'p=patch("ctypes.CDLL",side_effect=OSError("missing")); p.start(); '\
             'raise SystemExit(main(["--data-dir",'+repr(str(self.config.data_dir))+']))'
        run=subprocess.run([sys.executable,'-c',code],env=ENV,capture_output=True,text=True,timeout=20)
        self.assertEqual(run.returncode,2)
        self.assertFalse(self.config.data_dir.exists())

    def test_inherited_socket_and_process_creation_cannot_bypass_policy(self):
        # Positive control: this host must allow socket creation before loading
        # VECTOR's filter. No connection or external network packet is attempted.
        handle=socket.socket()
        self.addCleanup(handle.close)
        code='''import os,errno,socket
from vector_core.security import activate
activate()
try: os.fstat(FD)
except OSError as e: assert e.errno==errno.EBADF
else: raise AssertionError('inherited socket survived')
try: os.fork()
except OSError as e: assert e.errno==errno.EPERM
else: raise AssertionError('fork allowed')
print('kernel controls verified')
'''.replace('FD',str(handle.fileno()))
        run=subprocess.run([sys.executable,'-c',code],env=ENV,pass_fds=(handle.fileno(),),capture_output=True,text=True,timeout=20)
        self.assertEqual(run.returncode,0,run.stderr)
        self.assertIn('kernel controls verified',run.stdout)

    def test_unsafe_shared_data_parent_is_rejected_before_creation(self):
        parent=self.base/'shared'
        parent.mkdir(mode=0o777)
        parent.chmod(0o777)
        with self.assertRaises(ValueError):Config.load(data_dir=str(parent/'data'))
        self.assertFalse((parent/'data').exists())
