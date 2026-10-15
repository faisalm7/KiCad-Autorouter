import time,resource
START=time.monotonic()
def cpu():return sum(r.ru_utime+r.ru_stime for r in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,review_export as e
from autorouter.runner import run
out=ROOT/'.runs/ir-chains-workflow001-readback-execution-001';out.mkdir();tools=p.tool_manifest();reader=ROOT/'.runs/read-ir-chains-workflow001-001.py';pin=p.sha(reader)
code="import subprocess,runpy;real=subprocess.Popen\ndef gate(argv,*a,**k):\n if argv!=['git','rev-parse','HEAD'] or str(k.get('cwd'))!="+repr(str(ROOT))+":raise AssertionError('Only exact read-onlyGitHEAD allowed')\n return real(argv,*a,**k)\nsubprocess.Popen=gate\nrunpy.run_path("+repr(str(reader))+",run_name='__main__')"
process=run([*f.SANDBOX,str(ROOT/'.venv/bin/python'),'-B','-c',code],cwd=out,log=out/'command.log',timeout=max(.001,58-(time.monotonic()-START)),max_log_bytes=1024**2,max_workdir_bytes=2*1024**2,max_group_rss_bytes=2*1024**3)
dest=ROOT/'.runs/ir-chains-workflow001-readback-001';child_witness=e.witness(dest) if dest.is_dir() else None
current=p.tool_manifest()==tools and p.sha(reader)==pin and child_witness is not None and e.witness(dest)==child_witness
checks=f.read_json(dest/'result.json') if current else None
current=bool(current and checks and checks['status']=='completed' and checks['controls_passed'] is True and f.read_json(dest/'execution.json')['result_sha256']==p.sha(dest/'result.json'))
wall=time.monotonic()-START;full=cpu()-CPU0
record=dict(schema=1,process=process,tools=tools,source_current=current,reader_sha256=pin,wrapper_sha256=p.sha(Path(__file__)),wall_seconds=wall,full_cpu_seconds=full,publication_allowance_seconds=2,within_budget=max(wall,full)+2<=60,scope='One independent pure shared-reader check of actualIRworkflow001 only; exact read-onlyGitHEAD allowed, allNative/JVM/network/othersubprocess refused. No priorworkflowsemantic replay, solver or Native rerun.')
p.save_json(out/'execution.json',record);print(json.dumps({k:record[k] for k in ('source_current','wall_seconds','full_cpu_seconds','within_budget')}));raise SystemExit(0 if current and record['within_budget'] and process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] else 2)
