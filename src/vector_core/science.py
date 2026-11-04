"""Reviewed offline publications and restartable, original-linked text pages.

No downloader, extractor process, second database, fact promotion or model calls.
Original containers and rights evidence precede separately attributed derivatives.
"""
import hashlib,json,re,time
from pathlib import Path
from vector_core.coordination import write_operation
from vector_core.intake import read_file
from vector_core.memory import canonical,now
from vector_core.persistence import register
from vector_core.portable import unique
from vector_core.projects import append,identity,latest,page,text
from vector_core.storage import DIGEST,safe_path

CONTRACTS={'scientific_editions','scientific_runs'}
LICENSES={'CC0-1.0','CC-BY-4.0','CC-BY-SA-4.0','CC-BY-3.0','CC-BY-SA-3.0','US-GOV-PUBLIC-DOMAIN','US-PUBLIC-DOMAIN','GFDL-1.2-no-invariants','GFDL-1.3-no-invariants','MIT'}
USES={'preservation','text-indexing','source-linked-retrieval'}
FEATURES={'equations','tables','figures','external_assets','text_completeness'}

def checksum(value):
    if not isinstance(value,str) or not DIGEST.fullmatch(value):raise ValueError('Invalid scientific content checksum.')
    return value

def descriptor(p):
    if not isinstance(p,dict) or set(p)!={'sha256','bytes','media_type'}:raise ValueError('Explicit scientific object descriptor required.')
    checksum(p['sha256']);text(p['media_type'],128)
    if type(p['bytes']) is not int or p['bytes']<1:raise ValueError('Nonempty original/evidence object required.')

def metadata(p):
    fields={'provider_id','title','authors','language','edition','publication_date','revision_date','subjects','source_url','download_url','acquired','original','evidence','rights','medical','extraction_sha256'}
    if not isinstance(p,dict) or set(p)!=fields:raise ValueError('Unknown or missing scientific metadata fields.')
    for k in ('provider_id','title','edition','source_url','download_url','acquired'):text(p[k],2000)
    for k in ('source_url','download_url'):
        if not p[k].startswith(('https://','urn:')):raise ValueError('Explicit source URL required; it is never fetched by VECTOR.')
    if not isinstance(p['language'],str) or not re.fullmatch('[A-Za-z][A-Za-z0-9-]{0,63}',p['language']):raise ValueError('Invalid scientific language.')
    for k in ('authors','subjects'):
        if not isinstance(p[k],list) or not 1<=len(p[k])<=50:raise ValueError('Scientific attribution and subject areas required.')
        for value in p[k]:text(value,500)
    for k in ('publication_date','revision_date'):
        if p[k] is not None and (not isinstance(p[k],str) or not re.fullmatch(r'\d{4}(?:-\d{2}(?:-\d{2})?)?',p[k])):raise ValueError('Publication dates must be explicit ISO dates or null.')
    descriptor(p['original']);checksum(p['extraction_sha256'])
    if not isinstance(p['evidence'],list) or not 1<=len(p['evidence'])<=8:raise ValueError('Source-specific rights evidence required.')
    for evidence in p['evidence']:descriptor(evidence)
    r=p['rights']
    if not isinstance(r,dict) or set(r)!={'license','jurisdiction','basis','attribution','restrictions','reviewed_uses','future_training','ai_retrieval_permitted'}:raise ValueError('Explicit rights review required.')
    if r['license'] not in LICENSES or r['jurisdiction']!='US' or r['ai_retrieval_permitted'] is not True:raise PermissionError('Uncleared, noncommercial or AI-restricted sources are not eligible for this pilot.')
    if not isinstance(r['reviewed_uses'],list) or set(r['reviewed_uses'])!=USES or len(r['reviewed_uses'])!=len(USES):raise PermissionError('All pilot uses must be explicitly reviewed.')
    for k in ('basis','attribution'):text(r[k],4000)
    if not isinstance(r['restrictions'],list) or len(r['restrictions'])>20:raise ValueError('Explicit bounded license exceptions required.')
    for restriction in r['restrictions']:text(restriction,1000)
    if r['future_training']!='requires-separate-review':raise ValueError('This acquisition does not authorize future model training.')
    m=p['medical']
    if not isinstance(m,dict) or set(m)!={'is_medical','temporal_status'} or type(m['is_medical']) is not bool:raise ValueError('Medical temporal metadata required.')
    if m['temporal_status'] not in ({'historical','dated-reference-not-current-guidance'} if m['is_medical'] else {'not-medical'}):raise ValueError('Medical sources cannot silently become current guidance.')
    if m['is_medical'] and p['publication_date'] is None:raise ValueError('Medical publication date required.')
    if len(canonical(p).encode())>24576:raise ValueError('Scientific metadata exceeds record budget.')
    return p

