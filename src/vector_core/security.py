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

def activate(*,pipe_fds=(),display_fd=None):
    if sys.platform != 'linux':
        raise SecurityError('Linux seccomp required; startup refused.')
    for fd in (0,1,2):
        try:
            if stat.S_ISSOCK(os.fstat(fd).st_mode):
                raise SecurityError('Socket standard streams forbidden.')
        except OSError:
            pass
    retained=set(pipe_fds)
    for fd in retained:
        if type(fd) is not int or fd<3 or not stat.S_ISFIFO(os.fstat(fd).st_mode):raise SecurityError('Only explicit IPC pipes may be retained.')
    if display_fd is not None:
        if type(display_fd) is not int or display_fd<3:raise SecurityError('Invalid display descriptor.')
        view=socket.fromfd(display_fd,socket.AF_UNIX,socket.SOCK_STREAM)
        try:
            peer=view.getpeername()
            if not isinstance(peer,str) or not peer.lstrip('\0').startswith('/tmp/.X11-unix/X'):raise SecurityError('Only a preconnected local X11 display is permitted.')
        finally:view.close()
        retained.add(display_fd)
    start=3
    for fd in sorted(retained):
        os.closerange(start,fd);start=fd+1
    os.closerange(start,resource.getrlimit(resource.RLIMIT_NOFILE)[0])
    try:
        libc = ctypes.CDLL('libc.so.6', use_errno=True)
        lib = ctypes.CDLL('libseccomp.so.2', use_errno=True)
        lib.seccomp_init.argtypes = [ctypes.c_uint32]
        lib.seccomp_init.restype = ctypes.c_void_p
        lib.seccomp_syscall_resolve_name.argtypes = [ctypes.c_char_p]
        lib.seccomp_syscall_resolve_name.restype = ctypes.c_int
        lib.seccomp_rule_add.argtypes = [ctypes.c_void_p,ctypes.c_uint32,ctypes.c_int,ctypes.c_uint]
        class Compare(ctypes.Structure):
            _fields_=[('arg',ctypes.c_uint),('op',ctypes.c_uint),('a',ctypes.c_uint64),('b',ctypes.c_uint64)]
        lib.seccomp_rule_add_array.argtypes=[ctypes.c_void_p,ctypes.c_uint32,ctypes.c_int,ctypes.c_uint,ctypes.POINTER(Compare)]
        lib.seccomp_attr_set.argtypes=[ctypes.c_void_p,ctypes.c_uint,ctypes.c_uint32]
        lib.seccomp_load.argtypes = [ctypes.c_void_p]
        lib.seccomp_release.argtypes = [ctypes.c_void_p]
        if libc.prctl(38,1,0,0,0):
            raise SecurityError('no_new_privs unavailable.')
        context = lib.seccomp_init(0x7fff0000)
        if not context:
            raise SecurityError('Kernel policy allocation failed.')
        try:
            if lib.seccomp_attr_set(context,4,1):raise SecurityError('Thread-synchronized filtering unavailable.')
            for name in DENIED:
                number = lib.seccomp_syscall_resolve_name(name.encode())
                if display_fd is not None and name in ('sendto','sendmsg','sendmmsg','recvfrom','recvmsg','recvmmsg'):
                    comparison=Compare(0,1,display_fd,0)
                    added=lib.seccomp_rule_add_array(context,0x50000|errno.EPERM,number,1,ctypes.byref(comparison)) if number>=0 else -1
                else:added=lib.seccomp_rule_add(context,0x00050000|errno.EPERM,number,0) if number>=0 else -1
                if number < 0 or added:
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
