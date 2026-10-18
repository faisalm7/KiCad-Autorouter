"""Experimental Windows-only substrate; no product portability claim."""
import ctypes as C,ctypes.wintypes as W,hashlib,json,math,os,re,subprocess,sys,time
from contextlib import contextmanager,nullcontext,ExitStack
from pathlib import Path
if os.name!='nt':raise RuntimeError('Windows-only capability prototype')
K=C.WinDLL('kernel32',use_last_error=True)
K.GetStdHandle.argtypes=[W.DWORD];K.GetStdHandle.restype=W.HANDLE
class IO(C.Structure):_fields_=[(n,C.c_ulonglong) for n in ('ReadOperationCount','WriteOperationCount','OtherOperationCount','ReadTransferCount','WriteTransferCount','OtherTransferCount')]
class BASIC(C.Structure):_fields_=[('PerProcessUserTimeLimit',C.c_longlong),('PerJobUserTimeLimit',C.c_longlong),('LimitFlags',W.DWORD),('MinimumWorkingSetSize',C.c_size_t),('MaximumWorkingSetSize',C.c_size_t),('ActiveProcessLimit',W.DWORD),('Affinity',C.c_size_t),('PriorityClass',W.DWORD),('SchedulingClass',W.DWORD)]
class LIMIT(C.Structure):_fields_=[('BasicLimitInformation',BASIC),('IoInfo',IO),('ProcessMemoryLimit',C.c_size_t),('JobMemoryLimit',C.c_size_t),('PeakProcessMemoryUsed',C.c_size_t),('PeakJobMemoryUsed',C.c_size_t)]
class ACCOUNT(C.Structure):_fields_=[(n,C.c_longlong) for n in ('TotalUserTime','TotalKernelTime','ThisPeriodTotalUserTime','ThisPeriodTotalKernelTime')]+[(n,W.DWORD) for n in ('TotalPageFaultCount','TotalProcesses','ActiveProcesses','TotalTerminatedProcesses')]
class JOBPIDS(C.Structure):_fields_=[('NumberOfAssignedProcesses',W.DWORD),('NumberOfProcessIdsInList',W.DWORD),('ProcessIdList',C.c_size_t*32)]
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
def run(argv,*,cwd,log,root,firewall_check,seconds=30,cancel_after=None,appcontainer=None):
 """Create suspended; assign without breakaway; terminate/wait entire owned job."""
 if type(argv) is not list or not argv or any(type(x) is not str for x in argv):raise ValueError('typed argv and live firewall gate required')
 if appcontainer is None:
  if not callable(firewall_check):raise ValueError('typed argv and live firewall gate required')
 else:
  if __package__:from .appcontainer_launch import AppContainerLaunch
  else:from appcontainer_launch import AppContainerLaunch
  if type(appcontainer) is not AppContainerLaunch or firewall_check is not None:raise ValueError('exact experimental AppContainer guard and no firewall callback required')
 cwd=safe(cwd,root);log=safe(log,root);exe=Path(argv[0]).resolve(strict=True);before=digest(exe)
 if appcontainer is None:
  network=firewall_check(exe,before)
  if network.get('verified_active_outbound_block') is not True or network.get('verified_active_inbound_block') is not True:raise RuntimeError('live per-program network deny absent')
 else:
  if Path(argv[0]).absolute()!=exe:raise ValueError('canonical AppContainer executable argv required')
  network=appcontainer.before_launch(exe,cwd,log,root,seconds)
 delivery_started=time.monotonic()
 result=_run_job(argv,cwd=cwd,log=log,root=root,seconds=seconds,cancel_after=cancel_after,appcontainer=appcontainer,launch_contract=network)
 if digest(exe)!=before or (firewall_check(exe,before) if appcontainer is None else appcontainer.check_contract())!=network:raise RuntimeError('tool/network gate changed')
 result['wall_seconds']=time.monotonic()-delivery_started
 result['network']=network
 if appcontainer is not None:result.update(accepted=False,product_support=False,experimental_network_proof=dict(kind='experimental-appcontainer-token-v1',token=result.pop('_suspended_token'),contract=network,network_tests_performed_by_adapter=False,all_network_denial_claimed=False,profile_cleanup_pending_context_exit=True))
 else:result.pop('_suspended_token')
 return result

