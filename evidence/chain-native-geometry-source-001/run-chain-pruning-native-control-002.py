"""Bounded sequential native component controls, no routing or production admission."""
import time,resource
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import json,sys,os,stat,fcntl,subprocess
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,config as c
from autorouter.runner import run
O=R/'.runs/chain-pruning-native-control-execution-002';O.mkdir();out=R/'.runs/chain-pruning-native-control-002'
tools=p.tool_manifest();own={str(q.relative_to(R)):p.sha(q) for q in (R/'experiments/chain_pruning_v1').glob('*.py')}
clean=lambda:subprocess.check_output(['git','status','--porcelain=v1','--untracked-files=normal'],cwd=R)==b''
assert clean() and all(p.sha(R/n)==pin for n,pin in own.items()) and not out.exists()
for n,pin in own.items():assert __import__('hashlib').sha256(subprocess.check_output(['git','show',tools['git_head']+':'+n],cwd=R)).hexdigest()==pin
wrapper=c.PCBNEW.with_name('pcbnew.py');wrapperpin=p.sha(wrapper);assert wrapperpin=='cd1c06c4709c653256ebd0c98c66d80cd72033767fac27c34ea01b5ec586116a'
fd=os.open(R/'.runs/quality-experiment.lock',os.O_RDWR|os.O_NOFOLLOW);lock=os.fdopen(fd,'r+');assert stat.S_ISREG(os.fstat(lock.fileno()).st_mode);fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
record=dict(schema=1,passed=False,native_executed=False,routing_executed=False,production_admitted=False,tools=tools,extra_source_sha256=own,wrapper_sha256=wrapperpin,controller_sha256=p.sha(Path(__file__)),budget_seconds=110,cpu_budget_seconds=110,publication_allowance_seconds=2)
try:
 process=run([str(R/'.venv/bin/python'),'-B',str(R/'experiments/chain_pruning_v1/native_control.py'),'--run-native','--output',str(out)],cwd=O,log=O/'command.log',timeout=max(.001,108-(time.monotonic()-START)),max_log_bytes=128*1024,max_workdir_bytes=2*1024**2,max_group_rss_bytes=4*1024**3);record.update(process=process,native_executed=True)
 stable=p.tool_manifest()==tools and clean() and all(p.sha(R/n)==pin for n,pin in own.items()) and p.sha(wrapper)==wrapperpin
 record['source_current']=stable
 if (out/'result.json').is_file():
  receipt=f.read_json(out/'result.json');record.update(receipt_sha256=p.sha(out/'result.json'),observed_status=receipt.get('status'),observed_passed=receipt.get('passed'),actual_controls=len(receipt.get('controls',[])))
  material=f.evidence_inventory(out);assert material==receipt['completed_material']
  record['passed']=stable and process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] and receipt.get('status')=='completed' and receipt.get('passed') is True
except BaseException as ex:record.update(passed=False,error=type(ex).__name__+': '+str(ex))
finally:
 record.update(wall_seconds=time.monotonic()-START,full_cpu_seconds=cpu()-CPU0,log_sha256=p.sha(O/'command.log') if (O/'command.log').is_file() else None)
 if max(record['wall_seconds'],record['full_cpu_seconds'])+2>110:record.update(passed=False,error='Whole control delivery exceeds110s')
 p.save_json(O/'execution.json',record);lock.close()
print(json.dumps({k:record.get(k) for k in ('passed','observed_status','actual_controls','wall_seconds','full_cpu_seconds','error')}));raise SystemExit(0 if record['passed'] else 2)
