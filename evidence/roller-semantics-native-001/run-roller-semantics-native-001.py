"""One prospectively pinned sequential native support diagnostic, no engine."""
from pathlib import Path
import json,sys,time,fcntl
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f
from autorouter.runner import run
out=ROOT/'.runs/roller-semantics-native-001-execution';out.mkdir()
protocol=ROOT/'.runs/roller-semantics-native-001-protocol.json';frozen=f.read_json(protocol);assert frozen['tools']==p.tool_manifest()
argv=[*f.SANDBOX,str(ROOT/'.venv/bin/python'),'-B','-c',"from pathlib import Path; import sys; sys.path.insert(0,'/Users/faisal/Projects/KiCad-Autorouter-local'); from experiments.roller_support_v1.driver import experiment; import json; r=experiment(Path('/Users/faisal/Projects/KiCad-Autorouter-local/.runs/roller-semantics-native-001'),run_native=True); print(json.dumps({k:r[k] for k in ('status','controls_passed')})); raise SystemExit(0 if r['controls_passed'] else 2)"]
start=time.monotonic();cpu=time.process_time()+f.child_cpu()
with (ROOT/'.runs/quality-experiment.lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 result=run(argv,cwd=out,log=out/'command.log',timeout=120,max_log_bytes=256*1024,max_workdir_bytes=32*1024**2,max_group_rss_bytes=2*1024**3)
wall=time.monotonic()-start;cost=time.process_time()+f.child_cpu()-cpu
record={'schema':1,'process':result,'wall_seconds':wall,'full_cpu_seconds':cost,'within120_wall_full_cpu':max(wall,cost)<=120,'protocol_sha256':p.sha(protocol),'wrapper_sha256':p.sha(Path(__file__)),'actual_result_sha256':p.sha(ROOT/'.runs/roller-semantics-native-001/result.json') if (ROOT/'.runs/roller-semantics-native-001/result.json').exists() else None,'scope':'Sequential native observer/refill/DRC support controls only; noengine orproductionadmission; exactoriginalclasses/layer/text/rules retained.'}
p.save_json(out/'execution.json',record);print(json.dumps({k:record[k] for k in ('wall_seconds','full_cpu_seconds','within120_wall_full_cpu')}));raise SystemExit(0 if result['status']=='success' and result['exit_code']==0 and record['within120_wall_full_cpu'] else 2)
