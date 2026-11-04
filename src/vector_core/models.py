"""Verified local Ollama assets, including narrowly validated v2 selector links."""
import hashlib
import json
import os
from pathlib import Path
import re
from vector_core.storage import safe_path,input_file,BLOCK,DIGEST
from vector_core.persistence import declare_external,import_asset,model_manifest
from vector_core.portable import unique

def manifest_identifier(parts):
    if len(parts)!=4 or any(not re.fullmatch(r'[A-Za-z0-9_.-]+',p) or '..' in p or p=='.' for p in parts):raise ValueError('Unsupported local manifest identity.')
    registry,namespace,model,tag=parts
    prefix='' if registry=='registry.ollama.ai' else registry+'/'
    if namespace!='library':prefix+=namespace+'/'
    return prefix+model+':'+tag

def manifest_relative(name):
    if not isinstance(name,str) or len(name)>200 or ':' not in name:raise ValueError('Explicit local model:tag identity required.')
    model,tag=name.rsplit(':',1);parts=model.split('/')
    if len(parts)==1:parts=['registry.ollama.ai','library',parts[0]]
    elif len(parts)==2:parts=['registry.ollama.ai',*parts]
    elif len(parts)!=3:raise ValueError('Unsupported local model namespace.')
    parts=(*parts,tag)
    if manifest_identifier(parts)!=name:raise ValueError('Noncanonical local model identifier.')
    return Path('manifests').joinpath(*parts)

def gguf_metadata(path):
    """Bounded scalar metadata only. Vocabulary/tensors are never loaded into RAM."""
    import struct,time
    result={};end=time.monotonic()+5;maximum=32*1024*1024;read_bytes=0
    with input_file(path) as f:
        size=os.fstat(f.fileno()).st_size
        def take(n):
            nonlocal read_bytes
            if n<0 or n>1024*1024 or read_bytes+n>4*1024*1024 or f.tell()+n>min(size,maximum) or time.monotonic()>end:raise ValueError('Bounded GGUF metadata budget reached.')
            raw=f.read(n);read_bytes+=n
            if len(raw)!=n:raise ValueError('Incomplete GGUF metadata.')
            return raw
        def integer():return struct.unpack('<Q',take(8))[0]
        def string(skip=False):
            n=integer()
            if n>1024*1024 or f.tell()+n>min(size,maximum):raise ValueError('GGUF metadata string exceeds bounds.')
            if skip:f.seek(n,1);return None
            return take(n).decode('utf-8')
        scalar={0:('B',1),1:('b',1),2:('H',2),3:('h',2),4:('I',4),5:('i',4),6:('f',4),7:('?',1),10:('Q',8),11:('q',8),12:('d',8)}
        def value(kind,skip=False):
            if kind in scalar:
                code,n=scalar[kind];raw=take(n);return None if skip else struct.unpack('<'+code,raw)[0]
            if kind==8:return string(skip)
            if kind==9:
                item=struct.unpack('<I',take(4))[0];count=integer()
                if count>1000000 or item==9:raise ValueError('GGUF array exceeds metadata bounds.')
                if item in scalar:
                    n=scalar[item][1]*count
                    if f.tell()+n>min(size,maximum):raise ValueError('GGUF array outside metadata bound.')
                    f.seek(n,1)
                elif item==8:
                    for _ in range(count):string(True)
                else:raise ValueError('Unknown GGUF array type.')
                return None
            raise ValueError('Unknown GGUF metadata type.')
        if take(4)!=b'GGUF':raise ValueError('Model payload is not GGUF.')
        version=struct.unpack('<I',take(4))[0]
        if version not in (2,3):raise ValueError('GGUF version is not supported by this metadata reader.')
        result['gguf.version']=version;tensors=integer();count=integer()
        if count>4096:raise ValueError('GGUF metadata entry budget exceeded.')
        result['gguf.tensor_count']=tensors
        for _ in range(count):
            key=string();kind=struct.unpack('<I',take(4))[0]
            keep=kind!=9 and len(key)<=128 and (key in {'general.architecture','general.name','general.file_type','general.parameter_count'} or key.endswith(('.context_length','.block_count','.embedding_length','.attention.head_count','.attention.head_count_kv')))
            item=value(kind,not keep)
            if keep:
                import math
                if isinstance(item,str) and len(item)>1024 or isinstance(item,float) and not math.isfinite(item):raise ValueError('Invalid bounded GGUF scalar metadata.')
                result[key]=item
            arch=result.get('general.architecture')
            if arch and all(arch+s in result for s in ('.context_length','.block_count','.embedding_length','.attention.head_count','.attention.head_count_kv')):break
    return result

