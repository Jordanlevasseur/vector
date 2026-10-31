import sqlite3
import unittest
from unittest.mock import patch

from vector_core.memory import verify_connection


class TrackingConnection(sqlite3.Connection):
    integrity_started = False
    integrity_finished = False

    def execute(self, sql, *args, **kwargs):
        if sql == 'PRAGMA integrity_check':
            self.integrity_started = True
        cursor = super().execute(sql, *args, **kwargs)
        if sql == 'PRAGMA integrity_check':
            self.integrity_finished = True
        return cursor


class VerificationDeadlineTests(unittest.TestCase):
    def test_deadline_interrupts_real_sql_integrity_scan_and_restores_connection(self):
        db = sqlite3.connect(':memory:', factory=TrackingConnection)
        self.addCleanup(db.close)
        db.execute('PRAGMA user_version=1')
        db.execute('CREATE TABLE audit(id INTEGER PRIMARY KEY, detail TEXT)')
        db.executemany('INSERT INTO audit(detail) VALUES (?)', [('retained legacy audit ' * 10,)] * 10000)
        db.commit()
        clock = iter((0.0, 2.0))
        with patch('time.monotonic', side_effect=lambda: next(clock, 2.0)):
            with self.assertRaises(TimeoutError):
                verify_connection(db, deadline=1.0)
        self.assertTrue(db.integrity_started)
        self.assertFalse(db.integrity_finished)
        self.assertEqual(db.execute('SELECT count(*) FROM audit').fetchone()[0], 10000)
        self.assertTrue(verify_connection(db)['passed'])
