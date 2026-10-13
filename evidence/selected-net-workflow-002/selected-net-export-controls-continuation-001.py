"""Finite actual export failure/authority controls using existing APIs/runner.

Only disposable owned copies are mutated. Injection seams alter data or deliver
real SIGTERM while native execution remains real; no fabricated native reports.
"""
from pathlib import Path
import json,os,signal,sys,time
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,handoff as h,floor_route as f,review_export as e,runner,sexpr as sx
out=ROOT/'.runs/selected-net-export-controls-continuation-001';out.mkdir();owner={};h.capture_destination(owner,out)
receipt=ROOT/'.runs/selected-net-native-positive-002/result.json';route=f.read_json(receipt)
start=time.monotonic();cpu0=time.process_time()+f.child_cpu();limit=300
record={'schema':1,'kind':'review-export-failure-controls-v1','status':'failed','accepted':False,'controls_passed':False,'cases':[],
 'native_reports_fabricated':False,'new_solver_execution':False,'human_pcb_approval_observed':False,'budget_seconds':limit,'cpu_budget_seconds':limit,
 'scope':'One existing selected schema1 receipt, fresh owned review/copies only. GUI rule metadata is untrusted; stale reviewed board rejected before creation; actual invalid-clearance native negative; real supervisor SIGTERM during native refill and cleanup. Additional full workflow cost, not routing gain.'}
p.check_result(receipt);pins={str(receipt.parent):e.witness(receipt.parent),str(Path(route['source']).parent):e.witness(Path(route['source']).parent,)}
record['original_inputs']=pins;record['tools']=p.tool_manifest();record['controller_sha256']=p.sha(Path(__file__))
def remaining():return max(0,min(limit-(time.monotonic()-start),limit-(time.process_time()+f.child_cpu()-cpu0)))
def stable():
 h.owned_destination(owner)
 if remaining()<=0:raise p.Rejected('control batch budget exhausted')
 if p.tool_manifest()!=record['tools']:raise p.Rejected('source/tools/HEAD changed')
 for path,w in pins.items():
  if e.witness(Path(path))!=w:raise p.Rejected('original source/routing changed')
def account():
 record.update(wall_seconds=time.monotonic()-start,total_cpu_seconds=time.process_time()+f.child_cpu()-cpu0)
 record['within_budget']=max(record['wall_seconds'],record['total_cpu_seconds'])<=limit
 record['controls_passed']=record['status']=='completed' and record['within_budget'] and len(record['cases'])==4 and all(x['passed'] for x in record['cases'])
def fresh(name):
 stable();folder=out/name;folder.mkdir();h.review_copy(receipt,folder/'review');return folder
previous=ROOT/'.runs/selected-net-export-controls-002';prior=f.read_json(previous/'result.json')
assert prior['status']=='failed' and prior['reason']=="TypeError: parse_report() missing 1 required positional argument: 'board_name'"
assert [x['name'] for x in prior['cases']]==['gui_rule_metadata','stale_board']
record['cases']=prior['cases'];record['continuation_of']=str(previous/'result.json');record['prior_controller_reason']=prior['reason']
record['prior_outer_executions']=[f.read_json(ROOT/'.runs'/('selected-net-export-controls-execution-'+x)/'execution.json') for x in ('001','002')]
record['no_completed_native_control_repeated']=True
try:
 e.check_export(previous/'gui_rule_metadata/export/export.json')
 assert not (previous/'stale_board/export').exists()
 folder=previous/'invalid_selected_clearance';proof=f.read_json(folder/'export/export.json');job=folder/'export/validation';candidate=Path(proof['candidate'])
 expected=dict(route['source_hashes']);expected[candidate.name]=proof['candidate_sha256']
 native=f.check_drc_stage(job,proof,'final-drc',candidate,job/'final-drc-input'/candidate.name,False,expected)
 assert proof['export_accepted'] is False and any(x['type'] in {'clearance','shorting_items'} for x in native['findings']) and not p.native_accepted(native)
 record['cases'].append({'name':'invalid_selected_clearance','passed':True,'native':native,'proof_sha256':p.sha(folder/'export/export.json'),'final_native_report_sha256':p.sha(job/'final-drc.json'),'native_steps':[s['name'] for s in proof['steps']],'readback_only_no_native_repetition':True})
 # Send a real signal only after a native group is observed alive.
 folder=fresh('cancel_native');h.review_choice(folder/'review/review.json',folder/'intent','accept');rss=runner._group_rss_bytes;observed=[]
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
result=f.publish(out,record,stable,account,remaining,owned=lambda:h.owned_destination(owner));print(f.canonical({k:result[k] for k in ('status','controls_passed','wall_seconds','total_cpu_seconds')}));raise SystemExit(0 if result['controls_passed'] else 2)
