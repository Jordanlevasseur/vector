"""Independent, private configuration; no switch can disable network enforcement."""
from dataclasses import dataclass
import os
from pathlib import Path
import stat
import grp
import pwd
import tomllib

@dataclass(frozen=True)
class Config:
    data_dir: Path
    max_source_bytes: int=8*1024*1024

    @classmethod
    def load(cls,path=None,data_dir=None):
        values={}
        if path:
            from vector_core.intake import read_file
            values=tomllib.loads(read_file(path,16384).decode('utf-8'))
            if set(values)-{'data_dir','max_source_bytes'}:
                raise ValueError('Unknown configuration option.')
        root=Path(data_dir or values.get('data_dir') or Path.home()/'.local/share/vector').expanduser()
        if not root.is_absolute() or any(p.is_symlink() for p in (root,*root.parents)):
            raise ValueError('Data path must be absolute without symbolic links.')
        root=root.resolve()
        for ancestor in root.parents:
            if not ancestor.exists():continue
            info=ancestor.stat()
            if info.st_uid not in (0,os.getuid()):
                raise ValueError('Data ancestors must be owned by this user or root.')
            if info.st_uid==0 and info.st_mode&stat.S_ISVTX:continue
            if info.st_mode&stat.S_IWOTH:
                raise ValueError('Data ancestors cannot be world-writable without root sticky protection.')
            if info.st_mode&stat.S_IWGRP:
                members={entry.pw_name for entry in pwd.getpwall() if entry.pw_gid==info.st_gid}
                members.update(grp.getgrgid(info.st_gid).gr_mem)
                if any(pwd.getpwnam(member).pw_uid not in (0,os.getuid()) for member in members):
                    raise ValueError('Data ancestors grant write access to another account.')
        for protected in (Path('/home/mint/VECTOR/helix'),Path(__file__).resolve().parents[2]):
            if root.is_relative_to(protected) or protected.is_relative_to(root):
                raise ValueError('Data must be independent of HELIX and application source.')
        maximum=values.get('max_source_bytes',8*1024*1024)
        if type(maximum) is not int or not 1024<=maximum<=16*1024*1024:
            raise ValueError('Source limit must be 1 KiB through 16 MiB.')
        return cls(root,maximum)

    def initialize(self):
        root=self.data_dir
        if Config.load(data_dir=str(root)).data_dir!=root:
            raise ValueError("Data path must be canonical.")
        if type(self.max_source_bytes) is not int or not 1024<=self.max_source_bytes<=16*1024*1024:
            raise ValueError("Invalid source byte limit.")
        if any(p.is_symlink() for p in (root,*root.parents)):
            raise ValueError('Data symbolic links forbidden.')
        if (root/".restore-incomplete").exists():
            raise ValueError("Incomplete restore is quarantined; originals were not overwritten.")
        missing=[]
        current=root
        while not current.exists():
            missing.append(current)
            current=current.parent
        root.mkdir(parents=True,mode=0o700,exist_ok=True)
        for created in missing:
            for directory in (created,created.parent):
                descriptor=os.open(directory,os.O_RDONLY|os.O_DIRECTORY)
                try:os.fsync(descriptor)
                finally:os.close(descriptor)
        if root.stat().st_uid!=os.getuid() or stat.S_IMODE(root.stat().st_mode)&0o077:
            raise ValueError('Data directory must be owned by this user and private (0700).')
        marker=root/'.vector-data'
        if not marker.exists():
            if any(root.iterdir()):
                raise ValueError('Refusing a nonempty unrelated directory.')
            descriptor=os.open(marker,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
            with os.fdopen(descriptor,'w') as output:
                output.write('VECTOR-DATA-1\n');output.flush();os.fsync(output.fileno())
        if marker.is_symlink() or marker.read_text()!='VECTOR-DATA-1\n':
            raise ValueError('Invalid VECTOR data marker.')
        for durable in (marker,root):
            descriptor=os.open(durable,os.O_RDONLY|os.O_NOFOLLOW)
            try:os.fsync(descriptor)
            finally:os.close(descriptor)
        return root
