"""Optional encryption: positive tests require the offline native dependency."""
import importlib.util
from pathlib import Path
import os
import tempfile
import unittest
from vector_core.config import Config
from vector_core.memory import Memory,Submission
from vector_core.portable import export_vector,restore_vector,verify_export
from vector_core.portable_crypto import create_key,require_crypto

HAS_CRYPTO=importlib.util.find_spec('cryptography') is not None

class CryptoAvailabilityTests(unittest.TestCase):
    def test_missing_crypto_never_silently_produces_plaintext(self):
        from unittest.mock import patch
        import builtins
        original=builtins.__import__
        def deny(name,*args,**kwargs):
            if name.startswith('cryptography'):raise ImportError('offline dependency absent')
            return original(name,*args,**kwargs)
        with patch('builtins.__import__',side_effect=deny):
            with self.assertRaisesRegex(RuntimeError,'no download or plaintext fallback'):require_crypto()

@unittest.skipUnless(HAS_CRYPTO,'Optional offline cryptography dependency absent; encrypted roundtrip not verified in this interpreter')
class CryptoRoundtripTests(unittest.TestCase):
    def test_authenticated_encryption_roundtrip_wrong_key_tampering_and_no_plaintext_export(self):
        with tempfile.TemporaryDirectory() as folder:
            base=Path(folder);config=Config.load(data_dir=str(base/'data'))
            key=base/'recovery.key';create_key(key)
            wrong=base/'wrong.key';create_key(wrong)
            with Memory(config) as memory:
                record=memory.ingest(Submission(b'SENSITIVE TEST PAYLOAD\x00','sensitive'))
                exported=export_vector(memory,base/'encrypted',key_file=key)
                second=export_vector(memory,base/'encrypted',key_file=key)
                self.assertEqual(second['new_blocks'],0)
            self.assertTrue(verify_export(base/'encrypted',key_file=key)['verified'])
            target=Config.load(data_dir=str(base/'restored'))
            restore_vector(target,base/'encrypted',key_file=key)
            with Memory(target) as restored:self.assertEqual(restored.original(record['event_id']),b'SENSITIVE TEST PAYLOAD\x00')
            with self.assertRaises(ValueError):restore_vector(Config.load(data_dir=str(base/'wrong')),base/'encrypted',key_file=wrong)
            for file in (base/'encrypted').rglob('*'):
                if file.is_file():self.assertNotIn(b'SENSITIVE TEST PAYLOAD',file.read_bytes())
            manifest=base/'encrypted/snapshots'/(second['snapshot_id']+'.gcm')
            raw=bytearray(manifest.read_bytes());raw[-1]^=1;manifest.write_bytes(raw)
            with self.assertRaises(ValueError):verify_export(base/'encrypted',key_file=key)