def key_for(entry):return hashlib.sha256(canonical([entry['provider_id'],entry['original']['sha256']]).encode()).hexdigest()[:32]

def json_object(root,digest,maximum=2*1024*1024):
    checksum(digest);raw=read_file(root/'objects'/digest,maximum)
    if hashlib.sha256(raw).hexdigest()!=digest:raise ValueError('Scientific manifest/evidence checksum mismatch.')
    return json.loads(raw,object_pairs_hook=unique,parse_constant=lambda v:(_ for _ in ()).throw(ValueError(v)))

def extraction_spec(root,entry):
    p=json_object(root,entry['extraction_sha256'])
    if not isinstance(p,dict) or set(p)!={'format','original_sha256','method','pages','features'} or p['format']!='vector-scientific-text-v1' or p['original_sha256']!=entry['original']['sha256']:raise ValueError('Extraction must identify the exact original.')
    text(p['method'],200)
    if not isinstance(p['features'],dict) or set(p['features'])!=FEATURES:raise ValueError('Extraction limitations must be explicit.')
    for value in p['features'].values():text(value,2000)
    if not isinstance(p['pages'],list) or len(p['pages'])>10000:raise ValueError('Invalid bounded extraction manifest; split larger extraction jobs explicitly.')
    for index,spec in enumerate(p['pages'],1):
        if not isinstance(spec,dict) or set(spec)!={'page','sha256','bytes','locator'} or spec['page']!=index or type(spec['page']) is not int:raise ValueError('Missing/reordered extraction page.')
        checksum(spec['sha256']);text(spec['locator'],1000)
        if type(spec['bytes']) is not int or not 0<=spec['bytes']<=512*1024:raise ValueError('Page extraction exceeds memory budget; preserve and flag rather than truncate.')
    return p

def read_pack(root):
    root=safe_path(root);raw=read_file(root/'manifest.ndjson',4*1024*1024)
    lines=raw.splitlines()
    if not lines or len(lines)>1001 or any(len(line)>32768 for line in lines):raise ValueError('Bounded, complete scientific manifest required.')
    decoded=[json.loads(line,object_pairs_hook=unique,parse_constant=lambda v:(_ for _ in ()).throw(ValueError(v))) for line in lines]
    if decoded[0]!={'format':'vector-scientific-pack-v1','jurisdiction':'US'}:raise ValueError('Unknown scientific package format/jurisdiction.')
    for entry in decoded[1:]:metadata(entry)
    return decoded[1:],hashlib.sha256(raw).hexdigest()

