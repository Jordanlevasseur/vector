import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from vector_core.config import Config
from vector_core.memory import Memory
from vector_core.models import register_external,import_model,materialize
from vector_core.portable import export_vector,restore_vector

class ModelPortabilityTests(unittest.TestCase):
    def test_verified_external_dependency_promotion_restore_and_runtime_layout(self):
        with tempfile.TemporaryDirectory() as folder:
            base=Path(folder);source=base/'external';(source/'blobs').mkdir(parents=True)
            def blob(raw):
                digest=hashlib.sha256(raw).hexdigest();path=source/'blobs'/('sha256-'+digest);path.write_bytes(raw)
                return {'digest':'sha256:'+digest,'size':len(raw)}
            metadata={'schemaVersion':2,'config':blob(b'{}'),'layers':[dict(blob(b'INERT FAKE TEST WEIGHTS'),mediaType='application/vnd.ollama.image.model')]}
            raw=json.dumps(metadata).encode();descriptor=blob(raw)
            old=source/'manifests/registry.ollama.ai/library/test/tiny';old.parent.mkdir(parents=True);old.write_bytes(raw)
            selector=source/'manifests-v2/ollama.com/library/test/tiny';selector.parent.mkdir(parents=True);selector.symlink_to(source/'blobs'/descriptor['digest'].replace(':','-'))
            with Memory(Config.load(data_dir=str(base/'data'))) as memory:
                registration=register_external(memory,source,'test:tiny');self.assertFalse(registration['self_contained_export'])
                with self.assertRaisesRegex(ValueError,'external asset'):export_vector(memory,base/'archive')
                imported=import_model(memory,source,'test:tiny','EXPLICIT FAKE MODEL FIXTURE');self.assertGreater(imported['assets'],2)
                self.assertEqual(memory.db.execute('SELECT count(*) FROM external_dependencies').fetchone()[0],0)
                export_vector(memory,base/'archive')
            target=Config.load(data_dir=str(base/'restored'));restore_vector(target,base/'archive')
            runtime=base/'runtime';runtime.mkdir()
            with Memory(target) as restored:
                materialize(restored,'test:tiny',runtime)
                self.assertEqual((runtime/'manifests/registry.ollama.ai/library/test/tiny').read_bytes(),raw)
                self.assertEqual((runtime/'manifests-v2/ollama.com/library/test/tiny').read_bytes(),raw)
                self.assertFalse((runtime/'manifests-v2/ollama.com/library/test/tiny').is_symlink())
                self.assertTrue(restored.verify()['passed'])
