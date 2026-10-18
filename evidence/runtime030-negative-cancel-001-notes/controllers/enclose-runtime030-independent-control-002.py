"""Reuse shared Native lane, runner and publication for one frozen control."""
import time,resource
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import argparse,fcntl,os,stat,sys,json
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,handoff as h
from autorouter.runner import run
from autorouter.gui import child_environment
ap=argparse.ArgumentParser();ap.add_argument('--protocol',type=Path,required=True);ap.add_argument('--protocol-sha256',required=True);a=ap.parse_args()
plan=f.read_json(a.protocol);pin=p.sha(a.protocol);assert pin==a.protocol_sha256
runtime=Path(plan['runtime']);child=Path(plan['controller']);manifest=runtime/'runtime-distribution.json'
assert child.parent==runtime/'.runs' and p.sha(child)==plan['controller_sha256'] and p.sha(manifest)==plan['runtime_manifest_sha256']
assert p.sha(Path(__file__))==plan['enclosure_sha256'] and plan['pass_key'] in ('control_passed','controls_passed')
args=plan.get('controller_args',[]);assert args in ([],['--runtime',str(runtime)])
budget=plan['whole_wall_full_cpu_seconds'];assert type(budget) is int and 30<=budget<=600
delivery=Path(plan['output']);assert delivery.parent==runtime/'.runs' and delivery.name.startswith('native7-comparison-') and not delivery.exists()
out=a.protocol.parent/'enclosure';out.mkdir();owner={};h.capture_destination(owner,out)
fd=os.open(ROOT/'.runs/quality-experiment.lock',os.O_RDWR|os.O_NOFOLLOW)
with os.fdopen(fd,'r+') as lane:
 info=os.fstat(lane.fileno());assert stat.S_ISREG(info.st_mode) and info.st_nlink==1
 fcntl.flock(lane,fcntl.LOCK_EX|fcntl.LOCK_NB)
 process=run([*f.SANDBOX,str(runtime/'.venv/bin/python'),'-B',str(child),*args,'--protocol',str(a.protocol),'--protocol-sha256',pin],cwd=out,env=child_environment(),log=out/'command.log',timeout=max(.001,budget-(time.monotonic()-START)),max_log_bytes=512*1024,max_group_rss_bytes=4*1024**3,max_workdir_bytes=2*1024**2)
 p.save_json(out/'process.json',process);receipt=delivery/'result.json';data=f.read_json(receipt) if receipt.is_file() else None
 material=f.evidence_inventory(delivery) if delivery.exists() else None
 passed=bool(data and data.get(plan['pass_key']) is True and data.get('status')=='completed' and data.get('accepted') is False and data.get('production_admitted') is False and process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] and not process['log_truncated'])
 record=dict(schema=1,accepted=False,production_admitted=False,passed=passed,status='completed' if passed else 'failed',project_complete=False,actual_GUI=False,protocol_sha256=pin,process=process,child_receipt=str(receipt),child_sha256=p.sha(receipt) if data else None,completed_evidence=material,scope=plan['scope'])
 def remaining():return min(budget-(time.monotonic()-START),budget-(cpu()-CPU0))
 def fresh():
  h.owned_destination(owner)
  assert p.sha(a.protocol)==pin and p.sha(Path(__file__))==plan['enclosure_sha256'] and p.sha(child)==plan['controller_sha256'] and p.sha(manifest)==plan['runtime_manifest_sha256']
  assert (f.evidence_inventory(delivery) if delivery.exists() else None)==material
 def account():
  record.update(complete_wall_seconds=time.monotonic()-START,complete_full_CPU_seconds=cpu()-CPU0)
  if remaining()<=0:record.update(passed=False,status='budget_exceeded')
  if record['status']!='completed':record['passed']=False
 f.publish(out,record,fresh,account,remaining,owned=lambda:h.owned_destination(owner),final_check=fresh)
 print(json.dumps({k:v for k,v in record.items() if k not in ('process','completed_evidence')}));raise SystemExit(0 if record['passed'] and record['status']=='completed' else 2)
