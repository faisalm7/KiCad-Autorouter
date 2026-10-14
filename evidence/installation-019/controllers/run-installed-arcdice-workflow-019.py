from pathlib import Path
import json,sys,time
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f
from autorouter.runner import run
out=root/'.runs/installation-019-workflow-execution';out.mkdir()
argv=[*f.SANDBOX,str(root/'.venv/bin/python'),'-B',str(root/'.runs/qualify-installed-arcdice-workflow-019.py')]
start=time.monotonic();cpu=time.process_time()+f.child_cpu();result=run(argv,cwd=out,log=out/'command.log',timeout=190,max_log_bytes=128*1024,max_workdir_bytes=32*1024**2,max_group_rss_bytes=2*1024**3)
record={'schema':1,'process':result,'wall_seconds':time.monotonic()-start,'full_cpu_seconds':time.process_time()+f.child_cpu()-cpu,'wrapper_sha256':p.sha(Path(__file__)),'controller_sha256':p.sha(root/'.runs/qualify-installed-arcdice-workflow-019.py'),'log_sha256':p.sha(out/'command.log'),'git_head':p.tool_manifest()['git_head'],'scope':'Actual installed CLI workflow, additional workflow cost. Existing sharednetworkdenial/runner/native APIs, one sequential worker. Output bound controls runner cwd; total180wall/fullCPU inside controller.'}
p.save_json(out/'execution.json',record);print(json.dumps({k:record[k] for k in ('wall_seconds','full_cpu_seconds')}));raise SystemExit(0 if result['status']=='success' and result['exit_code']==0 and max(record['wall_seconds'],record['full_cpu_seconds'])<=180 else 2)
