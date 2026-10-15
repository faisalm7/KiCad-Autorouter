import time,resource
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import sys,json,fcntl
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,placement_clearance as pc
from autorouter.runner import run
OUT=ROOT/'.runs/literal-composite-native-controls-execution-001';OUT.mkdir();ACTOR=ROOT/'experiments/literal_composite_controls_v1/run.py';RESULT=ROOT/'.runs/literal-composite-native-controls-001/result.json'
tools=p.tool_manifest();pins={n:p.sha(ROOT/n) for n in ('experiments/literal_composite_controls_v1/run.py','experiments/netclass_parent_transport_v1/fixture.py','experiments/placement_handoff_native_v1/driver.py','autorouter/netclass.py')};record=dict(schema=1,passed=False,source_current=False,tools=tools,publication_allowance_seconds=2,actor_sha256=p.sha(ACTOR),process=None)
try:
 lock=ROOT/'.runs/quality-experiment.lock';assert not lock.is_symlink()
 with lock.open('a') as held:
  fcntl.flock(held,fcntl.LOCK_EX|fcntl.LOCK_NB)
  record['process']=run([*f.SANDBOX,str(ROOT/'.venv/bin/python'),'-B',str(ACTOR)],cwd=OUT,log=OUT/'command.log',timeout=max(.001,178-(time.monotonic()-START)),max_log_bytes=128*1024,max_workdir_bytes=2*1024**2,max_group_rss_bytes=2*1024**3)
 result=f.read_json(RESULT);record['actor_result_sha256']=p.sha(RESULT)
 record['actor_material']=pc.inventory(RESULT.parent,max_bytes=64*1024**2,max_files=3000,max_entries=6000)
 record['source_current']=p.tool_manifest()==tools and all(p.sha(ROOT/n)==pin for n,pin in pins.items())
 record['passed']=record['source_current'] and result['controls_passed'] is True and result['source_unchanged'] is True and result['status']=='completed' and record['process']['status']=='success' and record['process']['exit_code']==0 and record['process']['cleanup_complete'] is True and record['process']['log_truncated'] is False
except BaseException as exc:record.update(reason=type(exc).__name__+': '+str(exc))
record.update(wall_seconds=time.monotonic()-START,full_cpu_seconds=cpu()-CPU0,source_pins=pins,controller_sha256=p.sha(Path(__file__)))
record['passed']=record['passed'] and max(record['wall_seconds'],record['full_cpu_seconds'])+2<=180
p.save_json(OUT/'execution.json',record);print(json.dumps({k:record.get(k) for k in ('passed','source_current','wall_seconds','full_cpu_seconds','reason')}));raise SystemExit(0 if record['passed'] else 2)
