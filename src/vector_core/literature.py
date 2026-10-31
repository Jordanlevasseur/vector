"""Offline original-linked library, bounded passage indexing and literary records."""
import hashlib
import json
import os
import re
import time
from pathlib import Path
from uuid import uuid4
from vector_core.coordination import write_operation
from vector_core.memory import canonical,now
from vector_core.projects import append,_insert,identity,page,text,latest
from vector_core.storage import input_file,safe_path,DIGEST
from vector_core.portable import unique

METHOD='literal-paragraph-v1'
PG_NOTICE='This eBook is for the use of anyone anywhere in the United States and most other parts of the world at no cost and with almost no restrictions whatsoever. You may copy it, give it away or re-use it under the terms of the Project Gutenberg License included with this eBook or online at www.gutenberg.org. If you are not located in the United States, you’ll have to check the laws of the country where you are located before using this ebook.'
NODE_KINDS={'concept','phoneme','morpheme','lemma','word_form','category','construction','sense','definition','idiom','metaphor','figure','etymology','cognate','borrowing','translation','semantic_relation','historical_usage','literary_form','rhetorical_device','poetry_structure','morphology','transliteration','gloss','commentary','textual_variant','theme','narrative','argument','grammar','ambiguity','register'}
RELATIONS={'exact-equivalence','approximate-translation','related-meaning','etymological','borrowing','uncertain','translation-of','edition-of','volume-of'}

def language_id(value):
    if not isinstance(value,str) or not re.fullmatch('[a-zA-Z][a-zA-Z0-9-]{0,63}',value):raise ValueError('Invalid extensible language identifier.')
    return value

def validate_record(db,contract,key,p):
    if not isinstance(p,dict):raise ValueError('Invalid literary record.')
    def event(value):
        identity(value)
        row=db.execute('SELECT sha256 FROM events WHERE id=?',(value,)).fetchone()
        if not row:raise ValueError('Missing literary original reference.')
        return row[0]
    if contract=='languages':
        if set(p)!={'id','name','scripts','varieties','historical','coverage','domains','provenance'} or language_id(key)!=p['id']:raise ValueError('Invalid language profile.')
        for name in ('name','coverage','provenance'):text(p[name],2000)
        for name in ('scripts','varieties','domains'):
            if not isinstance(p[name],list) or len(p[name])>64 or any(not isinstance(v,str) or len(v)>300 for v in p[name]):raise ValueError('Invalid curriculum fields.')
        if type(p['historical']) is not bool:raise ValueError('Invalid period flag.')
    elif contract=='literary_editions':
        if set(p)!={'id','work_id','event_id','rights_event_id','metadata','created'} or key!=identity(p['id']):raise ValueError('Invalid bibliographic record.')
        if event(p['event_id'])!=p['metadata']['sha256'] or event(p['rights_event_id'])!=p['metadata']['metadata_sha256']:raise ValueError('Bibliography/source checksum mismatch.')
        metadata(p['metadata']);text(p['work_id'],64)
    elif contract=='literary_analyses':
        if set(p)!={'event_id','sha256','method','start','end','characters','nonblank_lines','blank_line_blocks','word_form_tokens','word_form_candidates','script_sample','status','limits'} or key!=p['event_id'] or event(p['event_id'])!=p['sha256']:raise ValueError('Invalid literary observations.')
        if any(type(p[k]) is not int or p[k]<0 for k in ('start','end','characters','nonblank_lines','blank_line_blocks','word_form_tokens')) or p['end']<p['start']:raise ValueError('Invalid observation counts.')
        if not isinstance(p['word_form_candidates'],list) or len(p['word_form_candidates'])>32:raise ValueError('Invalid vocabulary preview.')
        for item in p['word_form_candidates']:
            if set(item)!={'form','count','quote','start','end'} or type(item['count']) is not int or item['count']<1 or not isinstance(item['quote'],str) or item['quote'].casefold()!=item['form'] or type(item['start']) is not int or type(item['end']) is not int or not p['start']<=item['start']<item['end']<=p['end'] or len(item['quote'])!=item['end']-item['start']:raise ValueError('Invalid form attestation.')
    elif contract=='literary_runs':
        if set(p)!={'event_id','method','offset','ordinal','status','error','updated'} or key!=p['event_id']:raise ValueError('Invalid processing checkpoint.')
        event(p['event_id'])
        if p['method']!=METHOD or p['status'] not in {'pending','partial','complete','deferred','failed'} or any(type(p[k]) is not int or p[k]<0 for k in ('offset','ordinal')):raise ValueError('Invalid processing state.')
        if not isinstance(p['error'],str) or len(p['error'])>2000:raise ValueError('Invalid processing error.')
    elif contract=='linguistic_records':
        if set(p)!={'id','language','kind','label','features','attestations','status','uncertainty','method','created'} or key!=identity(p['id']):raise ValueError('Invalid linguistic interpretation.')
        language_id(p['language']);text(p['label'],500);text(p['uncertainty'],2000);text(p['method'],1000)
        if p['kind'] not in NODE_KINDS or p['status'] not in {'pending','approved-interpretation','rejected'}:raise ValueError('Unsupported linguistic kind/status.')
        if not isinstance(p['features'],dict) or len(canonical(p['features']).encode())>16000:raise ValueError('Features exceed record budget.')
        if not isinstance(p['attestations'],list) or not 1<=len(p['attestations'])<=16:raise ValueError('Source attestations required.')
        for a in p['attestations']:
            if not isinstance(a,dict) or set(a)!={'event_id','start','end','quote','sha256'}:raise ValueError('Malformed attestation.')
            if event(a['event_id'])!=a['sha256'] or type(a['start']) is not int or type(a['end']) is not int or not 0<=a['start']<a['end'] or a['end']-a['start']>4000 or not isinstance(a['quote'],str) or len(a['quote'])!=a['end']-a['start']:raise ValueError('Invalid attestation span/hash.')
    elif contract=='linguistic_links':
        if set(p)!={'id','left','right','relation','reason','uncertainty','created'} or key!=identity(p['id']) or p['relation'] not in RELATIONS:raise ValueError('Invalid linguistic relationship.')
        for field in ('left','right'):
            identity(p[field])
            target_contract='literary_editions' if p['relation'] in {'translation-of','edition-of','volume-of'} else 'linguistic_records'
            if not db.execute("SELECT 1 FROM persistent_records WHERE contract=? AND record_key=?",(target_contract,p[field])).fetchone():raise ValueError('Linguistic target missing.')
        if p['left']==p['right']:raise ValueError('Distinct relationship targets required.')
        text(p['reason'],2000);text(p['uncertainty'],2000)

