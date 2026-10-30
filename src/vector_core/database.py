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
        db.setlimit(sqlite3.SQLITE_LIMIT_LENGTH,32*1024*1024)
        db.enable_load_extension(False)
        db.execute('PRAGMA trusted_schema=OFF')
        db.execute('PRAGMA foreign_keys=ON')
        # REPLACE performs an implicit DELETE; recursive triggers must protect it.
        db.execute('PRAGMA recursive_triggers=ON')
        db.execute('PRAGMA synchronous=FULL')
        db.execute('PRAGMA cache_size=-4096')
        identity=db.execute('PRAGMA application_id').fetchone()[0]
        version=db.execute('PRAGMA user_version').fetchone()[0]
        if identity not in (0,APPLICATION_ID) or not 0<=version<=len(MIGRATIONS):
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

MIGRATIONS.append("""
CREATE TABLE entities(id TEXT PRIMARY KEY,name TEXT NOT NULL,normalized TEXT NOT NULL UNIQUE);
CREATE TABLE claims(id TEXT PRIMARY KEY,event_id TEXT NOT NULL REFERENCES events(id),
 start_char INTEGER NOT NULL,end_char INTEGER NOT NULL,quote TEXT NOT NULL,
 subject_id TEXT NOT NULL REFERENCES entities(id),predicate TEXT NOT NULL,value TEXT NOT NULL,
 value_key TEXT NOT NULL,scope TEXT NOT NULL,unit TEXT NOT NULL,kind TEXT NOT NULL,
 exclusive INTEGER NOT NULL,object_id TEXT REFERENCES entities(id),origin TEXT NOT NULL,created TEXT NOT NULL,
 UNIQUE(event_id,start_char,end_char,subject_id,predicate,value_key,scope,unit,kind,exclusive));
CREATE INDEX claims_group ON claims(subject_id,predicate,scope,unit,exclusive,value_key);
CREATE INDEX claims_event ON claims(event_id);
CREATE INDEX claims_object ON claims(object_id);
CREATE TABLE assessments(id TEXT PRIMARY KEY,claim_id TEXT NOT NULL REFERENCES claims(id),
 previous_id TEXT REFERENCES assessments(id),state TEXT NOT NULL,confidence REAL NOT NULL,
 reason TEXT NOT NULL,actor TEXT NOT NULL,created TEXT NOT NULL);
CREATE INDEX assessments_claim ON assessments(claim_id,created,id);
CREATE TABLE assessment_evidence(assessment_id TEXT NOT NULL REFERENCES assessments(id),
 evidence_id TEXT NOT NULL REFERENCES claims(id),PRIMARY KEY(assessment_id,evidence_id));
CREATE TABLE overrides(id TEXT PRIMARY KEY,claim_id TEXT NOT NULL REFERENCES claims(id),scope TEXT NOT NULL,
 value TEXT NOT NULL,reason TEXT NOT NULL,previous_assessment TEXT REFERENCES assessments(id),
 previous_override TEXT REFERENCES overrides(id),actor TEXT NOT NULL,created TEXT NOT NULL);
CREATE INDEX overrides_claim ON overrides(claim_id,scope,created,id);
CREATE TABLE extraction_runs(id TEXT PRIMARY KEY,event_id TEXT NOT NULL REFERENCES events(id),
 parser TEXT NOT NULL,scope TEXT NOT NULL,status TEXT NOT NULL,detail TEXT NOT NULL,created TEXT NOT NULL);
CREATE TRIGGER claims_no_update BEFORE UPDATE ON claims BEGIN SELECT RAISE(ABORT,'append-only claims'); END;
CREATE TRIGGER claims_no_delete BEFORE DELETE ON claims BEGIN SELECT RAISE(ABORT,'append-only claims'); END;
CREATE TRIGGER assessments_no_update BEFORE UPDATE ON assessments BEGIN SELECT RAISE(ABORT,'versioned assessments'); END;
CREATE TRIGGER assessments_no_delete BEFORE DELETE ON assessments BEGIN SELECT RAISE(ABORT,'versioned assessments'); END;
CREATE TRIGGER overrides_no_update BEFORE UPDATE ON overrides BEGIN SELECT RAISE(ABORT,'auditable overrides'); END;
CREATE TRIGGER overrides_no_delete BEFORE DELETE ON overrides BEGIN SELECT RAISE(ABORT,'auditable overrides'); END;
CREATE TRIGGER runs_no_update BEFORE UPDATE ON extraction_runs BEGIN SELECT RAISE(ABORT,'append-only extraction'); END;
CREATE TRIGGER runs_no_delete BEFORE DELETE ON extraction_runs BEGIN SELECT RAISE(ABORT,'append-only extraction'); END;
""")
