from pathlib import Path
import fcntl,json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from experiments.licensed_acquisition_v1 import fetch as shared
from experiments.original_project_native_v1 import driver
with shared.cancellation(),(ROOT/'.runs/experiment.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 result=driver.experiment('als311-clock',ROOT/'.runs/als311-original-native-001',run_native=True)
print(json.dumps({k:result.get(k) for k in ('status','error','native_routing_scope_accepted','schematic_parity_findings','wall_seconds','total_cpu_seconds','within_budget')}));raise SystemExit(0 if result['status']=='observed' else 2)
