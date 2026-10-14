"""Actual fixed public five-GET qualification with existing runner/publisher."""
from pathlib import Path
import os,sys,time
START=time.monotonic();ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
import json
from autorouter import pipeline as p,floor_route as f,handoff as h
from autorouter.runner import run
from scripts import fetch_led_demo as demo
from experiments.licensed_acquisition_v1 import fetch as shared
out=ROOT/'.runs/fresh-analog-filter-fetch-001';out.mkdir();owner={};h.capture_destination(owner,out)
assert not (ROOT/'.data/analog-filter-demo-001').exists()
tools=p.tool_manifest();witness={n:p.sha(ROOT/n) for n in (*demo.MATERIAL,*demo.ARC_MATERIAL)}
record={'schema':1,'accepted':False,'status':'incomplete','controls_passed':False,'budget_seconds':305,'cpu_budget_seconds':305,'tools':tools,'source_implementation_sha256':witness,'controller_sha256':p.sha(Path(__file__)),'scope':'Actual fixed analog-filter five public GETs; exact raw5/native7 notice packet. No research-cache transport/native/engine/production/physical claim. Whole post-bootstrap wall plus explicit1second allowance; lifetimeSELF+waitedCHILDCPU; separate acquisition cost.'}
def remaining():return min(305-(time.monotonic()-START+1),305-h.cpu_seconds())
def stable():
 h.owned_destination(owner)
 if remaining()<=0 or p.tool_manifest()!=tools or any(p.sha(ROOT/n)!=sha for n,sha in witness.items()):raise p.Rejected('fetch outer source/tool/owner/deadline changed')
 if record.get('source_receipt_sha256'):
  if p.sha(ROOT/'.data/analog-filter-demo-001/result.json')!=record['source_receipt_sha256']:raise p.Rejected('fetch receipt changed')
  demo.capture_native_source('analog-filter',root=ROOT)
def account():
 record.update(charged_wall_seconds=time.monotonic()-START+1,lifetime_full_cpu_seconds=h.cpu_seconds(),within_budget=remaining()>0)
 if not record['within_budget'] or record['status']!='completed':record['controls_passed']=False
with shared.cancellation():
 try:
  env=os.environ.copy()
  for name in ('PYTHONHOME','PYTHONPATH','GIT_DIR','GIT_WORK_TREE','GIT_INDEX_FILE'):env.pop(name,None)
  env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1',GIT_CONFIG_GLOBAL='/dev/null',GIT_CONFIG_NOSYSTEM='1')
  process=run([str(ROOT/'.venv/bin/python'),'-B',str(ROOT/'scripts/fetch_led_demo.py'),'--project','analog-filter','--fetch','--output','.data/analog-filter-demo-001'],cwd=out,log=out/'command.log',timeout=remaining(),env=env,max_log_bytes=128*1024,max_workdir_bytes=2*1024**2,max_group_rss_bytes=2*1024**3)
  record.update(process=process,log_sha256=p.sha(out/'command.log'))
  if process['status']!='success' or process['exit_code']!=0 or not process['cleanup_complete']:raise p.Rejected('fixed acquisition subprocess failed')
  receipt=f.read_json(ROOT/'.data/analog-filter-demo-001/result.json')
  if (receipt['status']!='acquired_unqualified' or receipt['new_network_requests']!=5 or receipt['received_bytes']!=189336
      or receipt['kind']!='fixed_public_analog_filter_source_acquisition' or not receipt['source_files_exact'] or receipt['native_accepted']):raise p.Rejected('fixed acquisition scope/identity differs')
  if not all(x['http_status']==200 and x['url']==x['final_url'] for x in receipt['requests']):raise p.Rejected('actual public GET evidence differs')
  record.update(status='completed',controls_passed=True,source_receipt_sha256=p.sha(ROOT/'.data/analog-filter-demo-001/result.json'))
 except (Exception,KeyboardInterrupt) as exc:record.update(status='failed',controls_passed=False,error=type(exc).__name__+': '+str(exc))
 f.publish(out,record,stable,account,remaining,owned=lambda:h.owned_destination(owner))
print(json.dumps({k:record.get(k) for k in ('status','controls_passed','charged_wall_seconds','lifetime_full_cpu_seconds','error')}));raise SystemExit(0 if record.get('controls_passed') else 2)
