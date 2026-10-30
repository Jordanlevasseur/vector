"""Verified local Ollama assets, including narrowly validated v2 selector links."""
import hashlib
import json
import os
from pathlib import Path
import re
from vector_core.storage import safe_path,input_file,BLOCK,DIGEST
from vector_core.persistence import declare_external,import_asset,model_manifest
from vector_core.portable import unique


def validate_layout(root):
    root=safe_path(root)
    if not all((root/name).is_dir() for name in ('blobs','manifests')):raise ValueError('Model directory needs blobs and manifests.')
    for path in root.rglob('*'):
        if not path.is_symlink():continue
        # Ollama v2 uses selector links to small manifest blobs, not arbitrary paths.
        if not path.relative_to(root).parts[0]=='manifests-v2':raise ValueError('Unexpected model symlink.')
        target=path.resolve();safe_path(target)
        if target.parent!=root/'blobs' or not re.fullmatch(r'sha256-[0-9a-f]{64}',target.name):raise ValueError('Model selector escapes verified blob storage.')
        if target.stat().st_size>65536:raise ValueError('Model selector must point to bounded manifest metadata.')
        with input_file(target) as source:body=source.read(65537)
        if hashlib.sha256(body).hexdigest()!=target.name[7:]:raise ValueError('Model selector digest mismatch.')
    return root


def selected_files(root,name):
    root=validate_layout(root)
    if not isinstance(name,str) or not re.fullmatch(r'[A-Za-z0-9_.-]+:[A-Za-z0-9_.-]+',name):raise ValueError('This adapter supports explicit library model:tag names.')
    model,tag=name.split(':');manifest=root/'manifests/registry.ollama.ai/library'/model/tag
    with input_file(manifest) as source:body=source.read(65537)
    if len(body)>65536:raise ValueError('Model manifest too large.')
    result=[{'path':manifest,'relative':str(manifest.relative_to(root)),'sha256':hashlib.sha256(body).hexdigest(),'bytes':len(body)}]
    pending=[json.loads(body,object_pairs_hook=unique)];visited=set()
    while pending:
        metadata=pending.pop()
        if not isinstance(metadata,dict) or not isinstance(metadata.get('config'),dict) or not isinstance(metadata.get('layers'),list):raise ValueError('Unsupported model dependency manifest.')
        for item in [metadata['config'],*metadata['layers']]:
            digest=item.get('digest','');size=item.get('size')
            if not isinstance(digest,str) or not re.fullmatch(r'sha256:[0-9a-f]{64}',digest) or type(size) is not int or size<0:raise ValueError('Malformed model dependency.')
            if digest in visited:continue
            visited.add(digest)
            if len(visited)>4096:raise ValueError('Model dependency budget exceeded.')
            path=root/'blobs'/digest.replace(':','-');hasher=hashlib.sha256();length=0
            with input_file(path) as source:
                before=os.fstat(source.fileno())
                while chunk:=source.read(BLOCK):hasher.update(chunk);length+=len(chunk)
                after=os.fstat(source.fileno())
            if length!=size or hasher.hexdigest()!=digest[7:] or (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):raise ValueError('Model dependency missing, changed or corrupt.')
            result.append({'path':path,'relative':str(path.relative_to(root)),'sha256':digest[7:],'bytes':length})
            if item.get('mediaType')=='application/vnd.docker.distribution.manifest.v2+json':
                if size>65536:raise ValueError('Nested model manifest too large.')
                with input_file(path) as source:pending.append(json.loads(source.read(65537),object_pairs_hook=unique))
    return result


def register_external(memory,root,name):
    files=selected_files(root,name)
    for item in files:
        if memory.db.execute("SELECT 1 FROM external_dependencies WHERE contract='models' AND path=? AND digest=?",(str(item['path']),item['sha256'])).fetchone() is None:
            declare_external(memory,'models',name+':'+item['relative'],item['path'])
    return {'model':name,'external':True,'required_files':len(files),'self_contained_export':False,
            'reason':'Selected local weights are outside VECTOR. Explicitly import managed assets for complete portability.'}


def import_model(memory,root,name,runtime_version):
    files=selected_files(root,name);names=[]
    for item in files:
        logical=name+'/'+item['relative']
        import_asset(memory,'models',logical,item['path'],'model-weight' if item['relative'].startswith('blobs/') else 'portable-data')
        names.append(logical)
    record=model_manifest(memory,name,files[0]['sha256'],'ollama '+runtime_version,names)
    # External declarations are retained historical dependencies; explicit promotion is not automatic.
    return {'manifest_record':record,'assets':len(names),'external_declarations_retained':True}
