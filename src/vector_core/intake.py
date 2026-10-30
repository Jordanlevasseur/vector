"""Explicitly selected bounded regular files, with no symlink traversal."""
import os
from pathlib import Path
import stat

def read_file(path,maximum):
    path=Path(path).expanduser().absolute()
    if '..' in path.parts:
        raise ValueError('Parent traversal forbidden.')
    descriptors=[]
    try:
        descriptor=os.open('/',os.O_RDONLY|os.O_DIRECTORY)
        descriptors.append(descriptor)
        for component in path.parts[1:-1]:
            descriptor=os.open(component,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=descriptor)
            descriptors.append(descriptor)
        source=os.open(path.name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=descriptor)
        descriptors.append(source)
        before=os.fstat(source)
        if not stat.S_ISREG(before.st_mode) or before.st_size>maximum:
            raise ValueError('Input must be a bounded regular file.')
        chunks,length=[],0
        while length<=maximum:
            part=os.read(source,min(65536,maximum+1-length))
            if not part: break
            chunks.append(part)
            length+=len(part)
        after=os.fstat(source)
        if length>maximum or (before.st_size,before.st_mtime_ns,before.st_ctime_ns)!=(after.st_size,after.st_mtime_ns,after.st_ctime_ns):
            raise ValueError('Input changed or oversized; not committed.')
        return b''.join(chunks)
    finally:
        for descriptor in reversed(descriptors): os.close(descriptor)


def write_new_file(path,content):
    """Explicit byte export only, never replacing files or touching HELIX/code."""
    path=Path(path).expanduser().absolute()
    protected=(Path('/home/mint/VECTOR/helix'),Path(__file__).resolve().parents[2])
    if any(path.is_relative_to(p) for p in protected) or '..' in path.parts:
        raise ValueError('Export target cannot be application source or HELIX.')
    descriptors=[]
    try:
        parent=os.open('/',os.O_RDONLY|os.O_DIRECTORY);descriptors.append(parent)
        for component in path.parts[1:-1]:
            parent=os.open(component,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=parent)
            descriptors.append(parent)
        fd=os.open(path.name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600,dir_fd=parent)
        with os.fdopen(fd,'wb') as output:
            output.write(content);output.flush();os.fsync(output.fileno())
        os.fsync(parent)
    finally:
        for fd in reversed(descriptors):os.close(fd)


def write_new_chunks(path,chunks):
    """Publish a new explicit export only after the whole original verifies."""
    from uuid import uuid4
    path=Path(path).expanduser().absolute()
    protected=(Path('/home/mint/VECTOR/helix'),Path(__file__).resolve().parents[2])
    if any(path.is_relative_to(p) for p in protected) or '..' in path.parts:raise ValueError('Protected export target.')
    descriptors=[];temporary='.vector-export-'+uuid4().hex
    try:
        parent=os.open('/',os.O_RDONLY|os.O_DIRECTORY);descriptors.append(parent)
        for component in path.parts[1:-1]:
            parent=os.open(component,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=parent);descriptors.append(parent)
        fd=os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600,dir_fd=parent)
        try:
            with os.fdopen(fd,'wb') as output:
                for chunk in chunks:output.write(chunk)
                output.flush();os.fsync(output.fileno())
            os.link(temporary,path.name,src_dir_fd=parent,dst_dir_fd=parent,follow_symlinks=False)
            os.fsync(parent)
        finally:
            os.unlink(temporary,dir_fd=parent);os.fsync(parent)
    finally:
        for fd in reversed(descriptors):os.close(fd)