def _poll_setup_main(process):
 """Observe the retained main handle without waiting or reopening a PID."""
 result=dict(pid=int(process.dwProcessId),state='unknown',exit_code=None)
 try:
  wait=int(K.WaitForSingleObject(process.hProcess,0));result['wait_result']=wait
  if wait==258:result['state']='running'
  elif wait==0:
   code=W.DWORD()
   if K.GetExitCodeProcess(process.hProcess,C.byref(code)):result.update(state='exited',exit_code=int(code.value))
   else:result['error']=dict(api='GetExitCodeProcess',winerror=int(C.get_last_error()))
  else:result['error']=dict(api='WaitForSingleObject',winerror=int(C.get_last_error()))
 except Exception as error:result['error']=dict(exception=type(error).__name__,message=str(error)[:256])
 return result

def _observe_setup_job(job,account,elapsed,trigger,main):
 """Bounded Job-only PID snapshot; PID image/exit identities are unobserved."""
 members=dict(status='unknown',capacity=32,pids=[],image_identity_observed=False,
              identity_scope='Point-in-time owned Job PID list only; no child PID opened or stable child identity established.')
 try:
  listing=JOBPIDS();ok=K.QueryInformationJobObject(job,3,C.byref(listing),C.sizeof(listing),None)
  error=int(C.get_last_error()) if not ok else None
  count=int(listing.NumberOfProcessIdsInList);assigned=int(listing.NumberOfAssignedProcesses)
  members.update(assigned_processes=assigned,listed_processes=count,truncated=count<assigned or assigned>32 or count>32)
  if ok and 0<=count==assigned<=32:
   pids=[int(listing.ProcessIdList[index]) for index in range(count)]
   if len(set(pids))==count and all(pid>0 for pid in pids):members.update(status='observed',pids=pids)
   else:members['error']=dict(message='Invalid or duplicate Job PID list')
  else:members['error']=dict(api='QueryInformationJobObject(JobObjectBasicProcessIdList)',winerror=error)
 except Exception as error:members['error']=dict(exception=type(error).__name__,message=str(error)[:256])
 return dict(trigger=trigger,elapsed_seconds=elapsed,main=main,members=members,
             accounting_active_processes=int(account.ActiveProcesses),accounting_total_processes=int(account.TotalProcesses),
             snapshots_atomic=False,status='observed' if main['state']!='unknown' and members['status']=='observed' else 'unknown')

