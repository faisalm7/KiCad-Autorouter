"""Finite shared supervisor for first real composite-class JAR/native controls."""
from pathlib import Path
import time,sys,json
START=time.monotonic();ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,handoff as h
from autorouter.runner import run
from experiments.licensed_acquisition_v1.fetch import cancellation
out=h.real_path(ROOT/'.runs/netclass-parent-transport-002',existing=False)
if out.exists():raise p.Rejected('fresh exclusive transport output required')
out.mkdir();owner={};h.capture_destination(owner,out);initial=p.tool_manifest()
controller=ROOT/'experiments/netclass_parent_transport_v1/driver.py';pin=p.sha(controller)
with cancellation():
 process=run([*f.SANDBOX,str(ROOT/'.venv/bin/python'),'-B',str(controller),'--output',str(out/'controls'),'--run-native','--continue-preserved'],cwd=out,log=out/'command.log',timeout=95,max_log_bytes=256*1024,max_workdir_bytes=22*1024**2,max_group_rss_bytes=2*1024**3)
 record={'schema':1,'status':'completed','accepted':False,'process':process,'tools':initial,'controller_sha256':pin,'supervisor_sha256':p.sha(Path(__file__)),'charged_wall_seconds':time.monotonic()-START+1,'lifetime_full_cpu_seconds':h.cpu_seconds(),'scope':'Continuation of preserved001: readonly actual positive/JAR/class/refill requalification, only two new protected wrongwidth/removal DRCs. No repeated positive/JAR/ArcDice, production admission or routing gain. Inner90 and outer95wall/fullCPU; oldcompletecost plus conservative10wall/fullCPU preparation-readback allowance charged; wholecombined180. Startup+1second and lifetimeCPU; shared polling limits unchanged.'}
 h.owned_destination(owner)
 if p.tool_manifest()!=initial or p.sha(controller)!=pin:raise p.Rejected('supervisor Source/tool freeze changed')
 result=f.read_json(out/'controls/result.json');record.update(combined_charged_wall_seconds=14.319728707996546+10+record['charged_wall_seconds'],combined_full_cpu_seconds=9.494764+10+record['lifetime_full_cpu_seconds'],preparation_readback_allowance_seconds=10,result_sha256=p.sha(out/'controls/result.json'),controls_passed=result['controls_passed'])
 if max(record['charged_wall_seconds'],record['lifetime_full_cpu_seconds'])>95 or max(record['combined_charged_wall_seconds'],record['combined_full_cpu_seconds'])>180 or process['cleanup_complete'] is not True:
  result.update(status='outer_invalidated',controls_passed=False);p.save_json(out/'controls/result.json',result);record.update(status='outer_invalidated',controls_passed=False,result_sha256=p.sha(out/'controls/result.json'))
 p.save_json(out/'execution.json',record);h.owned_destination(owner)
 assert f.read_json(out/'execution.json')==record
print(json.dumps({k:record[k] for k in ('status','controls_passed','charged_wall_seconds','lifetime_full_cpu_seconds')}));raise SystemExit(0 if process['status']=='success' and process['exit_code']==0 and record['controls_passed'] else 2)
