"""New final-DRC cancellation question after early budget-field fix; no old rerun."""
from pathlib import Path
import os,signal,sys,time
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,handoff as h,floor_route as f,review_export as e,runner
out=ROOT/'.runs/review-export-final-stage-cancel-budget-001';out.mkdir();owner={};h.capture_destination(owner,out)
receipt=ROOT/'.runs/default-tuning-native-001/result.json';report=f.read_json(receipt);sources={str(receipt.parent):e.witness(receipt.parent),str(Path(report['source']).parent):e.witness(Path(report['source']).parent)}
start=time.monotonic();cpu=time.process_time()+f.child_cpu();h.review_copy(receipt,out/'review');h.review_choice(out/'review/review.json',out/'intent','accept')
step=e.ExportJob.step;rss=runner._group_rss_bytes;state={};observed=[]
def stage(job,name,*args,**kwargs):
 state['native_stage']=name
 try:return step(job,name,*args,**kwargs)
 finally:state.pop('native_stage',None)
def cancel(pgid,cwd):
 result=rss(pgid,cwd)
 if state.get('native_stage')=='final-drc' and not observed:
  os.killpg(pgid,0);observed.append({'native_stage':'final-drc','live_group':pgid,'signal':'SIGTERM','target':os.getpid()});os.kill(os.getpid(),signal.SIGTERM)
 return result
caught=None
with patch.object(e.ExportJob,'step',stage),patch.object(runner,'_group_rss_bytes',cancel):
 try:e.export(out/'intent/choice.json',out/'export',120)
 except p.Rejected as exc:caught=str(exc)
proof=f.read_json(out/'export/export.json');process=f.read_json(out/'export/validation/final-drc-process.json')
assert caught and observed and not proof['export_accepted'] and proof['status']=='cancelled' and process['status']=='cancelled' and process['cleanup_complete'] is True and process['cancel_signal']=='SIGTERM'
assert proof['budget_seconds']==120 and proof['cpu_budget_seconds']==120;p.check_resource_accounting(proof,child_key='child_step_cpu_seconds')
assert [x['name'] for x in proof['steps']]==['refill-drc','floor-final','final-drc']
try:os.killpg(observed[0]['live_group'],0)
except ProcessLookupError:pass
else:raise p.Rejected('native group survived')
for path,w in sources.items():assert e.witness(Path(path))==w
wall=time.monotonic()-start;full_cpu=time.process_time()+f.child_cpu()-cpu;assert max(wall,full_cpu)<120
h.owned_destination(owner);p.save_json(out/'control.json',{'schema':1,'controls_passed':True,'native_validation_accepted':False,'human_pcb_approval_observed':False,'error':caught,'observed':observed,'process':process,'cancelled_proof_sha256':p.sha(out/'export/export.json'),'shared_resource_accounting_passed':True,'wall_seconds':wall,'full_cpu_seconds':full_cpu,'tools':p.tool_manifest(),'controller_sha256':p.sha(Path(__file__)),'original_inputs':sources,'scope':'After early budget binding fix, actual attempted final-DRC group cancelled following two completed real stages. Empty log does not prove DRC algorithm entry. No solver, priorcontrol rerun, nativecorrectness/GUI/physical claim.'});print(f.canonical({'controls_passed':True,'wall_seconds':wall,'full_cpu_seconds':full_cpu}))
