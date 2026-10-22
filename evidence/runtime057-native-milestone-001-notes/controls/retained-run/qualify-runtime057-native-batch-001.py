"""Eleven fixed sequential jobs through the existing workflow enclosure."""
from pathlib import Path
import fcntl,json,os,resource,stat,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,gui
from autorouter.runner import run
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu();base=ROOT/'.runs/runtime057-native-qualification-001'
frozen=f.read_json(base/'frozen.json');assert len(frozen['protocols'])==11
assert frozen['source_head']=='ac1a48c3b25b2217e0f8252e0e6da21905f144a4'
encloser=ROOT/'.runs/enclose-runtime044-workflow-001.py';assert p.sha(encloser)==frozen['enclosure_sha256']
result=base/'batch-result.json';assert not result.exists();rows=[]
fd=os.open(ROOT/'.runs/quality-experiment.lock',os.O_RDWR|os.O_NOFOLLOW)
with os.fdopen(fd,'r+') as lane:
 info=os.fstat(lane.fileno());assert stat.S_ISREG(info.st_mode) and info.st_nlink==1
 fcntl.flock(lane,fcntl.LOCK_EX|fcntl.LOCK_NB)
 for row in frozen['protocols']:
  protocol=Path(row['protocol']);assert p.sha(protocol)==row['protocol_sha256']
  folder=protocol.parent;assert not (folder/'execution.json').exists() and not (folder/'batch-process.json').exists()
  process=run(['/usr/bin/time','-lp',str(ROOT/'.venv/bin/python'),'-B',str(encloser),'--protocol',str(protocol)],
   cwd=folder,env=gui.child_environment(),log=folder/'complete-command-and-time.log',timeout=min(270,max(.001,900-max(time.monotonic()-START,cpu()-CPU0))),
   max_log_bytes=128*1024,max_workdir_bytes=4*1024**2,max_group_rss_bytes=4*1024**3)
  p.save_json(folder/'batch-process.json',process)
  completed=f.read_json(folder/'execution.json') if (folder/'execution.json').exists() else None
  passed=bool(completed and completed['controls_passed'] and completed['workflow_delivered'] and process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] and not process['log_truncated'])
  rows.append(dict(case=row['case'],passed=passed,execution_sha256=p.sha(folder/'execution.json') if completed else None,process_sha256=p.sha(folder/'batch-process.json'),complete_log_sha256=p.sha(folder/'complete-command-and-time.log')))
  print(json.dumps(rows[-1]),flush=True)
  if not passed:break
record=dict(schema=1,kind='eleven-fixed-current-owned-workflow-dispatch-v1',passed=len(rows)==11 and all(row['passed'] for row in rows) and max(time.monotonic()-START,cpu()-CPU0)<=900,rows=rows,wall_seconds=time.monotonic()-START,full_CPU_seconds=cpu()-CPU0,frozen_sha256=p.sha(base/'frozen.json'),controller_sha256=p.sha(Path(__file__)),project_complete=False,actual_GUI=False,scope='Thin finite sequential dispatcher only. Existing unchanged workflow enclosure/qualifier owns Native/source/protected/delivery checks. Individual complete external time records are in each combined log; their nested samples overlap. Batch external exit costs additional supervisor overhead; no reruns or new comparison/breadth/GUI claim.')
p.save_json(result,record);print(json.dumps(dict(passed=record['passed'],completed_cases=len(rows),project_complete=False)))
raise SystemExit(0 if record['passed'] else 2)
