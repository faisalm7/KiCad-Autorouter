from pathlib import Path
import sys,json,fcntl
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from experiments.roller_export_alias_v1 import driver
with (ROOT/'.runs/quality-experiment.lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 result=driver.experiment(ROOT/'.runs/roller-export-alias-native-003',run_native=True,resume_completed_exports=True)
print(json.dumps({k:result.get(k) for k in ('status','controls_passed','reason','wall_seconds','full_cpu_seconds','combined_active_wall_seconds','combined_full_cpu_seconds')}))
raise SystemExit(0 if result['controls_passed'] else 2)
