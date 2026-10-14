"""Final new LED readback using shared validators, without native reruns."""
from pathlib import Path
import time,sys
START=time.monotonic();CPU0=time.process_time()
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
import copy,json,signal
from autorouter import pipeline as p,floor_route as f,placement_clearance as pc,handoff as h,sexpr as sx
from scripts import experiment_portfolio as m,experiment_paired as paired,experiment_quality as q
CPU0+=f.child_cpu()
CAP=15.;base=ROOT/'.runs/push-button-led-native-paired-complete-sch-001';out=ROOT/'.runs/push-button-led-native-paired-complete-sch-004-qualification';out.mkdir();owner={};h.capture_destination(owner,out)
prospective=ROOT/'.runs/push-button-led-native-paired-complete-sch-001-protocol.json'
inputs=pc.inventory(base,max_bytes=96*1024**2,max_files=6000,max_entries=12000,with_directories=True);protocol=f.read_json(base/'run/protocol.json');spec=f.read_json(prospective);summary=f.read_json(base/'run/paired-summary.json');outer=f.read_json(base/'execution.json')
board=Path(protocol['source']);original=p.preflight(board);rows=[]
report={'schema':1,'kind':'LED-complete-schematic-four-arm-final-readback-v1','status':'incomplete','accepted':False,'comparison_eligible':False,'new_native_execution':False,'physical_electrical_validation':False,'controller_sha256':p.sha(Path(__file__)),'prospective_protocol_sha256':p.sha(prospective),'paired_summary_sha256':p.sha(base/'run/paired-summary.json'),'outer_execution_sha256':p.sha(base/'execution.json'),'audit_wall_and_full_cpu_charge_seconds':CAP,'failed_prior_audit_fixed_wall_full_cpu_charge_seconds':5.,'qualification_amendment_sha256':p.sha(ROOT/'.runs/push-button-led-native-paired-complete-sch-004-qualification-protocol.json'),'shared_original_qualification_cost':spec['shared_original_qualification_cost'],'prior_corrective_audit_fixed_wall_full_cpu_charge_seconds':5.,'prior_failed_supplemental_audit_charge_seconds':15.,'audit_charge_policy':'Charge prior failed5, corrected5 and failed supplemental15 audits plus new15 wall/fullCPU allowance for previously unsampled pair bootstrap/final emission and this complete supplemental readback to EVERYarm. Original native prequalification/fullouter excess also retained. Conservative charges, not exact routing latency or speedup.','claims_limit':'One small exposed modern LED support/control task; no proven independent pedigree, heldout, broad completion-rate, speedup or physical claim.'}
def remaining():return min(CAP-(time.monotonic()-START),CAP-(time.process_time()+f.child_cpu()-CPU0))
def stable():
 try:
  h.owned_destination(owner);q.verify_freeze(protocol['freeze'],board)
  if pc.inventory(base,max_bytes=96*1024**2,max_files=6000,max_entries=12000,with_directories=True)!=inputs:raise p.Rejected('completed input changed')
  if p.sha(prospective)!=report['prospective_protocol_sha256']:raise p.Rejected('prospective protocol changed')
  if report['comparison_eligible'] and remaining()<=0:raise p.Rejected('complete audit exceeds predeclared charge')
 except BaseException:report.update(comparison_eligible=False,comparisons=[]);raise

def final_candidate(folder,data):
 candidate=folder/'candidate'/board.name
 p.verify_candidate_files(candidate,protocol['freeze']['source_hashes'],data['candidate_sha256'])
 tree=sx.read(candidate);assert p.immutable(tree)==p.immutable(original)
 protected=p.protected_for_record(f.read_json(base/'run/C_feedback/result.json'),original)
 assert all(route in p.routes(tree) for route in protected)
 before=dict(protocol['freeze']['source_hashes']);before[board.name]=data['candidate_sha256']
 native=f.check_drc_stage(folder,data,'final-drc',candidate,folder/'final-drc-input'/board.name,False,before,schematic_parity=True,sandboxed=False)
 assert native==data['native'] and p.sha(folder/'final-drc.json')==data['native_report_sha256']
 return {'path':str(candidate),'candidate_sha256':data['candidate_sha256'],'native_report_sha256':data['native_report_sha256'],'native_counts':{k:native[k] for k in ('opens','blocking','warnings','exclusions')},'native_rejection_reasons':p.native_rejection_reasons(native),'original_design_checks':True,'complete_schematic_native_checks':True}

def account():
 report.update(observed_audit_wall_seconds=time.monotonic()-START,observed_audit_full_cpu_seconds=time.process_time()+f.child_cpu()-CPU0)
 valid=report['status']=='completed' and remaining()>0
 for row in rows:
  row['charged_wall_seconds']=row['paired_charged_wall_seconds']+max(0,outer['wall_seconds']-summary['batch_wall_seconds'])+CAP+25.+spec['shared_original_qualification_cost']['wall_seconds']
  row['charged_full_cpu_seconds']=row['paired_charged_full_cpu_seconds']+max(0,outer['full_cpu_seconds']-summary['batch_cpu_seconds'])+CAP+25.+spec['shared_original_qualification_cost']['full_cpu_seconds']
  row['within_equal120_wall_full_cpu_caps']=max(row['charged_wall_seconds'],row['charged_full_cpu_seconds'])<=120
  row['accepted']=valid and row['native_accepted'] and row['within_equal120_wall_full_cpu_caps']
 report.update(results=rows,comparison_eligible=valid and all(x['within_equal120_wall_full_cpu_caps'] for x in rows),comparisons=paired.comparisons(rows) if valid else [])
 if remaining()<=0:report.update(status='budget_exceeded',comparison_eligible=False,comparisons=[])

