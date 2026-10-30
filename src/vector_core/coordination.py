"""Cooperative durable writer serialization for safe volume relocation."""
from contextlib import contextmanager
from functools import wraps
import fcntl
import os
from pathlib import Path

@contextmanager
def writer(memory):
    depth=getattr(memory,'_writer_depth',0)
    if depth:
        memory._writer_depth=depth+1
        try:yield
        finally:memory._writer_depth-=1
        return
    root=memory.config.data_dir
    descriptor=os.open(root/'.writer.lock',os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW,0o600)
    try:
        fcntl.flock(descriptor,fcntl.LOCK_EX)
        if (root/'.location.json').exists():raise ValueError('Data relocated; reopen VECTOR using its current location.')
        memory._writer_depth=1
        try:yield
        finally:memory._writer_depth=0
    finally:
        fcntl.flock(descriptor,fcntl.LOCK_UN);os.close(descriptor)


def write_operation(function):
    @wraps(function)
    def wrapped(owner,*args,**kwargs):
        memory=getattr(owner,'memory',owner)
        with writer(memory):return function(owner,*args,**kwargs)
    return wrapped


def move_data(memory,destination,*,deadline_seconds=900):
    """Verified copy plus durable redirection. Originals at the old volume remain."""
    from vector_core.config import Config
    from vector_core.portable import export_vector,restore_vector
    from vector_core.storage import atomic_json,safe_path
    from vector_core.maintenance import sync
    import tempfile
    target=Config.load(data_dir=str(destination)).data_dir
    source=memory.config.data_dir
    if target.exists():raise FileExistsError('Move destination must be new; existing data is preserved.')
    if target.is_relative_to(source) or source.is_relative_to(target):raise ValueError('Move requires an independent directory.')
    with writer(memory):
        # Temporary repository is reproducible; neither installation is deleted.
        with tempfile.TemporaryDirectory(prefix='vector_move_') as directory:
            repository=Path(directory)/'portable'
            exported=export_vector(memory,repository,deadline_seconds=deadline_seconds)
            restored=restore_vector(Config.load(data_dir=str(target)),repository,deadline_seconds=deadline_seconds)
        atomic_json(source/'.location.json',{'format':1,'target':str(target)})
        sync(source)
    return {'moved':True,'directory':str(target),'previous_directory':str(source),
            'old_originals_retained':True,'snapshot_id':exported['snapshot_id'],'integrity':restored['integrity']}
