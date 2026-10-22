"""One finite post-reader/pre-open metadata control; no product or Native changes.
Temporarily pause only the freshly verified owned GUI so its existing CLI reader
can finish. Link one job-owned export PRL after its positive JSON, then always
resume the GUI. Does not prove that CallAfter was enqueued before intervention.
"""
from pathlib import Path
import ctypes,datetime,json,os,signal,subprocess,sys,time
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R));sys.dont_write_bytecode=True
from autorouter import pipeline as p,placement_clearance as io
from scripts.native_cancellation import process_metadata,output_bytes,_DarwinBSDInfo
T=R/'.runs/runtime057 fresh install 001';B=T/'.runs/gui-session091';W=B/'jobs/autorouter-gui-4baaf37eb6f34cb295f2843f19f69830'
GUI=dict(pid=21991,ppid=21842,pgid=21840);C=B/'late-metadata-control-001';C.mkdir(mode=0o700)
pre=B/'preopen-late-metadata-001/preopen.json';baseline=json.loads(io.read_bytes(pre,1024**2));assert baseline['workspace']==str(W) and baseline['route']['current'] and baseline['export']['current']
assert io.inventory(W/'export',max_bytes=64*1024**2)==baseline['snapshot_hashes']
prl=W/'export/validation/final-drc-input/owned1007-transport.kicad_prl';assert prl.stat().st_nlink==1 and prl.stat().st_flags==0
start=time.monotonic();stopped=False;report=dict(schema=1,kind='one-post-CLI-reader-before-opening-PRL-metadata-control',actual_GUI_outcome_observed=False,CallAfter_enqueued_before_mutation_proved=False,controller_sha256=p.sha(Path(__file__)),preopen_sha256=p.sha(pre),GUI=GUI,workspace=str(W),passed=False,Native_executed_by_controller=False,helper_sha256=p.sha(R/'scripts/native_cancellation.py'))
def command(pid):
 q=subprocess.run(['/bin/ps','-p',str(pid),'-o','command='],capture_output=True,timeout=2,check=True);assert len(q.stdout)<16384 and not q.stderr;return q.stdout.decode().strip()
assert ctypes.sizeof(_DarwinBSDInfo)==136
lib=ctypes.CDLL('/usr/lib/libproc.dylib',use_errno=True)
lib.proc_pidinfo.argtypes=[ctypes.c_int,ctypes.c_int,ctypes.c_uint64,ctypes.c_void_p,ctypes.c_int];lib.proc_pidinfo.restype=ctypes.c_int
def identity(pid):
 info=_DarwinBSDInfo();ctypes.set_errno(0);size=lib.proc_pidinfo(pid,3,0,ctypes.byref(info),ctypes.sizeof(info))
 assert size==136 and ctypes.get_errno()==0 and info.pid==pid and info.uid==os.getuid()
 return dict(pid=int(info.pid),ppid=int(info.ppid),pgid=int(info.pgid),uid=int(info.uid),start_seconds=int(info.start_seconds),start_microseconds=int(info.start_microseconds)),dict(status=int(info.status),xstatus=int(info.xstatus))
gui_identity,_=identity(GUI['pid']);assert all(gui_identity[k]==v for k,v in GUI.items())
report['GUI_start_identity']=gui_identity
report['exit_status_API_sources']=['https://github.com/apple/darwin-xnu/blob/main/bsd/kern/proc_info.c','https://github.com/apple/darwin-xnu/blob/main/tests/proc_info.c']
def gui_current():
 assert GUI in process_metadata(parent_pid=GUI['ppid']) and identity(GUI['pid'])[0]==gui_identity
 assert command(GUI['pid']).endswith('/Python -B -m autorouter.gui')
def state(pid):
 q=subprocess.run(['/bin/ps','-p',str(pid),'-o','stat='],capture_output=True,timeout=2,check=True);assert len(q.stdout)<128 and not q.stderr;return q.stdout.decode().strip()
try:
 gui_current();prior=set(W.glob('inspect-export-*.command.log'));assert not prior
 while time.monotonic()-start<20:
  cli=process_metadata(parent_pid=GUI['pid']);logs=set(W.glob('inspect-export-*.command.log'))-prior
  if len(cli)==len(logs)==1:
   row=cli[0];cli_identity,_=identity(row['pid']);assert all(cli_identity[k]==v for k,v in row.items());cmd=command(row['pid']);assert str(T/'.venv/bin/python')+' -B -m autorouter review-export-check '+str(W/'export/export.json')==cmd
   log=next(iter(logs));assert not log.with_suffix('.process.json').exists()
   gui_current();os.kill(GUI['pid'],signal.SIGSTOP);stopped=True
   report.update(CLI=row,command=cmd,inspection_log=str(log),pause_requested_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
   while time.monotonic()-start<30 and not state(row['pid']).startswith('Z'):time.sleep(.02)
   assert state(row['pid']).startswith('Z'),'CLI not observed exited within finite pause'
   after_identity,exit_info=identity(row['pid']);assert after_identity==cli_identity and exit_info['xstatus']==0
   # The stopped GUI owns the stdout pipe reader: do not assume it flushed JSON.
   # Its exact positive log/process and final GUI refusal must be checked AFTER resume.
   report.update(CLI_start_identity=cli_identity,CLI_exit_info=exit_info,positive_JSON_after_resume_required=True)
   assert io.inventory(W/'export',max_bytes=64*1024**2)==baseline['snapshot_hashes'];assert prl.stat().st_nlink==1 and prl.stat().st_flags==0
   pin=p.sha(prl);os.link(prl,C/'retained-PRL-link.kicad_prl');assert prl.stat().st_nlink==2 and p.sha(prl)==pin
   output_bytes(C);report.update(CLI_observed_zombie=True,mutation='Created one retained hardlink to final-drc-input PRL only after owned reader CLI zombie/exit0 while GUI paused; positive stdout proof is required after resume.',PRL_path=str(prl),PRL_sha256_unchanged=pin,PRL_links_before=1,PRL_links_after=2,PRL_flags=0,mutation_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),control_intervention_completed=True);break
  time.sleep(.01)
 else:raise AssertionError('No unique new owned opening reader; no intervention')
except BaseException as exc:report['error']=type(exc).__name__+': '+str(exc)
finally:
 if stopped:
  try:gui_current();os.kill(GUI['pid'],signal.SIGCONT);report['resume_requested']=True;report['resume_requested_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
  except BaseException as exc:report['resume_error']=type(exc).__name__+': '+str(exc)
 report.update(wall_seconds=time.monotonic()-start,waiting_deadline_seconds=30,post_wait_work='Bounded <=64MiB inventory/hash/link and2s process queries can extend the wait deadline; actual pause interval is recorded, not OS-enforced.',scope='One temporary owned-GUI process pause; exact original source/settings/runtime unchanged. No engine/Native run, old PID signal, global OS setting, deletion or repair. GUI outcome and post-reader final-fence refusal require separate actual observation. No claim callback already enqueued or hostile concurrent-writer atomicity.')
 p.save_json(C/'intervention.json',report)
print(json.dumps(report));raise SystemExit(0 if report.get('control_intervention_completed') and report.get('resume_requested') and 'error' not in report else 2)
