"""Unexecuted Windows-only substrate prototype; no product portability claim."""
import ctypes as C,ctypes.wintypes as W,hashlib,json,os,subprocess,time
from contextlib import contextmanager
from pathlib import Path
if os.name!='nt':raise RuntimeError('Windows-only capability prototype')
K=C.WinDLL('kernel32',use_last_error=True)
K.GetStdHandle.argtypes=[W.DWORD];K.GetStdHandle.restype=W.HANDLE
class IO(C.Structure):_fields_=[(n,C.c_ulonglong) for n in ('ReadOperationCount','WriteOperationCount','OtherOperationCount','ReadTransferCount','WriteTransferCount','OtherTransferCount')]
class BASIC(C.Structure):_fields_=[('PerProcessUserTimeLimit',C.c_longlong),('PerJobUserTimeLimit',C.c_longlong),('LimitFlags',W.DWORD),('MinimumWorkingSetSize',C.c_size_t),('MaximumWorkingSetSize',C.c_size_t),('ActiveProcessLimit',W.DWORD),('Affinity',C.c_size_t),('PriorityClass',W.DWORD),('SchedulingClass',W.DWORD)]
class LIMIT(C.Structure):_fields_=[('BasicLimitInformation',BASIC),('IoInfo',IO),('ProcessMemoryLimit',C.c_size_t),('JobMemoryLimit',C.c_size_t),('PeakProcessMemoryUsed',C.c_size_t),('PeakJobMemoryUsed',C.c_size_t)]
class ACCOUNT(C.Structure):_fields_=[(n,C.c_longlong) for n in ('TotalUserTime','TotalKernelTime','ThisPeriodTotalUserTime','ThisPeriodTotalKernelTime')]+[(n,W.DWORD) for n in ('TotalPageFaultCount','TotalProcesses','ActiveProcesses','TotalTerminatedProcesses')]
class FILEINFO(C.Structure):_fields_=[('dwFileAttributes',W.DWORD),('ftCreationTime',W.FILETIME),('ftLastAccessTime',W.FILETIME),('ftLastWriteTime',W.FILETIME),('dwVolumeSerialNumber',W.DWORD),('nFileSizeHigh',W.DWORD),('nFileSizeLow',W.DWORD),('nNumberOfLinks',W.DWORD),('nFileIndexHigh',W.DWORD),('nFileIndexLow',W.DWORD)]
class STARTUP(C.Structure):_fields_=[('cb',W.DWORD),('lpReserved',W.LPWSTR),('lpDesktop',W.LPWSTR),('lpTitle',W.LPWSTR),('dwX',W.DWORD),('dwY',W.DWORD),('dwXSize',W.DWORD),('dwYSize',W.DWORD),('dwXCountChars',W.DWORD),('dwYCountChars',W.DWORD),('dwFillAttribute',W.DWORD),('dwFlags',W.DWORD),('wShowWindow',W.WORD),('cbReserved2',W.WORD),('lpReserved2',C.POINTER(C.c_byte)),('hStdInput',W.HANDLE),('hStdOutput',W.HANDLE),('hStdError',W.HANDLE)]
class PROCESS(C.Structure):_fields_=[('hProcess',W.HANDLE),('hThread',W.HANDLE),('dwProcessId',W.DWORD),('dwThreadId',W.DWORD)]
for name,args,result in [('CreateJobObjectW',[C.c_void_p,W.LPCWSTR],W.HANDLE),('SetInformationJobObject',[W.HANDLE,C.c_int,C.c_void_p,W.DWORD],W.BOOL),('QueryInformationJobObject',[W.HANDLE,C.c_int,C.c_void_p,W.DWORD,C.c_void_p],W.BOOL),('AssignProcessToJobObject',[W.HANDLE,W.HANDLE],W.BOOL),('TerminateJobObject',[W.HANDLE,W.UINT],W.BOOL),('TerminateProcess',[W.HANDLE,W.UINT],W.BOOL),('ResumeThread',[W.HANDLE],W.DWORD),('CloseHandle',[W.HANDLE],W.BOOL),('WaitForSingleObject',[W.HANDLE,W.DWORD],W.DWORD),('GetExitCodeProcess',[W.HANDLE,C.POINTER(W.DWORD)],W.BOOL),('CreateFileW',[W.LPCWSTR,W.DWORD,W.DWORD,C.c_void_p,W.DWORD,W.DWORD,W.HANDLE],W.HANDLE),('GetFileInformationByHandle',[W.HANDLE,C.POINTER(FILEINFO)],W.BOOL),('CreateProcessW',[W.LPCWSTR,W.LPWSTR,C.c_void_p,C.c_void_p,W.BOOL,W.DWORD,C.c_void_p,W.LPCWSTR,C.POINTER(STARTUP),C.POINTER(PROCESS)],W.BOOL)]:
 fn=getattr(K,name);fn.argtypes=args;fn.restype=result
def yes(value):
 if not value:raise C.WinError(C.get_last_error())
def safe(path,root):
 path=Path(path).absolute();root=Path(root).absolute()
 if '..' in path.parts or path.drive.startswith('\\\\') or any(':' in part for part in path.parts[1:]) or not path.is_relative_to(root):raise ValueError('owned local DOS path required')
 for part in [path,*path.parents]:
  if part.exists() and part.lstat().st_file_attributes&0x400:raise ValueError('reparse point refused')
 if path.resolve()!=path:raise ValueError('canonical path required')
 return path