def validate_record(db,contract,key,p):
    if not isinstance(p,dict):raise ValueError('Invalid scientific record.')
    def event(event_id,digest=None):
        identity(event_id);row=db.execute('SELECT sha256 FROM events WHERE id=?',(event_id,)).fetchone()
        if row is None or (digest is not None and row[0]!=digest):raise ValueError('Missing or mismatched scientific original/evidence.')
    if contract=='scientific_editions':
        if set(p)!={'id','original_event_id','evidence_event_ids','extraction_event_id','extraction','metadata','created'} or identity(p['id'])!=key:raise ValueError('Invalid scientific edition fields.')
        metadata(p['metadata'])
        if key_for(p['metadata'])!=key:raise ValueError('Scientific identity/source mismatch.')
        event(p['original_event_id'],p['metadata']['original']['sha256']);event(p['extraction_event_id'],p['metadata']['extraction_sha256'])
        if not isinstance(p['evidence_event_ids'],list) or len(p['evidence_event_ids'])!=len(p['metadata']['evidence']):raise ValueError('Incomplete rights evidence references.')
        for e,d in zip(p['evidence_event_ids'],p['metadata']['evidence']):event(e,d['sha256'])
        x=p['extraction']
        if not isinstance(x,dict) or set(x)!={'total_pages','method','features'} or type(x['total_pages']) is not int or not 0<=x['total_pages']<=10000 or not isinstance(x['features'],dict) or set(x['features'])!=FEATURES:raise ValueError('Invalid extraction coverage/limitations.')
        text(x['method'],200)
        for value in x['features'].values():text(value,2000)
        text(p['created'],64)
    elif contract=='scientific_runs':
        if set(p)!={'id','manifest_sha256','next_page','total_pages','status','updated'} or identity(p['id'])!=key:raise ValueError('Invalid scientific indexing checkpoint.')
        row=db.execute("SELECT payload FROM persistent_records WHERE contract='scientific_editions' AND record_key=? ORDER BY rowid DESC LIMIT 1",(key,)).fetchone()
        if row is None or json.loads(row[0])['metadata']['extraction_sha256']!=checksum(p['manifest_sha256']):raise ValueError('Checkpoint lost its original extraction manifest.')
        edition=json.loads(row[0])
        if p['total_pages']!=edition['extraction']['total_pages']:raise ValueError('Checkpoint coverage differs from registered extraction.')
        if any(type(p[k]) is not int or p[k]<0 for k in ('next_page','total_pages')) or p['next_page']>p['total_pages']:raise ValueError('Invalid scientific page cursor.')
        if p['status'] not in {'partial','complete','deferred'} or (p['status']=='complete')!=(p['total_pages']>0 and p['next_page']==p['total_pages']):raise ValueError('Incomplete scientific extraction cannot be complete.')
        if p['status']=='deferred' and p['total_pages']!=0:raise ValueError('Deferred extraction must state no available pages.')
        if p['next_page']:
            count=db.execute("SELECT count(DISTINCT json_extract(metadata,'$.page_number')) FROM events WHERE parent_id=? AND json_extract(metadata,'$.scientific_key')=? AND json_extract(metadata,'$.resource_type')='scientific-extracted-text' AND json_extract(metadata,'$.extraction_sha256')=? AND json_extract(metadata,'$.page_number') BETWEEN 1 AND ?",(edition['original_event_id'],key,p['manifest_sha256'],p['next_page'])).fetchone()[0]
            if count!=p['next_page']:raise ValueError('Checkpoint cannot acknowledge missing scientific text pages.')
        text(p['updated'],64)

