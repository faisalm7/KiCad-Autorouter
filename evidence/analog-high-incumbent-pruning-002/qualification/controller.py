from pathlib import Path
import time
START=time.monotonic();CPU0=time.process_time()
import json,sys,copy
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,handoff as h,placement_clearance as pc
from scripts import experiment_quality as q,experiment_paired as paired
from experiments.native_paired_v1 import readback as shared
CPU0+=f.child_cpu()
protocol=ROOT/'.runs/analog-high-incumbent-pruning-002-protocol.json';spec=f.read_json(protocol);base=ROOT/'.runs/analog-high-incumbent-pruning-002';data=f.read_json(base/'run/result.json');outer=f.read_json(base/'execution.json')
old=f.read_json(ROOT/'.runs/analog-filter-cumulative-audit-additive-001/result.json');original_record=f.read_json(ROOT/'.runs/analog-filter-original-native-001/result.json')
original_native=original_record['parity_native'];board=Path(spec['source']);original=p.preflight(board);cap=spec['final_audit_wall_full_cpu_charge_seconds']
pins={str(protocol):p.sha(protocol),**spec['artifacts'],str(base/'execution.json'):p.sha(base/'execution.json'),str(base/'run/result.json'):p.sha(base/'run/result.json')}
witness=pc.inventory(base,max_bytes=64*1024**2,max_files=6000,max_entries=12000,with_directories=True)
out=ROOT/'.runs/analog-high-incumbent-qualification-002';out.mkdir();owner={};h.capture_destination(owner,out)
report={'schema':1,'kind':'exposed separately fixed High-incumbent pruning comparison','status':'incomplete','accepted':False,'comparison_eligible':False,'new_native_execution':False,'controller_sha256':p.sha(Path(__file__)),'protocol_sha256':p.sha(protocol),'native_run_execution_sha256':p.sha(base/'execution.json'),'audit_wall_full_cpu_charge_seconds':cap,'cumulative_audit_closure_required':True,'cumulative_audit_closure_passed':False,'results':[],'final_candidates':[],'C_trial_candidates':[],'prior_defaultC_exploration_charge':spec['prior_defaultC_exploration_charge'],'prior_failed_high_attempts':spec['prior_attempts'],'selection_exposure':spec['selection_exposure'],'physical_electrical_human_validation':False}
def remaining():return min(cap-(time.monotonic()-START),cap-(time.process_time()+f.child_cpu()-CPU0))
def stable():
 h.owned_destination(owner);q.verify_freeze(spec['freeze'],board)
 for name,pin in pins.items():
  if p.sha(Path(name))!=pin:raise p.Rejected('final comparison basis changed')
 if pc.inventory(base,max_bytes=64*1024**2,max_files=6000,max_entries=12000,with_directories=True)!=witness:raise p.Rejected('new native run changed')
 if remaining()<=0:raise p.Rejected('new audit allowance exceeded')
def warnings(native):return f.canonical([row for row in native['findings'] if row['severity']=='warning'])
def final(folder,row,parent=None):
 checked=shared.final_candidate_readback(folder,row,board,original,spec['freeze']['source_hashes'],resource_parent=parent)
 checked['unchanged_original_warning_signatures']=warnings(row['native'])==warnings(original_native)
 if row['accepted'] and not checked['unchanged_original_warning_signatures']:raise p.Rejected('accepted final original warnings changed')
 return checked
def account():
 report.update(observed_audit_wall_seconds=time.monotonic()-START,observed_audit_full_cpu_seconds=time.process_time()+f.child_cpu()-CPU0)
 if remaining()<=0:report.update(status='audit_budget_exceeded',comparison_eligible=False)
