"""Local bounded logging and consistent, non-overwriting backup foundations."""
import hashlib
import json
import logging
from logging.handlers import RotatingFileHandler
import os
import sqlite3
from uuid import uuid4

def logger(root):
    path=root/'operations.log'
    if path.is_symlink(): raise ValueError('Log symbolic links forbidden.')
    result=logging.getLogger('vector.'+str(root))
    if not result.handlers:
        handler=RotatingFileHandler(path,maxBytes=262144,backupCount=2)
        os.chmod(path,0o600)
        handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
        result.addHandler(handler)
        result.setLevel(logging.INFO)
        result.propagate=False
    return result

def sync(path):
    fd=os.open(path,os.O_RDONLY)
    try: os.fsync(fd)
    finally: os.close(fd)

def backup(db,root,timeout_seconds=120):
    if db.execute("SELECT 1 FROM sqlite_master WHERE name='managed_objects'").fetchone() and db.execute('SELECT 1 FROM managed_objects LIMIT 1').fetchone():
        raise ValueError('Database-only backup cannot include managed assets; use export-vector.')
    parent=root/'backups'
    if parent.is_symlink(): raise ValueError('Backup symbolic links forbidden.')
    parent.mkdir(mode=0o700,exist_ok=True)
    folder=parent/uuid4().hex
    folder.mkdir(mode=0o700)
    path=folder/'archive.sqlite3'
    import time
    if not isinstance(timeout_seconds,(int,float)) or not 0<timeout_seconds<=3600:
        raise ValueError('Backup deadline must be positive and at most one hour.')
    deadline=time.monotonic()+timeout_seconds
    def progress(status,remaining,total):
        if time.monotonic()>deadline:raise TimeoutError('Backup deadline exceeded; incomplete copy not certified.')
    target=sqlite3.connect(path)
    try: db.backup(target,pages=128,progress=progress)
    finally: target.close()
    path.chmod(0o600)
    sync(path)
    digest=file_hash(path)
    with (folder/'manifest.json').open('x') as output:
        json.dump({'format':1,'sha256':digest,'database':'archive.sqlite3'},output)
        output.flush();os.fsync(output.fileno())
    sync(folder);sync(parent)
    return {'directory':str(folder),'sha256':digest,'complete':True,'scope':'legacy-database-only','portable_installation_complete':False}


def file_hash(path):
    digest=hashlib.sha256()
    with path.open('rb') as source:
        while part:=source.read(1024*1024): digest.update(part)
    return digest.hexdigest()


def restore(config,directory):
    from pathlib import Path
    from vector_core.intake import read_file
    from vector_core.database import APPLICATION_ID,MIGRATIONS
    from vector_core.memory import verify_connection
    directory=Path(directory).expanduser().absolute()
    if any(p.is_symlink() for p in (directory,*directory.parents)):
        raise ValueError('Backup symbolic links forbidden.')
    manifest=json.loads(read_file(directory/'manifest.json',16384))
    if set(manifest)!={'format','sha256','database'} or manifest['format']!=1 or manifest['database']!='archive.sqlite3':
        raise ValueError('Unsupported backup manifest.')
    if config.data_dir.exists(): raise FileExistsError('Restore requires a new data directory; existing data preserved.')
    source=directory/'archive.sqlite3'
    if source.is_symlink() or not source.is_file(): raise ValueError('Invalid backup file.')
    root=config.initialize()
    incomplete=root/'.restore-incomplete'
    incomplete.write_text('Restore not yet verified\n');sync(incomplete);sync(root)
    target=root/'vector.sqlite3'
    digest=hashlib.sha256()
    fd=os.open(source,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    import stat
    if not stat.S_ISREG(os.fstat(fd).st_mode):
        os.close(fd)
        raise ValueError("Backup must be a regular file.")
    import shutil
    expected=os.fstat(fd).st_size
    if expected>shutil.disk_usage(root).free-64*1024*1024:
        os.close(fd)
        raise ValueError('Insufficient free space for restore plus safety reserve; destination remains quarantined.')
    with os.fdopen(fd,'rb') as original,target.open('xb') as output:
        copied=0
        for part in iter(lambda: original.read(min(1024*1024,expected+1-copied)),b''):
            copied+=len(part)
            if copied>expected:raise ValueError('Backup changed during copy; destination quarantined.')
            digest.update(part);output.write(part)
        output.flush();os.fsync(output.fileno())
    if copied!=expected:raise ValueError('Backup changed during copy; destination quarantined.')
    target.chmod(0o600)
    if digest.hexdigest()!=manifest['sha256']:
        raise ValueError('Backup checksum mismatch; destination quarantined, not activated.')
    from urllib.parse import quote
    db=sqlite3.connect('file:'+quote(str(target),safe='/')+'?mode=ro',uri=True)
    try:
        db.execute('PRAGMA trusted_schema=OFF')
        if db.execute('PRAGMA application_id').fetchone()[0]!=APPLICATION_ID or not 1<=db.execute('PRAGMA user_version').fetchone()[0]<=len(MIGRATIONS):
            raise ValueError('Backup database version/identity invalid.')
        if db.execute("SELECT 1 FROM sqlite_master WHERE name='managed_objects'").fetchone() and db.execute('SELECT 1 FROM managed_objects LIMIT 1').fetchone():
            raise ValueError('Database-only backup has required external files; use a complete portable export.')
        integrity=verify_connection(db)
        if not integrity['passed']: raise ValueError('Backup contents failed integrity verification.')
    finally: db.close()
    incomplete.unlink();sync(root)
    return {'restored':True,'directory':str(root),'integrity':integrity}