class ScientificLibrary:
    def __init__(self,memory):self.memory=memory;self.db=memory.db
    def _register(self):
        for name in CONTRACTS:
            if self.db.execute('SELECT 1 FROM persistence_contracts WHERE name=?',(name,)).fetchone() is None:register(self.memory,name,'Scientific originals, reviewed rights and restartable derived-text indexing; no facts or training authority')
    def edition(self,key):return latest(self.memory,'scientific_editions',identity(key))
    def editions(self,after=0,limit=30):
        page(after,limit)
        rows=self.db.execute("SELECT rowid AS cursor,payload FROM persistent_records r WHERE contract='scientific_editions' AND rowid>? AND rowid=(SELECT max(rowid) FROM persistent_records WHERE contract=r.contract AND record_key=r.record_key) ORDER BY rowid LIMIT ?",(after,limit)).fetchall()
        return {'items':[{**json.loads(r['payload']),'cursor':r['cursor']} for r in rows],'next_cursor':rows[-1]['cursor'] if rows else after}
    def import_pack(self,root,*,offset=0,limit=1,manifest_sha256=None,approved=False):
        if approved is not True:raise PermissionError('Explicit scientific package/rights approval required.')
        page(offset,limit);entries,digest=read_pack(root)
        if (offset and manifest_sha256!=digest) or (manifest_sha256 is not None and manifest_sha256!=digest):raise ValueError('Scientific manifest changed or resume identity missing.')
        if offset>len(entries):raise ValueError('Scientific package cursor outside manifest.')
        selected=entries[offset:offset+limit]
        items=[self.import_entry(root,entry,approved=True) for entry in selected]
        return {'items':items,'next_cursor':offset+len(items),'manifest_sha256':digest,'complete':offset+len(items)==len(entries),'originals_preserved':True}
    def _archive(self,root,key,role,desc,*,name,parent=None,extra=None):
        # A crash after the original event COMMIT but before catalog/checkpoint
        # publication must reuse that exact event, not invent another submission.
        row=self.db.execute("SELECT id FROM events WHERE sha256=? AND json_extract(metadata,'$.scientific_key')=? AND json_extract(metadata,'$.role')=? ORDER BY occurred,id LIMIT 1",(desc['sha256'],key,role)).fetchone()
        if row:
            event=self.memory.event(row[0])
            if event['parent_id']!=parent or event['byte_count']!=desc['bytes'] or event['media_type']!=desc['media_type'] or any(event['metadata'].get(k)!=v for k,v in (extra or {}).items()):raise ValueError('Scientific restart identity mismatch.')
            for _ in self.memory.original_chunks(row[0]):pass
            return row[0]
        meta={'scientific_key':key,'role':role,**(extra or {})}
        result=self.memory.ingest_file(root/'objects'/desc['sha256'],name=name[:512],media_type=desc['media_type'],metadata=meta,parent_id=parent,expected_sha256=desc['sha256'])
        if result['bytes']!=desc['bytes']:raise ValueError('Scientific source size mismatch; catalog not accepted.')
        return result['event_id']
    @write_operation
    def import_entry(self,root,entry,*,approved=False):
        if approved is not True:raise PermissionError('Explicit source-specific package/rights approval required.')
        metadata(entry);root=safe_path(root);spec=extraction_spec(root,entry);key=key_for(entry)
        existing=self.db.execute("SELECT 1 FROM persistent_records WHERE contract='scientific_editions' AND record_key=?",(key,)).fetchone()
        if existing:
            old=self.edition(key)
            if old['metadata']!=entry:raise ValueError('Edition metadata changed; explicit revision review required.')
            return {**old,'already_imported':True}
        # Descriptor sizes and bounded evidence are checked before publishing
        # catalog state; full streaming SHA verification occurs during intake.
        for d in [entry['original'],*entry['evidence']]:
            path=safe_path(root/'objects'/d['sha256'])
            if path.stat().st_size!=d['bytes']:raise ValueError('Scientific source/evidence length mismatch.')
        for d in entry['evidence']:
            raw=read_file(root/'objects'/d['sha256'],8*1024*1024)
            if hashlib.sha256(raw).hexdigest()!=d['sha256']:raise ValueError('Rights evidence checksum mismatch; no publication imported.')
        self._register()
        original=self._archive(root,key,'original',entry['original'],name=entry['title'],extra={'resource_type':'scientific-original'})
        evidence=[self._archive(root,key,'rights-'+str(i),d,name='Rights evidence: '+entry['provider_id']) for i,d in enumerate(entry['evidence'])]
        manifest_path=root/'objects'/entry['extraction_sha256']
        extract=self._archive(root,key,'extraction-manifest',{'sha256':entry['extraction_sha256'],'bytes':manifest_path.stat().st_size,'media_type':'application/json'},name='Extraction manifest: '+entry['provider_id'],parent=original)
        record={'id':key,'original_event_id':original,'evidence_event_ids':evidence,'extraction_event_id':extract,'extraction':{'total_pages':len(spec['pages']),'method':spec['method'],'features':spec['features']},'metadata':entry,'created':now()}
        append(self.memory,'scientific_editions',key,record,new=True)
        return record
    @write_operation
    def index(self,root,key,*,limit=10,deadline_seconds=5,approved=False):
        if approved is not True:raise PermissionError('Explicit scientific indexing approval required.')
        if type(limit) is not int or not 1<=limit<=100 or type(deadline_seconds) not in (int,float) or not 0<deadline_seconds<=30:raise ValueError('Invalid bounded scientific indexing slice.')
        root=safe_path(root);edition=self.edition(key);entry=edition['metadata'];spec=extraction_spec(root,entry)
        try:prior=latest(self.memory,'scientific_runs',key)
        except ValueError:prior={'next_page':0}
        offset=prior['next_page'];total=len(spec['pages']);done=0;start=time.monotonic()
        if offset>total:raise ValueError('Scientific resume cursor exceeds manifest.')
        while offset<total and done<limit and time.monotonic()-start<deadline_seconds:
            part=spec['pages'][offset];raw=read_file(root/'objects'/part['sha256'],512*1024)
            if len(raw)!=part['bytes'] or hashlib.sha256(raw).hexdigest()!=part['sha256']:raise ValueError('Scientific extracted page checksum/size mismatch.')
            raw.decode('utf-8')
            extra={'resource_type':'scientific-extracted-text','original_event_id':edition['original_event_id'],'original_sha256':entry['original']['sha256'],'page_number':part['page'],'locator':part['locator'],'extraction_sha256':entry['extraction_sha256']}
            self._archive(root,key,'page-'+str(part['page']),{'sha256':part['sha256'],'bytes':part['bytes'],'media_type':'text/plain'},name=entry['title']+' / '+part['locator'],parent=edition['original_event_id'],extra=extra)
            offset+=1;done+=1
            checkpoint={'id':key,'manifest_sha256':entry['extraction_sha256'],'next_page':offset,'total_pages':total,'status':'complete' if offset==total else 'partial','updated':now()}
            append(self.memory,'scientific_runs',key,checkpoint)
        if total==0:
            checkpoint={'id':key,'manifest_sha256':entry['extraction_sha256'],'next_page':0,'total_pages':0,'status':'deferred','updated':now()};append(self.memory,'scientific_runs',key,checkpoint)
        elif not done:
            checkpoint=latest(self.memory,'scientific_runs',key) if offset else {'id':key,'manifest_sha256':entry['extraction_sha256'],'next_page':0,'total_pages':total,'status':'partial','updated':now()}
        return {**checkpoint,'pages_committed':done,'features':spec['features'],'original_preserved':True,'complete_scope':'All supplied extracted text pages only; equations/tables/figures retain declared limitations.'}

