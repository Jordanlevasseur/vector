import copy,hashlib,json,os,subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from vector_core.config import Config
from vector_core.memory import Memory
from vector_core.science import ScientificLibrary,key_for,metadata,provenance

def fixture(root,pages=None):
    (root/'objects').mkdir(parents=True)
    def store(raw,media='text/plain'):
        h=hashlib.sha256(raw).hexdigest();(root/'objects'/h).write_bytes(raw)
        return {'sha256':h,'bytes':len(raw),'media_type':media}
    original=store(b'%PDF Explicit unit-test preservation fixture, not an extracted publication','application/pdf')
    evidence=store(b'Explicit user-authored CC0 fixture rights evidence.')
    texts=pages or ['Energy relation: E = m c\u00b2. Specific heat has units J/(kg K).','Table fixture\nMaterial  Density\nWater  1000 kg/m\u00b3\nFIGURE NOT EXTRACTED.']
    parts=[]
    for i,t in enumerate(texts,1):
        d=store(t.encode());parts.append({'page':i,'sha256':d['sha256'],'bytes':d['bytes'],'locator':'PDF page '+str(i)})
    extraction={'format':'vector-scientific-text-v1','original_sha256':original['sha256'],'method':'explicit-unit-test-fixture','pages':parts,'features':{'equations':'Unverified linear text only','tables':'Unstructured text only','figures':'Not extracted; original retained','external_assets':'None','text_completeness':'All supplied fixture pages; not a real PDF extraction'}}
    x=store(json.dumps(extraction).encode(),'application/json')
    return {'provider_id':'fixture:science','title':'Explicit science fixture','authors':['Fixture author'],'language':'en','edition':'Unit-test edition','publication_date':'2001','revision_date':None,'subjects':['physics','materials'],'source_url':'urn:fixture:science','download_url':'urn:fixture:science','acquired':'fixture','original':original,'evidence':[evidence],'rights':{'license':'CC0-1.0','jurisdiction':'US','basis':'Explicit user-authored test material','attribution':'Fixture author','restrictions':[],'reviewed_uses':['preservation','text-indexing','source-linked-retrieval'],'future_training':'requires-separate-review','ai_retrieval_permitted':True},'medical':{'is_medical':False,'temporal_status':'not-medical'},'extraction_sha256':x['sha256']}