def _run_job(argv,*,cwd,log,root,seconds,cancel_after=None,appcontainer=None,launch_contract=None,owned_setup=False,setup_authoring=None):
 """Shared owned process lifecycle only; public entry points own admission gates."""
 compiler_role=None
 if setup_authoring is not None:
  if not owned_setup or appcontainer is not None or type(setup_authoring) is not dict:raise ValueError('exact owned setup authoring contract required')
  if setup_authoring.get('kind')=='fixed-owned-C-canary-build':
   compiler_role=setup_authoring.get('role')
   if type(compiler_role) is not int or compiler_role not in (1,2):raise ValueError('exact owned compiler role required')
  elif setup_authoring.get('kind')!='fixed-owned-DNS-helper':raise ValueError('unknown owned setup authoring contract')
 exe=Path(argv[0]).resolve(strict=True)
 job=K.CreateJobObjectW(None,None);yes(job);limits=LIMIT();limits.BasicLimitInformation.LimitFlags=0x2000|0x200|4;limits.BasicLimitInformation.PerJobUserTimeLimit=int(seconds*10_000_000);limits.JobMemoryLimit=2*1024**3
 process=PROCESS();started=time.monotonic();reason=None;created=False;assigned=False;token_proof=None
 setup_observations=[];last_main_state=None;setup_termination_observed=False;setup_main_polls=0;compiler_finalization=None
 try:
  yes(K.SetInformationJobObject(job,9,C.byref(limits),C.sizeof(limits)))
  # A regular owned file replaces pipe reader threads; parent alone retains its fd.
  with log.open('xb',buffering=0) as stream:
   import msvcrt
   fd=msvcrt.get_osfhandle(stream.fileno());os.set_handle_inheritable(fd,True)
   startup=STARTUP();startup.cb=C.sizeof(startup);startup.dwFlags=0x100;startup.hStdOutput=startup.hStdError=fd;startup.hStdInput=K.GetStdHandle(-10)
   env={k:v for k,v in os.environ.items() if k.upper() in {'SYSTEMROOT','WINDIR','TEMP','TMP','PATH','APPDATA','LOCALAPPDATA','USERPROFILE','PROGRAMDATA','COMSPEC','KICAD_CONFIG_HOME'}};env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1')
   if owned_setup:env.update(TEMP=str(cwd),TMP=str(cwd))
   block=C.create_unicode_buffer('\0'.join(k+'='+v for k,v in sorted(env.items()))+'\0\0')
   attributes=appcontainer.launch_attributes(startup,fd) if appcontainer is not None else nullcontext((C.byref(startup),0))
   try:
    with attributes as (startup_pointer,extra_flags):
     yes(K.CreateProcessW(str(exe),C.create_unicode_buffer(subprocess.list2cmdline(argv)),None,None,True,0x4|0x400|0x08000000|extra_flags,block,str(cwd),startup_pointer,C.byref(process)));created=True
     if appcontainer is not None:appcontainer.process_created()
   finally:os.set_handle_inheritable(fd,False)
   yes(K.AssignProcessToJobObject(job,process.hProcess));assigned=True
   if appcontainer is not None:
    token_proof=appcontainer.verify_suspended_token(process.hProcess,process.dwProcessId)
    if appcontainer.check_contract()!=launch_contract:raise RuntimeError('experimental launch contract changed before resume')
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
    if owned_setup and not setup_termination_observed:
     main=_poll_setup_main(process);setup_main_polls+=1
     if main['state']=='unknown':reason=reason or 'process_diagnostic_unknown'
     state=(main['state'],main['exit_code'])
     trigger=('before_termination' if reason and account.ActiveProcesses else 'job_inactive' if account.ActiveProcesses==0
              else 'initial' if not setup_observations else 'main_state_changed' if state!=last_main_state else None)
     if trigger:
      observation=_observe_setup_job(job,account,elapsed,trigger,main)
      if observation['status']=='unknown':reason=reason or 'process_diagnostic_unknown'
      observation.update(before_termination=bool(reason and account.ActiveProcesses),termination_reason=reason)
      if len(setup_observations)>=4:raise RuntimeError('owned setup diagnostic observation bound')
      setup_observations.append(observation)
     last_main_state=state
     if reason and account.ActiveProcesses:setup_termination_observed=True
     if compiler_role is not None and reason is None and main['state']=='exited' and main['exit_code']==0 and account.ActiveProcesses:
      # Recheck all original bounds after diagnostics, before owned cleanup.
      yes(K.QueryInformationJobObject(job,1,C.byref(account),C.sizeof(account),None));elapsed=time.monotonic()-started
      if account.ActiveProcesses and cancel_after is not None and elapsed>=cancel_after:reason='cancelled'
      if elapsed>=seconds or (account.TotalUserTime+account.TotalKernelTime)/10_000_000>=seconds:reason='budget_exceeded'
      if log.stat().st_size>256*1024:reason='log_limit'
      entries=0;total=0
      for path in cwd.rglob('*'):
       entries+=1;safe(path,root)
       if entries>4000:raise RuntimeError('scratch entry bound')
       if path.is_file():total+=path.stat().st_size
      if total>128*1024**2:reason='scratch_limit'
      # Directory accounting also consumes the unchanged wall envelope.
      elapsed=time.monotonic()-started
      if account.ActiveProcesses and cancel_after is not None and elapsed>=cancel_after:reason='cancelled'
      if elapsed>=seconds:reason='budget_exceeded'
      if reason is None and account.ActiveProcesses:
       compiler_finalization=dict(kind='exact-owned-C-build-main-zero-then-job-reap-v1',role=compiler_role,
                                  main=main,main_observed_elapsed_seconds=setup_observations[-1]['elapsed_seconds'],
                                  accounting_active_before_request=int(account.ActiveProcesses),
                                  member_snapshot=setup_observations[-1]['members'],termination_exit_code=130,
                                  termination_requested=True,terminate_job_succeeded=False,
                                  remaining_members_natural_completion_claimed=False,zero_active_processes_verified=False)
       setup_observations[-1].update(before_termination=True,termination_reason='compiler_main_zero_owned_cleanup')
       yes(K.TerminateJobObject(job,130));compiler_finalization['terminate_job_succeeded']=True;setup_termination_observed=True
      elif reason:
       setup_observations[-1].update(before_termination=bool(account.ActiveProcesses),termination_reason=reason)
       if account.ActiveProcesses:setup_termination_observed=True
    if account.ActiveProcesses==0:break
    if reason:yes(K.TerminateJobObject(job,130 if reason=='cancelled' else 2))
    time.sleep(.02)
   yes(K.WaitForSingleObject(process.hProcess,5000)==0);code=W.DWORD();yes(K.GetExitCodeProcess(process.hProcess,C.byref(code)));yes(K.QueryInformationJobObject(job,1,C.byref(account),C.sizeof(account),None));yes(account.ActiveProcesses==0)
  result=dict(argv=argv,cwd=str(cwd),log=str(log),log_sha256=digest(log),status=reason or ('success' if code.value==0 else 'nonzero_exit'),exit_code=code.value,cleanup_complete=True,wall_seconds=time.monotonic()-started,full_job_cpu_seconds=(account.TotalUserTime+account.TotalKernelTime)/10_000_000,process_count=account.TotalProcesses,_suspended_token=token_proof,limits=dict(bytes=128*1024**2,rss=2*1024**3,log=256*1024,entries=4000,seconds=seconds),os_job_memory_limit=True,scope='Owned pinned tool process job; not hostile-code sandbox or main product runner.')
  if owned_setup:result['setup_process_observations']=dict(main_polls=setup_main_polls,max_snapshots=4,snapshots=setup_observations,completion_semantics_changed=compiler_finalization is not None)
  if compiler_finalization is not None:
   compiler_finalization['zero_active_processes_verified']=True
   result['compiler_finalization']=compiler_finalization
  return result
 finally:
  cleanup_errors=[];reaped=not created
  def cleanup(label,action):
   try:action()
   except BaseException as error:cleanup_errors.append(label+': '+type(error).__name__+': '+str(error))
  if created:
   cleanup('terminate owned job/process',lambda:yes(K.TerminateJobObject(job,130) if assigned else K.TerminateProcess(process.hProcess,130)))
   cleanup('wait owned process',lambda:yes(K.WaitForSingleObject(process.hProcess,5000)==0))
   try:
    if assigned:
     until=time.monotonic()+5
     while True:
      final_account=ACCOUNT();yes(K.QueryInformationJobObject(job,1,C.byref(final_account),C.sizeof(final_account),None))
      if final_account.ActiveProcesses==0:reaped=True;break
      if time.monotonic()>=until:raise RuntimeError('owned job members remain after termination')
      time.sleep(.02)
    else:reaped=K.WaitForSingleObject(process.hProcess,0)==0
    if not reaped:raise RuntimeError('owned suspended process reaping unproved')
   except BaseException as error:cleanup_errors.append('reap owned process tree: '+type(error).__name__+': '+str(error))
   if appcontainer is not None and reaped:cleanup('record AppContainer job reaping',appcontainer.job_reaped)
   for handle in (process.hThread,process.hProcess):cleanup('close owned process handle',lambda h=handle:yes(K.CloseHandle(h)))
  cleanup('close owned job',lambda:yes(K.CloseHandle(job)))
  if cleanup_errors:raise RuntimeError('Windows process cleanup incomplete: '+'; '.join(cleanup_errors))

