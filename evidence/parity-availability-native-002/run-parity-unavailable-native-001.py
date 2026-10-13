from pathlib import Path
import json,sys,time,fcntl
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f
from autorouter.runner import run
out=ROOT/'.runs/parity-unavailable-native-001-execution';out.mkdir();source=ROOT/'.runs/parity-availability-draft-001/native_control.py'
p.save_json(out/'protocol.json',{'tools':p.tool_manifest(),'controller_sha256':p.sha(source),'native_stages':1,'wall_full_cpu_cap_seconds':30,'intentional_controller_exit_code':2,'scope':'Owned copied validationSCH temporaryunavailability; exactbefore/afteroriginalrestored, actualnative skiplogged. Diagnosticonly, noengine orroutingreceipt.'})
start=time.monotonic();cpu=time.process_time()+f.child_cpu()
with (ROOT/'.runs/quality-experiment.lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 r=run([*f.SANDBOX,str(ROOT/'.venv/bin/python'),'-B',str(source),'--output',str(ROOT/'.runs/parity-unavailable-native-001')],cwd=ROOT,log=out/'command.log',timeout=30,max_log_bytes=128*1024,max_group_rss_bytes=2*1024**3)
record={'process':r,'wall_seconds':time.monotonic()-start,'full_cpu_seconds':time.process_time()+f.child_cpu()-cpu,'wrapper_sha256':p.sha(Path(__file__)),'scope':'Completeforegroundnativeavailabilitycontrol, intentionalnegativeexit2; noacceptedroute/solver/benchmark.'}
p.save_json(out/'execution.json',record);print(json.dumps({k:record[k] for k in ('wall_seconds','full_cpu_seconds')}))
