import time,resource
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p
from autorouter.runner import run
out=ROOT/'.runs/free-angle-pair-final-readback-001';out.mkdir()
argv=[str(ROOT/'.venv/bin/python'),'-B',str(ROOT/'.runs/read-free-angle-pair-002.py'),str(out)]
process=run(argv,cwd=out,log=out/'command.log',timeout=90,max_log_bytes=256*1024,max_workdir_bytes=64*1024**2,max_group_rss_bytes=1024**3)
r=dict(process=process,wall_seconds=time.monotonic()-START,full_cpu_seconds=cpu()-CPU0,controller_sha256=p.sha(Path(__file__)),log_sha256=p.sha(out/'command.log'),reader_sha256=p.sha(ROOT/'.runs/read-free-angle-pair-002.py'))
p.save_json(out/'execution.json',r);print(json.dumps({k:r[k] for k in ['wall_seconds','full_cpu_seconds']}));raise SystemExit(0 if process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] else 2)
