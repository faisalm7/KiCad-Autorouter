from pathlib import Path
import datetime,hashlib,json,resource,sys,time
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root));sys.dont_write_bytecode=True
from autorouter import floor_route as f,pipeline as p
from autorouter.runner import run
outer=root/'.runs/placement-pruning-controls-001';outer.mkdir()
argv=[*f.SANDBOX,str(root/'.venv/bin/python'),'-B',str(root/'experiments/placement_pruning_controls_v1/driver.py'),'--run-native','--output',str(outer/'run')]
start=time.monotonic();cpu=time.process_time()+f.child_cpu();started=datetime.datetime.now(datetime.timezone.utc).isoformat();head=p.tool_manifest()['git_head']
result=run(argv,cwd=outer,log=outer/'command.log',timeout=195,max_log_bytes=256*1024,max_workdir_bytes=64*1024**2,max_group_rss_bytes=2*1024**3)
record={'schema':1,'git_head':head,'started_utc':started,'process':result,'wall_seconds':time.monotonic()-start,'full_cpu_seconds':time.process_time()+f.child_cpu()-cpu,
    'wrapper_sha256':p.sha(Path(__file__)),'log_sha256':p.sha(outer/'command.log'),'scope':'Four engineered search/C integration arms plus two parent/deletion witnesses; no public-board gain claim. Shared inner180wall/fullCPU and outer64MiB polling.'}
p.save_json(outer/'execution.json',record);print(json.dumps({'status':result['status'],'exit_code':result['exit_code'],'wall_seconds':record['wall_seconds'],'full_cpu_seconds':record['full_cpu_seconds']}))
raise SystemExit(0 if result['status']=='success' and result['exit_code']==0 else 2)
