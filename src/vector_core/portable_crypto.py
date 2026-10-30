"""Optional standard AES-256-GCM/HKDF envelope; never an encryption fallback."""
import hashlib
import hmac
import os
from pathlib import Path
from vector_core.storage import input_file,BLOCK


def require_crypto():
    try:
        from cryptography.hazmat.primitives.ciphers import Cipher,algorithms,modes
        from cryptography.hazmat.primitives.kdf.hkdf import HKDF
        from cryptography.hazmat.primitives import hashes
    except ImportError as error:
        raise RuntimeError('Authenticated encryption requires locally installed cryptography; no download or plaintext fallback.') from error
    return Cipher,algorithms,modes,HKDF,hashes


def load_key(path):
    with input_file(path) as stream:
        import stat
        info=os.fstat(stream.fileno())
        if info.st_uid!=os.getuid() or stat.S_IMODE(info.st_mode)&0o077:raise ValueError('Recovery key must be private and owned by this account.')
        key=stream.read(33)
    if len(key)!=32:raise ValueError('Recovery key must contain exactly 32 random bytes.')
    return key


def create_key(path):
    from vector_core.intake import write_new_file
    write_new_file(path,os.urandom(32))
    return {'key_file':str(Path(path).absolute()),'policy':'Keep offline separately. No recovery/backdoor if lost; never store it in exported data.'}


def derived(key,descriptor,context):
    _,_,_,HKDF,hashes=require_crypto()
    return HKDF(algorithm=hashes.SHA256(),length=32,salt=bytes.fromhex(descriptor['salt']),
                info=b'VECTOR portable v1/'+context.encode()).derive(key)


def object_name(digest,key,descriptor):
    if key is None:return digest
    naming=derived(key,descriptor,'object-names')
    return hmac.new(naming,bytes.fromhex(digest),hashlib.sha256).hexdigest()


def seal(source,target,key,descriptor,context):
    Cipher,algorithms,modes,_,_=require_crypto()
    nonce=os.urandom(12)
    encryptor=Cipher(algorithms.AES(derived(key,descriptor,context)),modes.GCM(nonce)).encryptor()
    encryptor.authenticate_additional_data((descriptor['id']+'/'+context).encode())
    with input_file(source) as plain,target.open('xb') as output:
        output.write(b'VGCM1'+nonce)
        while chunk:=plain.read(BLOCK):output.write(encryptor.update(chunk))
        output.write(encryptor.finalize());output.write(encryptor.tag)
        output.flush();os.fsync(output.fileno())
    target.chmod(0o600)


def unseal(source,target,key,descriptor,context):
    Cipher,algorithms,modes,_,_=require_crypto()
    from cryptography.exceptions import InvalidTag
    try:
        with input_file(source) as encrypted,target.open('xb') as output:
            size=os.fstat(encrypted.fileno()).st_size
            if size<33 or encrypted.read(5)!=b'VGCM1':raise ValueError('Invalid encrypted envelope.')
            nonce=encrypted.read(12);encrypted.seek(-16,2);tag=encrypted.read(16);encrypted.seek(17)
            decryptor=Cipher(algorithms.AES(derived(key,descriptor,context)),modes.GCM(nonce,tag)).decryptor()
            decryptor.authenticate_additional_data((descriptor['id']+'/'+context).encode())
            remaining=size-33
            while remaining:
                chunk=encrypted.read(min(BLOCK,remaining))
                if not chunk:raise ValueError('Truncated encrypted envelope.')
                remaining-=len(chunk);output.write(decryptor.update(chunk))
            output.write(decryptor.finalize());output.flush();os.fsync(output.fileno())
        target.chmod(0o600)
    except InvalidTag as error:
        raise ValueError('Wrong recovery key or archive authentication failed; nothing activated.') from error