# Setup is restricted to this one canary's authoring prerequisites.  This is not
# a configurable gate, Native runner alternative, or network-isolation claim.
_SETUP_ROOTS={}

@contextmanager
def _owned_setup_root(root):
 if (os.environ.get('GITHUB_ACTIONS')!='true' or os.environ.get('RUNNER_OS')!='Windows'
     or os.environ.get('RUNNER_ENVIRONMENT')!='github-hosted'
     or os.environ.get('GITHUB_REPOSITORY')!='faisalm7/KiCad-Autorouter'):
  raise RuntimeError('owned setup is restricted to standard GitHub Windows hosted CI')
 runner=Path(os.environ['RUNNER_TEMP']).absolute();root=safe(root,runner)
 if root.parent!=runner or not re.fullmatch(r'kicad-appcontainer007-[0-9a-f]{32}-setup',root.name):raise ValueError('exact owned AppContainer007 setup scope required')
 key=str(root)
 if key not in _SETUP_ROOTS:root.mkdir()
 handle=K.CreateFileW(str(root),0x80000000,3,None,3,0x02200000,None)
 if handle==C.c_void_p(-1).value:raise C.WinError(C.get_last_error())
 try:
  info=FILEINFO();yes(K.GetFileInformationByHandle(handle,C.byref(info)))
  if not info.dwFileAttributes&0x10 or info.dwFileAttributes&0x400:raise ValueError('owned setup directory required')
  identity=[info.dwVolumeSerialNumber,info.nFileIndexHigh,info.nFileIndexLow]
  contract=dict(file_id=identity,runner_pid=os.getpid(),runner_source_sha256=digest(__file__))
  if key in _SETUP_ROOTS and _SETUP_ROOTS[key]!=contract:raise RuntimeError('owned setup identity/source changed')
  _SETUP_ROOTS[key]=dict(contract)
  yield root,dict(contract)
  after=FILEINFO();yes(K.GetFileInformationByHandle(handle,C.byref(after)))
  if identity!=[after.dwVolumeSerialNumber,after.nFileIndexHigh,after.nFileIndexLow] or digest(__file__)!=contract['runner_source_sha256']:raise RuntimeError('owned setup directory/source changed')
 finally:yes(K.CloseHandle(handle))

