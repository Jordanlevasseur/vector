"""Mandatory Linux kernel syscall enforcement for standalone VECTOR."""
import ctypes
import errno
import os
import resource
import socket
import stat
import sys

DENIED = ('socket','socketpair','connect','bind','listen','accept','accept4',
          'sendto','sendmsg','sendmmsg','recvfrom','recvmsg','recvmmsg',
          'io_uring_setup','io_uring_enter','io_uring_register',
          'execve','execveat','fork','vfork','clone','clone3','ptrace',
          'process_vm_writev','bpf','pidfd_getfd','setns','unshare')

class SecurityError(RuntimeError):
    pass

def activate():
    if sys.platform != 'linux':
        raise SecurityError('Linux seccomp required; startup refused.')
    for fd in (0,1,2):
        try:
            if stat.S_ISSOCK(os.fstat(fd).st_mode):
                raise SecurityError('Socket standard streams forbidden.')
        except OSError:
            pass
    os.closerange(3, resource.getrlimit(resource.RLIMIT_NOFILE)[0])
    try:
        libc = ctypes.CDLL('libc.so.6', use_errno=True)
        lib = ctypes.CDLL('libseccomp.so.2', use_errno=True)
        lib.seccomp_init.argtypes = [ctypes.c_uint32]
        lib.seccomp_init.restype = ctypes.c_void_p
        lib.seccomp_syscall_resolve_name.argtypes = [ctypes.c_char_p]
        lib.seccomp_syscall_resolve_name.restype = ctypes.c_int
        lib.seccomp_rule_add.argtypes = [ctypes.c_void_p,ctypes.c_uint32,ctypes.c_int,ctypes.c_uint]
        lib.seccomp_load.argtypes = [ctypes.c_void_p]
        lib.seccomp_release.argtypes = [ctypes.c_void_p]
        if libc.prctl(38,1,0,0,0):
            raise SecurityError('no_new_privs unavailable.')
        context = lib.seccomp_init(0x7fff0000)
        if not context:
            raise SecurityError('Kernel policy allocation failed.')
        try:
            for name in DENIED:
                number = lib.seccomp_syscall_resolve_name(name.encode())
                if number < 0 or lib.seccomp_rule_add(context,0x00050000|errno.EPERM,number,0):
                    raise SecurityError('Required syscall rule unavailable: '+name)
            if lib.seccomp_load(context):
                raise SecurityError('Kernel policy load failed.')
        finally:
            lib.seccomp_release(context)
    except (OSError,AttributeError) as error:
        raise SecurityError('Mandatory local libseccomp unavailable.') from error
    if libc.prctl(39,0,0,0,0)!=1 or libc.prctl(21,0,0,0,0)!=2:
        raise SecurityError('Kernel did not confirm filtering/no_new_privs.')
    return probe()

def probe():
    observed = {}
    for name,family,kind in [('ipv4',socket.AF_INET,socket.SOCK_STREAM),
                             ('ipv6',socket.AF_INET6,socket.SOCK_DGRAM),
                             ('unix',socket.AF_UNIX,socket.SOCK_STREAM)]:
        try:
            handle=socket.socket(family,kind)
        except OSError as error:
            observed[name]=error.errno==errno.EPERM
        else:
            handle.close()
            observed[name]=False
    if not all(observed.values()):
        raise SecurityError('Network denial verification failed.')
    return {'kernel_policy':'seccomp-offline-v1','network_denied':observed,
            'inference':'disabled; no separately qualified local service',
            'external_network_authorized':False}
