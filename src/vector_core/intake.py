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