def local_inventory(roots):
    """Presence + small verified metadata. Full weight SHA remains a launch gate."""
    found={}
    for raw_root in roots:
        try:root=validate_layout(raw_root)
        except (OSError,ValueError) as error:
            found['root:'+str(raw_root)]={'name':'Unavailable model store','root':str(raw_root),'installed':False,'compatible':False,'unavailable_reason':str(error)};continue
        for path in sorted((root/'manifests').rglob('*')):
            if not path.is_file():continue
            try:name=manifest_identifier(path.relative_to(root/'manifests').parts)
            except ValueError as error:
                found['unsupported:'+str(path)]={'name':'Unsupported manifest: '+str(path.relative_to(root/'manifests')),'root':str(root),'installed':True,'compatible':False,'unavailable_reason':str(error)}
                if len(found)>256:raise ValueError('Local model catalogue exceeds256entries.')
                continue
            item={'name':name,'root':str(root),'installed':True,'runtime_inspected':False,'compatible':None,'availability':'present; full weight integrity and runtime support not yet qualified','tool_calling':None,'capabilities':[]}
            try:
                with input_file(path) as f:raw=f.read(65537)
                if len(raw)>65536:raise ValueError('Model manifest exceeds64KiB.')
                manifest=json.loads(raw,object_pairs_hook=unique)
                if not isinstance(manifest,dict) or not isinstance(manifest.get('config'),dict) or not isinstance(manifest.get('layers'),list) or len(manifest['layers'])>4096:raise ValueError('Malformed bounded model manifest.')
                item['digest']=hashlib.sha256(raw).hexdigest();item['source_manifest_sha256']=item['digest']
                registry,namespace,model,tag=manifest_relative(name).parts[1:]
                selector=root/'manifests-v2'/('ollama.com' if registry=='registry.ollama.ai' else registry)/namespace/model/tag
                if selector.exists():
                    with input_file(selector.resolve()) as f:selector_raw=f.read(65537)
                    selector_digest=hashlib.sha256(selector_raw).hexdigest()
                    linked={layer.get('digest') for layer in manifest['layers'] if isinstance(layer,dict) and layer.get('mediaType')=='application/vnd.docker.distribution.manifest.v2+json'}
                    if len(selector_raw)>65536 or selector_digest!=item['digest'] and 'sha256:'+selector_digest not in linked:raise ValueError('V2 selector is not linked to the verified source manifest.')
                    item['digest']=selector_digest;item['selector_sha256']=selector_digest
                config=manifest['config'];digest=config['digest'];length=config['size']
                if not re.fullmatch('sha256:[0-9a-f]{64}',digest) or type(length) is not int or not 0<=length<=65536:raise ValueError('Invalid local configuration descriptor.')
                with input_file(root/'blobs'/digest.replace(':','-')) as f:raw_config=f.read(65537)
                if len(raw_config)!=length or hashlib.sha256(raw_config).hexdigest()!=digest[7:]:raise ValueError('Local model configuration integrity failed.')
                cfg=json.loads(raw_config,object_pairs_hook=unique)
                if not isinstance(cfg,dict):raise ValueError('Local model configuration must be an object.')
                for field in ('model_format','model_family','model_type','file_type'):
                    if field in cfg and (not isinstance(cfg[field],str) or len(cfg[field])>128):raise ValueError('Invalid bounded model configuration field: '+field)
                families=cfg.get('model_families',[])
                if not isinstance(families,list) or len(families)>32 or any(not isinstance(v,str) or len(v)>128 for v in families):raise ValueError('Invalid bounded model families.')
                weights=[];size=0
                for layer in manifest['layers']:
                    if not isinstance(layer,dict):raise ValueError('Invalid model layer object.')
                    d=layer.get('digest','');n=layer.get('size')
                    if not re.fullmatch('sha256:[0-9a-f]{64}',d) or type(n) is not int or n<0:raise ValueError('Invalid model layer descriptor.')
                    source=root/'blobs'/d.replace(':','-')
                    if source.is_symlink() or not source.is_file() or source.stat().st_size!=n:raise ValueError('Model layer missing or changed size.')
                    size+=n
                    if layer.get('mediaType')=='application/vnd.ollama.image.model':weights.append(source)
                item.update(size=size,weight_bytes=sum(p.stat().st_size for p in weights),format=cfg.get('model_format'),architecture=cfg.get('model_family'),quantization=cfg.get('file_type'),details={'family':cfg.get('model_family','unknown'),'families':cfg.get('model_families',[]),'parameter_size':cfg.get('model_type'),'quantization_level':cfg.get('file_type'),'format':cfg.get('model_format')})
                parameter=re.fullmatch(r'([0-9]{1,12}(?:\.[0-9]{1,6})?)([KMBT])',str(cfg.get('model_type','')).upper())
                item['parameter_count']=int(float(parameter[1])*{'K':1e3,'M':1e6,'B':1e9,'T':1e12}[parameter[2]]) if parameter else None
                if len(weights)!=1 or cfg.get('model_format')!='gguf':raise ValueError('This local adapter needs one GGUF model layer; unsupported packages remain listed.')
                info=gguf_metadata(weights[0]);item['model_info']=info;arch=info.get('general.architecture',item['architecture']);item['architecture']=arch;item['context_length']=info.get(str(arch)+'.context_length');item['gguf_version']=info['gguf.version'];item['weight_file']=str(weights[0])
            except (OSError,ValueError,KeyError,TypeError,RecursionError,OverflowError) as error:item.update(compatible=False,unavailable_reason=type(error).__name__+': '+str(error),availability='unavailable; no model execution attempted')
            if name in found and found[name].get('digest')!=item.get('digest'):item.update(compatible=False,unavailable_reason='Conflicting exact model identity across approved stores.')
            elif name in found:continue
            found[name]=item
            if len(found)>256:raise ValueError('Local model catalogue exceeds256entries.')
    return list(found.values())