def metadata(p):
    fields={'provider_id','title','authors','language','edition','publication_date','digital_release','translators','subjects','genre','source_url','sha256','bytes','metadata_sha256','rights','acquired','print_edition_note','transport'}
    if not isinstance(p,dict) or set(p)!=fields:raise ValueError('Unknown/missing bibliography fields.')
    for field in ('provider_id','title','edition','source_url','acquired','print_edition_note','transport'):text(p[field],2000)
    if not isinstance(p['subjects'],str) or len(p['subjects'])>2000:raise ValueError('Subject metadata must be bounded text; blank means unknown.')
    language_id(p['language'])
    for field in ('authors','translators'):
        if not isinstance(p[field],list) or len(p[field])>50 or any(not isinstance(v,str) or not v.strip() or len(v)>500 for v in p[field]):raise ValueError('Invalid author/translator metadata.')
    if not p['authors']:raise ValueError('Author or explicitly anonymous attribution required.')
    for field in ('publication_date','digital_release'):
        if p[field] is not None and (not isinstance(p[field],str) or len(p[field])>100):raise ValueError('Unknown dates must remain null.')
    if p['genre'] not in {'poetry','prose','drama','technical','mixed'} or type(p['bytes']) is not int or p['bytes']<1:raise ValueError('Invalid source descriptor.')
    for field in ('sha256','metadata_sha256'):
        if not isinstance(p[field],str) or not DIGEST.fullmatch(p[field]):raise ValueError('Invalid package checksum.')
    rights=p['rights']
    if not isinstance(rights,dict) or set(rights)!={'status','jurisdiction','basis','evidence_url','license_url'}:raise ValueError('Explicit rights evidence required.')
    for value in rights.values():text(value,2000)
    if rights['status'] not in {'provider-unrestricted-us','cc0','user-owned'}:raise ValueError('Uncertain/restricted rights rejected.')
    if rights['status']=='provider-unrestricted-us' and (rights['jurisdiction']!='US' or not re.fullmatch('pg:[0-9]+',p['provider_id'])):raise ValueError('PG rights are U.S.-only and edition-specific.')
    if not p['source_url'].startswith(('https://','urn:')):raise ValueError('Source reference must be explicit; it is never fetched at runtime.')
    return p

