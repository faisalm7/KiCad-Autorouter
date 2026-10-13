from pathlib import Path
import json,sys,time
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f
from autorouter.runner import run
outer=root/'.runs/modern-semantics-controls-execution-001';outer.mkdir()
argv=[*f.SANDBOX,str(root/'.venv/bin/python'),'-B',str(root/'experiments/modern_semantics_controls_v1/driver.py'),'--run-native','--output',str(root/'.runs/modern-semantics-controls-001')]
start=time.monotonic();cpu=time.process_time()+f.child_cpu();head=p.tool_manifest()['git_head'];result=run(argv,cwd=outer,log=outer/'command.log',timeout=95,max_log_bytes=128*1024,max_workdir_bytes=20*1024**2,max_group_rss_bytes=2*1024**3)
record={'schema':1,'process':result,'wall_seconds':time.monotonic()-start,'full_cpu_seconds':time.process_time()+f.child_cpu()-cpu,'wrapper_sha256':p.sha(Path(__file__)),'log_sha256':p.sha(outer/'command.log'),'git_head':head,'scope':'New warning/ignore text and isolatedhole-warning controls only; no previouserrorcontrol rerun/solver/production candidate. Shared native originalrule/candidate/process/ownership/readback, sequential; completeouter90wall/fullCPU required.'}
p.save_json(outer/'execution.json',record);print(json.dumps({k:record[k] for k in ('wall_seconds','full_cpu_seconds')}));raise SystemExit(0 if result['status']=='success' and result['exit_code']==0 and max(record['wall_seconds'],record['full_cpu_seconds'])<=90 else 2)
