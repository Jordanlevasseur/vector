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

MIGRATIONS.append("""
CREATE TABLE blobs(sha256 TEXT PRIMARY KEY, body BLOB NOT NULL, byte_count INTEGER NOT NULL CHECK(byte_count=length(body)));
CREATE TABLE sources(id TEXT PRIMARY KEY, name TEXT NOT NULL, created TEXT NOT NULL);
CREATE TABLE events(id TEXT PRIMARY KEY, source_id TEXT NOT NULL REFERENCES sources(id),
 sha256 TEXT NOT NULL REFERENCES blobs(sha256), occurred TEXT NOT NULL,
 media_type TEXT NOT NULL, submission_name TEXT NOT NULL, metadata TEXT NOT NULL, parent_id TEXT REFERENCES events(id));
CREATE INDEX events_source_time ON events(source_id,occurred,id);
CREATE INDEX events_hash ON events(sha256);
CREATE INDEX events_time ON events(occurred,id);
CREATE TABLE texts(event_id TEXT PRIMARY KEY REFERENCES events(id), text TEXT, status TEXT NOT NULL);
CREATE TRIGGER blobs_no_update BEFORE UPDATE ON blobs BEGIN SELECT RAISE(ABORT,'immutable originals'); END;
CREATE TRIGGER blobs_no_delete BEFORE DELETE ON blobs BEGIN SELECT RAISE(ABORT,'immutable originals'); END;
CREATE TRIGGER sources_no_update BEFORE UPDATE ON sources BEGIN SELECT RAISE(ABORT,'immutable source'); END;
CREATE TRIGGER sources_no_delete BEFORE DELETE ON sources BEGIN SELECT RAISE(ABORT,'immutable source'); END;
CREATE TRIGGER events_no_update BEFORE UPDATE ON events BEGIN SELECT RAISE(ABORT,'append-only events'); END;
CREATE TRIGGER events_no_delete BEFORE DELETE ON events BEGIN SELECT RAISE(ABORT,'append-only events'); END;
""")

MIGRATIONS.append("""
CREATE VIRTUAL TABLE text_search USING fts5(text,content='',tokenize='unicode61');
INSERT INTO text_search(rowid,text) SELECT rowid,text FROM texts WHERE status='utf8-extracted';
""")
