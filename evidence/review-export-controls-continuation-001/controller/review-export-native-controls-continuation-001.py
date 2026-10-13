"""Read completed GUI/stale/missing-via controls; execute only remaining SIGTERM."""
from pathlib import Path
import json,os,signal,sys,time
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,handoff as h,floor_route as f,review_export as e,runner
out=ROOT/'.runs/review-export-controls-continuation-001';out.mkdir();owner={};h.capture_destination(owner,out)
prior=ROOT/'.runs/review-export-controls-001';before=e.witness(prior);previous=f.read_json(prior/'result.json');execution=f.read_json(ROOT/'.runs/review-export-controls-execution-001/execution.json')
assert previous['status']=='failed' and previous['reason']=="TypeError: parse_report() missing 1 required positional argument: 'board_name'"
start=time.monotonic();cpu0=time.process_time()+f.child_cpu();limit=300
receipt=ROOT/'.runs/default-tuning-native-001/result.json';route=f.read_json(receipt);pins=previous['original_inputs'];tools=p.tool_manifest();assert tools==previous['tools']
record={'schema':1,'kind':'review-export-failure-controls-continuation-v1','status':'failed','accepted':False,'controls_passed':False,'cases':[],
 'budget_seconds':limit,'cpu_budget_seconds':limit,'prior_controller_status_unchanged':'failed','prior_execution':execution,'prior_inventory':before,
 'scope':'Correct only stored-report parse call; read completed GUI/stale/missing-via evidence unchanged. Execute only previously unexecuted actual SIGTERM native cancellation. No earlier native case rerun or failure overwrite.',
 'controller_sha256':p.sha(Path(__file__)),'tools':tools,'human_pcb_approval_observed':False,'new_solver_execution':False}
def remaining():return max(0,min(limit-execution['wall_seconds']-(time.monotonic()-start),limit-execution['full_cpu_seconds']-(time.process_time()+f.child_cpu()-cpu0)))
def stable():
 h.owned_destination(owner)
 if remaining()<=0:raise p.Rejected('cumulative control budget exhausted')
 if p.tool_manifest()!=tools or e.witness(prior)!=before:raise p.Rejected('prior artifacts/source/tools changed')
 for path,w in pins.items():
  if e.witness(Path(path))!=w:raise p.Rejected('original source/routing changed')
def account():
 record.update(wall_seconds=time.monotonic()-start,total_cpu_seconds=time.process_time()+f.child_cpu()-cpu0)
 record.update(cumulative_wall_seconds=execution['wall_seconds']+record['wall_seconds'],cumulative_full_cpu_seconds=execution['full_cpu_seconds']+record['total_cpu_seconds'])
 record['within_budget']=max(record['cumulative_wall_seconds'],record['cumulative_full_cpu_seconds'])<=limit
 record['controls_passed']=record['status']=='completed' and record['within_budget'] and len(record['cases'])==4 and all(x['passed'] for x in record['cases'])
try:
 p.check_result(receipt);stable()
 gui=prior/'gui_rule_metadata';exported=e.check_export(gui/'export/export.json');proof=f.read_json(gui/'export/export.json');assert exported['current'] and proof['export_accepted'] and p.sha(Path(proof['project_file']))==p.sha(Path(route['source']).with_suffix('.kicad_pro'))
 record['cases'].append(previous['cases'][0]);assert record['cases'][0]['passed']
 stale=prior/'stale_board';assert not (stale/'export').exists() and p.sha(stale/'review/project'/Path(route['source']).name)==previous['cases'][1]['after_sha256'];record['cases'].append(previous['cases'][1]);assert record['cases'][1]['passed']
 negative=prior/'missing_required_via/export';proof=f.read_json(negative/'export.json');native=p.parse_report(negative/'validation/final-drc.json',Path(route['source']).name)
 assert proof['export_accepted'] is False and native==proof['native'] and native['opens']>0 and not p.native_accepted(native)
 assert p.sha(negative/'validation/final-drc.json')==proof['native_report_sha256'] and p.sha(Path(proof['candidate']))==proof['candidate_sha256']
 record['cases'].append({'name':'missing_required_via','passed':True,'native':native,'export_error':proof['error'],'candidate_sha256':proof['candidate_sha256'],'native_report_sha256':proof['native_report_sha256'],'native_steps':[s['name'] for s in proof['steps']],'prior_native_not_reexecuted':True})
 folder=out/'cancel_native';folder.mkdir();h.review_copy(receipt,folder/'review');h.review_choice(folder/'review/review.json',folder/'intent','accept');rss=runner._group_rss_bytes;observed=[]
 def terminate(pgid,cwd):
  value=rss(pgid,cwd)
  if not observed:
   os.killpg(pgid,0);observed.append({'live_native_group':pgid,'signal':'SIGTERM','signal_target':os.getpid(),'monotonic':time.monotonic()});os.kill(os.getpid(),signal.SIGTERM)
  return value
 caught=None
 with patch.object(runner,'_group_rss_bytes',terminate):
  try:e.export(folder/'intent/choice.json',folder/'export',min(e.SECONDS,remaining()))
  except p.Rejected as exc:caught=str(exc)
 proof=f.read_json(folder/'export/export.json');process=f.read_json(folder/'export/validation/refill-drc-process.json')
 assert caught and proof['export_accepted'] is False and proof['status']=='cancelled' and process['status']=='cancelled' and process['cancel_signal']=='SIGTERM' and process['cleanup_complete'] is True and observed
 try:os.killpg(observed[0]['live_native_group'],0)
 except ProcessLookupError:pass
 else:raise p.Rejected('cancelled native group remains')
 record['cases'].append({'name':'cancel_native','passed':True,'reason':caught,'observed':observed,'process':process,'proof_sha256':p.sha(folder/'export/export.json'),'live_group_gone':True})
 stable();record['status']='completed'
except (Exception,KeyboardInterrupt) as exc:record.update(reason=type(exc).__name__+': '+str(exc),status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'failed')
result=f.publish(out,record,stable,account,remaining,owned=lambda:h.owned_destination(owner));print(f.canonical({k:result[k] for k in ('status','controls_passed','cumulative_wall_seconds','cumulative_full_cpu_seconds')}));raise SystemExit(0 if result['controls_passed'] else 2)
