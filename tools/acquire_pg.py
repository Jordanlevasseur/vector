#!/usr/bin/env python3
"""DEVELOPMENT ONLY. Never imported/called by VECTOR. Explicit PG partial mirror.
Use only after reviewing provider policies and selecting U.S. jurisdiction.
No external runtime service/permissions are added. No website crawling.
"""
import argparse,csv,gzip,hashlib,json,re,subprocess,time
from pathlib import Path
import xml.etree.ElementTree as ET

NS={'dcterms':'http://purl.org/dc/terms/','pgterms':'http://www.gutenberg.org/2009/pgterms/','rdf':'http://www.w3.org/1999/02/22-rdf-syntax-ns#','dcam':'http://purl.org/dc/dcam/','marcrel':'http://id.loc.gov/vocabulary/relators/'}
def read_metadata(path):
 raw=path.read_bytes()
 if len(raw)>1024*1024 or b'<!DOCTYPE' in raw.upper() or b'<!ENTITY' in raw.upper():raise ValueError('Unsafe metadata XML')
 node=ET.fromstring(raw)
 def values(xpath):return [v.text for v in node.findall(xpath,NS) if v.text]
 rights=values('.//dcterms:rights')
 if not any('public domain in the usa' in r.lower() for r in rights):raise ValueError('Not explicitly unrestricted in the U.S.')
 return {'rights':rights,'translators':values('.//marcrel:trl//pgterms:name'),'authors':values('.//dcterms:creator//pgterms:name')}

def select(catalog,target=1500):
 with gzip.open(catalog,'rt',encoding='utf-8-sig') as stream:rows=list(csv.DictReader(stream))
 quotas={'en':800,'fr':100,'de':100,'es':80,'it':60,'pt':40,'nl':40,'ru':30,'la':25,'el':20,'he':3,'ar':5,'zh':25,'ja':5,'fi':20,'sv':20,'da':15,'no':10,'pl':10,'hu':10}
 chosen=[];keys=set();authors={}
 for language,quota in quotas.items():
  found=0
  # Catalog ordering favors foundational older accessions; selected subjects are explicit.
  for row in rows:
   if row['Type']!='Text' or row['Language']!=language or not row['Authors']:continue
   title=row['Title'];author=row['Authors']
   if re.search(r'\b(vol(?:ume)?s?\.?|magazine|journal|periodical|catalogue|index|encyclop|dictionary|collected works|complete works)\b',title,re.I):continue
   if re.search(r'\b(part|tome)\s+[IVX\d]',title,re.I):continue
   if len(title)>1600 or len(author)>1600:continue
   if not re.search(r'fiction|poetry|philosoph|literature|history|science|essays|speeches|classical|religion|drama|language',row['Subjects']+' '+row['Bookshelves'],re.I):continue
   key=re.sub(r'\W+',' ',author+' '+title).casefold()
   if key in keys or authors.get(author,0)>=8:continue
   chosen.append(row);keys.add(key);authors[author]=authors.get(author,0)+1;found+=1
   if found>=quota:break
 return chosen[:target]

def rsync(root,names,remote,mode):
 if any(not re.fullmatch(r'\d+/pg\d+\.(rdf|txt)',name) for name in names):raise ValueError('Unexpected provider path')
 listing=root/(mode+'-files.txt');listing.write_text(''.join(n+'\n' for n in names))
 common=['/usr/bin/rsync','-r','--relative','--no-links','--no-perms','--ignore-existing','--timeout=30','--contimeout=20','--bwlimit=2048','--max-size='+('1m' if mode=='metadata' else '8m'),'--files-from='+str(listing)]
 if mode=='books':
  preview=subprocess.run(common+['--list-only',remote,str(root/'mirror')+'/'],capture_output=True,text=True,timeout=120)
  (root/'books-size-preview.txt').write_text(preview.stdout+preview.stderr)
  if preview.returncode not in (0,23,24):raise RuntimeError('Cannot verify remote transfer sizes: '+str(preview.returncode)+' '+preview.stderr[:1000])
  sizes={}
  for line in preview.stdout.splitlines():
   match=re.match(r'^-\S+\s+([\d,]+)\s+\S+\s+\S+\s+(\d+/pg\d+\.txt)$',line)
   if match:sizes[match[2]]=int(match[1].replace(',',''))
  remaining=480*1024*1024-sum(p.stat().st_size for p in (root/'mirror').rglob('*') if p.is_file());chosen=[]
  for name in names:
   size=sizes.get(name,0)
   if (root/'mirror'/name).is_file():chosen.append(name);continue
   if 0<size<=8*1024*1024 and size<=remaining:chosen.append(name);remaining-=size
  if not chosen:raise RuntimeError('No bounded provider transfer could be planned')
  listing.write_text(''.join(name+'\n' for name in chosen))
  (root/'books-budget.json').write_text(json.dumps({'planned_files':len(chosen),'planned_bytes':sum(sizes[n] for n in chosen),'network_cap_bytes':512*1024*1024}))
 with (root/(mode+'.log')).open('w') as output:
  process=subprocess.Popen(common+[remote,str(root/'mirror')+'/'],stdout=output,stderr=subprocess.STDOUT)
  started=time.monotonic()
  try:
   while process.poll() is None:
    if time.monotonic()-started>1800:raise TimeoutError('Acquisition deadline')
    if sum(p.stat().st_size for p in (root/'mirror').rglob('*') if p.is_file())>512*1024*1024:raise RuntimeError('Acquisition byte cap exceeded; stopped')
    time.sleep(1)
  except BaseException:process.terminate();process.wait(timeout=10);raise
  if process.returncode not in (0,23,24):raise RuntimeError('rsync failed: '+str(process.returncode))