def _setup_argv(argv,root):
 """Allow exactly the two owned probe builds or the fixed DNS helper."""
 if type(argv) is not list or not argv or any(type(x) is not str or not x or any(c in x for c in '\0\r\n') for x in argv):raise ValueError('typed owned setup argv required')
 exe=Path(argv[0]).absolute()
 if exe.resolve(strict=True)!=exe:raise ValueError('canonical owned setup executable required')
 current=Path(sys.executable).resolve(strict=True)
 if exe==current:
  helper=Path(__file__).with_name('appcontainer_dns.py').resolve(strict=True)
  if argv!=[str(current),'-I','-B',str(helper)]:raise ValueError('exact isolated owned DNS-helper argv required')
  return exe,[helper],dict(kind='fixed-owned-DNS-helper',helper_sha256=digest(helper))
 # Compiler paths and options cannot be repurposed to launch a Native worker,
 # another source file, a response file, post-build hook or arbitrary linker.
 allowed=[Path(os.environ[key]).absolute()/'Microsoft Visual Studio' for key in ('ProgramFiles','ProgramFiles(x86)')]
 if exe.name.lower()!='cl.exe' or not any(exe.is_relative_to(p) for p in allowed):raise ValueError('preinstalled Visual Studio cl.exe or exact owned DNS helper required')
 if [p.lower() for p in exe.parts[-4:]]!=['bin','hostx64','x64','cl.exe']:raise ValueError('exact MSVC x64 compiler path required')
 vc=exe.parents[3]
 if vc.parent.name!='MSVC' or not re.fullmatch(r'[0-9]+(?:\.[0-9]+)+',vc.name):raise ValueError('versioned MSVC compiler required')
 probe=Path(__file__).with_name('appcontainer_probe.c').resolve(strict=True)
 if len(argv)!=24 or argv[1:8]!=['/nologo','/W4','/WX','/O1','/MT','/DUNICODE','/D_UNICODE'] or argv[8] not in ('/DPROBE_ROLE=1','/DPROBE_ROLE=2'):raise ValueError('exact owned canary compiler flags required')
 role=argv[8][-1]
 kit=Path(os.environ['ProgramFiles(x86)']).absolute()/'Windows Kits/10'
 include=argv[9:13]
 if any(not item.startswith('/I') for item in include):raise ValueError('fixed explicit compiler includes required')
 sdk=Path(include[1][2:]).parent
 safe(sdk,kit/'Include')
 if sdk.parent!=kit/'Include' or not re.fullmatch(r'[0-9]+(?:\.[0-9]+)+',sdk.name):raise ValueError('versioned official Windows SDK required')
 includes=[vc/'include',sdk/'ucrt',sdk/'shared',sdk/'um']
 libraries=[vc/'lib/x64',kit/'Lib'/sdk.name/'ucrt/x64',kit/'Lib'/sdk.name/'um/x64']
 target=root/('probe-parent.exe' if role=='1' else 'probe-child.exe')
 expected=[str(exe),'/nologo','/W4','/WX','/O1','/MT','/DUNICODE','/D_UNICODE','/DPROBE_ROLE='+role,
           *['/I'+str(p) for p in includes],str(probe),'/Fo'+str(root/('role'+role+'.obj')),'/Fe'+str(target),
           '/link','/INCREMENTAL:NO',*['/LIBPATH:'+str(p) for p in libraries],'kernel32.lib','advapi32.lib','ws2_32.lib']
 if argv!=expected:raise ValueError('only the exact owned AppContainer probe build is allowed')
 for path in [*includes,*libraries]:
  safe(path,vc if path.is_relative_to(vc) else kit)
  if not path.is_dir():raise ValueError('preinstalled compiler/SDK directory absent')
 if target.exists() or (root/('role'+role+'.obj')).exists():raise ValueError('fresh owned compiler outputs required')
 return exe,[probe],dict(kind='fixed-owned-C-canary-build',role=int(role),probe_sha256=digest(probe),compiler_sha256=digest(exe),SDK_version=sdk.name,MSVC_version=vc.name)

