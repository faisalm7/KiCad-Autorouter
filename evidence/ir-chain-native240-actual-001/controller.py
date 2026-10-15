"""Finite local five-method experiment; shared runner, lock, source freeze and inventories."""
import time,resource
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import sys,os,stat,fcntl,shutil,subprocess,json,datetime
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,placement_clearance as pc
from autorouter.runner import run
from scripts import experiment_quality as q
from experiments.native_paired_v1.observations import require,inventory
P=R/'.runs/ir-chain-fivearm-001-protocol.json';spec=f.read_json(P);pin=p.sha(P);O=Path(spec['output']);CAP=800
clean=lambda:subprocess.check_output(['git','status','--porcelain=v1','--untracked-files=normal'],cwd=R)==b''
def stable():
 q.verify_freeze(spec['freeze'],Path(spec['source']))
 require(p.sha(P)==pin and spec['status']=='frozen' and spec['limits']==dict(reader=45,delivered=240,inner=120,outer=800,output=44*1024**2),'frozen protocol limits differ')
 for key,path in [('controller',Path(__file__)),('actor',R/'.runs/ir-chain-fivearm-001-actor.py'),('reader',R/'.runs/read-ir-chain-fivearm-001.py')]:require(p.sha(path)==spec[key+'_sha256'],key+' source changed')
 for name,digest in {**spec['pins'],**spec['dependencies']}.items():require(p.sha(R/name)==digest,'support changed: '+name)
stable();require(clean() and not O.exists(),'clean current checkpoint and unused output required')
fd=os.open(R/'.runs/quality-experiment.lock',os.O_RDWR|os.O_NOFOLLOW);lock=os.fdopen(fd,'r+');require(stat.S_ISREG(os.fstat(lock.fileno()).st_mode),'invalid lane lock');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
O.mkdir();shutil.copyfile(P,O/'prospective-protocol.json')
for key,path in [('controller',Path(__file__)),('actor',R/'.runs/ir-chain-fivearm-001-actor.py'),('reader',R/'.runs/read-ir-chain-fivearm-001.py')]:shutil.copyfile(path,O/(key+'.py'))
for name in spec['dependencies']:
 dest=O/'reader-dependencies'/name.removeprefix('experiments/');dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(R/name,dest)
record=dict(schema=1,passed=False,qualified=False,accepted=False,production_qualified=False,git_head=spec['git_head'],tools=spec['tools'],protocol_sha256=pin,controller_sha256=spec['controller_sha256'],actor_sha256=spec['actor_sha256'],reader_sha256=spec['reader_sha256'],clean_before=True,source_current=False,started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
try:
 record['process']=run([*f.SANDBOX,str(R/'.venv/bin/python'),'-B',str(R/'.runs/ir-chain-fivearm-001-actor.py')],cwd=O,log=O/'command.log',timeout=max(.001,CAP-2-(time.monotonic()-START)),max_log_bytes=256*1024,max_workdir_bytes=44*1024**2,max_group_rss_bytes=4*1024**3)
 stable();record['source_current']=True;record['clean_after']=clean()
 for field,name in [('paired_summary','run/paired-summary.json'),('paired_protocol','run/protocol.json'),('chain_invocation','chain-invocation.json'),('actor_result','actor-result.json')]:record[field+'_sha256']=p.sha(O/name) if (O/name).is_file() else None
 process=record['process'];actor=f.read_json(O/'actor-result.json') if (O/'actor-result.json').is_file() else {}
 record['passed']=record['clean_after'] and process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] is True and process.get('log_truncated') is False and actor.get('status')=='completed'
except (Exception,KeyboardInterrupt) as exc:record.update(passed=False,reason=type(exc).__name__+': '+str(exc))
finally:
 try:
  # Receipt is written only after witnessing the complete actor output.
  record['material']=inventory(O)
 except Exception as exc:record.update(passed=False,material_error=type(exc).__name__+': '+str(exc))
 record.update(wall_seconds=time.monotonic()-START,full_cpu_seconds=cpu()-CPU0)
 if max(record['wall_seconds'],record['full_cpu_seconds'])+2>CAP:record.update(passed=False,budget_error=True)
 p.save_json(O/'execution.json',record);lock.close()
print(json.dumps({k:record.get(k) for k in ('passed','reason','wall_seconds','full_cpu_seconds')}));raise SystemExit(0 if record['passed'] else 2)