def pg_license_span(original):
    heading=re.search(r'(?im)^[ \t]*(?:THE[ \t]+)?FULL[ \t]+PROJECT[ \t]+GUTENBERG(?:-TM|™)?[ \t]+LICENSE[ \t]*\r?$',original)
    if heading is None:raise ValueError('Complete attached license heading not found; original needs review.')
    license=original[heading.start():]
    if not all(marker in license for marker in ('1.A.','1.E.1.','1.F.')) or 'section 5' not in license.casefold():raise ValueError('Attached license appears incomplete; original needs review.')
    return heading.start(),len(original)

def verify_rights(entry,raw,evidence):
    if entry['rights']['status']=='provider-unrestricted-us':
        import xml.etree.ElementTree as ET
        if b'<!DOCTYPE' in evidence.upper() or b'<!ENTITY' in evidence.upper():raise ValueError('DTD/entities forbidden.')
        try:node=ET.fromstring(evidence)
        except ET.ParseError as error:raise ValueError('Malformed rights XML.') from error
        ns={'d':'http://purl.org/dc/terms/','p':'http://www.gutenberg.org/2009/pgterms/'}
        rights=[n.text or '' for n in node.findall('.//d:rights',ns)]
        ebook=node.find('.//p:ebook',ns)
        expected='ebooks/'+entry['provider_id'].split(':')[1]
        if ebook is None or ebook.get('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about')!=expected or not any('public domain in the usa' in r.lower() for r in rights):raise ValueError('Rights metadata does not identify this unrestricted edition.')
        original=raw.decode('utf-8');start=re.search(r'\*\*\*\s*START OF (?:THE |THIS )?PROJECT GUTENBERG',original,re.I)
        if not re.search(r'END OF (?:THE |THIS )?PROJECT GUTENBERG',original,re.I):raise ValueError('Incomplete book marker; source rejected.')
        pg_license_span(original)
        if not start or re.search(r'copyright(?:ed|\s*(?:\(c\)|[0-9]))|permission of|copyright holder',original[:start.start()],re.I) or 'FULL PROJECT GUTENBERG LICENSE' not in original.upper():raise ValueError('Missing license or special copyright notice requires separate review.')
    elif not evidence.strip():raise ValueError('Rights evidence is empty.')

