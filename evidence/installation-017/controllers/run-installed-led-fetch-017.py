from pathlib import Path
import time,sys
START=time.monotonic();ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
import json,os
from autorouter import pipeline as p,floor_route as f,handoff as h
from autorouter.runner import run
clone=ROOT/'.runs/installation-017/checkout';installation=f.read_json(ROOT/'.runs/installation-017/result.json');assert installation['passed']
assert not (clone/'.data/led-demo-001').exists()
out=ROOT/'.runs/installation-017-led-fetch-execution';out.mkdir();owner={};h.capture_destination(owner,out)
env=os.environ.copy()
for name in ('PYTHONHOME','PYTHONPATH','GIT_DIR','GIT_WORK_TREE','GIT_INDEX_FILE'):env.pop(name,None)
env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1',GIT_CONFIG_GLOBAL='/dev/null',GIT_CONFIG_NOSYSTEM='1')
argv=[str(clone/'.venv/bin/python'),'-B',str(clone/'scripts/fetch_led_demo.py'),'--fetch','--output','.data/led-demo-001']
process=run(argv,cwd=clone,log=out/'command.log',timeout=305,env=env,max_log_bytes=128*1024,max_workdir_bytes=512*1024**2,max_group_rss_bytes=2*1024**3)
record={'schema':1,'status':process['status'],'process':process,'charged_wall_seconds':time.monotonic()-START+1,'lifetime_full_cpu_seconds':h.cpu_seconds(),'controller_sha256':p.sha(Path(__file__)),'log_sha256':p.sha(out/'command.log'),'installation_head':installation['git_head'],'scope':'Actual fixed five public original GETs in fresh installed checkout, no root research cache/priorcorpus. Acquisition/setup cost only; explicit1second bootstrap allowance. No native or routing claim.'}
if process['status']=='success' and process['exit_code']==0:
 result=f.read_json(clone/'.data/led-demo-001/result.json');assert result['status']=='acquired_unqualified' and result['new_network_requests']==5 and result['received_bytes']==161071 and not result['native_accepted'] and result['source_files_exact']
 record['source_receipt_sha256']=p.sha(clone/'.data/led-demo-001/result.json')
h.owned_destination(owner);p.save_json(out/'execution.json',record);print(json.dumps({k:record[k] for k in ('status','charged_wall_seconds','lifetime_full_cpu_seconds')}));raise SystemExit(0 if process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] else 2)
