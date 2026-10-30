import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from vector_core.config import Config
from vector_core.memory import Memory
from vector_core.literature import Library
from vector_core.languages import seed,identify
from vector_core.context import build_context
from vector_core.portable import export_vector,restore_vector

class LiteraryTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name);self.memory=Memory(Config.load(data_dir=str(self.root/'data')));self.addCleanup(self.memory.close);self.library=Library(self.memory)
 def fixture(self,body='First line\nSecond line\n\nThird stanza\n',language='en',number=1):
  # Authored test material, never counted as an acquired literary corpus.
  root=self.root/('pack'+str(number));(root/'objects').mkdir(parents=True,exist_ok=True);raw=body.encode();evidence=b'CC0 declaration for this independently authored synthetic test fixture.'
  digest=hashlib.sha256(raw).hexdigest();proof=hashlib.sha256(evidence).hexdigest();(root/'objects'/digest).write_bytes(raw);(root/'objects'/proof).write_bytes(evidence)
  entry={'provider_id':'fixture:'+str(number),'title':'Explicit test fixture '+str(number),'authors':['Test fixture author'],'language':language,'edition':'Authored fixture edition','publication_date':None,'digital_release':None,'translators':[],'subjects':'Fixture, not real acquired knowledge','genre':'poetry','source_url':'urn:vector:fixture:'+str(number),'sha256':digest,'bytes':len(raw),'metadata_sha256':proof,'rights':{'status':'cc0','jurisdiction':'test fixture','basis':'Author declaration','evidence_url':'urn:fixture:rights','license_url':'https://creativecommons.org/publicdomain/zero/1.0/'},'acquired':'2026-10-30T00:00:00Z','print_edition_note':'No print source; synthetic test fixture','transport':'Locally authored test data'}
  (root/'manifest.ndjson').write_text(json.dumps({'format':'vector-literary-pack-v1'})+'\n'+json.dumps(entry)+'\n');return root,entry
 def imported(self,body='First line\nSecond line\n\nThird stanza\n',language='en',number=1):
  root,entry=self.fixture(body,language,number);return self.library.import_entry(root,entry,approved=True)
 def process(self,event):
  while True:
   result=self.library.process(event,limit=2)
   if result['status']=='complete':return result
 def test_curriculum_is_explicit_extensible_and_not_proficiency(self):
  seed(self.memory);seed(self.memory)
  self.assertEqual(self.memory.db.execute("SELECT count(*) FROM persistent_records WHERE contract='languages'").fetchone()[0],43)
  self.assertIn('Hebr',identify('בְּרֵאשִׁית')['script_counts']);self.assertEqual(identify('中文')['language'],'und')
  self.assertEqual(self.library.stats()['qualified_language_proficiency'],0)
 def test_exact_poetry_structure_incremental_indexing_and_unchanged_skip(self):
  body='First line\r\nSecond line\r\n\r\nThird stanza\r\n';record=self.imported(body);event=record['event_id']
  self.process(event);self.assertEqual(self.memory.original(event),body.encode())
  results=self.library.search('Second line');self.assertEqual(results[0]['event_id'],event);passage=self.library.passage(results[0]['id'])
  self.assertIn('First line\r\nSecond line',passage['quote']);self.assertEqual(passage['quote'],self.memory.read_text_span(event,passage['start'],passage['end']))
  self.assertTrue(self.library.process(event)['unchanged_skipped'])
  from vector_core.literary_analysis import observe
  observed=observe(self.memory,event,0,len(body));self.assertEqual(observed['nonblank_lines'],3);self.assertEqual(observed['stanzas'],2);self.assertEqual(observed['lines'][1]['text'],'Second line')
 def test_rights_hash_unsafe_paths_and_unapproved_import_fail_closed(self):
  root,entry=self.fixture()
  with self.assertRaises(PermissionError):self.library.import_entry(root,entry)
  with self.assertRaises(ValueError):self.library.import_entry(root,{**entry,'rights':{**entry['rights'],'status':'unknown'}},approved=True)
  with self.assertRaises(ValueError):self.library.import_entry(root,{**entry,'sha256':'../escape'},approved=True)
  (root/'objects'/entry['sha256']).write_bytes(b'corrupt')
  with self.assertRaises(ValueError):self.library.import_entry(root,entry,approved=True)
  self.assertEqual(self.memory.db.execute('SELECT count(*) FROM events').fetchone()[0],0)
  target=self.root/'symlink';target.symlink_to(root,target_is_directory=True)
  with self.assertRaises(ValueError):self.library.import_pack(target,approved=True)
 def test_strict_manifest_framing_resume_and_idempotent_editions(self):
  root,entry=self.fixture();first=self.library.import_pack(root,limit=1,approved=True);self.assertTrue(first['complete'])
  again=self.library.import_pack(root,approved=True);self.assertTrue(again['items'][0]['already_imported']);self.assertEqual(self.library.stats()['editions'],1)
  with self.assertRaises(ValueError):self.library.import_pack(root,offset=2,approved=True)
  (root/'manifest.ndjson').write_text('{"format":"vector-literary-pack-v1","format":"vector-literary-pack-v1"}\n')
  with self.assertRaises(ValueError):self.library.import_pack(root,approved=True)
 def test_source_linked_interpretations_review_versions_and_cross_language_links(self):
  en=self.imported('The written form liberty occurs here.','en',1);la=self.imported('The written form libertas occurs here.','la-x-classic',2)
  self.process(en['event_id']);self.process(la['event_id']);nodes=[]
  for record,language,word in ((en,'en','liberty'),(la,'la-x-classic','libertas')):
   original=self.memory.original(record['event_id']).decode();start=original.index(word);a={'event_id':record['event_id'],'sha256':record['metadata']['sha256'],'start':start,'end':start+len(word),'quote':word}
   node=self.library.annotate(language,'sense',word,{'fixture_meaning':'Explicit controlled test interpretation; not acquired linguistic scholarship'},[a],uncertainty='Test interpretation only',approved=True)
   with self.assertRaises(PermissionError):self.library.review(node['id'],node['revision'],accept=True)
   nodes.append(self.library.review(node['id'],node['revision'],accept=True,approved=True))
  relation=self.library.relate(nodes[0]['id'],nodes[1]['id'],'approximate-translation','Explicit fixture correspondence','No independent translation competence claim',approved=True)
  built=build_context(self.memory,'liberty',budget_bytes=16000)['context']
  self.assertTrue({en['event_id'],la['event_id']}<={s['event_id'] for s in built['sources']});self.assertTrue(built['linguistic_records'])
  forged={**nodes[0]['attestations'][0],'quote':'FORGED!'}
  with self.assertRaises(ValueError):self.library.annotate('en','etymology','fabrication',{},[forged],uncertainty='Unknown',approved=True)
  self.assertNotIn('verified',nodes[0]['status']);self.assertEqual(relation['relation'],'approximate-translation')
 def test_context_uses_bounded_source_accurate_book_passages(self):
  record=self.imported(('Introduction. '*400)+'\n\nThe amber laboratory has 17 prisms.\n\n'+('Other chapter. '*400));self.process(record['event_id'])
  context=build_context(self.memory,'amber laboratory prisms',budget_bytes=4096)
  self.assertLessEqual(context['bytes'],4096);source=context['context']['sources'][0];self.assertIn('17 prisms',source['quote']);self.assertGreater(source['start'],500)
  self.assertEqual(source['quote'],self.memory.read_text_span(source['event_id'],source['start'],source['end']))
 def test_portable_restoration_all_linguistic_state_and_corruption_rejection(self):
  record=self.imported();self.process(record['event_id']);seed(self.memory)
  from vector_core.literary_analysis import propose_vocabulary
  proposed=propose_vocabulary(self.memory,record['event_id'],0,10,'en',approved=True);self.assertEqual(proposed['facts_created'],0)
  export_vector(self.memory,self.root/'archive');target=Config.load(data_dir=str(self.root/'restored'));restore_vector(target,self.root/'archive')
  with Memory(target) as memory:
   self.assertEqual(memory.original(record['event_id']),self.memory.original(record['event_id']));self.assertTrue(Library(memory).search('First line'));self.assertTrue(Library(memory).concepts('First')['items'])
  unit=self.library.search('First line')[0]['id'];self.memory.db.execute('UPDATE literary_units SET digest=? WHERE id=?',('0'*64,unit))
  with self.assertRaises(ValueError):self.library.passage(unit)
 def test_historical_layers_abstain_without_attested_morphology(self):
  from vector_core.literary_analysis import historical_frame
  for language in ('la-x-classic','grc','hbo'):
   result=historical_frame(language);self.assertFalse(result['qualified']);self.assertIn('literal_gloss',result['layers']);self.assertIn('scholarly_disagreement',result['layers'])
 def test_pg_metadata_dtd_and_special_rights_not_accepted(self):
  root,entry=self.fixture('*** START OF THE PROJECT GUTENBERG EBOOK fixture ***\ntext\n*** END OF THE PROJECT GUTENBERG EBOOK fixture ***\nFULL PROJECT GUTENBERG LICENSE')
  from vector_core.literature import verify_rights
  pg={**entry,'provider_id':'pg:999','rights':{**entry['rights'],'status':'provider-unrestricted-us','jurisdiction':'US'}}
  with self.assertRaises(ValueError):verify_rights(pg,(root/'objects'/entry['sha256']).read_bytes(),b'<!DOCTYPE x [<!ENTITY x "untrusted">]><x/>')

