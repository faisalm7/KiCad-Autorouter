"""Generic finite local native five-method comparison. No source acquisition or free incumbent."""
import time,resource
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import sys,os,stat,fcntl,shutil,subprocess,json,argparse
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f
from autorouter.runner import run
from scripts import experiment_quality as q
from experiments.native_paired_v1.observations import require,inventory
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--prospective',type=Path,required=True);args=parser.parse_args();P=args.prospective.resolve(strict=True);spec=f.read_json(P);pin=p.sha(P);O=Path(spec['output']);CAP=800
clean=lambda:subprocess.check_output(['git','status','--porcelain=v1','--untracked-files=normal'],cwd=R)==b''
def stable():
 q.verify_freeze(spec['freeze'],Path(spec['source']))
 require(p.sha(P)==pin and spec['status']=='frozen' and spec['limits']==dict(reader=90,delivered=300,inner=120,outer=800,output=128*1024**2),'frozen protocol limits differ')
 require(spec['include_chain_ablation'] is True and spec['arm_order']==['B0','B1','B2_portfolio','C_feedback','C_chains'],'fivearm contract differs')
 for key in ('controller','reader'):require(p.sha(Path(spec[key+'_source']))==spec[key+'_sha256'],key+' source changed')
 require(p.sha(Path(__file__))==spec['controller_sha256'],'wrong controller')
 for name,digest in {**spec['pins'],**spec['reader_dependencies_sha256']}.items():require(p.sha(R/name)==digest,'support changed: '+name)
stable();require(clean() and not O.exists(),'clean current checkpoint and unused output required')
fd=os.open(R/'.runs/quality-experiment.lock',os.O_RDWR|os.O_NOFOLLOW);lock=os.fdopen(fd,'r+');require(stat.S_ISREG(os.fstat(lock.fileno()).st_mode),'invalid lane lock');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
O.mkdir();shutil.copyfile(P,O/'prospective-protocol.json')
for key in ('controller','reader'):shutil.copyfile(Path(spec[key+'_source']),O/(key+'.py'))
for name in spec['reader_dependencies_sha256']:
 dest=O/'reader-dependencies'/name.removeprefix('experiments/');dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(R/name,dest)
record=dict(schema=1,passed=False,qualified=False,accepted=False,production_qualified=False,git_head=spec['git_head'],tools=spec['tools'],protocol_sha256=pin,controller_sha256=spec['controller_sha256'],reader_sha256=spec['reader_sha256'],clean_before=True,source_current=False)
try:
 argv=[*f.SANDBOX,str(R/'.venv/bin/python'),'-B',str(R/'scripts/experiment_paired.py'),'--project',spec['project'],'--system','native-all','--chain-ablation','--external-reserve-seconds','0','--output',str(O/'run')]
 # The shared CLI owns this SAME mutex throughout all five arms. Do not
 # recursively retain the parent's independent flock while it acquires it.
 fcntl.flock(lock,fcntl.LOCK_UN)
 try:
  record['process']=run(argv,cwd=O,log=O/'command.log',timeout=max(.001,CAP-2-(time.monotonic()-START)),max_log_bytes=256*1024,max_workdir_bytes=128*1024**2,max_group_rss_bytes=4*1024**3)
 finally:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 record['lock_scope']='parent preparation/finalization; unchanged shared CLI owns same mutex during actual fivearm execution'
 stable();record['source_current']=True;record['clean_after']=clean()
 for field,name in [('paired_summary','run/paired-summary.json'),('paired_protocol','run/protocol.json')]:record[field+'_sha256']=p.sha(O/name) if (O/name).is_file() else None
 proc=record['process'];summary=f.read_json(O/'run/paired-summary.json') if (O/'run/paired-summary.json').is_file() else {}
 record['passed']=record['clean_after'] and proc['status']=='success' and proc['exit_code']==0 and proc['cleanup_complete'] is True and proc.get('log_truncated') is False and summary.get('status')=='completed'
except (Exception,KeyboardInterrupt) as exc:record.update(passed=False,reason=type(exc).__name__+': '+str(exc))
finally:
 try:record['material']=inventory(O)
 except Exception as exc:record.update(passed=False,material_error=type(exc).__name__+': '+str(exc))
 record.update(wall_seconds=time.monotonic()-START,full_cpu_seconds=cpu()-CPU0)
 if max(record['wall_seconds'],record['full_cpu_seconds'])+2>CAP:record.update(passed=False,budget_error=True)
 p.save_json(O/'execution.json',record);lock.close()
print(json.dumps({k:record.get(k) for k in ('passed','reason','wall_seconds','full_cpu_seconds')}));raise SystemExit(0 if record['passed'] else 2)
