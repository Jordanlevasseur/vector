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

def backup(db,root):
    parent=root/'backups'
    if parent.is_symlink(): raise ValueError('Backup symbolic links forbidden.')
    parent.mkdir(mode=0o700,exist_ok=True)
    folder=parent/uuid4().hex
    folder.mkdir(mode=0o700)
    path=folder/'archive.sqlite3'
    target=sqlite3.connect(path)
    try: db.backup(target,pages=128)
    finally: target.close()
    path.chmod(0o600)
    sync(path)
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    with (folder/'manifest.json').open('x') as output:
        json.dump({'format':1,'sha256':digest,'database':'archive.sqlite3'},output)
        output.flush();os.fsync(output.fileno())
    sync(folder);sync(parent)
    return {'directory':str(folder),'sha256':digest,'complete':True}