def installed_catalog(roots):
    """Bounded file presence only; never qualification or a SHA substitute."""
    return local_inventory(roots)


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


def runtime_files(roots,names=None):
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
            name=manifest_identifier(relative)
            if names is not None and name not in names:continue
            files=selected_files(root,name)
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
        try:manifest_relative(name)
        except ValueError:continue
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
    relative=manifest_relative(name);registry,namespace,model,tag=relative.parts[1:];manifest=root/relative
    with input_file(manifest) as source:body=source.read(65537)
    if len(body)>65536:raise ValueError('Model manifest too large.')
    result=[{'path':manifest,'relative':str(manifest.relative_to(root)),'sha256':hashlib.sha256(body).hexdigest(),'bytes':len(body)}]
    pending=[json.loads(body,object_pairs_hook=unique)];visited=set();verified_manifests=set();verified_sizes={}
    while pending:
        metadata=pending.pop()
        if not isinstance(metadata,dict) or not isinstance(metadata.get('config'),dict) or not isinstance(metadata.get('layers'),list):raise ValueError('Unsupported model dependency manifest.')
        for item in [metadata['config'],*metadata['layers']]:
            if not isinstance(item,dict):raise ValueError('Malformed model layer.')
            digest=item.get('digest','');size=item.get('size')
            if not isinstance(digest,str) or not re.fullmatch(r'sha256:[0-9a-f]{64}',digest) or type(size) is not int or size<0:raise ValueError('Malformed model dependency.')
            nested=item.get('mediaType')=='application/vnd.docker.distribution.manifest.v2+json'
            if digest in visited:
                if verified_sizes[digest]!=size:raise ValueError('Conflicting dependency sizes.')
                if nested and digest not in verified_manifests:
                    if size>65536:raise ValueError('Nested model manifest too large.')
                    with input_file(root/'blobs'/digest.replace(':','-')) as source:pending.append(json.loads(source.read(65537),object_pairs_hook=unique))
                    verified_manifests.add(digest)
                continue
            visited.add(digest)
            if len(visited)>4096:raise ValueError('Model dependency budget exceeded.')
            path=root/'blobs'/digest.replace(':','-');hasher=hashlib.sha256();length=0
            with input_file(path) as source:
                before=os.fstat(source.fileno())
                while chunk:=source.read(BLOCK):hasher.update(chunk);length+=len(chunk)
                after=os.fstat(source.fileno())
            if length!=size or hasher.hexdigest()!=digest[7:] or (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):raise ValueError('Model dependency missing, changed or corrupt.')
            verified_sizes[digest]=length
            result.append({'path':path,'relative':str(path.relative_to(root)),'sha256':digest[7:],'bytes':length})
            if nested:
                verified_manifests.add(digest)
                if size>65536:raise ValueError('Nested model manifest too large.')
                with input_file(path) as source:pending.append(json.loads(source.read(65537),object_pairs_hook=unique))
    selector=root/'manifests-v2'/('ollama.com' if registry=='registry.ollama.ai' else registry)/namespace/model/tag
    if selector.exists():
        target=selector.resolve()
        with input_file(target) as source:raw=source.read(65537)
        if len(raw)>65536:raise ValueError('Model selector metadata too large.')
        if hashlib.sha256(raw).hexdigest()!=result[0]['sha256'] and 'sha256:'+hashlib.sha256(raw).hexdigest() not in verified_manifests:raise ValueError('Model selector is not linked to the verified dependency graph.')
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
        if not (re.fullmatch(r'blobs/sha256-[0-9a-f]{64}',relative) or re.fullmatch(r'manifests(?:-v2)?/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+',relative)):
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
        manifest=root/manifest_relative(name)
        with input_file(manifest) as source:raw=source.read(65537)
        if len(raw)>65536 or hashlib.sha256(raw).hexdigest()!=payload['model_version']:raise ValueError('Managed runtime manifest differs from the recorded version.')
        target=root/'blobs'/('sha256-'+payload['model_version'])
        if not target.exists():write_new_chunks(target,[raw])
        else:
            with input_file(target) as source:existing=source.read(65537)
            if existing!=raw:raise ValueError('Managed manifest alias differs from verified bytes.')
    return {'model':name,'materialized_bytes':total,'ephemeral':True}