def provenance(memory,event_id):
    event=memory.event(event_id);m=event['metadata']
    if m.get('resource_type')!='scientific-extracted-text':return None
    edition=ScientificLibrary(memory).edition(m['scientific_key']);entry=edition['metadata']
    if event['parent_id']!=edition['original_event_id'] or m['original_event_id']!=edition['original_event_id'] or m['original_sha256']!=entry['original']['sha256'] or m['extraction_sha256']!=entry['extraction_sha256']:raise ValueError('Scientific derived-source provenance mismatch.')
    manifest=json.loads(memory.original(edition['extraction_event_id']),object_pairs_hook=unique)
    number=m['page_number']
    if type(number) is not int or not 1<=number<=len(manifest['pages']):raise ValueError('Scientific source page outside registered manifest.')
    part=manifest['pages'][number-1]
    if part['sha256']!=event['sha256'] or part['bytes']!=event['byte_count'] or part['locator']!=m['locator']:raise ValueError('Scientific page differs from original extraction manifest.')
    return {'title':entry['title'],'authors':entry['authors'],'edition':entry['edition'],'publication_date':entry['publication_date'],'revision_date':entry['revision_date'],'subjects':entry['subjects'],'source_url':entry['source_url'],'original_event_id':edition['original_event_id'],'original_sha256':entry['original']['sha256'],'locator':m['locator'],'license':entry['rights']['license'],'attribution':entry['rights']['attribution'],'medical':entry['medical'],'extraction_limits':edition['extraction']['features'],'status':'Source-attributed extracted text; not verified scientific fact or current clinical guidance.'}