def _compiled_role_output(root,role):
 """Read the exact fresh compiler output only after the Job has been reaped."""
 if type(role) is not int or role not in (1,2):raise ValueError('exact owned compiler output role required')
 target=safe(root/('probe-parent.exe' if role==1 else 'probe-child.exe'),root)
 size=target.stat().st_size
 if not target.is_file() or not 64<=size<=4*1024**2:raise ValueError('bounded regular compiler role output required')
 with preserved(target,root) as identity:
  raw=target.read_bytes();offset=int.from_bytes(raw[60:64],'little')
  if len(raw)!=size or raw[:2]!=b'MZ' or not 64<=offset<=len(raw)-26:raise ValueError('compiler role DOS/PE header invalid')
  optional=int.from_bytes(raw[offset+20:offset+22],'little');flags=int.from_bytes(raw[offset+22:offset+24],'little')
  if (raw[offset:offset+6]!=b'PE\0\0\x64\x86' or optional<112 or offset+24+optional>len(raw)
      or raw[offset+24:offset+26]!=b'\x0b\x02' or not flags&2 or flags&0x2000):raise ValueError('compiler role must be an AMD64 PE32+ executable')
  return dict(path=str(target),role=role,bytes=size,sha256=identity['sha256'],file_id=identity['file_id'],
              validated=True,validation_after_job_reaped=True,format='AMD64 PE32+ executable; actual canary controls still required')

def run_owned_setup(argv,*,cwd,log,root,seconds=30):
 """Trusted CI authoring only; no network-isolation or Native admission path.

 First call exclusively creates root; later calls reuse its captured identity.
 Compiler outputs stay there and are copied by the controller after completion.
 Every setup process/descendant uses the same suspended Job Object lifecycle.
 """
 if type(seconds) not in (int,float) or not math.isfinite(seconds) or not 0<seconds<=30:raise ValueError('owned setup seconds must be finite and in (0,30]')
 started=time.monotonic()
 with _owned_setup_root(root) as (owned,scope_contract):
  if Path(cwd).absolute()!=owned:raise ValueError('owned setup cwd must equal its fresh root')
  log=safe(log,owned)
  if log.parent!=owned:raise ValueError('owned setup log must be directly inside scope')
  exe,inputs,authoring=_setup_argv(argv,owned)
  pins={str(p):digest(p) for p in [exe,*inputs]}
  with ExitStack() as protection:
   for path in [exe,*inputs]:
    proof=protection.enter_context(preserved(path,path.parent))
    if proof['sha256']!=pins[str(path)]:raise RuntimeError('owned setup input changed before protected launch')
   result=_run_job(argv,cwd=owned,log=log,root=owned,seconds=seconds,owned_setup=True,setup_authoring=authoring)
   if any(digest(path)!=sha for path,sha in pins.items()):raise RuntimeError('owned setup source/tool bytes changed')
   if authoring['kind']=='fixed-owned-C-canary-build' and result['status']=='success':
    if result['cleanup_complete'] is not True:result['status']='compiler_cleanup_unproved'
    else:
     try:result['compiler_output']=_compiled_role_output(owned,authoring['role'])
     except Exception as error:
      result.update(status='compiler_output_invalid',compiler_output=dict(validated=False,error=type(error).__name__+': '+str(error)[:256]))
  result.pop('_suspended_token')
  result.update(accepted=False,product_support=False,Native_admitted=False,Native_executed=False,
                network=dict(kind='owned-setup-no-network-isolation-claim',network_isolation_claimed=False),
                authoring=authoring,source_tool_sha256=pins,setup_scope=scope_contract,
                scope='Additional owned canary authoring/DNS cost only; no routing, Native admission or network-isolation claim.')
 result['wall_seconds']=time.monotonic()-started
 return result