class Library:
    def __init__(self,memory):self.memory=memory;self.db=memory.db
    def editions(self,query='',*,language=None,author=None,subject=None,since=None,until=None,after=0,limit=30):
        page(after,limit)
        if not isinstance(query,str) or len(query)>512:raise ValueError('Invalid library query.')
        conditions=["contract='literary_editions'",'rowid>?'];parameters=[after]
        for path,value in [('title',query),('authors',author),('subjects',subject)]:
            if value:
                text(value,512);conditions.append("instr(lower(json_extract(payload,'$.metadata."+path+"')),lower(?))>0");parameters.append(value)
        if language:conditions.append("json_extract(payload,'$.metadata.language')=?");parameters.append(language_id(language))
        for value,operator in ((since,'>='),(until,'<=')):
            if value:
                if not isinstance(value,str) or not re.fullmatch(r'\d{4}(?:-\d{2}(?:-\d{2})?)?',value):raise ValueError('Publication filter must be YYYY or ISO date; unknown dates are excluded.')
                conditions.append("json_extract(payload,'$.metadata.publication_date')"+operator+'?');parameters.append(value)
        rows=self.db.execute('SELECT rowid AS cursor,payload FROM persistent_records WHERE '+' AND '.join(conditions)+' ORDER BY rowid LIMIT ?',parameters+[limit]).fetchall()
        return {'items':[{**json.loads(r['payload']),'cursor':r['cursor']} for r in rows],'next_cursor':rows[-1]['cursor'] if rows else after}
    def edition(self,edition_id):return latest(self.memory,'literary_editions',identity(edition_id))
    @write_operation
    def import_entry(self,root,entry,*,approved=False):
        if approved is not True:raise PermissionError('Explicit offline package/rights approval required.')
        metadata(entry);root=safe_path(root);digest=entry['sha256']
        from vector_core.intake import read_file
        # Verify before acknowledging/archiving the work. Larger originals use normal streamed intake.
        if entry['bytes']>self.memory.config.max_source_bytes:raise ValueError('Package text exceeds bounded extraction budget; preserve separately using streamed original intake.')
        raw=read_file(root/'objects'/digest,entry['bytes'])
        evidence=read_file(root/'objects'/entry['metadata_sha256'],1024*1024)
        if len(raw)!=entry['bytes'] or hashlib.sha256(raw).hexdigest()!=digest or hashlib.sha256(evidence).hexdigest()!=entry['metadata_sha256']:raise ValueError('Package source/evidence checksum mismatch.')
        raw.decode('utf-8');verify_rights(entry,raw,evidence)
        key=hashlib.sha256((entry['provider_id']+':'+digest).encode()).hexdigest()[:32]
        if self.db.execute("SELECT 1 FROM persistent_records WHERE contract='literary_editions' AND record_key=?",(key,)).fetchone():return {**self.edition(key),'already_imported':True}
        rights=self.memory.ingest_file(root/'objects'/entry['metadata_sha256'],name='Rights metadata: '+entry['provider_id'],media_type='application/rdf+xml')
        original=self.memory.ingest_file(root/'objects'/digest,name=entry['title'][:512],media_type='text/plain',metadata={'resource_type':'literary-work','language':entry['language'],'provider_id':entry['provider_id']})
        work_id=hashlib.sha256(canonical([entry['authors'],' '.join(entry['title'].casefold().split())]).encode()).hexdigest()
        record={'id':key,'work_id':work_id,'event_id':original['event_id'],'rights_event_id':rights['event_id'],'metadata':entry,'created':now()}
        append(self.memory,'literary_editions',key,record,new=True)
        append(self.memory,'literary_runs',original['event_id'],{'event_id':original['event_id'],'method':METHOD,'offset':0,'ordinal':0,'status':'pending','error':'','updated':now()})
        return record
    def import_pack(self,root,*,offset=0,limit=4,approved=False,fingerprint=None):
        if approved is not True:raise PermissionError('Explicit package import approval required.')
        page(offset,limit);root=safe_path(root);items=[]
        with input_file(root/'manifest.ndjson') as stream:
            before=os.fstat(stream.fileno());header=stream.readline(32769)
            if len(header)>32768:raise ValueError('Package header too large.')
            current_fingerprint=[before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns,hashlib.sha256(header).hexdigest()]
            if offset and fingerprint!=current_fingerprint:raise ValueError('Manifest changed or resume identity missing; restart at zero to reuse verified editions safely.')
            parsed=json.loads(header,object_pairs_hook=unique)
            if not isinstance(parsed,dict) or parsed.get('format')!='vector-literary-pack-v1':raise ValueError('Unsupported offline package format.')
            if offset:
                if offset<len(header) or offset>before.st_size:raise ValueError('Invalid manifest cursor.')
                stream.seek(offset-1)
                if stream.read(1)!=b'\n':raise ValueError('Cursor must be a complete manifest boundary.')
            while len(items)<limit:
                line=stream.readline(32769)
                if not line:break
                if len(line)>32768 or not line.endswith(b'\n'):raise ValueError('Manifest record exceeds framing budget.')
                entry=json.loads(line,object_pairs_hook=unique);items.append(self.import_entry(root,entry,approved=True))
            cursor=stream.tell();complete=not bool(stream.read(1));after=os.fstat(stream.fileno())
            if (before.st_size,before.st_mtime_ns,before.st_ctime_ns)!=(after.st_size,after.st_mtime_ns,after.st_ctime_ns):raise ValueError('Manifest changed during import; committed originals remain.')
        return {'items':items,'next_cursor':cursor,'fingerprint':current_fingerprint,'complete':complete,'originals_preserved':True}
    @write_operation
    def process(self,event_id,*,limit=500,deadline_seconds=5,rebuild=False):
        if type(limit) is not int or not 1<=limit<=1000:raise ValueError('Processing batch must contain 1–1000 units.')
        if type(deadline_seconds) not in (int,float) or not 0<deadline_seconds<=30:raise ValueError('Invalid processing deadline.')
        identity(event_id);event=self.memory.event(event_id)
        edition=self.db.execute("SELECT payload FROM persistent_records WHERE contract='literary_editions' AND json_extract(payload,'$.event_id')=?",(event_id,)).fetchone()
        if not edition:raise ValueError('Not a registered edition.')
        try:prior=latest(self.memory,'literary_runs',event_id)
        except ValueError:prior={'offset':0,'ordinal':0,'status':'pending'}
        if prior['status']=='complete' and not rebuild and self.db.execute("SELECT 1 FROM persistent_records WHERE contract='literary_analyses' AND record_key=?",(event_id,)).fetchone():return {**prior,'unchanged_skipped':True}
        if event['byte_count']>self.memory.config.max_source_bytes:return append(self.memory,'literary_runs',event_id,{'event_id':event_id,'method':METHOD,'offset':0,'ordinal':0,'status':'deferred','error':'Original exceeds text extraction budget; retained unchanged.','updated':now()})
        raw=self.memory.original(event_id);original=raw.decode('utf-8');offset=0 if rebuild else prior['offset'];ordinal=0 if rebuild else prior['ordinal'];tick=time.monotonic();count=0
        body_start=0;body_end=len(original)
        if json.loads(edition[0])['metadata']['rights']['status']=='provider-unrestricted-us':
            begin=re.search(r'^\*\*\*\s*START OF.*$',original,re.I|re.M);finish=re.search(r'^\*\*\*\s*END OF.*$',original,re.I|re.M)
            if not begin or not finish:raise ValueError('Missing edition body boundaries.')
            body_start=original.find('\n',begin.start())+1;offset=max(offset,body_start);body_end=finish.start()
        if not self.db.execute("SELECT 1 FROM persistence_contracts WHERE name='literary_analyses'").fetchone():
            from vector_core.persistence import register
            register(self.memory,'literary_analyses','Versioned literal source-body observations and attested form candidates')
        self.db.execute('BEGIN IMMEDIATE')
        try:
            if rebuild:
                for row in self.db.execute('SELECT rowid,start_char,end_char FROM literary_units WHERE event_id=?',(event_id,)).fetchall():
                    self.db.execute("INSERT INTO literary_search(literary_search,rowid,text) VALUES ('delete',?,?)",(row['rowid'],original[row['start_char']:row['end_char']]))
                self.db.execute('DELETE FROM literary_units WHERE event_id=?',(event_id,))
            while offset<body_end and count<limit and time.monotonic()-tick<deadline_seconds:
                # Literal blank-line units preserve original CRLF, poetic lines and punctuation.
                blank=re.search(r'(?:\r?\n)[ \t]*(?:\r?\n)',original[offset:min(body_end,offset+4002)])
                end=offset+blank.start() if blank else min(body_end,offset+2000)
                if end==offset:offset+=blank.end();continue
                continuation=end>offset+2000 or (not blank and end<body_end)
                end=min(end,offset+2000)
                passage=original[offset:end]
                kind='stanza' if json.loads(edition[0])['metadata']['genre']=='poetry' else 'paragraph'
                if continuation:kind+='-continuation'
                if re.match(r'\s*(CHAPTER|BOOK|CANTO|SECTION)\s+[IVXLCDM\d]+\b',passage):kind='section-heading-candidate'
                digest=hashlib.sha256(passage.encode()).hexdigest();unit=hashlib.sha256(canonical([event_id,METHOD,ordinal,offset,end,digest]).encode()).hexdigest()
                self.db.execute('INSERT INTO literary_units VALUES (?,?,?,?,?,?,?,?)',(unit,event_id,ordinal,kind,offset,end,digest,METHOD));rowid=self.db.execute('SELECT last_insert_rowid()').fetchone()[0]
                self.db.execute('INSERT INTO literary_search(rowid,text) VALUES (?,?)',(rowid,passage))
                ordinal+=1;count+=1;offset=end
            record={'event_id':event_id,'method':METHOD,'offset':offset,'ordinal':ordinal,'status':'complete' if offset>=body_end else 'partial','error':'','updated':now()}
            if record['status']=='complete':
                from vector_core.literary_analysis import summarize_body
                _insert(self.memory,'literary_analyses',event_id,summarize_body(original,event_id,event['sha256'],body_start,body_end))
            _insert(self.memory,'literary_runs',event_id,record);self.db.commit()
        except BaseException as error:
            self.db.rollback()
            if isinstance(error,Exception):
                append(self.memory,'literary_runs',event_id,{'event_id':event_id,'method':METHOD,'offset':prior['offset'],'ordinal':prior['ordinal'],'status':'failed','error':str(error)[:2000],'updated':now()})
            raise
        return {**record,'units_committed':count}
    def processing(self,after=0,limit=30):
        page(after,limit)
        rows=self.db.execute("SELECT rowid AS cursor,payload FROM persistent_records r WHERE contract='literary_runs' AND rowid>? AND rowid=(SELECT max(rowid) FROM persistent_records WHERE contract=r.contract AND record_key=r.record_key) ORDER BY rowid LIMIT ?",(after,limit)).fetchall()
        return {'items':[{**json.loads(r['payload']),'cursor':r['cursor']} for r in rows],'next_cursor':rows[-1]['cursor'] if rows else after}
    def passage(self,unit_id):
        if not isinstance(unit_id,str) or not DIGEST.fullmatch(unit_id):raise ValueError('Invalid passage identifier.')
        row=self.db.execute('SELECT u.*,e.source_id,e.sha256,e.occurred,e.submission_name AS name FROM literary_units u JOIN events e ON e.id=u.event_id WHERE u.id=?',(unit_id,)).fetchone()
        if not row:raise ValueError('Passage not found.')
        result=dict(row);quote=self.memory.read_text_span(result['event_id'],result['start_char'],result['end_char'])
        if hashlib.sha256(quote.encode()).hexdigest()!=result['digest']:raise ValueError('Corrupt derived passage; rebuild before use.')
        edition=self.db.execute("SELECT record_key,payload FROM persistent_records WHERE contract='literary_editions' AND json_extract(payload,'$.event_id')=? LIMIT 1",(result['event_id'],)).fetchone()
        if edition:
            m=json.loads(edition['payload'])['metadata'];result.update(edition_id=edition['record_key'],language=m['language'],rights_notice=PG_NOTICE if m['rights']['status']=='provider-unrestricted-us' else m['rights']['basis'],rights_status=m['rights']['status'])
        result.update(start=result['start_char'],end=result['end_char'],quote=quote,excerpt=quote)
        return result
    def search(self,query,*,language=None,event_id=None,limit=20):
        page(0,limit)
        if not isinstance(query,str) or len(query)>512:raise ValueError('Invalid passage query.')
        terms=re.findall(r'[^\W_]+',query)
        if not terms or len(terms)>16:raise ValueError('Use 1–16 literal terms.')
        conditions=['literary_search MATCH ?'];parameters=[' AND '.join('"'+t+'"' for t in terms)]
        if event_id:conditions.append('u.event_id=?');parameters.append(identity(event_id))
        if language:
            # IDs are validated text; remove column affinity to use records_event.
            conditions.append("EXISTS (SELECT 1 FROM persistent_records r WHERE r.contract='literary_editions' AND json_extract(r.payload,'$.event_id')=+u.event_id AND json_extract(r.payload,'$.metadata.language')=?)");parameters.append(language_id(language))
        rows=self.db.execute('SELECT u.id,bm25(literary_search) AS rank FROM literary_units u JOIN literary_search ON literary_search.rowid=u.rowid WHERE '+' AND '.join(conditions)+' ORDER BY rank,u.event_id,u.ordinal LIMIT ?',parameters+[limit]).fetchall()
        results=[]
        for row in rows:
            item=self.passage(row['id']);item['rank']=row['rank'];excerpt=item['quote'];match=re.search('|'.join(re.escape(t) for t in terms),excerpt,re.I);left=max(0,match.start()-120) if match else 0
            item.update(start=item['start']+left,end=item['start']+min(len(excerpt),left+500),excerpt=excerpt[left:left+500]);results.append(item)
        return results
    def annotate(self,language,kind,label,features,attestations,*,uncertainty,record_id=None,revision=None,approved=False):
        if approved is not True:raise PermissionError('Explicit interpretation submission required.')
        for a in attestations:
            if self.memory.read_text_span(a['event_id'],a['start'],a['end'])!=a['quote']:raise ValueError('Fabricated linguistic attestation.')
        p={'id':record_id or uuid4().hex,'language':language,'kind':kind,'label':label,'features':features,'attestations':attestations,'status':'pending','uncertainty':uncertainty,'method':'explicit source-linked interpretation; not verified fact','created':now()}
        if record_id and revision is None:raise ValueError('Expected revision required.')
        return append(self.memory,'linguistic_records',p['id'],p,expected=revision,new=record_id is None)
    def review(self,record_id,revision,*,accept,approved=False):
        if approved is not True or type(accept) is not bool:raise PermissionError('Explicit human review required.')
        p=latest(self.memory,'linguistic_records',identity(record_id));p.pop('revision')
        for a in p['attestations']:
            if self.memory.read_text_span(a['event_id'],a['start'],a['end'])!=a['quote']:raise ValueError('Invalid attestation.')
        p['status']='approved-interpretation' if accept else 'rejected'
        return append(self.memory,'linguistic_records',record_id,p,expected=identity(revision))
    def relate(self,left,right,relation,reason,uncertainty,*,approved=False):
        if approved is not True:raise PermissionError('Explicit relationship approval required.')
        return append(self.memory,'linguistic_links',key:=uuid4().hex,{'id':key,'left':left,'right':right,'relation':relation,'reason':reason,'uncertainty':uncertainty,'created':now()},new=True)
    def concepts(self,query,language=None,after=0,limit=30):
        page(after,limit);text(query,512);conditions=["contract='linguistic_records'",'rowid>?',"instr(lower(json_extract(payload,'$.label')),lower(?))>0","rowid=(SELECT max(rowid) FROM persistent_records WHERE contract=r.contract AND record_key=r.record_key)"];parameters=[after,query]
        if language:conditions.append("json_extract(payload,'$.language')=?");parameters.append(language_id(language))
        rows=self.db.execute('SELECT rowid AS cursor,id,payload FROM persistent_records r WHERE '+' AND '.join(conditions)+' ORDER BY rowid LIMIT ?',parameters+[limit]).fetchall()
        items=[]
        for row in rows:
            record=json.loads(row['payload'])
            for a in record['attestations']:
                if self.memory.read_text_span(a['event_id'],a['start'],a['end'])!=a['quote']:raise ValueError('Invalid linguistic evidence.')
            relations=self.db.execute("SELECT payload FROM persistent_records WHERE contract='linguistic_links' AND (json_extract(payload,'$.left')=? OR json_extract(payload,'$.right')=?) ORDER BY rowid LIMIT 20",(record['id'],record['id'])).fetchall()
            items.append({**record,'revision':row['id'],'cursor':row['cursor'],'relationships':[json.loads(r[0]) for r in relations]})
        return {'items':items,'next_cursor':rows[-1]['cursor'] if rows else after}
    @write_operation
    def reset_index(self,*,approved=False):
        if approved is not True:raise PermissionError('Explicit derived-index rebuild approval required.')
        self.db.execute('BEGIN IMMEDIATE');count=0
        try:
            self.db.execute("INSERT INTO literary_search(literary_search) VALUES ('delete-all')")
            self.db.execute('DELETE FROM literary_units')
            for row in self.db.execute("SELECT json_extract(payload,'$.event_id') FROM persistent_records WHERE contract='literary_editions'"):
                _insert(self.memory,'literary_runs',row[0],{'event_id':row[0],'method':METHOD,'offset':0,'ordinal':0,'status':'pending','error':'','updated':now()});count+=1
            self.db.commit()
        except BaseException:self.db.rollback();raise
        return {'editions_queued':count,'originals_modified':False,'interpretations_modified':False,'next':'Process queued editions to rebuild derived postings.'}
    def stats(self):
        rows=self.db.execute("SELECT count(*) AS editions,count(DISTINCT json_extract(payload,'$.work_id')) AS unused FROM persistent_records WHERE contract='literary_editions'").fetchone()
        count=self.db.execute("SELECT count(DISTINCT json_extract(payload,'$.work_id')),count(DISTINCT json_extract(payload,'$.metadata.language')) FROM persistent_records WHERE contract='literary_editions'").fetchone()
        authors=self.db.execute("SELECT count(DISTINCT a.value) FROM persistent_records r,json_each(r.payload,'$.metadata.authors') a WHERE r.contract='literary_editions'").fetchone()[0]
        translations=self.db.execute("SELECT count(*) FROM persistent_records WHERE contract='literary_editions' AND json_array_length(payload,'$.metadata.translators')>0").fetchone()[0]
        return {'editions':rows['editions'],'conservative_work_groups':count[0],'authors':authors,'languages':count[1],'explicit_translated_editions':translations,'passages':self.db.execute('SELECT count(*) FROM literary_units').fetchone()[0],'body_observations':self.db.execute("SELECT count(DISTINCT record_key) FROM persistent_records WHERE contract='literary_analyses'").fetchone()[0],'qualified_language_proficiency':0}