def main():
 p=argparse.ArgumentParser();p.add_argument('directory');p.add_argument('--catalog',required=True);p.add_argument('--phase',choices=['metadata','books','package'],required=True);p.add_argument('--target',type=int,default=1000);p.add_argument('--pack-name',default='pack')
 args=p.parse_args();root=Path(args.directory).absolute();root.mkdir(parents=True,exist_ok=True);(root/'mirror').mkdir(exist_ok=True)
 if args.phase=='metadata':
  rows=select(args.catalog);(root/'selected.json').write_text(json.dumps(rows,ensure_ascii=False))
  rsync(root,[r['Text#']+'/pg'+r['Text#']+'.rdf' for r in rows],'rsync://gutenberg.pglaf.org/gutenberg-epub/','metadata');return
 rows=json.loads((root/'selected.json').read_text());eligible=[]
 for row in rows:
  try:metadata=read_metadata(root/'mirror'/row['Text#']/('pg'+row['Text#']+'.rdf'))
  except (ValueError,OSError,ET.ParseError):continue
  eligible.append((row,metadata))
 if args.phase=='books':
  # Explicit known generated UTF-8 names only; no remote directory enumeration/crawl.
  rsync(root,[r['Text#']+'/pg'+r['Text#']+'.txt' for r,m in eligible],'rsync://gutenberg.pglaf.org/gutenberg-epub/','books');return
 if not re.fullmatch('[a-z0-9-]{1,64}',args.pack_name):raise ValueError('Invalid package name')
 package=root/args.pack_name;package.mkdir(exist_ok=False);objects=package/'objects';objects.mkdir(exist_ok=True)
 successes=[];rejected=[];keys=set();size=0
 for row,metadata in eligible:
  number=row['Text#'];file=root/'mirror'/number/('pg'+number+'.txt')
  try:
   raw=file.read_bytes()
   if not 100<=len(raw)<=8*1024*1024:raise ValueError('Unsupported source size')
   text=raw.decode('utf-8');marker=re.search(r'\*\*\*\s*START OF (?:THE |THIS )?PROJECT GUTENBERG',text,re.I)
   if not marker or not re.search(r'END OF (?:THE |THIS )?PROJECT GUTENBERG',text,re.I):raise ValueError('Missing complete source/license markers')
   if re.search(r'copyright(?:ed|\s*(?:\(c\)|[0-9]))|permission of|copyright holder',text[:marker.start()],re.I):raise ValueError('Special copyright notice requires review')
   if 'FULL PROJECT GUTENBERG LICENSE' not in text.upper():raise ValueError('Attached license missing')
   key=re.sub(r'\W+',' ',row['Authors']+' '+row['Title']).casefold()
   if key in keys:continue
   digest=hashlib.sha256(raw).hexdigest();rdf=(root/'mirror'/number/('pg'+number+'.rdf')).read_bytes();rdfhash=hashlib.sha256(rdf).hexdigest()
   for data,d in ((raw,digest),(rdf,rdfhash)):
    dest=objects/d
    if not dest.exists():dest.write_bytes(data)
    elif dest.read_bytes()!=data:raise ValueError('Digest collision/corruption')
   record={'provider_id':'pg:'+number,'title':row['Title'],'authors':metadata['authors'] or [v.strip() for v in row['Authors'].split(';')],
    'language':row['Language'],'edition':'Project Gutenberg digital edition #'+number,'publication_date':None,'digital_release':row['Issued'],
    'translators':metadata['translators'],'subjects':row['Subjects'],'genre':'poetry' if re.search(r'poetry|poems|verse',row['Subjects'],re.I) else 'prose',
    'source_url':'https://www.gutenberg.org/ebooks/'+number,'sha256':digest,'bytes':len(raw),'metadata_sha256':rdfhash,
    'rights':{'status':'provider-unrestricted-us','jurisdiction':'US','basis':metadata['rights'][0],'evidence_url':'https://www.gutenberg.org/cache/epub/'+number+'/pg'+number+'.rdf','license_url':'https://www.gutenberg.org/policy/license.html'},
    'acquired':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'print_edition_note':'PG digital edition identified; original print edition/date not independently established.','transport':'provider-supported rsync mirror; checksums are not publisher signatures'}
   successes.append(record);keys.add(key);size+=len(raw)+len(rdf)
   if len(successes)>=args.target:break
  except (OSError,UnicodeError,ValueError) as error:rejected.append({'id':number,'error':str(error)})
 with (package/'manifest.ndjson').open('w') as manifest:
  manifest.write(json.dumps({'format':'vector-literary-pack-v1','jurisdiction':'US','provider':'Project Gutenberg','notice':'Rights are U.S.-only provider assertions; originals include the full license. No worldwide clearance claimed.'})+'\n')
  for record in successes:manifest.write(json.dumps(record,ensure_ascii=False)+'\n')
 (root/(args.pack_name+'-report.json')).write_text(json.dumps({'actual_editions':len(successes),'actual_bytes':size,'distinct_authors':len({a for r in successes for a in r['authors']}),'languages':sorted({r['language'] for r in successes}),'rejected':rejected,'package':str(package)},indent=2))
 print(json.dumps({'actual_editions':len(successes),'actual_bytes':size}))
if __name__=='__main__':main()