try:
 with p.validation_readback_session():
  stable();assert data['accepted'] and data['incumbent_scoring_variant']=='via_high' and data['tools']==spec['freeze']['tools'] and outer['protocol_sha256']==p.sha(protocol)
  assert outer['process']['status']=='success' and outer['process']['exit_code']==0 and outer['process']['cleanup_complete']
  assert old['comparison_eligible'];p.check_result(base/'run/result.json')
  for attempt in spec['prior_attempts']:
   failed=f.read_json(Path(attempt['result']));p.check_resource_accounting(failed)
   assert failed['status']=='incumbent_rejected' and not failed['accepted']
  for row in old['results']:
   if row['id']=='C_feedback':continue
   kept=copy.deepcopy(row);kept['charged_wall_seconds']+=cap+1;kept['charged_full_cpu_seconds']+=cap+1
   kept['within_equal120_wall_full_cpu_caps']=max(kept['charged_wall_seconds'],kept['charged_full_cpu_seconds'])<=120
   kept['accepted']=kept['native_accepted'] and kept['within_equal120_wall_full_cpu_caps']
   if kept['id']=='B2_portfolio':
    for trial in kept['trials']:
     path=Path(trial['result']);r=f.read_json(path);assert p.sha(path)==trial['result_sha256']
     if trial['eligible']:p.check_result(path)
     report['final_candidates'].append({'id':'B2/'+trial['id'],**final(path.parent,r)})
   else:
    path=Path(kept['result']);r=f.read_json(path);assert p.sha(path)==kept['result_sha256']
    if kept['native_accepted']:p.check_result(path)
    report['final_candidates'].append({'id':kept['id'],**final(path.parent,r)})
   report['results'].append(kept)
  report['final_candidates'].append({'id':'C_high',**final(base/'run',data)})
  incumbent=f.read_json(base/'run/incumbent/result.json');report['final_candidates'].append({'id':'C_high/own_incumbent',**final(base/'run/incumbent',incumbent)})
  for reference in data['trials']:
   folder=base/'run/trials'/reference['id'];r=f.read_json(folder/'result.json');shared.inherited_trial_accounting(folder,r,data)
   row={'id':r['id'],'status':r['status'],'accepted':r['accepted'],'receipt_sha256':p.sha(folder/'result.json'),'worker_costs_bound_to_parent':True,'reason':r.get('reason')}
   if r.get('candidate_sha256') and r.get('native_report_sha256'):row.update(final(folder,r,data))
   else:row['final_native_available']=False
   report['C_trial_candidates'].append(row)
  charge={key:spec['already_committed_C_charge'][key]+outer['wall_seconds' if key=='wall_seconds' else 'full_cpu_seconds'] for key in ('wall_seconds','full_cpu_seconds')}
  metrics=data['metrics'];c={'id':'C_feedback','method_configuration':'fixed via_high fresh incumbent plus native feedback pruning','result':str(base/'run/result.json'),'result_sha256':p.sha(base/'run/result.json'),'candidate_sha256':data['candidate_sha256'],'native_report_sha256':data['native_report_sha256'],'native_accepted':True,'length_mm':metrics['track_length_mm'],'vias':metrics['vias'],'charged_wall_seconds':charge['wall_seconds'],'charged_full_cpu_seconds':charge['full_cpu_seconds'],'within_equal120_wall_full_cpu_caps':max(charge.values())<=120,'accepted':max(charge.values())<=120}
  report['results'].append(c);report['comparisons']=paired.comparisons(report['results'])
  report['all_method_exploration_C_charges']={key:charge[key]+spec['prior_defaultC_exploration_charge']['charged_'+key] for key in charge}
  report.update(status='completed',qualified_before_cumulative_audit_closure=all(row['accepted'] for row in report['results'] if row['id'] in ('B1','B2_portfolio','C_feedback')),incumbent_metrics=incumbent['metrics'],improvements=data['improvements'])
except Exception as exc:report.update(status='failed',comparison_eligible=False,reason=type(exc).__name__+': '+str(exc))
f.publish(out,report,stable,account,remaining,owned=lambda:h.owned_destination(owner))
p.save_json(out/'execution.json',{'wall_seconds':time.monotonic()-START,'full_cpu_seconds':time.process_time()+f.child_cpu()-CPU0,'result_sha256':p.sha(out/'result.json'),'bootstrap_publication_allowance_seconds':1,'scope':'Before imports through publication; cumulative independent audit/bootstrap/emission still must fit charged15.'})
print(json.dumps({k:report.get(k) for k in ('status','reason','qualified_before_cumulative_audit_closure','observed_audit_wall_seconds','observed_audit_full_cpu_seconds')}))
raise SystemExit(0 if report['status']=='completed' else 2)
