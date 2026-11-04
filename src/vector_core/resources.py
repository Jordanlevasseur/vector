"""Unified, bounded library views over existing originals. No second knowledge store."""
import codecs
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
import stat
import tarfile
import tempfile
import time
import zipfile
from html.parser import HTMLParser
from uuid import uuid4

from vector_core.memory import canonical,now
from vector_core.projects import append,identity,latest
from vector_core.storage import object_chunks,object_path,input_file,safe_path

CONTRACTS={'library_collections','library_memberships','library_reading','library_bookmarks','library_manuals'}
CATEGORIES=('Books','Science','Extracted text','Rights & references','Other documents','Attachments','Retained objects')
TEXT_FORMATS={'Text','Markdown','HTML','XML','JSON','NCBI ASN.1'}
READ_OPERATIONS={'resource_list','resource_detail','resource_inventory','resource_search','resource_passage','resource_reference','resource_read','resource_outline','resource_find','resource_compare','resource_collections','resource_bookmarks'}

def resource_id(value):
    if not isinstance(value,str) or not re.fullmatch(r'(?:[0-9a-f]{32}|(?:asset:[0-9a-f]{32})|(?:blob|object):[0-9a-f]{64})',value):raise ValueError('Invalid resource identity.')
    return value

def validate_record(db,contract,key,p):
    if not isinstance(p,dict):raise ValueError('Invalid library record.')
    if contract=='library_collections':
        if set(p)!={'id','name','description','created'} or identity(p['id'])!=key or not isinstance(p['name'],str) or not 1<=len(p['name'].strip())<=160 or not isinstance(p['description'],str) or len(p['description'])>2000:raise ValueError('Invalid collection.')
    elif contract=='library_memberships':
        if set(p)!={'collection_id','resource_id','included','updated'} or type(p['included']) is not bool:raise ValueError('Invalid collection membership.')
        identity(p['collection_id']);resource_id(p['resource_id'])
        if key!=p['collection_id']+':'+p['resource_id'] or not db.execute("SELECT 1 FROM persistent_records WHERE contract='library_collections' AND record_key=?",(p['collection_id'],)).fetchone():raise ValueError('Missing collection.')
    elif contract in {'library_reading','library_bookmarks'}:
        fields={'resource_id','member','page','offset','font_size','scroll','updated'}
        if contract=='library_bookmarks':fields|={'id','label'}
        if set(p)!=fields:raise ValueError('Invalid reading state fields.')
        resource_id(p['resource_id'])
        rid=p['resource_id']
        if ':' not in rid:
            if not db.execute('SELECT 1 FROM events WHERE id=?',(rid,)).fetchone():raise ValueError('Reading source is missing.')
        elif rid.startswith('asset:'):
            if not db.execute('SELECT 1 FROM managed_refs WHERE id=?',(rid[6:],)).fetchone():raise ValueError('Reading attachment missing.')
        elif not db.execute('SELECT 1 FROM '+('managed_objects' if rid.startswith('object:') else 'blobs')+' WHERE '+('digest' if rid.startswith('object:') else 'sha256')+'=?',(rid.split(':')[1],)).fetchone():raise ValueError('Reading original missing.')
        if type(p['scroll']) not in (int,float) or not math.isfinite(p['scroll']) or not 0<=p['scroll']<=1:raise ValueError('Invalid scroll position.')
        if not isinstance(p['member'],str) or len(p['member'])>1024 or type(p['page']) is not int or not 1<=p['page']<=1000000 or type(p['offset']) is not int or not 0<=p['offset']<=2**40 or type(p['font_size']) is not int or not 8<=p['font_size']<=36:raise ValueError('Invalid reading location.')
        if contract=='library_reading' and key!=p['resource_id']:raise ValueError('Reading state belongs to a different resource.')
        if contract=='library_bookmarks' and (identity(p['id'])!=key or not isinstance(p['label'],str) or not 1<=len(p['label'])<=200):raise ValueError('Invalid bookmark.')
    elif contract=='library_manuals':
        if set(p)!={'id','title','sections','event_id','created'} or identity(p['id'])!=key or not isinstance(p['title'],str) or not 1<=len(p['title'])<=200 or not isinstance(p['sections'],list) or not 1<=len(p['sections'])<=100:raise ValueError('Invalid manual.')
        identity(p['event_id'])
        if not db.execute('SELECT 1 FROM events WHERE id=?',(p['event_id'],)).fetchone():raise ValueError('Manual original missing.')
        for s in p['sections']:
            if set(s)!={'title','body','level'} or not isinstance(s['title'],str) or not 1<=len(s['title'])<=200 or not isinstance(s['body'],str) or len(s['body'])>32000 or type(s['level']) is not int or not 1<=s['level']<=6:raise ValueError('Invalid manual section.')
        row=db.execute('SELECT sha256,metadata FROM events WHERE id=?',(p['event_id'],)).fetchone()
        source=('# '+p['title']+'\n\n'+'\n\n'.join('#'*s['level']+' '+s['title']+'\n\n'+s['body'] for s in p['sections'])).encode()
        if row[0]!=hashlib.sha256(source).hexdigest() or json.loads(row[1]).get('manual_id')!=key:raise ValueError('Manual structure differs from its complete immutable source.')

