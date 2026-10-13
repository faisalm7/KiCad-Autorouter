from pathlib import Path
import datetime,json,sys,time
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root));sys.dont_write_bytecode=True
from autorouter import floor_route as f,pipeline as p
from autorouter.runner import run
outer=root/'.runs/review-export-native-001';outer.mkdir()
argv=[*f.SANDBOX,str(root/'.venv/bin/python'),'-B',str(root/'scripts/qualify_review_export.py'),'--output',str(outer/'run'),'--run-native']
start=time.monotonic();cpu=time.process_time()+f.child_cpu();head=p.tool_manifest()['git_head']
result=run(argv,cwd=outer,log=outer/'command.log',timeout=620,max_log_bytes=256*1024,max_workdir_bytes=256*1024**2,max_group_rss_bytes=2*1024**3)
record={'schema':1,'git_head':head,'process':result,'wall_seconds':time.monotonic()-start,'full_cpu_seconds':time.process_time()+f.child_cpu()-cpu,'wrapper_sha256':p.sha(Path(__file__)),'log_sha256':p.sha(outer/'command.log'),
 'scope':'Sequential five existing receipts through new review/intent/fresh native export/proof and rejection. No solver/previousnative repetition; separate workflow qualification cost, no GUI/human/physical approval. Existing sandbox/runner used,600cumulativewall/fullCPU +full outerrecord,256MiB output bound.'}
p.save_json(outer/'execution.json',record);print(json.dumps({'status':result['status'],'exit_code':result['exit_code'],'wall_seconds':record['wall_seconds'],'full_cpu_seconds':record['full_cpu_seconds']}))
raise SystemExit(0 if result['status']=='success' and result['exit_code']==0 and max(record['wall_seconds'],record['full_cpu_seconds'])<=600 else 2)
