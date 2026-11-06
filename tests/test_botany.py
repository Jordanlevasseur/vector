"""Explicit fixtures, never medical corpus or real-model acceptance evidence."""
import copy,hashlib,json,tempfile,unittest
from pathlib import Path
from vector_core.config import Config
from vector_core.memory import Memory,Submission,canonical
from vector_core.botany import Botany,EVIDENCE,DEFAULT

def reviewed(records):
    manifest={'version':1,'records':records}
    return manifest,hashlib.sha256(canonical(manifest).encode()).hexdigest()

class BotanicalTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.path=str(Path(self.tmp.name)/'data');self.m=Memory(Config.load(data_dir=self.path));self.addCleanup(lambda:self.m.close())
        self.b=Botany(self.m)
        self.body='EXPLICIT TEST FIXTURE. CC0-1.0 public domain dedication. Source reports a plant and uncertainty, not clinical safety. A safety concern must remain visible.'
        e=self.m.ingest(Submission(self.body.encode(),'Botanical fixture','text/plain'))
        # Submission API returns event dictionary, never a model-created citation.
        self.event=e['event_id'];self.digest=e['sha256']
        self.c={'event_id':self.event,'sha256':self.digest,'start':0,'end':len(self.body),'quote':self.body}
        self.source=self.record('fixture-source','source',{'url':'https://example.org/test-fixture','publisher':'EXPLICIT TEST FIXTURE','edition':'1','license':'CC0-1.0','status':'approved','commercial':True,'modification':True,'indexing':True,'attribution':'Explicit synthetic test fixture','third_party_exclusions':'No third-party assets','rights_evidence':[self.c],'asset_events':[self.event],'transformation':'No transformation','notes':'Not installed botanical content','jurisdiction':'US','ai_processing':'indexing-and-retrieval-only; training-requires-separate-review','cultural_permissions':{'status':'not-applicable','basis':'Explicit synthetic test fixture'}},sources=[])
        self.taxon=self.record('fixture-taxon','taxon',{'scientific_name':'Fixture species','authority':None,'rank':'species','kingdom':'Plantae','family':None,'genus':'Fixture','taxonomy_status':'EXPLICIT TEST FIXTURE','use_scope':'general-research','names':[{'name':'Test synonym','language':'la','type':'synonym'}]})
    def record(self,key,kind,data,sources=None):return {'id':key,'kind':kind,'title':key,'sources':['fixture-source'] if sources is None else sources,'citations':[copy.deepcopy(self.c)],'reviewed':'2026-11-06','uncertainty':'EXPLICIT TEST FIXTURE; not medically qualified.','data':data}
    def publish(self,key,records):return self.b.publish(key,*reviewed(records))
    def seed(self):self.publish('fixture-first',[self.source,self.taxon])
    def evidence(self,key='fixture-risk',category=None,domain='toxicity',system='neutral',subject='fixture-taxon',subject_kind='taxon'):
        return self.record(key,'evidence',{'subject_id':subject,'subject_kind':subject_kind,'domain':domain,'claim':'Explicit synthetic finding.','category':category or EVIDENCE[6],'system':system,**dict.fromkeys(('part','preparation','route','dose','population','condition','tradition','cultural_context','mechanism_status'),None)})
    def test_atomic_failure_and_restart_recovery(self):
        def fail(i):raise RuntimeError('Simulated process interruption')
        with self.assertRaises(RuntimeError):self.b.publish('fixture-fault',*reviewed([self.source,self.taxon]),fault=fail)
        self.assertEqual(self.b.counts()['by_kind'],{})
        self.seed();self.m.close();self.m=Memory(Config.load(data_dir=self.path));self.b=Botany(self.m)
        self.assertEqual(self.b.get('fixture-taxon')['data']['scientific_name'],'Fixture species')
        self.assertTrue(self.publish('fixture-first',[self.source,self.taxon])['resumed'])
    def test_licensing_and_manifest_change_rejected(self):
        for licence in ('CC-BY-NC-4.0','unknown',None):
            s=copy.deepcopy(self.source);s['data']['license']=licence
            with self.assertRaises(ValueError):self.publish('bad-license',[s,self.taxon])
        with self.assertRaises(ValueError):self.b.publish('changed',{'version':1,'records':[self.source]},'0'*64)
        self.assertEqual(self.b.counts()['by_kind'],{})
    def test_unlicensed_citation_and_forged_quote_rejected(self):
        self.seed();r=self.evidence();r['citations'][0]['quote']='F'+self.body[1:]
        with self.assertRaises(ValueError):self.publish('bad-quote',[r])
        other=self.m.ingest(Submission(b'not licensed','Unlicensed fixture','text/plain'))
        r=self.evidence();r['citations']=[{'event_id':other['event_id'],'sha256':other['sha256'],'start':0,'end':12,'quote':'not licensed'}]
        with self.assertRaises(ValueError):self.publish('bad-source',[r])
    def test_update_and_rollback_preserve_original_and_prior_version(self):
        self.seed();new=copy.deepcopy(self.taxon);new['title']='A changed description'
        self.publish('fixture-second',[new]);self.assertEqual(self.b.get(new['id'])['title'],new['title'])
        self.b.rollback('fixture-second','Explicit rollback fixture')
        self.assertEqual(self.b.get(new['id'])['title'],self.taxon['title'])
        self.assertEqual(self.m.original(self.event),self.body.encode())
        with self.assertRaises(ValueError):self.publish('fixture-second',[new])
    def test_dependent_rollback_is_refused_atomically(self):
        self.seed();self.publish('fixture-dependent',[self.evidence()])
        with self.assertRaises(ValueError):self.b.rollback('fixture-first','Would strand dependent evidence')
        self.assertEqual(self.b.get('fixture-taxon')['id'],'fixture-taxon')
    def test_synonym_unicode_and_duplicate_taxon(self):
        self.seed();self.assertEqual(len(self.b.list('Test synonym')['items']),1)
        other=copy.deepcopy(self.taxon);other['id']='duplicate'
        with self.assertRaises(ValueError):self.publish('bad-duplicate',[other])
        for bad in ('../../etc/passwd','https://untrusted','unknown'):
            with self.assertRaises(ValueError):self.b.get(bad)
    def test_missing_unknowns_and_all_evidence_categories(self):
        self.seed()
        self.publish('fixture-evidence',[self.evidence('e'+str(i),c) for i,c in enumerate(EVIDENCE)])
        self.assertIsNone(self.b.get('fixture-taxon')['data']['authority'])
        self.assertEqual(len(self.b.detail('fixture-taxon')['related']),8)
        invalid=self.evidence();invalid['data']['category']='proven safe'
        with self.assertRaises(ValueError):self.publish('bad-category',[invalid])
    def test_natural_first_never_hides_negative_or_conventional_evidence(self):
        self.seed();records=[self.evidence(),self.evidence('fixture-negative',EVIDENCE[5],'clinical','natural'),self.evidence('fixture-conventional',EVIDENCE[0],'conventional-comparison','conventional')]
        self.publish('fixture-evidence',records)
        for pref in ('NATURAL-FIRST','BALANCED','CONVENTIONAL-FIRST'):
            self.b.settings({**DEFAULT,'preference':pref});context=self.b.context('fixture-taxon','Explicit test question',12000)['context']
            self.assertEqual(set(context['botanical']['mandatory_evidence']),{r['id'] for r in records})
        with self.assertRaises(ValueError):self.b.context('fixture-taxon','Question',1024)
    def test_selecting_a_favourable_claim_cannot_omit_subject_safety(self):
        self.seed();good=self.evidence('favourable',EVIDENCE[1],'clinical','natural');risk=self.evidence()
        self.publish('mixed-evidence',[good,risk])
        built=self.b.context('favourable','A favourable question',12000)
        self.assertEqual(built['context']['botanical']['id'],'fixture-taxon')
        self.assertIn(risk['id'],built['context']['botanical']['mandatory_evidence'])
    def test_distribution_not_upgraded_to_city_and_availability_distinct(self):
        self.seed()
        r=self.record('fixture-distribution','distribution',{'subject_id':'fixture-taxon','region':{**DEFAULT['region'],'country':'Canada','subdivision':'Yukon'},'availability':'wild','status':'present','origin':'native','scope':'subdivision','site_verified':False})
        self.publish('fixture-range',[r])
        self.assertEqual(len(self.b.list(region={**DEFAULT['region'],'country':'Canada'},availability='wild')['items']),1)
        self.assertEqual(self.b.list(region={**DEFAULT['region'],'country':'United States','city':'Eagle River'})['items'],[])
        self.assertEqual(self.b.list(availability='purchased-imported')['items'],[])
        r['data']['site_verified']=True
        with self.assertRaises(ValueError):self.publish('bad-site',[r])
    def test_formula_evidence_does_not_become_herb_evidence(self):
        self.seed();f=self.record('fixture-formula','formula',{'tradition':'Explicit fixture tradition','components':[{'label':'Unknown historical herb','taxon_id':None,'part':None,'amount':None}],'processing':None,'historical':True,'indications':'Historical source assertions, not clinical endorsement.'})
        e=self.evidence('formula-study',subject=f['id'],subject_kind='formula')
        self.publish('fixture-formula-batch',[f,e])
        self.assertEqual(self.b.detail('fixture-taxon')['related'],[])
        self.assertEqual(len(self.b.detail('fixture-formula')['related']),1)
        bad=self.evidence('mismatched-formula',subject=f['id'])
        with self.assertRaises(ValueError):self.publish('bad-formula',[bad])
    def test_malformed_records_paths_and_photo_licence(self):
        self.seed();r=self.record('fixture-photo','image',{'subject_id':'fixture-taxon','event_id':self.event,'sha256':self.digest,'creator':'Fixture photographer','license':'CC-BY-4.0','attribution':'Fixture','source_url':'https://example.org/photo','modifications':'None','taxonomic_provenance':'Unverified fixture label','depicts':'Fixture'})
        with self.assertRaises(ValueError):self.publish('bad-photo',[r])
        bad=self.evidence();bad['data']['run_command']='curl outside'
        with self.assertRaises(ValueError):self.publish('bad-command',[bad])
    def test_hazard_research_scope_and_compound_separation(self):
        self.seed();restricted=copy.deepcopy(self.taxon);restricted['data']['use_scope']='identification-and-safety-only'
        self.publish('restricted-scope',[restricted])
        with self.assertRaises(ValueError):self.publish('bad-food',[self.evidence('food',EVIDENCE[7],'food-preparation')])
        self.publish('actual-warning',[self.evidence()])
        compound=self.record('fixture-compound','compound',{'name':'Fixture molecule','identifiers':[],'description':'Explicit isolated-compound fixture'})
        e=self.evidence('lab-study',EVIDENCE[2],'compound-mechanism',subject='fixture-compound',subject_kind='compound')
        self.publish('compound-batch',[compound,e])
        self.assertNotIn('lab-study',[r['id'] for r in self.b.detail('fixture-taxon')['related']])
    def test_snapshot_verification_rejects_forged_manifest(self):
        from vector_core.botany import verify_state
        from vector_core.persistence import put
        self.seed();self.assertEqual(verify_state(self.m)['verified_records'],2)
        put(self.m,'botanical_batches','invented',{'id':'invented','sha256':'0'*64,'status':'active','count':1,'created':'2026-11-06T00:00:00','reason':'Forged explicit fixture'})
        with self.assertRaises(ValueError):verify_state(self.m)
    def test_snapshot_verification_and_validated_restore(self):
        from vector_core.portable import validate_database
        self.seed();value=validate_database(self.m.db,self.m.config.data_dir)
        self.assertTrue(value['passed'])
    def test_local_pack_crash_resume_and_rejected_licence_before_intake(self):
        from vector_core.botany import import_pack
        folder=Path(self.tmp.name)/'pack';(folder/'objects').mkdir(parents=True)
        (folder/'objects'/self.digest).write_bytes(self.body.encode())
        s=copy.deepcopy(self.source);t=copy.deepcopy(self.taxon)
        for r in (s,t):r['citations'][0]['event_id']='@source-text'
        s['data']['rights_evidence'][0]['event_id']='@source-text';s['data']['asset_events']=['@source-text']
        asset={'key':'source-text','sha256':self.digest,'bytes':len(self.body.encode()),'media_type':'text/plain','name':'Explicit local pack fixture','source_id':'fixture-source','parent_key':None,'role':'original','temporal_status':'Explicit test fixture','locator':'Complete fixture text'}
        pack={'format':'vector-botanical-pack-v1','batch_id':'local-fixture','assets':[asset],'records':[s,t]}
        def save():
            raw=canonical(pack).encode();(folder/'manifest.json').write_bytes(raw);return hashlib.sha256(raw).hexdigest()
        count=self.m.db.execute('SELECT count(*) FROM events').fetchone()[0]
        s['data']['license']='CC-BY-NC-4.0'
        with self.assertRaises(ValueError):import_pack(self.m,folder,save())
        self.assertEqual(self.m.db.execute('SELECT count(*) FROM events').fetchone()[0],count)
        s['data']['license']='CC0-1.0';digest=save()
        def stop(stage,key):
            if stage=='asset':raise RuntimeError('Simulated interrupted local intake')
        with self.assertRaises(RuntimeError):import_pack(self.m,folder,digest,fault=stop)
        self.assertEqual(self.b.counts()['by_kind'],{})
        from vector_core.retrieval import search
        self.assertFalse(any(r['event_id']!=self.event for r in search(self.m,'FIXTURE')))
        value=import_pack(self.m,folder,digest);self.assertEqual(value['publication']['count'],2)
        from vector_core.resources import Resources
        resources=Resources(self.m)
        try:
            self.assertEqual(resources.list(category='Botanical sources')['total'],1)
            self.assertIn('Botanical rights & extracted data',resources.list()['categories'])
        finally:resources.close()
        self.assertEqual(self.m.db.execute('SELECT count(*) FROM events').fetchone()[0],count+1)
        self.assertTrue(import_pack(self.m,folder,digest)['publication']['resumed'])
        from vector_core.botany import provenance
        self.assertIsNotNone(provenance(self.m,value['assets']['source-text']))
        self.b.rollback('local-fixture','Explicit test rollback')
        self.assertIsNone(provenance(self.m,value['assets']['source-text']))
    def test_source_update_cannot_invalidate_existing_licensed_records(self):
        self.seed();withdrawn=copy.deepcopy(self.source);withdrawn['data'].update(status='excluded',asset_events=[],commercial=False,modification=False,indexing=False)
        with self.assertRaises(ValueError):self.publish('withdrawn-source',[withdrawn])
        self.assertEqual(self.b.get('fixture-source')['data']['status'],'approved')
    def test_scope_update_cannot_leave_existing_food_claims_active(self):
        self.seed();self.publish('food-fixture',[self.evidence('food',EVIDENCE[7],'edibility')])
        restricted=copy.deepcopy(self.taxon);restricted['data']['use_scope']='identification-and-safety-only'
        with self.assertRaises(ValueError):self.publish('restricted-update',[restricted])
        self.assertEqual(self.b.get('fixture-taxon')['data']['use_scope'],'general-research')
    def test_metadata_pages_are_byte_bounded_without_omitting_records(self):
        self.seed();records=[]
        for i in range(6):
            r=copy.deepcopy(self.taxon);r['id']='large'+str(i);r['data']['scientific_name']='Fixture species'+str(i);r['data']['names']=[{'name':str(j)+'-'+'a'*400,'language':'la','type':'synonym'} for j in range(180)];records.append(r)
        self.publish('large-fixture',records);cursor=0;seen=[]
        while True:
            page=self.b.list(kind='taxon',after=cursor,limit=100);self.assertLess(len(canonical(page).encode()),512*1024);seen.extend(r['id'] for r in page['items'])
            if page['next_cursor'] is None:break
            self.assertGreater(page['next_cursor'],cursor);cursor=page['next_cursor']
        self.assertEqual(set(seen),{'fixture-taxon',*(r['id'] for r in records)});self.assertEqual(len(seen),7)
    def test_small_model_budget_reports_complete_instruction_limit(self):
        self.seed()
        with self.assertRaisesRegex(ValueError,'Complete botanical instructions'):
            self.b.context('fixture-taxon','Question',128)
        from vector_core.service import Application
        app=Application(self.m)
        class Forbidden:
            def generate(self,*args,**kwargs):raise AssertionError('Incomplete instructions must never reach a model')
        app.adapter=Forbidden()
        with self.assertRaisesRegex(ValueError,'context allowance'):
            app.handle('botany_research',{'id':'fixture-taxon','question':'What is known?','evidence_only':False})
        saved=json.loads(self.m.db.execute("SELECT payload FROM persistent_records WHERE contract='conversations' ORDER BY rowid DESC LIMIT 1").fetchone()[0])
        self.assertEqual(saved['question'],'What is known?');self.assertEqual(saved['outcome']['status'],'failed')
        self.assertIn('context allowance',saved['outcome']['errors'][0])
    def test_desktop_service_cannot_publish_or_fetch(self):
        from vector_core.service import Application
        app=Application(self.m)
        for operation in ('botany_import','botany_fetch','botany_publish'):
            with self.assertRaises(ValueError):app.handle(operation,{'url':'https://example.org'})
        self.assertEqual(app.handle('botany_preferences_get',{})['preference'],'NATURAL-FIRST')
        self.assertNotIn('botanical_research',[r[0] for r in self.m.db.execute("SELECT record_key FROM persistent_records WHERE contract='preferences'")])
