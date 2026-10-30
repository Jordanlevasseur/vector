"""Actual restores and adversarial transfer tests; no fabricated model assets."""
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import zlib
import unittest
from unittest.mock import patch

from vector_core.config import Config
from vector_core.memory import Memory,Submission
from vector_core.knowledge import Knowledge,learn
from vector_core.persistence import register,put,records,import_asset,declare_external,model_manifest
from vector_core.portable import export_vector,restore_vector,verify_export
from vector_core.storage import object_path,recover_objects

class PortableTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.base=Path(self.temp.name);self.memory=Memory(Config.load(data_dir=str(self.base/'data')))
        self.addCleanup(self.memory.close)
        self.repo=self.base/'portable'

    def populated(self):
        first=self.memory.ingest(Submission(b'Original\x00\xff','first','application/octet-stream'))
        duplicate=self.memory.ingest(Submission(b'Original\x00\xff','repeat','application/octet-stream'))
        revision=self.memory.ingest(Submission(b'Revision','revision',parent_id=first['event_id']))
        one=learn(self.memory,Submission(b'Valve | state | open','one'),'plant',True)
        learn(self.memory,Submission(b'Valve | state | closed','two'),'plant',True)
        claim=one['knowledge']['claim_ids'][0];knowledge=Knowledge(self.memory)
        knowledge.assess(claim,'disputed',0.3,'Competing evidence')
        knowledge.override(claim,'closed','plant','Explicit user operating assumption',approved=True)
        register(self.memory,'future_subsystem','Generic state and required assets')
        for contract in ('conversations','projects','procedures','preferences','future_subsystem'):
            put(self.memory,contract,'first',{'content':'persistent '+contract})
        weights=self.base/'weights.bin';weights.write_bytes(b'LOCAL TEST ASSET NOT A REAL MODEL\x00'*100000)
        asset=import_asset(self.memory,'models','test-weights',weights,'model-weight')
        model_manifest(self.memory,'test-manifest','v1','test-fixture-no-inference',['test-weights'])
        return first,duplicate,revision,claim,asset

    def test_full_population_restores_at_different_location_with_ids_and_assets(self):
        first,duplicate,revision,claim,asset=self.populated()
        snapshot=export_vector(self.memory,self.repo)
        self.assertTrue(snapshot['complete'])
        target=Config.load(data_dir=str(self.base/'different-machine'))
        restore_vector(target,self.repo)
        with Memory(target) as restored:
            self.assertEqual(restored.original(first['event_id']),b'Original\x00\xff')
            self.assertEqual(restored.original(duplicate['event_id']),b'Original\x00\xff')
            self.assertEqual(restored.event(revision['event_id'])['parent_id'],first['event_id'])
            self.assertEqual(Knowledge(restored).effective(claim,'plant')['operating_conclusion'],'closed')
            self.assertEqual(len(Knowledge(restored).contradictions()),1)
            self.assertEqual(records(restored,'future_subsystem')['items'][0]['payload']['content'],'persistent future_subsystem')
            self.assertEqual(object_path(target.data_dir,asset['digest']).read_bytes(),object_path(self.memory.config.data_dir,asset['digest']).read_bytes())
            from vector_core.retrieval import rebuild,search
            rebuild(restored)
            self.assertTrue(search(restored,'Revision'))
        self.assertTrue(verify_export(self.repo)['actual_restoration'])

    def test_incremental_reuses_unchanged_blocks_and_restores_both_snapshots(self):
        self.populated()
        one=export_vector(self.memory,self.repo)
        two=export_vector(self.memory,self.repo)
        self.assertEqual(two['new_blocks'],0)
        self.assertGreater(two['reused_blocks'],0)
        self.memory.ingest(Submission(b'new event','new'))
        three=export_vector(self.memory,self.repo)
        self.assertGreater(three['new_blocks'],0)
        self.assertGreater(three['reused_blocks'],0)
        for snapshot in (one,two,three):self.assertTrue(verify_export(self.repo,snapshot=snapshot['snapshot_id'])['verified'])

    def test_unknown_files_unknown_tables_and_missing_required_assets_fail(self):
        self.populated()
        unknown=self.memory.config.data_dir/'secret.txt';unknown.write_text('not registered')
        with self.assertRaises(ValueError):export_vector(self.memory,self.repo)
        unknown.unlink()
        self.memory.db.execute('CREATE TABLE unexpected(value TEXT)')
        with self.assertRaises(ValueError):export_vector(self.memory,self.repo)
        self.memory.db.execute('DROP TABLE unexpected')
        row=self.memory.db.execute('SELECT digest FROM managed_objects LIMIT 1').fetchone()
        object_path(self.memory.config.data_dir,row[0]).unlink()
        with self.assertRaisesRegex(ValueError,'integrity failed'):export_vector(self.memory,self.repo)
        self.assertFalse((self.repo/'latest.json').exists())

    def test_model_manifest_cannot_omit_required_asset_even_through_generic_state(self):
        with self.assertRaisesRegex(ValueError,'model asset'):
            put(self.memory,'models','broken',{'model_version':'1','runtime':'inert','assets':[{'asset_id':'missing','sha256':'0'*64}],
                'execution_authorized':False,'offline_runtime_qualified':False})

    def test_publication_crash_resumes_without_overwrite_and_cleans_staging(self):
        self.populated()
        def crash(stage):
            if stage=='after-publish':raise RuntimeError('simulated publication crash')
        with self.assertRaises(RuntimeError):export_vector(self.memory,self.repo,fault=crash)
        identifier=next((self.repo/'pending').iterdir()).name
        published=self.repo/'snapshots'/(identifier+'.sqlite3')
        checksum=hashlib.sha256(published.read_bytes()).hexdigest()
        result=export_vector(self.memory,self.repo,resume=identifier)
        self.assertTrue(result['recovered_publication'])
        self.assertEqual(hashlib.sha256(published.read_bytes()).hexdigest(),checksum)
        self.assertFalse(any((self.memory.config.data_dir/'portable_work').rglob('database.sqlite3')))
        self.assertTrue(verify_export(self.repo)['verified'])

    def test_verified_external_model_dependency_blocks_self_contained_export(self):
        file=self.base/'external';file.write_bytes(b'external weights')
        declare_external(self.memory,'models','external model',file)
        with self.assertRaisesRegex(ValueError,'external asset'):export_vector(self.memory,self.repo)

    def test_corrupt_block_and_unsafe_catalogue_path_never_activate(self):
        self.memory.ingest(Submission(b'archive','file'))
        exported=export_vector(self.memory,self.repo)
        catalogue=self.repo/'snapshots'/(exported['snapshot_id']+'.sqlite3')
        db=sqlite3.connect(catalogue)
        digest=db.execute('SELECT digest FROM blocks LIMIT 1').fetchone()[0]
        block=self.repo/'objects'/digest[:2]/digest[2:]
        data=block.read_bytes();block.write_bytes(b'!'*len(data))
        with self.assertRaises((ValueError,zlib.error)):restore_vector(Config.load(data_dir=str(self.base/'bad')),self.repo)
        self.assertTrue((self.base/'bad/.restore-incomplete').exists())
        block.write_bytes(data)
        db.execute("UPDATE files SET name='../../escape'");db.commit();db.close()
        with self.assertRaises(ValueError):restore_vector(Config.load(data_dir=str(self.base/'unsafe')),self.repo)
        self.assertFalse((self.base/'escape').exists())

    def test_interrupted_export_and_restore_resume_without_overwrite(self):
        self.populated()
        def fail(stage):raise RuntimeError('simulated interruption')
        with self.assertRaises(RuntimeError):export_vector(self.memory,self.repo,fault=fail)
        self.assertFalse((self.repo/'latest.json').exists())
        job=next((self.repo/'pending').iterdir()).name
        exported=export_vector(self.memory,self.repo,resume=job)
        target=Config.load(data_dir=str(self.base/'restored'))
        with self.assertRaises(RuntimeError):restore_vector(target,self.repo,fault=fail)
        with self.assertRaises(ValueError):Memory(target)
        self.assertTrue(restore_vector(target,self.repo,resume=True)['activated'])
        with self.assertRaises(FileExistsError):restore_vector(target,self.repo)

    def test_disk_full_before_export_or_restore_never_claims_complete(self):
        self.populated()
        with patch('vector_core.storage.shutil.disk_usage',return_value=type('Disk',(),{'free':1,'total':1000000000})()):
            with self.assertRaises(OSError):export_vector(self.memory,self.repo)
        self.assertFalse((self.repo/'latest.json').exists())
        exported=export_vector(self.memory,self.repo)
        with patch('vector_core.storage.shutil.disk_usage',return_value=type('Disk',(),{'free':1,'total':1000000000})()):
            with self.assertRaises(OSError):restore_vector(Config.load(data_dir=str(self.base/'full')),self.repo)
        self.assertTrue(self.memory.verify()['passed'])

    def test_completed_asset_transfer_recovers_without_discarding_content(self):
        file=self.base/'asset';file.write_bytes(b'recoverable'*10000)
        def fail(stage):raise RuntimeError('interruption')
        with self.assertRaises(RuntimeError):import_asset(self.memory,'extensions','extension',file,'extension',fault=fail)
        with self.assertRaises(ValueError):export_vector(self.memory,self.repo)
        self.assertEqual(recover_objects(self.memory)['recovered'],1)
        self.assertTrue(export_vector(self.memory,self.repo)['complete'])

    def test_preferences_follow_restore_without_old_config_file(self):
        configfile=self.base/'custom.toml';configfile.write_text('max_source_bytes=32768\n')
        config=Config.load(configfile,data_dir=str(self.base/'custom-data'))
        with Memory(config) as custom:
            exported=export_vector(custom,self.repo)
        restored_config=Config.load(data_dir=str(self.base/'restored-settings'))
        restore_vector(restored_config,self.repo)
        with Memory(restored_config) as restored:self.assertEqual(restored.config.max_source_bytes,32768)

    def test_move_retains_old_bytes_redirects_configuration_and_blocks_stale_writer(self):
        from vector_core.coordination import move_data
        event=self.memory.ingest(Submission(b'original retained','move'))
        source=self.memory.config.data_dir
        target=self.base/'larger-volume'
        result=move_data(self.memory,target)
        self.assertTrue(result['old_originals_retained'])
        self.assertTrue((source/'vector.sqlite3').exists())
        self.assertEqual(Config.load(data_dir=str(source)).data_dir,target)
        with self.assertRaisesRegex(ValueError,'relocated'):self.memory.ingest(Submission(b'cannot split history','late'))
        with self.assertRaisesRegex(ValueError,'relocated'):learn(self.memory,Submission(b'A | state | late','late claim'),'scope')
        with Memory(Config.load(data_dir=str(source))) as moved:
            self.assertEqual(moved.original(event['event_id']),b'original retained')
            moved.ingest(Submission(b'new location event','new'))

    def test_malformed_descriptor_symlink_and_expansion_bound_fail_closed(self):
        from vector_core.portable import _decode_block,open_catalogue
        from vector_core.storage import BLOCK
        self.memory.ingest(Submission(b'private original','safe'))
        export_vector(self.memory,self.repo)
        descriptor_path=self.repo/'repository.json'
        descriptor=json.loads(descriptor_path.read_text())
        bad=dict(descriptor,id=42);descriptor_path.write_text(json.dumps(bad))
        with self.assertRaises(ValueError):verify_export(self.repo)
        descriptor_path.write_text(json.dumps(descriptor))
        with open_catalogue(self.repo) as (root,desc,db,meta,key,work):
            with self.assertRaisesRegex(ValueError,'expansion bound'):
                _decode_block(root,('0'*64,BLOCK+1,1,'zlib'),key,desc,work)
            digest=db.execute('SELECT digest FROM blocks LIMIT 1').fetchone()[0]
        block=self.repo/'objects'/digest[:2]/digest[2:]
        original=self.base/'foreign';original.write_bytes(b'foreign')
        block.unlink();block.symlink_to(original)
        with self.assertRaises(ValueError):verify_export(self.repo)
        self.assertEqual(original.read_bytes(),b'foreign')

    def test_a_single_partial_page_is_not_a_collection_limit(self):
        for i in range(250):put(self.memory,'conversations',str(i),{'turn':i})
        cursor=0;count=0
        while True:
            page=records(self.memory,'conversations',after=cursor,limit=17)
            if not page['items']:break
            count+=len(page['items']);cursor=page['next_cursor']
        self.assertEqual(count,250)
