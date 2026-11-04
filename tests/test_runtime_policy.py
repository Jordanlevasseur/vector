"""Selection-policy fixtures do not establish real high-memory inference."""
import hashlib,json,struct,tempfile,unittest
from pathlib import Path
from vector_core.models import local_inventory,manifest_identifier,manifest_relative
from vector_core.runtime_policy import hardware,plan,memory_estimate,MIB

def gguf(architecture='generic',context=8192):
    fields={'general.architecture':architecture,architecture+'.context_length':context,architecture+'.block_count':12,architecture+'.embedding_length':1024,architecture+'.attention.head_count':16,architecture+'.attention.head_count_kv':4}
    raw=b'GGUF'+struct.pack('<IQQ',3,1,len(fields))
    for key,v in fields.items():
        b=key.encode();raw+=struct.pack('<Q',len(b))+b
        if isinstance(v,str):b=v.encode();raw+=struct.pack('<IQ',8,len(b))+b
        else:raw+=struct.pack('<II',4,v)
    return raw

def model(root,name='other-company/custom:small',raw=None):
    raw=gguf() if raw is None else raw
    def blob(b):
        digest=hashlib.sha256(b).hexdigest();(root/'blobs').mkdir(exist_ok=True);(root/'blobs'/('sha256-'+digest)).write_bytes(b);return {'digest':'sha256:'+digest,'size':len(b)}
    cfg=blob(json.dumps({'model_format':'gguf','model_family':'generic','model_type':'600M','file_type':'Q4_K_M'}).encode());weight=blob(raw);manifest={'config':cfg,'layers':[{**weight,'mediaType':'application/vnd.ollama.image.model'}]};p=root/manifest_relative(name);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(manifest));return name

def host(gib,available=None):return {'effective_total':gib*1024*MIB,'effective_available':(available if available is not None else gib-1)*1024*MIB,'effective_cores':4.,'fingerprint':'explicit-policy-fixture','parent_pids_max':512}

class RuntimePolicyTests(unittest.TestCase):
    def test_generic_namespaces_and_actual_bounded_gguf_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);name=model(root);row=local_inventory([root])[0]
            self.assertEqual(row['name'],name);self.assertEqual(row['architecture'],'generic');self.assertEqual(row['context_length'],8192);self.assertEqual(row['quantization'],'Q4_K_M');self.assertIsNone(row['compatible']);self.assertFalse(row['runtime_inspected']);self.assertIsNone(row['tool_calling'])
        for name in ('ordinary:tag','author/ordinary:tag','local.example/author/ordinary:tag'):self.assertEqual(manifest_identifier(manifest_relative(name).parts[1:]),name)
        for name in ('../a:x','a/b/c/d:x','a:../x','/a:x'):
            with self.assertRaises(ValueError):manifest_relative(name)
    def test_corrupt_unselected_model_remains_visible_without_hiding_valid_model(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);model(root,'working:latest');model(root,'broken:latest',b'not-gguf');rows={m['name']:m for m in local_inventory([root])}
            self.assertIsNone(rows['working:latest']['compatible']);self.assertFalse(rows['broken:latest']['compatible']);self.assertIn('GGUF',rows['broken:latest']['unavailable_reason'])
    def test_simulated_small_and_large_hardware_select_different_viable_models(self):
        models=[{'name':'small:latest','digest':'a'*64,'weight_bytes':400*MIB,'parameter_count':500000000},{'name':'general:latest','digest':'b'*64,'weight_bytes':1400*MIB,'parameter_count':2000000000}]
        self.assertEqual(plan(models,host(4,2))['models'],['small:latest']);large=plan(models,host(16,12));self.assertEqual(large['models'],['general:latest']);self.assertGreater(large['memory_bytes'],2*1024*MIB);self.assertFalse(large['gpu_enabled'])
    def test_explicit_manual_model_never_silently_substitutes_or_weakens_hard_reserve(self):
        models=[{'name':'small:latest','weight_bytes':400*MIB},{'name':'large:latest','weight_bytes':2000*MIB}];h=host(4,2)
        p=plan(models,h,manual_names=['large:latest']);self.assertEqual(p['models'],['large:latest']);self.assertLess(p['memory_bytes'],2000*MIB)
        with self.assertRaises(RuntimeError):plan(models,h,manual_names=['missing:latest'])
        with self.assertRaises(RuntimeError):plan(models,host(4,.4))
        exp=plan(models,h,manual_names=['large:latest'],experimental=True,manual_limit=2*1024*MIB);self.assertEqual(exp['memory_bytes'],2*1024*MIB);self.assertTrue(exp['experimental'])
    def test_known_incompatibility_and_context_failure_exclude_larger_model(self):
        models=[{'name':'small:latest','weight_bytes':400*MIB,'parameter_count':1},{'name':'huge:latest','weight_bytes':800*MIB,'parameter_count':100,'compatible':False,'unavailable_reason':'Explicit fixture: unsupported architecture'}]
        self.assertEqual(plan(models,host(16))['models'],['small:latest']);models[1].update(compatible=None,unavailable_reason='',context_length=1024);self.assertEqual(plan(models,host(16),context_required=2048)['models'],['small:latest'])
    def test_measured_warm_peak_cannot_erase_weight_floor_and_accuracy_is_not_a_gate(self):
        m={'name':'model:latest','digest':'a'*64,'weight_bytes':400*MIB,'accuracy_passed':False};obs=[{'id':'actual-runtime-observation','model_digest':'a'*64,'simulated':False,'inference_completed':True,'context_tokens':2048,'peak_memory_bytes':100*MIB}]
        self.assertGreater(memory_estimate(m,observations=obs)['estimated_bytes'],400*MIB);self.assertEqual(plan([m],host(4),observations=obs)['models'],['model:latest'])
    def test_bounded_exclusions_and_sequential_participant_plan(self):
        models=[{'name':'one:latest','weight_bytes':100*MIB},{'name':'two:latest','weight_bytes':200*MIB},{'name':'three:latest','weight_bytes':300*MIB}]
        p=plan(models,host(16),manual_names=[m['name'] for m in models]);self.assertEqual(len(p['participants']),3);self.assertEqual(p['execution'],'sequential')
        with self.assertRaises(RuntimeError):plan(models,host(16),exclude=[m['name'] for m in models])
    def test_actual_host_detection_reports_constraints_without_fixed_lenovo_assumptions(self):
        h=hardware();self.assertGreater(h['physical_memory'],0);self.assertGreater(h['effective_cores'],0);self.assertEqual(len(h['fingerprint']),64);self.assertFalse(h['gpu_execution_qualified']);self.assertIn('cgroup_constraints',h)

