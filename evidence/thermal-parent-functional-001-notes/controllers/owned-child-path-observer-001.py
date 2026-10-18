"""Read bounded current children only through unprivileged macOS metadata.

API signatures/count semantics checked against Apple's libproc.h/libproc.c;
existing autorouter.runner uses this same library for sandboxed group metadata.
This diagnostic observer never sends a signal or changes an OS setting.
"""
import ctypes,errno
from pathlib import Path

def owned_paths(parent):
    if type(parent) is not int or parent<=0:raise ValueError('owned current parent PID required')
    library=ctypes.CDLL('/usr/lib/libproc.dylib',use_errno=True)
    library.proc_listchildpids.argtypes=[ctypes.c_int,ctypes.c_void_p,ctypes.c_int];library.proc_listchildpids.restype=ctypes.c_int
    library.proc_pidpath.argtypes=[ctypes.c_int,ctypes.c_void_p,ctypes.c_uint32];library.proc_pidpath.restype=ctypes.c_int
    def children():
        pids=(ctypes.c_int*512)();ctypes.set_errno(0);n=library.proc_listchildpids(parent,pids,ctypes.sizeof(pids));error=ctypes.get_errno()
        if n<0 or n==0 and error not in (0,errno.ESRCH):raise OSError(error,'owned child enumeration refused')
        if n>=len(pids):raise RuntimeError('owned child population saturated')
        return set(x for x in list(pids)[:n] if x>0)
    rows=[]
    for pid in children():
        raw=ctypes.create_string_buffer(4096);ctypes.set_errno(0);n=library.proc_pidpath(pid,raw,ctypes.sizeof(raw));error=ctypes.get_errno()
        if n==0:
            if error in (0,errno.ESRCH):continue
            raise OSError(error,'owned process path refused')
        if pid in children():rows.append(dict(pid=pid,ppid=parent,executable=str(Path(raw.value.decode('utf-8')).resolve())))
    return rows

if __name__=='__main__':
    import os,subprocess,json,time
    child=subprocess.Popen(['/bin/sleep','1'])
    try:
        time.sleep(.05);rows=owned_paths(os.getpid());matches=[r for r in rows if r['pid']==child.pid and r['executable']==str(Path('/bin/sleep').resolve())];assert len(matches)==1
        print(json.dumps(dict(precheck_passed=True,owned_exact_child=matches,scope='one owned bounded sleep child; no Native/router/process control or security changes')))
    finally:assert child.wait(timeout=3)==0
