"""Existing bounded runner/publication enclosure, one owned Native control pair."""
import time,resource
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in(resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import os,sys,json
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,handoff as h
from autorouter.runner import run
from experiments.hfe_original_native_v1.driver import material
out=ROOT/'.runs/duplicate-artwork-field-native-001';out.mkdir();owner={};h.capture_destination(owner,out)
driver=ROOT/'experiments/duplicate_artwork_fields_v1/driver.py';pin=p.sha(driver);tools=p.tool_manifest();processes=[]
env={k:v for k,v in os.environ.items()if k not in {'PYTHONPATH','PYTHONHOME','KICAD_API_SOCKET','KICAD_API_TOKEN'}}
def remaining():return min(120-(time.monotonic()-START),120-(cpu()-CPU0))
record=dict(schema=1,accepted=False,passed=False,status='failed',tools=tools,driver_sha256=pin,steps=processes,scope='Bounded Native field-census prerequisite, no engine/routing support/comparison claim. Prepare and full positive/hidden-field negative costs included; authoring/review costs unknown, not zero.')
try:
 for name,args,cap in [('prepare',['prepare','--preparation',str(out/'preparation')],30),('native',['run','--preparation',str(out/'preparation'),'--output',str(out/'native')],112)]:
  process=run([*f.SANDBOX,str(ROOT/'.venv/bin/python'),'-B',str(driver),*args],cwd=out,log=out/(name+'.log'),timeout=max(.001,min(cap,remaining()-2)),env=env,max_log_bytes=256*1024,max_workdir_bytes=128*1024**2,max_group_rss_bytes=2*1024**3)
  process['name']=name;processes.append(process)
  if process['status']!='success' or process['exit_code']!=0 or process['cleanup_complete']is not True or process['log_truncated']is not False:raise p.Rejected(name+': '+process['status']+' exit='+str(process['exit_code']))
 child=f.read_json(out/'native/result.json')
 if child.get('passed')is not True or child.get('status')!='completed' or child.get('accepted')is not False or material(out/'native')!=child['completed_evidence']:raise p.Rejected('Native child proof missing/changed/failed')
 record.update(passed=True,status='completed',child_sha256=p.sha(out/'native/result.json'))
except(Exception,KeyboardInterrupt)as exc:record.update(passed=False,status='cancelled'if isinstance(exc,KeyboardInterrupt)else'failed',reason=type(exc).__name__+': '+str(exc))
witness=material(out);record['completed_evidence']=witness
def stable():
 h.owned_destination(owner)
 if p.sha(driver)!=pin or p.tool_manifest()!=tools or material(out)!=witness:raise p.Rejected('enclosed controls/source/runtime changed')
def account():
 record.update(wall_seconds=time.monotonic()-START,full_CPU_seconds=cpu()-CPU0)
 if remaining()<=0:record.update(passed=False,status='budget_exceeded')
 if record['status']!='completed':record['passed']=False
f.publish(out,record,stable,account,remaining,owned=lambda:h.owned_destination(owner),final_check=stable)
stored=f.read_json(out/'result.json');print(json.dumps({k:stored.get(k)for k in ('passed','status','reason','wall_seconds','full_CPU_seconds')}));raise SystemExit(0 if stored.get('passed')is True and stored.get('status')=='completed'else 2)
