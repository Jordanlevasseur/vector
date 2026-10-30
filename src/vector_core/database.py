"""Versioned transactional SQLite initialization; no unrelated database adoption."""
import os
import sqlite3
import stat

APPLICATION_ID=0x56454354
MIGRATIONS=["""
CREATE TABLE audit(id INTEGER PRIMARY KEY, occurred TEXT NOT NULL, action TEXT NOT NULL, detail TEXT NOT NULL);
CREATE TRIGGER audit_no_update BEFORE UPDATE ON audit BEGIN SELECT RAISE(ABORT,'append-only audit'); END;
CREATE TRIGGER audit_no_delete BEFORE DELETE ON audit BEGIN SELECT RAISE(ABORT,'append-only audit'); END;
"""]

def connect(config):
    root=config.initialize()
    path=root/'vector.sqlite3'
    for name in ('vector.sqlite3','vector.sqlite3-wal','vector.sqlite3-shm','vector.sqlite3-journal'):
        if (root/name).is_symlink(): raise ValueError('Database symbolic links forbidden.')
    if not path.exists():
        fd=os.open(path,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
        os.close(fd)
    info=path.stat()
    if not stat.S_ISREG(info.st_mode) or info.st_nlink!=1 or info.st_uid!=os.getuid():
        raise ValueError('Invalid database identity.')
    db=sqlite3.connect(path,timeout=5,isolation_level=None)
    try:
        db.row_factory=sqlite3.Row
        db.enable_load_extension(False)
        db.execute('PRAGMA trusted_schema=OFF')
        db.execute('PRAGMA foreign_keys=ON')
        db.execute('PRAGMA synchronous=FULL')
        db.execute('PRAGMA cache_size=-4096')
        identity=db.execute('PRAGMA application_id').fetchone()[0]
        version=db.execute('PRAGMA user_version').fetchone()[0]
        if identity not in (0,APPLICATION_ID) or version>len(MIGRATIONS):
            raise ValueError('Unknown database identity/version.')
        if identity==0 and db.execute("SELECT count(*) FROM sqlite_master WHERE type='table'").fetchone()[0]:
            raise ValueError('Unrelated database; migration refused.')
        if db.execute('PRAGMA journal_mode=WAL').fetchone()[0]!='wal':
            raise RuntimeError('Required WAL durability unavailable.')
        for index in range(version,len(MIGRATIONS)):
            try:
                db.executescript('BEGIN IMMEDIATE;\n'+MIGRATIONS[index]+
                    f'\nPRAGMA application_id={APPLICATION_ID};\nPRAGMA user_version={index+1};\nCOMMIT;')
            except Exception:
                if db.in_transaction: db.rollback()
                raise
        return db
    except Exception:
        db.close()
        raise