class ScientificLibraryTests(unittest.TestCase):
    def test_original_preservation_incremental_restart_and_no_literary_reprocessing(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);entry=fixture(root/'pack')
            with Memory(Config.load(data_dir=str(root/'data'))) as m:
                science=ScientificLibrary(m)
                with self.assertRaises(PermissionError):science.import_entry(root/'pack',entry)
                item=science.import_entry(root/'pack',entry,approved=True)
                self.assertEqual(m.original(item['original_event_id']),(root/'pack/objects'/entry['original']['sha256']).read_bytes())
                first=science.index(root/'pack',item['id'],limit=1,approved=True);self.assertEqual(first['status'],'partial')
            with Memory(Config.load(data_dir=str(root/'data'))) as m:
                science=ScientificLibrary(m);self.assertTrue(science.import_entry(root/'pack',entry,approved=True)['already_imported'])
                self.assertEqual(science.index(root/'pack',item['id'],limit=1,approved=True)['status'],'complete')
                count=m.db.execute('SELECT count(*) FROM events').fetchone()[0]
                self.assertEqual(science.index(root/'pack',item['id'],approved=True)['pages_committed'],0)
                self.assertEqual(m.db.execute('SELECT count(*) FROM events').fetchone()[0],count)
                self.assertEqual(m.db.execute('SELECT count(*) FROM literary_units').fetchone()[0],0)
                self.assertEqual(m.db.execute("SELECT count(*) FROM persistent_records WHERE contract='literary_editions'").fetchone()[0],0)
                self.assertTrue(m.verify()['passed'])
    def test_retrieval_is_derived_attributed_and_checks_original_manifest(self):
        from vector_core.retrieval import search
        from vector_core.context import build_context
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);entry=fixture(root/'pack')
            with Memory(Config.load(data_dir=str(root/'data'))) as m:
                lib=ScientificLibrary(m);e=lib.import_entry(root/'pack',entry,approved=True);lib.index(root/'pack',e['id'],approved=True)
                hits=search(m,'Specific heat');self.assertEqual(len(hits),1);hit=hits[0]
                self.assertEqual(m.read_text_span(hit['event_id'],hit['start'],hit['end']),hit['excerpt'])
                p=hit['scientific_provenance'];self.assertEqual(p['original_sha256'],entry['original']['sha256']);self.assertEqual(p['locator'],'PDF page 1');self.assertIn('Not extracted',p['extraction_limits']['figures'])
                ctx=build_context(m,'Specific heat',budget_bytes=8192);self.assertTrue(any('scientific_provenance' in s for s in ctx['context']['sources']))
                from vector_core.memory import Submission
                fake=m.ingest(Submission(b'forged page','Forged',metadata=m.event(hit['event_id'])['metadata'],parent_id=e['original_event_id']))
                with self.assertRaises(ValueError):provenance(m,fake['event_id'])
    def test_mathematics_uses_existing_originals_catalogue_and_source_links(self):
        from vector_core.resources import Resources
        from vector_core.retrieval import search
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);entry=fixture(root/'pack')
            entry['subjects']=['collection:Mathematics','Mathematical analysis','Graduate','Sobolev spaces']
            entry['rights']['license']='US-PUBLIC-DOMAIN'
            with Memory(Config.load(data_dir=str(root/'data'))) as m:
                lib=ScientificLibrary(m);item=lib.import_entry(root/'pack',entry,approved=True)
                lib.index(root/'pack',item['id'],approved=True)
                resources=Resources(m)
                try:
                    rows=resources.list('Sobolev',category='Mathematics')['items']
                    self.assertEqual([r['id'] for r in rows],[item['original_event_id']])
                    self.assertEqual(resources.detail(rows[0]['id'])['sha256'],entry['original']['sha256'])
                    group=resources.collection('Mathematics',approved=True)
                    resources.membership(group['id'],rows[0]['id'],approved=True)
                    self.assertEqual(resources.list(collection=group['id'])['total'],1)
                    hit=search(m,'Specific heat')[0]
                    self.assertEqual(hit['scientific_provenance']['original_event_id'],rows[0]['id'])
                    self.assertEqual(hit['scientific_provenance']['locator'],'PDF page 1')
                    self.assertIn('equations',hit['scientific_provenance']['extraction_limits'])
                finally:resources.close()

    def test_new_rights_identifiers_preserve_explicit_review_and_authorization(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);entry=fixture(root/'pack')
            for license in ('US-PUBLIC-DOMAIN','GFDL-1.2-no-invariants','GFDL-1.3-no-invariants'):
                candidate=copy.deepcopy(entry);candidate['rights']['license']=license
                self.assertEqual(metadata(candidate)['rights']['license'],license)
                with Memory(Config.load(data_dir=str(root/license))) as m:
                    with self.assertRaises(PermissionError):ScientificLibrary(m).import_entry(root/'pack',candidate)
                candidate['rights']['ai_retrieval_permitted']=False
                with self.assertRaises(PermissionError):metadata(candidate)
            for license in ('GFDL','GFDL-1.3','CC-BY-NC-4.0','CC-BY-ND-4.0','CC-BY-NC-SA-4.0'):
                candidate=copy.deepcopy(entry);candidate['rights']['license']=license
                with self.assertRaises(PermissionError):metadata(candidate)

    def test_noncommercial_ai_restrictions_and_missing_medical_dates_fail_closed(self):
        with tempfile.TemporaryDirectory() as folder:
            entry=fixture(Path(folder)/'pack')
            for change in ({'license':'CC-BY-NC-SA-4.0'},{'ai_retrieval_permitted':False},{'license':'unknown'}):
                bad=copy.deepcopy(entry);bad['rights'].update(change)
                with self.assertRaises((ValueError,PermissionError)):metadata(bad)
            bad=copy.deepcopy(entry);bad['medical']={'is_medical':True,'temporal_status':'historical'};bad['publication_date']=None
            with self.assertRaises(ValueError):metadata(bad)
            bad['publication_date']='1950';metadata(bad)
            bad['medical']['temporal_status']='current-guidance'
            with self.assertRaises(ValueError):metadata(bad)
    def test_mismatched_expected_streamed_original_never_acknowledges_an_event(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);p=root/'source';p.write_bytes(b'actual bytes')
            with Memory(Config.load(data_dir=str(root/'data'))) as m:
                with self.assertRaises(ValueError):m.ingest_file(p,expected_sha256='0'*64)
                self.assertEqual(m.db.execute('SELECT count(*) FROM events').fetchone()[0],0)
                self.assertTrue(m.verify()['passed'])
    def test_corrupt_rights_evidence_does_not_publish_the_original(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);entry=fixture(root/'pack');p=root/'pack/objects'/entry['evidence'][0]['sha256'];b=p.read_bytes();p.write_bytes(b'x'+b[1:])
            with Memory(Config.load(data_dir=str(root/'data'))) as m:
                with self.assertRaises(ValueError):ScientificLibrary(m).import_entry(root/'pack',entry,approved=True)
                self.assertEqual(m.db.execute('SELECT count(*) FROM events').fetchone()[0],0)
    def test_missing_corrupt_page_never_advances_checkpoint_or_claims_completion(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);entry=fixture(root/'pack')
            with Memory(Config.load(data_dir=str(root/'data'))) as m:
                lib=ScientificLibrary(m);e=lib.import_entry(root/'pack',entry,approved=True);lib.index(root/'pack',e['id'],limit=1,approved=True)
                manifest=json.loads((root/'pack/objects'/entry['extraction_sha256']).read_text());page=root/'pack/objects'/manifest['pages'][1]['sha256'];page.write_bytes(b'corrupt')
                with self.assertRaises(ValueError):lib.index(root/'pack',e['id'],approved=True)
                from vector_core.projects import latest
                self.assertEqual(latest(m,'scientific_runs',e['id'])['next_page'],1)
    def test_catalog_crash_window_reuses_verified_original_events(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);entry=fixture(root/'pack')
            with Memory(Config.load(data_dir=str(root/'data'))) as m:
                with patch('vector_core.science.append',side_effect=RuntimeError('simulated interruption before catalog')):
                    with self.assertRaises(RuntimeError):ScientificLibrary(m).import_entry(root/'pack',entry,approved=True)
                n=m.db.execute('SELECT count(*) FROM events').fetchone()[0]
                ScientificLibrary(m).import_entry(root/'pack',entry,approved=True)
                self.assertEqual(m.db.execute('SELECT count(*) FROM events').fetchone()[0],n)
    def test_actual_process_crash_after_page_commit_resumes_without_duplicates(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);entry=fixture(root/'pack');(root/'entry.json').write_text(json.dumps(entry))
            with Memory(Config.load(data_dir=str(root/'data'))) as m:ScientificLibrary(m).import_entry(root/'pack',entry,approved=True)
            code='''
import json,os,sys
from pathlib import Path
from vector_core.security import activate
activate()
from vector_core.memory import Memory
from vector_core.config import Config
from vector_core.science import ScientificLibrary,key_for
root=Path(sys.argv[1]);entry=json.loads((root/'entry.json').read_text())
with Memory(Config.load(data_dir=str(root/'data'))) as m:
 original=m.ingest_file
 def crash(*a,**k):
  result=original(*a,**k)
  if k.get('metadata',{}).get('role','').startswith('page-'):os._exit(89)
  return result
 m.ingest_file=crash
 ScientificLibrary(m).index(root/'pack',key_for(entry),approved=True)
'''
            env={**os.environ,'PYTHONPATH':str(Path(__file__).resolve().parents[1]/'src')}
            r=subprocess.run([sys.executable,'-B','-c',code,str(root)],env=env,capture_output=True,text=True,timeout=20);self.assertEqual(r.returncode,89,r.stderr)
            with Memory(Config.load(data_dir=str(root/'data'))) as m:
                result=ScientificLibrary(m).index(root/'pack',key_for(entry),approved=True);self.assertEqual(result['status'],'complete')
                self.assertEqual(m.db.execute("SELECT count(*) FROM events WHERE json_extract(metadata,'$.role') LIKE 'page-%'").fetchone()[0],2);self.assertTrue(m.verify()['passed'])
    def test_scientific_state_survives_verified_portable_restore(self):
        from vector_core.portable import export_vector,restore_vector
        from vector_core.retrieval import search
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);entry=fixture(root/'pack')
            with Memory(Config.load(data_dir=str(root/'data'))) as m:
                lib=ScientificLibrary(m);e=lib.import_entry(root/'pack',entry,approved=True);lib.index(root/'pack',e['id'],approved=True);export_vector(m,root/'export')
            restore_vector(Config.load(data_dir=str(root/'restored')),root/'export')
            with Memory(Config.load(data_dir=str(root/'restored'))) as m:
                self.assertEqual(len(ScientificLibrary(m).editions()['items']),1);self.assertTrue(search(m,'Specific heat')[0]['scientific_provenance'])
    def test_symlink_objects_and_unapproved_indexing_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);entry=fixture(root/'pack');target=root/'pack/objects'/entry['original']['sha256'];other=root/'other';target.rename(other);target.symlink_to(other)
            with Memory(Config.load(data_dir=str(root/'data'))) as m:
                lib=ScientificLibrary(m)
                with self.assertRaises(ValueError):lib.import_entry(root/'pack',entry,approved=True)
                with self.assertRaises(PermissionError):lib.index(root/'pack','0'*32)
    def test_manifest_resume_and_missing_page_checkpoint_are_fail_closed(self):
        from vector_core.projects import append
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);entry=fixture(root/'pack')
            manifest=root/'pack/manifest.ndjson';manifest.write_text(json.dumps({'format':'vector-scientific-pack-v1','jurisdiction':'US'})+'\n'+json.dumps(entry)+'\n')
            with Memory(Config.load(data_dir=str(root/'data'))) as m:
                lib=ScientificLibrary(m);r=lib.import_pack(root/'pack',approved=True)
                with self.assertRaises(ValueError):lib.import_pack(root/'pack',offset=1,approved=True)
                self.assertTrue(lib.import_pack(root/'pack',offset=1,manifest_sha256=r['manifest_sha256'],approved=True)['complete'])
                with self.assertRaises(ValueError):append(m,'scientific_runs',key_for(entry),{'id':key_for(entry),'manifest_sha256':entry['extraction_sha256'],'next_page':2,'total_pages':2,'status':'complete','updated':'fixture'})
                manifest.write_text('{"format":"bad","format":"vector-scientific-pack-v1"}\n')
                with self.assertRaises(ValueError):lib.import_pack(root/'pack',approved=True)
    def test_supported_cli_preserves_network_denial_and_requires_import_approval(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);entry=fixture(root/'pack');(root/'pack/manifest.ndjson').write_text(json.dumps({'format':'vector-scientific-pack-v1','jurisdiction':'US'})+'\n'+json.dumps(entry)+'\n')
            env={**os.environ,'PYTHONPATH':str(Path(__file__).resolve().parents[1]/'src')}
            cmd=[sys.executable,'-B','-m','vector_core','--data-dir',str(root/'data'),'science','import','--package',str(root/'pack')]
            result=subprocess.run(cmd,env=env,capture_output=True,text=True,timeout=20);self.assertNotEqual(result.returncode,0)
            result=subprocess.run(cmd+['--approve'],env=env,capture_output=True,text=True,timeout=20);self.assertEqual(result.returncode,0,result.stderr)
            item=json.loads(result.stdout)['items'][0]
            result=subprocess.run([sys.executable,'-B','-m','vector_core','--data-dir',str(root/'data'),'science','index','--package',str(root/'pack'),'--edition',item['id'],'--limit','10','--approve'],env=env,capture_output=True,text=True,timeout=20);self.assertEqual(result.returncode,0,result.stderr)
            result=subprocess.run([sys.executable,'-B','-m','vector_core','--data-dir',str(root/'data'),'science','search','--query','Specific heat','--limit','10'],env=env,capture_output=True,text=True,timeout=20);self.assertEqual(result.returncode,0,result.stderr);self.assertTrue(json.loads(result.stdout)[0]['scientific_provenance'])

if __name__=='__main__':unittest.main()