if __name__=='__main__':unittest.main()

class SelectorIdentityTests(unittest.TestCase):
    def test_effective_v2_digest_is_linked_and_all_payloads_still_verified(self):
        import hashlib,json,tempfile,struct
        from vector_core.models import local_inventory,selected_files,runtime_files
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/'blobs').mkdir()
            def blob(raw,media):
                digest=hashlib.sha256(raw).hexdigest();(root/'blobs'/('sha256-'+digest)).write_bytes(raw)
                return {'digest':'sha256:'+digest,'size':len(raw),'mediaType':media}
            cfg=blob(json.dumps({'model_format':'gguf','model_family':'example','model_type':'1B','file_type':'Q4_K_M'}).encode(),'config')
            weights=blob(b'GGUF'+struct.pack('<IQQ',3,0,0),'application/vnd.ollama.image.model')
            inner=json.dumps({'config':cfg,'layers':[weights]}).encode();inner_layer=blob(inner,'application/vnd.docker.distribution.manifest.v2+json')
            manifest=root/'manifests/registry.ollama.ai/author/model/local';manifest.parent.mkdir(parents=True);manifest.write_text(json.dumps({'config':cfg,'layers':[weights,inner_layer]}))
            selector=root/'manifests-v2/ollama.com/author/model/local';selector.parent.mkdir(parents=True);selector.symlink_to(root/'blobs'/inner_layer['digest'].replace(':','-'))
            inventory=local_inventory([root]);self.assertIsNone(inventory[0]['compatible']);self.assertEqual(inventory[0]['digest'],hashlib.sha256(inner).hexdigest());self.assertNotEqual(inventory[0]['source_manifest_sha256'],inventory[0]['digest'])
            self.assertTrue(selected_files(root,'author/model:local'));self.assertIn('manifests-v2/ollama.com/author/model/local',runtime_files([root],['author/model:local']))
            (root/'blobs'/weights['digest'].replace(':','-')).write_bytes(b'X'*weights['size'])
            with self.assertRaisesRegex(ValueError,'corrupt'):selected_files(root,'author/model:local')
    def test_unlinked_selector_is_rejected(self):
        import tempfile,json,hashlib
        from vector_core.models import local_inventory,selected_files
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/'blobs').mkdir()
            raw=b'{}';d=hashlib.sha256(raw).hexdigest();(root/'blobs'/('sha256-'+d)).write_bytes(raw)
            p=root/'manifests/registry.ollama.ai/library/model/tag';p.parent.mkdir(parents=True);p.write_text(json.dumps({'config':{'digest':'sha256:'+d,'size':2},'layers':[]}))
            s=root/'manifests-v2/ollama.com/library/model/tag';s.parent.mkdir(parents=True);s.symlink_to(root/'blobs'/('sha256-'+d))
            self.assertFalse(local_inventory([root])[0]['compatible'])
            with self.assertRaisesRegex(ValueError,'not linked'):selected_files(root,'model:tag')

    def test_malformed_model_metadata_does_not_block_other_models(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);model(root,'good:tag');name=model(root,'bad:tag')
            manifest=root/manifest_relative(name);body=json.loads(manifest.read_text())
            raw=json.dumps({'model_format':'gguf','model_type':'9'*300+'B'}).encode();digest=hashlib.sha256(raw).hexdigest();(root/'blobs'/('sha256-'+digest)).write_bytes(raw);body['config']={'digest':'sha256:'+digest,'size':len(raw)};manifest.write_text(json.dumps(body))
            rows={r['name']:r for r in local_inventory([root])};self.assertIsNone(rows['good:tag']['compatible']);self.assertFalse(rows['bad:tag']['compatible']);self.assertIn('bounded',rows['bad:tag']['unavailable_reason'])
