"""Registered portable state contracts; inert manifests, never extension execution."""
from vector_core.coordination import write_operation

import json
import re
from uuid import uuid4
from vector_core.memory import canonical,now


@write_operation
def register(memory,name,description):
    if not isinstance(name,str) or not re.fullmatch(r'[a-z][a-z0-9_-]{0,63}',name):raise ValueError('Invalid contract name.')
    if not isinstance(description,str) or len(description)>4096:raise ValueError('Invalid contract description.')
    memory.db.execute('INSERT INTO persistence_contracts VALUES (?,?,?)',(name,1,description))


def require(memory,contract):
    row=memory.db.execute('SELECT version FROM persistence_contracts WHERE name=?',(contract,)).fetchone()
    if row is None or row[0]!=1:raise ValueError('Unknown/unsupported persistence contract; cannot omit its state.')


def validate_model(db,payload):
    if (not isinstance(payload,dict) or set(payload)!={'model_version','runtime','assets','execution_authorized','offline_runtime_qualified'}
        or payload['execution_authorized'] is not False or payload['offline_runtime_qualified'] is not False
        or not all(isinstance(payload[v],str) and 0<len(payload[v])<=512 for v in ('model_version','runtime'))
        or not isinstance(payload['assets'],list) or not payload['assets']):
        raise ValueError('Invalid inert model manifest.')
    for asset in payload['assets']:
        if (not isinstance(asset,dict) or set(asset)!={'asset_id','sha256'}
            or not all(isinstance(asset[field],str) for field in ('asset_id','sha256'))):
            raise ValueError('Invalid required model asset descriptor.')
        row=db.execute("SELECT digest FROM managed_refs WHERE id=? AND contract='models'",(asset['asset_id'],)).fetchone()
        if row is None or row[0]!=asset['sha256']:
            raise ValueError('Required model asset missing or mismatched.')


@write_operation
def put(memory,contract,key,payload):
    require(memory,contract)
    if not isinstance(key,str) or not 1<=len(key)<=512:raise ValueError('Bounded record key required.')
    if contract=='preferences' and key=='__vector_runtime__':
        if not isinstance(payload,dict) or set(payload)!={'max_source_bytes'} or type(payload['max_source_bytes']) is not int or not 1024<=payload['max_source_bytes']<=16*1024*1024:
            raise ValueError('Unsupported runtime preferences.')
    if contract=='models':validate_model(memory.db,payload)
    encoded=canonical(payload)
    if len(encoded.encode())>1024*1024:raise ValueError('Large payloads belong in streamed managed assets, not metadata records.')
    memory.db.execute('BEGIN IMMEDIATE')
    try:
        previous=memory.db.execute('SELECT id FROM persistent_records WHERE contract=? AND record_key=? ORDER BY rowid DESC LIMIT 1',(contract,key)).fetchone()
        identifier=uuid4().hex
        memory.db.execute('INSERT INTO persistent_records VALUES (?,?,?,?,?,?)',
            (identifier,contract,key,encoded,previous[0] if previous else None,now()))
        memory.db.commit()
    except Exception:memory.db.rollback();raise
    return identifier


def records(memory,contract,*,after=0,limit=100):
    require(memory,contract)
    if type(after) is not int or after<0 or type(limit) is not int or not 1<=limit<=1000:raise ValueError('Invalid page/cursor.')
    rows=memory.db.execute('SELECT rowid AS cursor,* FROM persistent_records WHERE contract=? AND rowid>? ORDER BY rowid LIMIT ?',
                           (contract,after,limit)).fetchall()
    result=[]
    for row in rows:
        item=dict(row);item['payload']=json.loads(item['payload']);result.append(item)
    return {'items':result,'next_cursor':result[-1]['cursor'] if result else after}


@write_operation
def import_asset(memory,contract,name,path,purpose='portable-data',fault=None):
    require(memory,contract)
    if not isinstance(name,str) or not 1<=len(name)<=512:raise ValueError('Asset name required.')
    if purpose not in ('portable-data','model-weight','adapter','extension','capability'):raise ValueError('Unknown asset purpose.')
    from vector_core.storage import import_object
    digest=import_object(memory,path,fault=fault)
    identity=uuid4().hex
    memory.db.execute('INSERT INTO managed_refs VALUES (?,?,?,?,?,?)',(identity,contract,name,digest,purpose,now()))
    return {'asset_id':identity,'digest':digest,'contract':contract,'logical_name':name,'execution_authorized':False}


@write_operation
def declare_external(memory,contract,name,path):
    """Explicitly verified external assets block a self-contained portable export."""
    require(memory,contract)
    from vector_core.storage import input_file,BLOCK
    import hashlib,os
    digest=hashlib.sha256();size=0
    with input_file(path) as source:
        before=os.fstat(source.fileno())
        while chunk:=source.read(BLOCK):digest.update(chunk);size+=len(chunk)
        after=os.fstat(source.fileno())
        if (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):raise ValueError('External asset changed.')
    memory.db.execute('INSERT INTO external_dependencies VALUES (?,?,?,?,?,?,?)',
        (uuid4().hex,contract,name,str(path),digest.hexdigest(),size,now()))


def model_manifest(memory,name,version,runtime,asset_names):
    if not all(isinstance(v,str) and 0<len(v)<=512 for v in (name,version,runtime)):raise ValueError('Model identity/runtime required.')
    if not isinstance(asset_names,list) or not asset_names:raise ValueError('A portable model must declare its managed assets.')
    references=[]
    for logical in asset_names:
        row=memory.db.execute('SELECT id,digest FROM managed_refs WHERE contract=? AND logical_name=? ORDER BY rowid DESC LIMIT 1',('models',logical)).fetchone()
        if row is None:raise ValueError('Required model asset missing: '+str(logical))
        references.append({'asset_id':row[0],'sha256':row[1]})
    return put(memory,'models',name,{'model_version':version,'runtime':runtime,'assets':references,
                                  'execution_authorized':False,'offline_runtime_qualified':False})