previous={sig:signal.signal(sig,lambda *_:(_ for _ in ()).throw(KeyboardInterrupt())) for sig in (signal.SIGINT,signal.SIGTERM)}
try:
 with p.validation_readback_session():
  stable();assert spec['audit_charge_seconds']==5. and f.read_json(ROOT/'.runs/push-button-led-native-paired-complete-sch-004-qualification-protocol.json')['new_equal_charge_seconds']==CAP and spec['prospective'] and spec['git_head']==protocol['freeze']['tools']['git_head']
  assert outer['prospective_protocol_sha256']==p.sha(prospective) and outer['process']['status']=='success' and outer['process']['exit_code']==0 and outer['process']['cleanup_complete']
  assert summary['status']=='completed' and protocol['arm_order']==['B0','B1','B2_portfolio','C_feedback']
  portfolio=f.read_json(base/'run/B2_portfolio/portfolio-summary.json');verified=paired.verify_portfolio(base/'run/B2_portfolio',portfolio,board,protocol['freeze']);assert verified['accepted']
  negatives=[];c_trials=[]
  for old in summary['results']:
   row=copy.deepcopy(old);row.update(native_accepted=old['accepted'],paired_charged_wall_seconds=old['charged_wall_seconds'],paired_charged_full_cpu_seconds=old['charged_cpu_seconds'])
   if row['id']!='B2_portfolio':
    path=Path(row['result']);d=f.read_json(path);assert p.sha(path)==row['result_sha256'] and d['tools']==protocol['freeze']['tools'] and d['source_hashes']==protocol['freeze']['source_hashes']
    if row['accepted']:p.check_result(path)
    else:
     raw=final_candidate(path.parent,d);p.check_protected_import(path.parent,d,original,Path(raw['path']),p.protected_for_record(d,original));p.check_resource_accounting(d);assert d['status']=='drc_rejected' and raw['native_rejection_reasons'];negatives.append(raw)
   rows.append(row)
  c=f.read_json(base/'run/C_feedback/result.json')
  for trial in c['trials']:
   folder=base/'run/C_feedback/trials'/trial['id'];d=f.read_json(folder/'result.json');assert trial['receipt']==str(folder/'result.json') and all(trial[k]==d[k] for k in ('id','status','accepted'))
   c_trials.append({'id':d['id'],'status':d['status'],'accepted_by_strategy':d['accepted'],**final_candidate(folder,d)})
  def signatures(path):return f.canonical([x for x in f.read_json(path)['native']['findings'] if x['severity']=='warning'])
  chosen=portfolio['selected'];assert signatures(Path(chosen['result']))==signatures(Path(rows[1]['result']))==signatures(Path(rows[3]['result']))
  report.update(status='completed',strong_B2_selected=chosen['id'],selected_B2_length_mm=chosen['length_mm'],C_length_mm=rows[3]['length_mm'],C_gain_vs_B2_mm=chosen['length_mm']-rows[3]['length_mm'],C_gain_vs_B1_mm=rows[1]['length_mm']-rows[3]['length_mm'],unchanged_warning_signatures=True,negative_final_candidates=negatives,C_trial_candidates=c_trials,paired_shared_charge={'wall_seconds':summary['shared_overhead_wall_seconds'],'full_cpu_seconds':summary['shared_overhead_cpu_seconds']},whole_outer_excess={'wall_seconds':max(0,outer['wall_seconds']-summary['batch_wall_seconds']),'full_cpu_seconds':max(0,outer['full_cpu_seconds']-summary['batch_cpu_seconds'])},source_sha256=protocol['freeze']['source_hashes'],tools=protocol['freeze']['tools'])
except (Exception,KeyboardInterrupt) as exc:report.update(status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'failed',comparison_eligible=False,reason=type(exc).__name__+': '+str(exc))
f.publish(out,report,stable,account,remaining,owned=lambda:h.owned_destination(owner))
try:
 wall=time.monotonic()-START;cpu=time.process_time()+f.child_cpu()-CPU0
 p.save_json(out/'execution.json',{'wall_seconds':wall,'full_cpu_seconds':cpu,'fixed_charge_seconds':CAP,'within_charged_allowance':max(wall,cpu)<CAP,'result_sha256':p.sha(out/'result.json'),'scope':'From before imports through canonical publication/readback; final execution write/readback also must fit fixed allowance.'})
 stable();assert f.read_json(out/'execution.json')['result_sha256']==p.sha(out/'result.json')
 if remaining()<=0:raise p.Rejected('final execution publication exceeds prospective5second charge')
except (Exception,KeyboardInterrupt) as exc:
 report.update(status='invalidated',comparison_eligible=False,comparisons=[],reason=type(exc).__name__+': '+str(exc));f.publish(out,report,lambda:(_ for _ in ()).throw(p.Rejected(report['reason'])),account,remaining,owned=lambda:h.owned_destination(owner))
finally:
 for sig,handler in previous.items():signal.signal(sig,handler)
print(json.dumps({k:report.get(k) for k in ('status','comparison_eligible','reason','C_gain_vs_B2_mm','observed_audit_wall_seconds','observed_audit_full_cpu_seconds')}));raise SystemExit(0 if report['comparison_eligible'] else 2)