def format_name(media,name):
    extension=Path(name).suffix.casefold()
    if media=='application/pdf' or extension=='.pdf':return 'PDF'
    if extension=='.epub' or media=='application/epub+zip':return 'EPUB'
    if media in {'application/x-gzip','application/gzip','application/zip','application/x-tar'} or extension in {'.gz','.tgz','.tar','.zip'}:return 'Archive'
    if media=='text/html' or extension in {'.html','.htm','.xhtml'}:return 'HTML'
    if 'xml' in media or extension in {'.xml','.nxml','.rdf'}:return 'XML'
    if media=='application/json' or extension=='.json':return 'JSON'
    if extension in {'.md','.markdown'}:return 'Markdown'
    if media.startswith('text/') or extension in {'.txt','.csv','.log','.rst'}:return 'Text'
    if media.startswith('image/') or extension in {'.jpg','.jpeg','.png','.gif'}:return 'Image'
    return 'Unrecognized'

class _Markup(HTMLParser):
    def __init__(self):super().__init__(convert_charrefs=True);self.parts=[];self.hidden=0
    def handle_starttag(self,tag,attrs):
        if tag in {'script','style','iframe','object'}:self.hidden+=1
        if tag in {'p','div','br','li','h1','h2','h3','h4','h5','h6','sec','title','tr'}:self.parts.append('\n')
    def handle_endtag(self,tag):
        if tag in {'script','style','iframe','object'} and self.hidden:self.hidden-=1
        if tag in {'p','div','li','sec','title','tr'}:self.parts.append('\n')
    def handle_data(self,data):
        if not self.hidden:self.parts.append(data)

