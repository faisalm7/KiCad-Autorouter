"""Finite actual export failure/authority controls using existing APIs/runner.

Only disposable owned copies are mutated. Injection seams alter data or deliver
real SIGTERM while native execution remains real; no fabricated native reports.
"""
from pathlib import Path
import json,os,signal,sys,time
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,handoff as h,floor_route as f,review_export as e,runner,sexpr as sx
out=ROOT/'.runs/review-export-controls-001';out.mkdir();owner={};h.capture_destination(owner,out)
receipt=ROOT/'.runs/default-tuning-native-001/result.json';route=f.read_json(receipt)
start=time.monotonic();cpu0=time.process_time()+f.child_cpu();limit=300
record={'schema':1,'kind':'review-export-failure-controls-v1','status':'failed','accepted':False,'controls_passed':False,'cases':[],
 'native_reports_fabricated':False,'new_solver_execution':False,'human_pcb_approval_observed':False,'budget_seconds':limit,'cpu_budget_seconds':limit,
 'scope':'One existing schema3 receipt, fresh owned review/copies only. GUI rule metadata is untrusted; stale reviewed board rejected before creation; actual missing-via native negative; real supervisor SIGTERM during native refill and cleanup. Additional full workflow cost, not routing gain.'}
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
try:
 # A saved GUI rule edit is captured by intent, but never becomes rule authority.
 folder=fresh('gui_rule_metadata');project=folder/'review/project'/Path(route['source']).with_suffix('.kicad_pro').name
 original_gui=p.sha(project);gui=f.read_json(project);gui['board']['design_settings']['rule_severities']['clearance']='ignore';p.save_json(project,gui)
 h.review_choice(folder/'review/review.json',folder/'intent','accept');result=e.export(folder/'intent/choice.json',folder/'export',min(e.SECONDS,remaining()));checked=e.check_export(folder/'export/export.json')
 exported=Path(result['project_file']);assert p.sha(exported)==p.sha(Path(route['source']).with_suffix('.kicad_pro')) and p.sha(exported)!=p.sha(project)
 record['cases'].append({'name':'gui_rule_metadata','passed':result['export_accepted'] and checked['current'],'original_project_sha256':original_gui,'edited_gui_project_sha256':p.sha(project),'exported_project_sha256':p.sha(exported),'native':result['native'],'export_sha256':p.sha(folder/'export/export.json'),'original_rules_authoritative':True})
 # A change after intent must reject before output creation/native execution.
 folder=fresh('stale_board');h.review_choice(folder/'review/review.json',folder/'intent','accept');board=folder/'review/project'/Path(route['source']).name;raw=board.read_bytes();(folder/'before-board.kicad_pcb').write_bytes(raw);board.write_bytes(raw+b'\n')
 caught=None
 try:e.export(folder/'intent/choice.json',folder/'export',min(e.SECONDS,remaining()))
 except p.Rejected as exc:caught=str(exc)
 assert caught and not (folder/'export').exists()
 record['cases'].append({'name':'stale_board','passed':True,'reason':caught,'output_not_created':True,'native_steps':0,'before_sha256':h.digest(raw),'after_sha256':p.sha(board)})
 # Inject a missing required via into newly owned candidate before real validation.
 folder=fresh('missing_required_via');h.review_choice(folder/'review/review.json',folder/'intent','accept');validate=p.validate_candidate;observed=[]
 def invalid(job,original,candidate,*args,**kwargs):
  tree=sx.read(candidate);vias=sx.children(tree,'via');assert len(vias)==1;route_before=p.sha(candidate);removed=vias[0];tree.remove(removed);sx.write(candidate,tree)
  observed.append({'candidate':str(candidate),'before_sha256':route_before,'invalid_sha256':p.sha(candidate),'removed_via_ast':removed})
  return validate(job,original,candidate,*args,**kwargs)
 caught=None
 with patch.object(p,'validate_candidate',invalid):
  try:e.export(folder/'intent/choice.json',folder/'export',min(e.SECONDS,remaining()))
  except p.Rejected as exc:caught=str(exc)
 proof=f.read_json(folder/'export/export.json');native=p.parse_report(folder/'export/validation/final-drc.json')
 assert caught and proof['export_accepted'] is False and native['opens']>0 and not p.native_accepted(native)
 record['cases'].append({'name':'missing_required_via','passed':True,'reason':caught,'injection':observed,'native':native,'proof_sha256':p.sha(folder/'export/export.json'),'final_native_report_sha256':p.sha(folder/'export/validation/final-drc.json'),'native_steps':[s['name'] for s in proof['steps']]})
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