def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
@contextmanager
def preserved(path,root):
 path=safe(path,root);handle=K.CreateFileW(str(path),0x80000000,1,None,3,0x00200000,None)
 if handle==C.c_void_p(-1).value:raise C.WinError(C.get_last_error())
 try:
  info=FILEINFO();yes(K.GetFileInformationByHandle(handle,C.byref(info)));yes(info.nNumberOfLinks==1 and not info.dwFileAttributes&0x400)
  before=digest(path);yield dict(sha256=before,file_id=[info.dwVolumeSerialNumber,info.nFileIndexHigh,info.nFileIndexLow],write_delete_sharing_denied=True)
  after=FILEINFO();yes(K.GetFileInformationByHandle(handle,C.byref(after)))
  if digest(path)!=before or (after.dwVolumeSerialNumber,after.nFileIndexHigh,after.nFileIndexLow)!=(info.dwVolumeSerialNumber,info.nFileIndexHigh,info.nFileIndexLow):raise RuntimeError('protected file changed')
 finally:yes(K.CloseHandle(handle))
def run(argv,*,cwd,log,root,firewall_check,seconds=30,cancel_after=None):
 """Create suspended; assign without breakaway; terminate/wait entire owned job."""
 if type(argv) is not list or not argv or any(type(x) is not str for x in argv) or not callable(firewall_check):raise ValueError('typed argv and live firewall gate required')
 cwd=safe(cwd,root);log=safe(log,root);exe=Path(argv[0]).resolve(strict=True);before=digest(exe);network=firewall_check(exe,before)
 if network.get('verified_active_outbound_block') is not True or network.get('verified_active_inbound_block') is not True:raise RuntimeError('live per-program network deny absent')
 job=K.CreateJobObjectW(None,None);yes(job);limits=LIMIT();limits.BasicLimitInformation.LimitFlags=0x2000|0x200|4;limits.BasicLimitInformation.PerJobUserTimeLimit=int(seconds*10_000_000);limits.JobMemoryLimit=2*1024**3
 process=PROCESS();started=time.monotonic();reason=None;created=False;assigned=False
 try:
  yes(K.SetInformationJobObject(job,9,C.byref(limits),C.sizeof(limits)))
  # A regular owned file replaces pipe reader threads; parent alone retains its fd.
  with log.open('xb',buffering=0) as stream:
   import msvcrt
   fd=msvcrt.get_osfhandle(stream.fileno());os.set_handle_inheritable(fd,True)
   startup=STARTUP();startup.cb=C.sizeof(startup);startup.dwFlags=0x100;startup.hStdOutput=startup.hStdError=fd;startup.hStdInput=K.GetStdHandle(-10)
   env={k:v for k,v in os.environ.items() if k.upper() in {'SYSTEMROOT','WINDIR','TEMP','TMP','PATH','APPDATA','LOCALAPPDATA','USERPROFILE','PROGRAMDATA','COMSPEC','KICAD_CONFIG_HOME'}};env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1')
   block=C.create_unicode_buffer('\0'.join(k+'='+v for k,v in sorted(env.items()))+'\0\0')
   try:yes(K.CreateProcessW(str(exe),C.create_unicode_buffer(subprocess.list2cmdline(argv)),None,None,True,0x4|0x400|0x08000000,block,str(cwd),C.byref(startup),C.byref(process)));created=True
   finally:os.set_handle_inheritable(fd,False)
   yes(K.AssignProcessToJobObject(job,process.hProcess));assigned=True
   if K.ResumeThread(process.hThread)==0xffffffff:raise C.WinError(C.get_last_error())
   while True:
    account=ACCOUNT();yes(K.QueryInformationJobObject(job,1,C.byref(account),C.sizeof(account),None));elapsed=time.monotonic()-started
    if account.ActiveProcesses and cancel_after is not None and elapsed>=cancel_after:reason='cancelled'
    if elapsed>=seconds or (account.TotalUserTime+account.TotalKernelTime)/10_000_000>=seconds:reason='budget_exceeded'
    if log.stat().st_size>256*1024:reason='log_limit'
    entries=0;total=0
    for path in cwd.rglob('*'):
     entries+=1;safe(path,root)
     if entries>4000:raise RuntimeError('scratch entry bound')
     if path.is_file():total+=path.stat().st_size
    if total>128*1024**2:reason='scratch_limit'
    if account.ActiveProcesses==0:break
    if reason:yes(K.TerminateJobObject(job,130 if reason=='cancelled' else 2))
    time.sleep(.02)
   yes(K.WaitForSingleObject(process.hProcess,5000)==0);code=W.DWORD();yes(K.GetExitCodeProcess(process.hProcess,C.byref(code)));yes(K.QueryInformationJobObject(job,1,C.byref(account),C.sizeof(account),None));yes(account.ActiveProcesses==0)
  if digest(exe)!=before or firewall_check(exe,before)!=network:raise RuntimeError('tool/network gate changed')
  return dict(argv=argv,cwd=str(cwd),log=str(log),log_sha256=digest(log),status=reason or ('success' if code.value==0 else 'nonzero_exit'),exit_code=code.value,cleanup_complete=True,wall_seconds=time.monotonic()-started,full_job_cpu_seconds=(account.TotalUserTime+account.TotalKernelTime)/10_000_000,process_count=account.TotalProcesses,network=network,limits=dict(bytes=128*1024**2,rss=2*1024**3,log=256*1024,entries=4000,seconds=seconds),os_job_memory_limit=True,scope='Owned pinned tool process job; not hostile-code sandbox or main product runner.')
 finally:
  if created:
   if assigned:K.TerminateJobObject(job,130)
   else:K.TerminateProcess(process.hProcess,130)
   K.WaitForSingleObject(process.hProcess,5000)
   for handle in (process.hThread,process.hProcess):K.CloseHandle(handle)
  K.CloseHandle(job)