class Resources:
    def __init__(self,memory,renderer=None,renderer_error=None):
        self.memory=memory;self.db=memory.db;self.renderer=renderer;self.renderer_error=renderer_error
        self.temporary=None
        if renderer:self.cache=Path(renderer.cache)
        else:self.temporary=tempfile.TemporaryDirectory(prefix='vector_library_');self.cache=Path(self.temporary.name);(self.cache/'inputs').mkdir(mode=0o700);(self.cache/'outputs').mkdir(mode=0o700)
        self.cached={};self.catalog=[];self.fingerprint=None;self.text_cache={};self.member_cache={}
    def close(self):
        if self.renderer:self.renderer.close();self.renderer=None
        if self.temporary:self.temporary.cleanup();self.temporary=None
    def _records(self,contract):
        return [json.loads(r[0]) for r in self.db.execute("SELECT payload FROM persistent_records r WHERE contract=? AND rowid=(SELECT max(rowid) FROM persistent_records WHERE contract=r.contract AND record_key=r.record_key) ORDER BY rowid",(contract,))]
    def _refresh(self):
        fingerprint=(self.db.execute('SELECT count(*),max(rowid) FROM events').fetchone()[:],self.db.execute('SELECT count(*),max(rowid) FROM managed_refs').fetchone()[:],self.db.execute('SELECT count(*),max(rowid) FROM managed_objects').fetchone()[:],tuple(self.db.execute("SELECT max(rowid) FROM persistent_records WHERE contract IN ('literary_editions','scientific_editions','library_manuals')").fetchone()))
        if fingerprint==self.fingerprint:return
        books={p['event_id']:p for p in self._records('literary_editions')};science={p['original_event_id']:p for p in self._records('scientific_editions')};manuals={p['event_id']:p for p in self._records('library_manuals')}
        # Do not read texts.status here: it follows a potentially huge TEXT field
        # in the SQLite record and can force overflow-page reads just to list titles.
        # FTS row identities establish index presence; search itself retains its
        # original status/hash/span verification unchanged.
        indexed={r[0] for r in self.db.execute('SELECT t.event_id FROM text_search f JOIN texts t ON t.rowid=f.rowid')}
        rows=self.db.execute('SELECT e.*,COALESCE(o.raw_bytes,b.byte_count) AS bytes,o.stored_bytes,o.codec,x.object_digest,b.sha256 AS blob_digest,(SELECT count(*) FROM claims c WHERE c.event_id=e.id) AS claims_count FROM events e LEFT JOIN blobs b ON b.sha256=e.sha256 LEFT JOIN external_originals x ON x.digest=e.sha256 LEFT JOIN managed_objects o ON o.digest=x.object_digest ORDER BY e.rowid')
        result=[]
        for row in rows:
            p=dict(row);p['extraction_status']='FTS text representation exists' if p['id'] in indexed else 'No direct FTS text; original retained';meta=json.loads(p['metadata']);edition=books.get(p['id']) or science.get(p['id']);m=edition['metadata'] if edition else {}
            category='Books' if p['id'] in books else 'Science' if p['id'] in science else 'Extracted text' if meta.get('resource_type')=='scientific-extracted-text' else 'Rights & references' if 'rights' in p['submission_name'].casefold() or p['media_type']=='application/rdf+xml' else 'Other documents'
            title=m.get('title') or p['submission_name'];subjects=m.get('subjects',[]);subjects=subjects if isinstance(subjects,list) else [subjects] if subjects else []
            fmt=format_name(p['media_type'],p['submission_name']);reason=''
            if not p['blob_digest']:reason='Original blob identity is missing.'
            elif p['object_digest']:
                try:
                    path=object_path(self.memory.config.data_dir,p['object_digest']);info=path.stat()
                    if not stat.S_ISREG(info.st_mode) or info.st_size!=p['stored_bytes']:reason='Managed original file length/type does not match its descriptor.'
                except (OSError,ValueError) as error:reason='Original file inaccessible: '+str(error)
            item={k:p[k] for k in ('id','source_id','sha256','bytes','media_type','parent_id','claims_count','extraction_status')}
            from urllib.parse import urlparse
            filename=Path(urlparse(m.get('source_url','')).path).name or p['submission_name']
            item.update(event_id=p['id'],title=title,name=p['submission_name'],file_name=filename,source_url=m.get('source_url'),authors=m.get('authors',[]),subjects=subjects,description=m.get('edition',''),category=category,format=fmt,created=p['occurred'],original_event_id=meta.get('original_event_id'),locator=meta.get('locator'),available=not reason,reason=reason,manual_id=manuals.get(p['id'],{}).get('id'),reader='pdf' if fmt=='PDF' else 'image' if fmt=='Image' else 'archive' if fmt in {'Archive','EPUB'} else 'text' if fmt in TEXT_FORMATS else 'unsupported')
            result.append(item)
        # Registered attachments and retained unacknowledged objects remain accounted for.
        for row in self.db.execute('SELECT r.*,o.raw_bytes FROM managed_refs r JOIN managed_objects o ON o.digest=r.digest WHERE r.purpose NOT IN (\'model-weight\',\'adapter\',\'extension\',\'capability\')'):
            p=dict(row);result.append(dict(id='asset:'+p['id'],event_id=None,source_id=None,sha256=p['digest'],title=p['logical_name'],name=p['logical_name'],authors=[],subjects=[],description=p['purpose'],category='Attachments',format=format_name('',p['logical_name']),bytes=p['raw_bytes'],media_type='application/octet-stream',created=p['created'],parent_id=None,original_event_id=None,locator=None,available=True,reason='',reader='unsupported',claims_count=0,extraction_status='not indexed'))
        for row in self.db.execute('SELECT * FROM managed_objects o WHERE NOT EXISTS (SELECT 1 FROM external_originals x WHERE x.object_digest=o.digest) AND NOT EXISTS (SELECT 1 FROM managed_refs r WHERE r.digest=o.digest)'):
            result.append(dict(id='object:'+row['digest'],event_id=None,source_id=None,sha256=row['digest'],title='Retained object '+row['digest'][:16],name=row['digest'],authors=[],subjects=[],description='Retained content without an acknowledged source event',category='Retained objects',format='Unrecognized',bytes=row['raw_bytes'],media_type='application/octet-stream',created='',parent_id=None,original_event_id=None,locator=None,available=True,reason='',reader='unsupported',claims_count=0,extraction_status='not indexed'))
        duplicates={}
        for p in result:duplicates[p['sha256']]=duplicates.get(p['sha256'],0)+1
        for p in result:p['duplicate_count']=duplicates[p['sha256']]-1
        self.catalog=result;self.by_id={p['id']:p for p in result};self.fingerprint=fingerprint
    def detail(self,key):
        self._refresh();resource_id(key)
        if key not in self.by_id:raise KeyError('Resource not found.')
        item=dict(self.by_id[key])
        descriptor=self.db.execute('SELECT * FROM managed_objects WHERE digest=?',(item['sha256'],)).fetchone()
        if descriptor:
            try:
                info=object_path(self.memory.config.data_dir,item['sha256']).stat()
                if not stat.S_ISREG(info.st_mode) or info.st_size!=descriptor['stored_bytes']:item.update(available=False,reason='Original file size/type differs from its immutable descriptor.')
            except (OSError,ValueError) as error:item.update(available=False,reason='Original inaccessible: '+str(error))
        item['reading']=self.state(key);return item
    def list(self,query='',*,category='',format='',collection='',sort='title',after=0,limit=40):
        if not isinstance(query,str) or len(query)>512 or type(after) is not int or after<0 or type(limit) is not int or not 1<=limit<=100:raise ValueError('Invalid catalogue page/query.')
        if category and category not in CATEGORIES:raise ValueError('Unknown category.')
        if sort not in {'title','author','format','newest'}:raise ValueError('Unknown sort.')
        self._refresh();members=None
        if collection:
            identity(collection);members={p['resource_id'] for p in self._records('library_memberships') if p['collection_id']==collection and p['included']}
        terms=query.casefold().split();rows=[]
        for item in self.catalog:
            if category and item['category']!=category or format and item['format']!=format or members is not None and item['id'] not in members:continue
            hay=' '.join([item['title'],item['name'],item.get('file_name',''),item['format'],item['category'],*item['authors'],*item['subjects']]).casefold()
            if all(t in hay for t in terms):rows.append(item)
        rows.sort(key=lambda p:(p['created'] if sort=='newest' else ' '.join(p['authors']).casefold() if sort=='author' else p['format'] if sort=='format' else p['title'].casefold(),p['id']),reverse=sort=='newest')
        return {'items':rows[after:after+limit],'total':len(rows),'next_cursor':after+limit if after+limit<len(rows) else None,'categories':list(CATEGORIES),'formats':sorted({p['format'] for p in self.catalog}),'collections':self.collections()}
    def collections(self):return self._records('library_collections')
    def _append(self,contract,key,p,**options):
        from vector_core.persistence import register
        if not self.db.execute('SELECT 1 FROM persistence_contracts WHERE name=?',(contract,)).fetchone():register(self.memory,contract,'Owner-authored library organization or reading state; original bytes remain authoritative')
        return append(self.memory,contract,key,p,**options)
    def collection(self,name,description='',approved=False):
        if approved is not True:raise PermissionError('Explicit owner action required.')
        key=uuid4().hex;return self._append('library_collections',key,{'id':key,'name':name,'description':description,'created':now()},new=True)
    def membership(self,collection,key,included=True,approved=False):
        if approved is not True:raise PermissionError('Explicit owner action required.')
        self.detail(key);return self._append('library_memberships',identity(collection)+':'+key,{'collection_id':collection,'resource_id':key,'included':included,'updated':now()})
    def state(self,key):
        row=self.db.execute("SELECT payload FROM persistent_records WHERE contract='library_reading' AND record_key=? ORDER BY rowid DESC LIMIT 1",(key,)).fetchone();return json.loads(row[0]) if row else None
    def position(self,key,*,member='',page=1,offset=0,font_size=12,scroll=0,bookmark=None):
        self.detail(key);p={'resource_id':key,'member':member,'page':page,'offset':offset,'font_size':font_size,'scroll':scroll,'updated':now()}
        if bookmark is not None:
            p.update(id=uuid4().hex,label=bookmark);return self._append('library_bookmarks',p['id'],p,new=True)
        if self.state(key) and all(self.state(key)[k]==v for k,v in p.items() if k!='updated'):return p
        return self._append('library_reading',key,p)
    def bookmarks(self,key):self.detail(key);return [p for p in self._records('library_bookmarks') if p['resource_id']==key]
    def chunks(self,key):
        p=self.detail(key)
        if not p['available']:raise ValueError(p['reason'])
        if p['event_id']:yield from self.memory.original_chunks(p['event_id'])
        else:
            row=self.db.execute('SELECT * FROM managed_objects WHERE digest=?',(p['sha256'],)).fetchone()
            if not row:raise ValueError('Managed attachment unavailable.')
            yield from object_chunks(self.memory.config.data_dir,row)
    def stage(self,key):
        p=self.detail(key);digest=p['sha256'];target=self.cache/'inputs'/digest
        # Revalidate the authoritative original on each new open. Keep no original mutation path.
        if key in self.cached:
            path,old_signature,cache_signature=self.cached[key]
            if path.exists() and self._signature(p)==old_signature and self._file_signature(path)==cache_signature:return path
        from vector_core.intake import write_new_chunks
        if not target.exists():
            entries=sorted((self.cache/'inputs').iterdir(),key=lambda p:p.stat().st_mtime_ns)
            size=sum(e.stat().st_size for e in entries)
            for old in entries:
                if len(entries)<=4 and size+(p['bytes'] or 0)<=256*1024*1024:break
                size-=old.stat().st_size;old.unlink();entries=entries[1:]
            write_new_chunks(target,self.chunks(key))
        else:
            h=hashlib.sha256()
            for block in self.chunks(key):h.update(block)
            if h.hexdigest()!=digest:raise ValueError('Original verification failed.')
        with input_file(target) as handle:
            if hashlib.file_digest(handle,'sha256').hexdigest()!=digest:raise ValueError('Reader cache integrity failed.')
        target.chmod(0o400);self.cached[key]=(target,self._signature(p),self._file_signature(target));return target
    def _file_signature(self,path):
        info=safe_path(path).stat();return info.st_size,info.st_mtime_ns,info.st_ctime_ns,info.st_ino
    def _signature(self,p):
        row=self.db.execute('SELECT digest FROM managed_objects WHERE digest=?',(p['sha256'],)).fetchone()
        if row:
            info=object_path(self.memory.config.data_dir,p['sha256']).stat()
            return info.st_size,info.st_mtime_ns,info.st_ctime_ns,info.st_ino
        # Small legacy originals are inexpensive to verify before reusing a cache.
        return hashlib.sha256(b''.join(self.chunks(p['id']))).hexdigest()
    def inventory(self):
        self.fingerprint=None;self._refresh();by_format={};by_category={};unavailable=[];unsupported=[];hashes={}
        for p in self.catalog:
            by_format[p['format']]=by_format.get(p['format'],0)+1;by_category[p['category']]=by_category.get(p['category'],0)+1;hashes[p['sha256']]=hashes.get(p['sha256'],0)+1
            if not p['available']:unavailable.append({'id':p['id'],'title':p['title'],'reason':p['reason']})
            elif p['reader']=='unsupported':unsupported.append({'id':p['id'],'title':p['title'],'format':p['format'],'reason':'No inert reader for this format; exact export remains available.'})
        needs_renderer=[{'id':p['id'],'title':p['title'],'reason':str(self.renderer_error or 'Qualified local renderer is stopped/unavailable.')} for p in self.catalog if p['available'] and p['reader'] in {'pdf','image'} and not(self.renderer and self.renderer.qualified)]
        return {'catalogue_entries':len(self.catalog),'unique_original_contents':len(hashes),'originals_located_entries':len(self.catalog)-len(unavailable),'direct_reader_supported_entries':len(self.catalog)-len(unavailable)-len(unsupported)-len(needs_renderer),'requires_different_reader_entries':len(unsupported)+len(needs_renderer),'duplicate_records':sum(n-1 for n in hashes.values()),'unavailable':unavailable,'unsupported':unsupported,'renderer_unavailable':needs_renderer,'unrecognized_formats':sum(p['format']=='Unrecognized' for p in self.catalog),'by_format':by_format,'by_category':by_category,'collections':[{'id':c['id'],'name':c['name'],'entries':sum(p['collection_id']==c['id'] and p['included'] for p in self._records('library_memberships'))} for c in self.collections()],'reader_qualification':self.renderer.report if self.renderer and self.renderer.qualified else None,'integrity_scope':'Location/descriptor checks and supported reader classification, not a claim that every page was rendered. SHA-256 is verified on original open/export; full verification is an explicit bounded inventory job.'}

    def _members(self,path):
        entries=[];total=0;end=time.monotonic()+15
        def source_format(name,size,regular,opener):
            fmt=format_name('',name)
            # .prt is ambiguous (CAD or NCBI data). Recognize only the actual
            # NCBI text header, and provide source text rather than claiming 3D.
            if fmt=='Unrecognized' and Path(name).suffix.casefold()=='.prt' and regular and size<=128*1024*1024:
                with opener() as stream:
                    if stream.read(64).startswith(b'Ncbi-mime-asn1 ::='):fmt='NCBI ASN.1'
            return fmt
        if zipfile.is_zipfile(path):
            with zipfile.ZipFile(path) as archive:
                for i,p in enumerate(archive.infolist()):
                    if i>=20000:raise ValueError('Archive member limit reached; original remains available for exact export.')
                    total+=p.file_size
                    if total>512*1024*1024 or time.monotonic()>end:raise ValueError('Archive listing exceeds a bounded 512 MiB/15-second slice.')
                    rejection='Archive symbolic link is not followed.' if stat.S_ISLNK(p.external_attr>>16) else 'Encrypted archive member requires a different reader.' if p.flag_bits&1 else 'Unsupported archive compression method '+str(p.compress_type)+'.' if p.compress_type not in {zipfile.ZIP_STORED,zipfile.ZIP_DEFLATED} else ''
                    if not p.is_dir():entries.append({'name':p.filename,'bytes':p.file_size,'format':source_format(p.filename,p.file_size,not rejection,lambda:archive.open(p)),'regular':not rejection,'rejection':rejection})
        else:
            try:
                with input_file(path) as check:
                    header=check.read(6)
                    if header.startswith((b'BZh',b'\xfd7zXZ\x00')):raise ValueError('This archive compression requires a different bounded reader. Original retained; no decompressor was started.')
                with tarfile.open(path,mode='r:*') as archive:
                    for i,p in enumerate(archive):
                        if i>=20000:raise ValueError('Archive member limit reached.')
                        total+=p.size
                        if total>512*1024*1024 or time.monotonic()>end:raise ValueError('Archive listing exceeds bounded size/time.')
                        if not p.isdir():entries.append({'name':p.name,'bytes':p.size,'format':source_format(p.name,p.size,p.isfile(),lambda:archive.extractfile(p)),'regular':p.isfile(),'rejection':'' if p.isfile() else 'Archive link or special-file type '+repr(p.type)+' is not opened.'})
            except tarfile.ReadError as error:raise ValueError('Archive format is not supported: '+str(error)) from error
        for p in entries:
            p['safe']=p['regular'] and not Path(p['name']).is_absolute() and '..' not in Path(p['name']).parts and len(p['name'])<=1024
            p['readable']=p['safe'] and p['format'] in (TEXT_FORMATS|{'PDF','Image'}) and p['bytes']<=128*1024*1024
            p['note']='Molecular-structure source text only; no 3D rendering.' if p['format']=='NCBI ASN.1' else ''
            p['reason']='' if p['readable'] else p['rejection'] if not p['regular'] else 'Unsafe archive member name; never extracted.' if not p['safe'] else 'Member exceeds the 128 MiB reader working-file limit.' if p['bytes']>128*1024*1024 else 'No qualified inert reader for '+(Path(p['name']).suffix or 'unrecognized format')+'; preserved without execution.'
        return entries
    def member(self,key,name):
        path=self.stage(key);matches=[p for p in self._members(path) if p['name']==name]
        if len(matches)!=1 or not matches[0]['readable']:raise ValueError('Unsupported, ambiguous or unsafe archive member.')
        meta=matches[0];token=hashlib.sha256((self.detail(key)['sha256']+'\0'+name).encode()).hexdigest();target=self.cache/'inputs'/token
        if target.exists() and (token not in self.member_cache or self.member_cache[token]!=self._file_signature(target)):target.unlink()
        if not target.exists():
            from vector_core.intake import write_new_chunks
            def copy(stream):
                length=0
                while block:=stream.read(1024*1024):
                    length+=len(block)
                    if length>meta['bytes']:raise ValueError('Archive member exceeds its declared length.')
                    yield block
                if length!=meta['bytes']:raise ValueError('Archive member truncated.')
            if zipfile.is_zipfile(path):
                with zipfile.ZipFile(path) as archive,archive.open(name) as stream:write_new_chunks(target,copy(stream))
            else:
                with tarfile.open(path,mode='r:*') as archive:
                    entry=archive.getmember(name)
                    if not entry.isfile():raise ValueError('Archive links and special files are never opened.')
                    with archive.extractfile(entry) as stream:write_new_chunks(target,copy(stream))
            target.chmod(0o400)
            self.member_cache[token]=self._file_signature(target)
        return target,meta
    def open(self,key,member=''):
        self.cached.pop(key,None)
        p=self.detail(key);path,meta=self.member(key,member) if member else (self.stage(key),p);fmt=meta['format']
        if fmt in {'Archive','EPUB'}:
            if path.stat().st_size>128*1024*1024:raise ValueError('Archive exceeds this reader’s bounded 128 MiB input budget. Complete original remains available for export.')
            members=self._members(path)
            if fmt=='EPUB':
                import posixpath,xml.etree.ElementTree as ET
                with zipfile.ZipFile(path) as z:
                    def xml(name):
                        info=z.getinfo(name)
                        if info.file_size>2*1024*1024:raise ValueError('EPUB structure exceeds reader budget.')
                        raw=z.read(name)
                        if b'<!DOCTYPE' in raw.upper() or b'<!ENTITY' in raw.upper():raise ValueError('EPUB external entities are forbidden.')
                        return ET.fromstring(raw)
                    container=xml('META-INF/container.xml');rootfile=next((v.get('full-path') for v in container.iter() if v.tag.endswith('rootfile')),None)
                    if not rootfile or rootfile.startswith('/') or '..' in Path(rootfile).parts:raise ValueError('Invalid EPUB root path.')
                    book=xml(rootfile);manifest={v.get('id'):v.get('href') for v in book.iter() if v.tag.endswith('item')};order=[]
                    for node in book.iter():
                        if node.tag.endswith('itemref'):
                            name=posixpath.normpath(posixpath.join(posixpath.dirname(rootfile),manifest.get(node.get('idref')) or ''))
                            if name.startswith(('../','/')):raise ValueError('EPUB chapter escapes the package.')
                            order.append(name)
                    members.sort(key=lambda v:(order.index(v['name']) if v['name'] in order else len(order),v['name']))
            return {'resource':p,'kind':'archive','members':members[:100],'member_total':len(members),'next_member_cursor':100 if len(members)>100 else None,'state':p['reading'],'message':'Complete original archive preserved. Select a static document; unsupported media remain inert.'}
        if fmt=='PDF':
            if not self.renderer:raise ValueError('PDF renderer unavailable: '+str(self.renderer_error or 'qualified local renderer not started'))
            info=self.renderer.request({'operation':'open','token':path.name},30);return {'resource':p,'kind':'pdf','member':member,**info,'state':p['reading']}
        if fmt=='Image':
            if not self.renderer:raise ValueError('Image reader unavailable: '+str(self.renderer_error))
            return {'resource':p,'kind':'image','member':member,'pages':1,'state':p['reading']}
        if fmt not in TEXT_FORMATS:return {'resource':p,'kind':'unsupported','member':member,'reason':'No safe built-in reader for '+fmt+'. Exact original export is available; file content is never executed.'}
        return {'resource':p,'kind':'text','member':member,'state':p['reading'],'format':fmt,'message':'Complete original text, paginated without using a passage index. Markup can be read as inert source or readable text.'}
    def read(self,key,*,member='',offset=0,page=1,width=900,raw=False):
        if type(offset) is not int or not 0<=offset<=2**40:raise ValueError('Invalid text offset.')
        p=self.detail(key);path,meta=self.member(key,member) if member else (self.stage(key),p)
        if meta['format'] in {'PDF','Image'}:
            if not self.renderer:raise ValueError('PDF renderer unavailable: '+str(self.renderer_error))
            request={'operation':'render','token':path.name,'page':page,'width':width} if meta['format']=='PDF' else {'operation':'image','token':path.name,'width':width}
            result=self.renderer.request(request,30)
            if not isinstance(result.get('image'),str) or not re.fullmatch(r'[0-9a-f]{64}-\d+-\d+\.png',result['image']):raise ValueError('Invalid page-image identity.')
            image=self.cache/'outputs'/result['image']
            if type(result.get('bytes')) is not int or not 0<result['bytes']<=16*1024*1024:raise ValueError('Invalid page-image size.')
            if image.exists():image.unlink()
            from vector_core.intake import write_new_chunks
            import base64
            def chunks():
                offset=0;end=time.monotonic()+30
                while offset<result['bytes']:
                    if time.monotonic()>end:raise TimeoutError('Reader image transfer timed out.')
                    reply=self.renderer.request({'operation':'image_chunk','name':result['image'],'offset':offset},5)
                    block=base64.b64decode(reply['data'],validate=True)
                    if not block or len(block)>65536 or offset+len(block)>result['bytes']:raise ValueError('Reader image chunk length invalid.')
                    offset+=len(block);yield block
            write_new_chunks(image,chunks())
            with input_file(image) as stream:
                header=stream.read(24);stream.seek(0)
                if len(header)!=24 or header[:8]!=b'\x89PNG\r\n\x1a\n' or image.stat().st_size>16*1024*1024 or hashlib.file_digest(stream,'sha256').hexdigest()!=result['sha256']:raise ValueError('Rendered image integrity failed.')
                import struct
                w,h=struct.unpack('>II',header[16:24])
                if not 1<=w<=1600 or not 1<=h<=5000 or w*h>8000000:raise ValueError('Rendered image exceeds display bounds.')
            for old in sorted((self.cache/'outputs').glob('*.png'),key=lambda p:p.stat().st_mtime_ns)[:-3]:old.unlink()
            return {**result,'image_path':str(image)}
        if meta['format'] not in TEXT_FORMATS:raise ValueError('Select a supported document member to read.')
        with input_file(path) as handle:
            # Character positions, CRLF and bytes remain distinct; no original normalization.
            stream=io.TextIOWrapper(handle,encoding='utf-8',errors='strict',newline='');remaining=offset
            while remaining:
                part=stream.read(min(65536,remaining))
                if not part:break
                remaining-=len(part)
            if remaining:raise ValueError('Reading location is outside the original.')
            text=stream.read(16000);more=bool(stream.read(1))
        display=text
        if not raw and meta['format'] in {'HTML','XML'}:
            parser=_Markup();parser.feed(text);display=''.join(parser.parts)
        return {'kind':'text','text':display,'source_text':text,'offset':offset,'next_offset':offset+len(text) if more else None,'previous_offset':max(0,offset-16000),'format':meta['format'],'original_source_preserved':True,'whole_original_supplied':offset==0 and not more,'range_is_excerpt':offset>0 or more}
    def outline(self,key,member=''):
        p=self.detail(key);path,meta=self.member(key,member) if member else (self.stage(key),p)
        if meta['format']=='PDF':
            if not self.renderer:raise ValueError('PDF reader unavailable.')
            result=self.renderer.request({'operation':'outline','token':path.name},30)
            if not result['items']:result['message']='This original has no PDF bookmarks. Use page navigation or search within the original.'
            return result
        result=[];position=0;end=time.monotonic()+10
        if meta['format'] not in TEXT_FORMATS:return {'items':self._members(path)}
        with input_file(path) as handle,io.TextIOWrapper(handle,encoding='utf-8',newline='') as text:
            while line:=text.readline(65536):
                if re.match(r'\s*(?:#{1,6}\s|(?:CHAPTER|Chapter|BOOK|Book|CANTO|SECTION|Section)\s+[\wIVXLCDM]+\b|<h[1-6]\b|<title\b)',line):result.append({'title':line.strip()[:200],'offset':position})
                position+=len(line)
                if len(result)>=1000 or time.monotonic()>end:break
        return {'items':result,'method':'Literal original heading candidates; original page/order unchanged.'}
    def find(self,key,query,*,member='',after=0,page=1):
        if not isinstance(query,str) or not 1<=len(query)<=200:raise ValueError('Enter 1–200 search characters.')
        p=self.detail(key);path,meta=self.member(key,member) if member else (self.stage(key),p)
        if meta['format']=='PDF':
            if not self.renderer:raise ValueError('PDF renderer unavailable.')
            return self.renderer.request({'operation':'find','token':path.name,'query':query,'page':page},30)
        if type(after) is not int or after<0:raise ValueError('Invalid search position.')
        position=0;tail='';end=time.monotonic()+15
        with input_file(path) as handle,io.TextIOWrapper(handle,encoding='utf-8',newline='') as stream:
            while chunk:=stream.read(65536):
                value=tail+chunk;origin=position-len(tail);match=re.compile(re.escape(query),re.I).search(value,max(0,after-origin))
                if match:
                    found=match.start();return {'found':True,'offset':origin+found,'excerpt':value[max(0,found-80):match.end()+160]}
                position+=len(chunk);tail=value[-len(query):]
                if time.monotonic()>end:return {'found':False,'incomplete':True,'next_offset':position,'reason':'Bounded search slice ended; continue without losing the rest of the document.'}
        return {'found':False,'incomplete':False}

    def search(self,query,limit=30):
        from vector_core.retrieval import search
        from vector_core.literature import Library
        rows=search(self.memory,query,limit=min(20,limit))+Library(self.memory).search(query,limit=min(20,limit));result=[]
        for row in rows[:limit]:
            result.append({'resource_id':row['event_id'],'title':row['name'],'excerpt':row['excerpt'],'start':row['start'],'end':row['end'],'sha256':row['sha256'],'original_event_id':(row.get('scientific_provenance') or {}).get('original_event_id'),'locator':(row.get('scientific_provenance') or {}).get('locator')})
        return {'items':result,'scope':'Existing bounded FTS only; deferred/unsupported originals remain browseable but are not claimed searchable.'}
    def reference(self,event_id,*,unit_id=None,start=0,end=None):
        if unit_id:
            from vector_core.literature import Library
            passage=Library(self.memory).passage(unit_id);event_id=passage['event_id'];start=passage['start']
        p=self.detail(identity(event_id));page=1
        if p['original_event_id']:
            match=re.fullmatch(r'PDF page (\d+)',p['locator'] or '')
            return {'resource_id':p['original_event_id'],'page':int(match[1]) if match else 1,'offset':0,'derived_event_id':event_id,'locator':p['locator']}
        return {'resource_id':event_id,'offset':start,'page':page}
    def manual(self,title,sections,*,manual_id=None,revision=None,approved=False):
        if approved is not True:raise PermissionError('Explicit owner save is required.')
        key=identity(manual_id) if manual_id else uuid4().hex;old=latest(self.memory,'library_manuals',key) if manual_id else None
        if old and old['revision']!=revision:raise ValueError('Manual revision changed; reload before saving.')
        # Validate complete structured revision before acknowledging an immutable source.
        if not isinstance(title,str) or not 1<=len(title.strip())<=200 or not isinstance(sections,list) or not 1<=len(sections)<=100:raise ValueError('Title and 1–100 custom sections required.')
        if len(canonical(sections).encode())>900000:raise ValueError('Structured manual metadata exceeds the portable record budget; import the complete large original instead.')
        body=[]
        for s in sections:
            if not isinstance(s,dict) or set(s)!={'title','body','level'} or not isinstance(s['title'],str) or not 1<=len(s['title'])<=200 or not isinstance(s['body'],str) or len(s['body'])>32000 or type(s['level']) is not int or not 1<=s['level']<=6:raise ValueError('Invalid custom section.')
            body.append('#'*s['level']+' '+s['title']+'\n\n'+s['body'])
        raw=('# '+title+'\n\n'+'\n\n'.join(body)).encode()
        if len(raw)>self.memory.config.max_source_bytes:raise ValueError('Manual revision exceeds the current original intake budget.')
        from vector_core.memory import Submission
        event=self.memory.ingest(Submission(raw,title+'.md','text/markdown',{'resource_type':'authored-manual','manual_id':key},parent_id=old['event_id'] if old else None))
        saved=self._append('library_manuals',key,{'id':key,'title':title,'sections':sections,'event_id':event['event_id'],'created':now()},expected=revision if old else None,new=not old)
        return {'manual':saved,'resource_id':event['event_id'],'originals_retained':True}

