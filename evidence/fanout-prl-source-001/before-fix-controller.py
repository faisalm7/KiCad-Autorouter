"""Bound one real-owned PRL software defect probe; no Native/JVM workers."""
import time,resource
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import sys,json
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f
from autorouter.runner import run
D=R/'.runs/fanout-prl-prefix-reproducer-001.py';PIN=sys.argv[1]
assert p.sha(D)==PIN
O=R/'.runs/fanout-prl-prefix-execution-001';O.mkdir()
process=run([str(R/'.venv/bin/python'),'-B',str(D)],cwd=O,log=O/'command.log',timeout=max(.001,118-(time.monotonic()-START)),max_log_bytes=64*1024,max_workdir_bytes=2*1024**2,max_group_rss_bytes=1024**3)
path=R/'.runs/fanout-prl-prefix-reproducer-001/result.json';child=f.read_json(path) if path.exists() else None
record=dict(schema=1,diagnostic_defect_reproduced=bool(process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] is True and process['log_truncated'] is False and child and child['passed'] is True and child['observed_defect'] is True and child['flags_restored'] is True),routing_native_evidence=False,process=process,child_receipt_sha256=p.sha(path) if child else None,driver_sha256=PIN,controller_sha256=p.sha(Path(__file__)),wall_seconds=time.monotonic()-START,full_cpu_seconds=cpu()-CPU0,scope='Exact pre-fix stable callback/shared publisher and actual owned PRL flags; synthetic reports/processes never executed. Complete runner child plus enclosing sample; no routing correctness, Native quality or live application evidence.')
assert p.sha(D)==PIN
p.save_json(O/'execution.json',record)
print(json.dumps({k:record[k] for k in ['diagnostic_defect_reproduced','wall_seconds','full_cpu_seconds']}));raise SystemExit(0 if record['diagnostic_defect_reproduced'] else 2)
