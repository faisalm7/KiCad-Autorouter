from pathlib import Path
import sys,time,json
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f
from autorouter.runner import run
O=R/'.runs/paired-return-before-001';O.mkdir();(O/'experiment_paired.py').write_bytes((R/'scripts/experiment_paired.py').read_bytes());pins={n:p.sha(R/n) for n in ['scripts/experiment_paired.py','tests/test_paired.py']};start=time.monotonic();cpu=time.process_time()+f.child_cpu()
process=run([str(R/'.venv/bin/python'),'-B','-m','unittest','discover','-s',str(R/'tests'),'-p','test_paired.py','-k','test_final_sample_return_matches_stored_after_successful_publication_cost','-v'],cwd=R,log=O/'command.log',timeout=60,max_log_bytes=128*1024,max_workdir_bytes=16*1024**3,max_group_rss_bytes=2*1024**3)
p.save_json(O/'execution.json',dict(schema=1,process=process,source_sha256=pins,wall_seconds=time.monotonic()-start,full_cpu_seconds=time.process_time()+f.child_cpu()-cpu,expected='One assertion failure reproduces actual returned/shared-charge metadata divergence; no Native/engine execution.'));print(json.dumps({k:process.get(k) for k in ['status','exit_code','cleanup_complete']}))
