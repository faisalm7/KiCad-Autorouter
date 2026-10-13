from pathlib import Path
import datetime,hashlib,json,resource,sys,time
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root));sys.dont_write_bytecode=True
from autorouter import floor_route as f,pipeline as p
from autorouter.runner import run
outer=root/'.runs/ardujoy-native-paired-001';outer.mkdir()
argv=[*f.SANDBOX,str(root/'.venv/bin/python'),'-B',str(root/'scripts/experiment_paired.py'),'--project','ardujoy-c64','--system','native-all','--output',str(outer/'run')]
start=time.monotonic();cpu=time.process_time()+f.child_cpu();started=datetime.datetime.now(datetime.timezone.utc).isoformat();head=p.tool_manifest()['git_head']
result=run(argv,cwd=outer,log=outer/'command.log',timeout=540,max_log_bytes=256*1024,max_workdir_bytes=96*1024**2,max_group_rss_bytes=2*1024**3)
record={'schema':1,'git_head':head,'started_utc':started,'process':result,'wall_seconds':time.monotonic()-start,'full_cpu_seconds':time.process_time()+f.child_cpu()-cpu,
    'wrapper_sha256':p.sha(Path(__file__)),'log_sha256':p.sha(outer/'command.log'),'scope':'Four fresh sequential exposed-development arms B0/B1/B2portfolio/Cnative-feedback, each120wall/fullCPU including shared charges; same original constraints. Outer96MiB polling and540s timeout; native validation required.'}
record['outer_charge_requires_final_readback']=True
p.save_json(outer/'execution.json',record);print(json.dumps({'status':result['status'],'exit_code':result['exit_code'],'wall_seconds':record['wall_seconds'],'full_cpu_seconds':record['full_cpu_seconds']}))
raise SystemExit(0 if result['status']=='success' and result['exit_code']==0 else 2)
