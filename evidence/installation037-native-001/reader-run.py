"""Installed035 pure reader; lead-only, no Native/JVM/tests/network/Git."""
import time,resource
START=time.monotonic()
def cpu():
 a=resource.getrusage(resource.RUSAGE_SELF);b=resource.getrusage(resource.RUSAGE_CHILDREN)
 return a.ru_utime+a.ru_stime+b.ru_utime+b.ru_stime
CPU0=cpu()
from pathlib import Path
import os,sys,json
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f
from autorouter.runner import run
out=ROOT/'.runs/current-installation037-review-001';installed=ROOT/'.runs/installation-037/checkout'
inputs=out/'input-pins.json';inputs_pin=p.sha(inputs);pins=f.read_json(inputs)
assert pins['kind']=='installation037-reader-inputs-v1'
assert all(p.sha(ROOT/name)==digest for name,digest in pins['files_sha256'].items())
env={k:v for k,v in os.environ.items() if k not in {'PYTHONPATH','PYTHONHOME'}}
env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1')
process=run([*f.SANDBOX,str(installed/'.venv/bin/python'),'-B',str(out/'audit.py')],cwd=out,env=env,log=out/'command.log',timeout=max(.001,58-(time.monotonic()-START)),max_log_bytes=64*1024,max_workdir_bytes=16*1024**2,max_group_rss_bytes=1024**3)
stable=(p.sha(inputs)==inputs_pin and all(p.sha(ROOT/name)==digest for name,digest in pins['files_sha256'].items()))
checks=f.read_json(out/'checks.json') if (out/'checks.json').is_file() else None
wall=time.monotonic()-START;full=cpu()-CPU0
passed=(stable and process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] is True
 and process['log_truncated'] is False and checks is not None and checks['passed'] is True and max(wall,full)+2<=60)
record=dict(schema=1,passed=passed,source_current=stable,process=process,wall_seconds=wall,full_cpu_seconds=full,
 publication_allowance_seconds=2,whole_delivery_within_budget=max(wall,full)+2<=60,input_pins_sha256=inputs_pin,
 reader_sha256=p.sha(out/'audit.py'),adapted_reader_source_sha256=p.sha(ROOT/'.runs/current-installation036-review-001/audit.py'),
 controller_sha256=p.sha(Path(__file__)),log_sha256=p.sha(out/'command.log'),checks_sha256=p.sha(out/'checks.json') if checks else None,
 scope='Successful035 complete installed reader adapted to current037 source and112 changed-area installed controls with no historical supplements; same existing seven groups and Native/source/tool/PRL/process/complete-inventory/late-material checks. Pure installed interpreter audit refuses all subprocess/network/Native/JVM/tests. No full installed suite/freshOS/fullSCH/GUI/benchmark/human claim.')
p.save_json(out/'execution.json',record)
print(json.dumps({k:record[k] for k in ('passed','source_current','wall_seconds','full_cpu_seconds','whole_delivery_within_budget','checks_sha256')}))
raise SystemExit(0 if passed else 2)
