import time,resource
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f
from autorouter.runner import run
out=Path(__file__).resolve().parent
process=run([*f.SANDBOX,str(ROOT/'.venv/bin/python'),'-B',str(out/'audit.py')],cwd=out,log=out/'command.log',timeout=max(.001,60-(time.monotonic()-START)),max_log_bytes=128*1024,max_workdir_bytes=16*1024**2,max_group_rss_bytes=2*1024**3)
wall=time.monotonic()-START;full=cpu()-CPU0
passed=process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] and not process['log_truncated'] and max(wall,full)+2<=62
record=dict(schema=1,passed=passed,process=process,wall_seconds=wall,full_cpu_seconds=full,publication_allowance_seconds=2,whole_wall_full_cpu_reservation_seconds=62,controller_sha256=p.sha(Path(__file__)),audit_sha256=p.sha(out/'audit.py'),log_sha256=p.sha(out/'command.log'),scope='Existing sharedretainedNative/source/PRL/process/fieldchecks only, noNative/JVM/GET/tests. Entire62reserved in cumulative190; parentcost samplesbeforefinalreceipt.')
p.save_json(out/'execution.json',record);print(json.dumps({k:record[k] for k in ('passed','wall_seconds','full_cpu_seconds')}));raise SystemExit(0 if passed else 2)