def dispatch(app,operation,p):
    if not hasattr(app,'resources'):app.resources=Resources(app.memory,getattr(app,'reader_transport',None),getattr(app,'reader_error',None))
    r=app.resources
    if operation=='resource_list':return r.list(**p)
    if operation=='resource_detail':return r.detail(p['id'])
    if operation=='resource_inventory':return r.inventory()
    if operation=='resource_open':return r.open(p['id'],p.get('member',''))
    if operation=='resource_read':return r.read(p['id'],**{k:v for k,v in p.items() if k!='id'})
    if operation=='resource_outline':return r.outline(p['id'],p.get('member',''))
    if operation=='resource_find':return r.find(p['id'],**{k:v for k,v in p.items() if k!='id'})
    if operation=='resource_position':return r.position(p['id'],**{k:v for k,v in p.items() if k!='id'})
    if operation=='resource_bookmarks':return {'items':r.bookmarks(p['id'])}
    if operation=='resource_members':
        after=p.get('after',0)
        if type(after) is not int or after<0:raise ValueError('Invalid archive cursor.')
        members=r._members(r.stage(p['id']));return {'items':members[after:after+100],'next_cursor':after+100 if after+100<len(members) else None,'total':len(members)}
    if operation=='resource_export':
        from vector_core.intake import write_new_chunks
        write_new_chunks(p['output'],r.chunks(p['id']));return {'complete_original_exported':True,'id':p['id'],'output':p['output']}
    if operation=='resource_collections':return {'items':r.collections()}
    if operation=='resource_collection_create':return r.collection(**p)
    if operation=='resource_membership':return r.membership(p['collection'],p['id'],p.get('included',True),p.get('approved',False))
    if operation=='resource_search':return r.search(p['query'])
    if operation=='resource_reference':return r.reference(**p)
    if operation=='resource_compare':
        if not isinstance(p.get('ids'),list) or not 1<=len(p['ids'])<=8:raise ValueError('Compare 1–8 resource identities.')
        return {'items':[r.detail(key) for key in p['ids']]}
    if operation=='resource_passage':
        if p.get('unit_id'):
            from vector_core.literature import Library
            return Library(r.memory).passage(p['unit_id'])
        resource=r.detail(p['id']);path,meta=r.member(p['id'],p['member']) if p.get('member') else (r.stage(p['id']),resource)
        if meta['format']=='PDF':
            if not r.renderer:raise ValueError('PDF reader unavailable.')
            passage=r.renderer.request({'operation':'text','token':path.name,'page':p.get('page',1),'offset':p.get('offset',0)},30)
        else:passage=r.read(p['id'],member=p.get('member',''),offset=p.get('offset',0))
        return {'resource':resource,'passage':passage}
    if operation=='resource_manual_save':return r.manual(**p)
    if operation=='resource_manual_get':return latest(r.memory,'library_manuals',identity(p['id']))
    raise ValueError('Unknown resource operation.')

def read_tool(app,request):
    """Future model tools have a read-only boundary, never the full dispatcher."""
    if not isinstance(request,dict) or set(request)!={'operation','parameters'} or request['operation'] not in READ_OPERATIONS or not isinstance(request['parameters'],dict):raise PermissionError('Only explicit bounded read-only library operations are allowed.')
    return dispatch(app,request['operation'],request['parameters'])
