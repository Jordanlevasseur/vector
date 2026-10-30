"""Independent, private configuration; no switch can disable network enforcement."""
from dataclasses import dataclass
import os
from pathlib import Path
import stat
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
        root.mkdir(parents=True,mode=0o700,exist_ok=True)
        if root.stat().st_uid!=os.getuid() or stat.S_IMODE(root.stat().st_mode)&0o077:
            raise ValueError('Data directory must be owned by this user and private (0700).')
        marker=root/'.vector-data'
        if not marker.exists():
            if any(root.iterdir()):
                raise ValueError('Refusing a nonempty unrelated directory.')
            with marker.open('x') as output: output.write('VECTOR-DATA-1\n')
            marker.chmod(0o600)
        if marker.is_symlink() or marker.read_text()!='VECTOR-DATA-1\n':
            raise ValueError('Invalid VECTOR data marker.')
        return root
