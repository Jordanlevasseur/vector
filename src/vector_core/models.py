"""Verified local Ollama assets, including narrowly validated v2 selector links."""
import hashlib
import json
import os
from pathlib import Path
import re
from vector_core.storage import safe_path,input_file,BLOCK,DIGEST
from vector_core.persistence import declare_external,import_asset,model_manifest
from vector_core.portable import unique


def installed_catalog(roots):
    """Bounded file presence only; never qualification or a SHA substitute."""
    found={}
    for root in roots:
        root=validate_layout(root)
        for path in sorted((root/'manifests').rglob('*')):
            if not path.is_file():continue
            parts=path.relative_to(root/'manifests').parts
            if len(parts)!=4 or parts[:2]!=('registry.ollama.ai','library'):continue
            name=parts[2]+':'+parts[3]
            if not re.fullmatch(r'[A-Za-z0-9_.-]+:[A-Za-z0-9_.-]+',name):continue
            found[name]={'name':name,'installed':True,'runtime_inspected':False,'details':{'family':'not inspected'}}
            if len(found)>256:raise ValueError('Local catalog exceeds256model entries.')
    return list(found.values())


def model_root(transport,name):
    """Resolve an authorized exact identifier to an already mounted local store."""
    roots=getattr(transport,'model_directories',(transport.model_directory,))
    matches=[]
    for root in roots:
        try:files=selected_files(root,name)
        except FileNotFoundError:continue
        matches.append((root,files[0]['sha256']))
    if not matches:raise ValueError('Selected local model is not in an authorized model store.')
    if len({item[1] for item in matches})>1:raise ValueError('Conflicting model manifests across authorized stores.')
    return matches[0][0]


def runtime_files(roots):
    """Verified namespace overlay, including manifest blobs needed by Ollama v2."""
    mounts={}
    def add(relative,item):
        previous=mounts.get(relative)
        if previous and previous['sha256']!=item['sha256']:raise ValueError('Conflicting authorized model store content.')
        mounts[relative]=item
    for root in roots:
        root=validate_layout(root)
        for manifest in sorted((root/'manifests').rglob('*')):
            if not manifest.is_file():continue
            relative=manifest.relative_to(root/'manifests').parts
            if len(relative)!=4 or relative[:2]!=('registry.ollama.ai','library'):raise ValueError('Unsupported local model manifest layout.')
            files=selected_files(root,relative[2]+':'+relative[3])
            for item in files:add(item['relative'],item)
            # The top-level manifest is itself addressed as a blob by v2. Its
            # verified bytes already exist; bind that file under its digest too.
            add('blobs/sha256-'+files[0]['sha256'],files[0])
    return mounts


def managed_catalog(memory):
    """Existing imported assets, not simulated runtime discovery or capability proof."""
    from vector_core.persistence import validate_model
    rows=memory.db.execute("SELECT record_key,payload FROM persistent_records r WHERE contract='models' AND rowid=(SELECT max(rowid) FROM persistent_records WHERE contract='models' AND record_key=r.record_key) ORDER BY rowid DESC LIMIT 100").fetchall()
    result=[]
    for row in rows:
        name=row['record_key'];p=json.loads(row['payload']);validate_model(memory.db,p)
        if not re.fullmatch(r'[A-Za-z0-9_.-]+:[A-Za-z0-9_.-]+',name):continue
        size=0
        for asset in p['assets']:
            descriptor=memory.db.execute('SELECT o.raw_bytes FROM managed_refs r JOIN managed_objects o ON o.digest=r.digest WHERE r.id=?',(asset['asset_id'],)).fetchone();size+=descriptor[0]
        result.append({'name':name,'digest':p['model_version'],'size':size,'managed':True,'runtime_inspected':False,'details':{'family':'not yet inspected'}})
    return result


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
    selector=root/'manifests-v2/ollama.com/library'/model/tag
    if selector.exists():
        target=selector.resolve()
        with input_file(target) as source:raw=source.read(65537)
        if len(raw)>65536:raise ValueError('Model selector metadata too large.')
        result.append({'path':target,'relative':str(selector.relative_to(root)),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)})
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
    from vector_core.persistence import put
    put(memory,'capabilities','model-import:'+name,{'model':name,'files':[{k:str(v) for k,v in item.items()} for item in files],
        'status':'managed assets hash-verified; external obligations resolved','runtime_version':runtime_version})
    for item in files:
        memory.db.execute("DELETE FROM external_dependencies WHERE contract='models' AND path=? AND digest=?",(str(item['path']),item['sha256']))
    return {'manifest_record':record,'assets':len(names),'external_declarations_retained':False}


def materialize(memory,name,directory):
    """Verified managed bytes into a private ephemeral runtime layout."""
    from vector_core.storage import object_chunks,capacity
    from vector_core.intake import write_new_chunks
    from vector_core.persistence import validate_model
    row=memory.db.execute("SELECT payload FROM persistent_records WHERE contract='models' AND record_key=? ORDER BY rowid DESC LIMIT 1",(name,)).fetchone()
    if row is None:raise ValueError('Managed model not found; explicitly import local assets first.')
    payload=json.loads(row[0]);validate_model(memory.db,payload);root=safe_path(directory)
    total=0
    for asset in payload['assets']:
        reference=memory.db.execute('SELECT logical_name,digest FROM managed_refs WHERE id=?',(asset['asset_id'],)).fetchone()
        prefix=name+'/'
        if not reference[0].startswith(prefix):raise ValueError('Managed model layout mismatch.')
        relative=reference[0][len(prefix):]
        if not (re.fullmatch(r'blobs/sha256-[0-9a-f]{64}',relative) or re.fullmatch(r'manifests(?:-v2)?/[A-Za-z0-9_.-]+/library/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+',relative)):
            raise ValueError('Unsafe managed model layout.')
        descriptor=memory.db.execute('SELECT digest,raw_bytes,stored_bytes,codec FROM managed_objects WHERE digest=?',(reference[1],)).fetchone()
        target=safe_path(root/relative);target.parent.mkdir(parents=True,mode=0o700,exist_ok=True)
        capacity(root,descriptor[1])
        if not target.exists():write_new_chunks(target,object_chunks(memory.config.data_dir,descriptor))
        else:
            digest=hashlib.sha256()
            with input_file(target) as source:
                while chunk:=source.read(BLOCK):digest.update(chunk)
            if digest.hexdigest()!=reference[1]:raise ValueError('Runtime materialization differs from managed asset.')
        total+=descriptor[1]
    # Ollama v2 may address the original manifest by its digest. This is bounded
    # metadata copied only into the already private ephemeral runtime, never into
    # the authoritative asset store or a host model installation.
    if re.fullmatch('[0-9a-f]{64}',payload['model_version']):
        model,tag=name.split(':');manifest=root/'manifests/registry.ollama.ai/library'/model/tag
        with input_file(manifest) as source:raw=source.read(65537)
        if len(raw)>65536 or hashlib.sha256(raw).hexdigest()!=payload['model_version']:raise ValueError('Managed runtime manifest differs from the recorded version.')
        target=root/'blobs'/('sha256-'+payload['model_version'])
        if not target.exists():write_new_chunks(target,[raw])
        else:
            with input_file(target) as source:existing=source.read(65537)
            if existing!=raw:raise ValueError('Managed manifest alias differs from verified bytes.')
    return {'model':name,'materialized_bytes':total,'ephemeral':True}
