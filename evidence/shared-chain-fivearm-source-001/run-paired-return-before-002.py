from pathlib import Path
import sys,time,json
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f
from autorouter.runner import run
O=R/'.runs/paired-return-before-002';O.mkdir();source=R/'.runs/paired-return-before-001/experiment_paired.py';before=p.sha(source);start=time.monotonic();cpu=time.process_time()+f.child_cpu()
process=run([str(R/'.venv/bin/python'),'-B',str(R/'.runs/test-paired-return-before-002.py')],cwd=O,log=O/'command.log',timeout=60,max_log_bytes=128*1024,max_workdir_bytes=2*1024**2,max_group_rss_bytes=2*1024**3)
assert p.sha(source)==before
p.save_json(O/'execution.json',dict(schema=1,process=process,source_sha256=before,wall_seconds=time.monotonic()-start,full_cpu_seconds=time.process_time()+f.child_cpu()-cpu,expected='One assertion failure on captured byte-exact pre-fix paired source reproduces actual returned/stored shared-charge divergence. Earlier launcher001invalid_request did not run tests. No Native/engine execution.'));print(json.dumps({k:process.get(k) for k in ['status','exit_code','cleanup_complete']}))