class LiteraryCrashTests(unittest.TestCase):
 def test_interrupted_processing_retains_original_and_no_half_committed_passage(self):
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder);source='''
import sys,os,json,hashlib
from pathlib import Path
from vector_core.security import activate
activate()
from vector_core.config import Config
from vector_core.memory import Memory,Submission
from vector_core.literature import Library
from vector_core.projects import append
import vector_core.literature as module
with Memory(Config.load(data_dir=sys.argv[1])) as memory:
 event=memory.ingest(Submission(b'One stanza\\n\\nAnother stanza','Explicit crash fixture'))
 proof=memory.ingest(Submission(b'User-owned fixture','Rights'))
 entry={'provider_id':'fixture:crash','title':'Fixture','authors':['Fixture'],'language':'en','edition':'Fixture','publication_date':None,'digital_release':None,'translators':[],'subjects':'Test','genre':'poetry','source_url':'urn:fixture','sha256':event['sha256'],'bytes':26,'metadata_sha256':proof['sha256'],'rights':{'status':'user-owned','jurisdiction':'fixture','basis':'User authored','evidence_url':'urn:fixture','license_url':'urn:fixture'},'acquired':'fixture','print_edition_note':'Fixture','transport':'local'}
 append(memory,'literary_editions','1'*32,{'id':'1'*32,'work_id':'fixture','event_id':event['event_id'],'rights_event_id':proof['event_id'],'metadata':entry,'created':'fixture'})
 module._insert=lambda *a,**k:os._exit(89)
 Library(memory).process(event['event_id'])
'''
   env={**os.environ,'PYTHONPATH':str(Path(__file__).resolve().parents[1]/'src')}
   result=subprocess.run([sys.executable,'-c',source,str(root/'data')],env=env,capture_output=True,text=True,timeout=20)
   self.assertEqual(result.returncode,89,result.stderr)
   with Memory(Config.load(data_dir=str(root/'data'))) as memory:
    self.assertEqual(memory.db.execute('SELECT count(*) FROM literary_units').fetchone()[0],0);self.assertEqual(memory.db.execute('SELECT count(*) FROM events').fetchone()[0],2);self.assertTrue(memory.verify()['passed'])
