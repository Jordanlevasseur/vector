"""Offline user-menu integration; existing customized launchers are preserved."""
import argparse
import json
from pathlib import Path
import sys


def launcher_text(executable):
    executable=Path(executable)
    if not executable.is_absolute():raise ValueError('Launcher executable must be absolute.')
    quoted='"'+str(executable).replace('\\','\\\\').replace('"','\\"').replace('`','\\`').replace('$','\\$').replace('%','%%')+'"'
    return f'''[Desktop Entry]
Type=Application
Name=VECTOR
Comment=Offline permanent memory, evidence and deterministic tools
Exec={quoted}
Icon=applications-science
Terminal=false
Categories=Science;Education;
Actions=LocalModels;ManagedModels;OpenData;
X-VECTOR-Launcher=true

[Desktop Action LocalModels]
Name=VECTOR — Local Models
Exec={quoted} --choose-models

[Desktop Action ManagedModels]
Name=VECTOR — Managed Models
Exec={quoted} --managed

[Desktop Action OpenData]
Name=VECTOR — Open Data Folder
Exec={quoted} --choose-data
'''


def install(output=None):
    executable=Path(sys.prefix)/'bin/vector-desktop'
    if not executable.is_file():raise RuntimeError('Install the offline VECTOR wheel into this environment first.')
    destination=Path(output) if output else Path.home()/'.local/share/applications/vector.desktop'
    from vector_core.intake import write_new_file
    text=launcher_text(executable)
    if destination.exists():
        from vector_core.intake import read_file
        if read_file(destination,16384).decode()==text:return {'installed':str(destination),'unchanged':True}
        raise FileExistsError('Existing launcher preserved. Review it before choosing a new output path.')
    destination.parent.mkdir(parents=True,exist_ok=True)
    write_new_file(destination,text.encode());destination.chmod(0o644)
    from vector_core.maintenance import sync
    sync(destination)
    return {'installed':str(destination),'executable':str(executable),'network':False}


def main(argv=None):
    from vector_core.security import activate
    activate()
    parser=argparse.ArgumentParser();parser.add_argument('--output');args=parser.parse_args(argv)
    try:print(json.dumps(install(args.output),indent=2));return 0
    except (ValueError,OSError,RuntimeError) as error:print('VECTOR launcher installation blocked: '+str(error),file=sys.stderr);return 1

if __name__=='__main__':raise SystemExit(main())
