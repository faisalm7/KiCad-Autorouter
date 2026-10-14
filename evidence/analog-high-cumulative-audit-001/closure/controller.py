from pathlib import Path
import time
START=time.monotonic(); CPU0=time.process_time()
import json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import floor_route as f,pipeline as p,handoff as h
from scripts import experiment_quality as q
CPU0+=f.child_cpu()
prior=ROOT/'.runs/analog-high-incumbent-qualification-002'
review=ROOT/'.runs/analog-high-incumbent-actual-review-001/checks.json'
supplement=ROOT/'.runs/analog-high-warning-supplement-001/checks.json'
qualified=f.read_json(prior/'result.json'); audit=f.read_json(review); extra=f.read_json(supplement)
assert qualified['status']=='completed' and qualified['qualified_before_cumulative_audit_closure']
assert qualified['cumulative_audit_closure_required'] and extra['passed'] and not extra['failures']
assert len(audit['failures'])==1 and audit['failures'][0]['check']=='original_warning_signatures'
assert audit['checks']['central_current_C']['passed'] and audit['checks']['all_pinned_material_unchanged']['passed']
assert all(audit['checks']['trial_trial-%04d'%i] for i in range(8))
exe=f.read_json(prior/'execution.json'); assert exe['result_sha256']==p.sha(prior/'result.json')
items=[{'id':'qualification','wall_seconds':exe['wall_seconds']+exe['bootstrap_publication_allowance_seconds'],'full_cpu_seconds':exe['full_cpu_seconds']+exe['bootstrap_publication_allowance_seconds'],'execution_sha256':p.sha(prior/'execution.json')},
       {'id':'independent-review-with-retained-filename-failure','wall_seconds':audit['cost']['charged_wall_seconds'],'full_cpu_seconds':audit['cost']['charged_full_cpu_seconds'],'checks_sha256':p.sha(review)},
       {'id':'original-warning-supplement','wall_seconds':extra['cost']['charged_wall_seconds'],'full_cpu_seconds':extra['cost']['charged_full_cpu_seconds'],'checks_sha256':p.sha(supplement)}]
wall0=sum(x['wall_seconds'] for x in items);cpu0=sum(x['full_cpu_seconds'] for x in items)
assert abs(wall0-extra['cost']['cumulative_through_supplement_wall_seconds'])<1e-9
assert abs(cpu0-extra['cost']['cumulative_through_supplement_full_cpu_seconds'])<1e-9
pins={str(path):p.sha(path) for path in (prior/'result.json',prior/'execution.json',review,supplement)}
pins.update(audit['checks']['all_pinned_material_unchanged']['pins'])
protocol=ROOT/'.runs/analog-high-incumbent-pruning-002-protocol.json';spec=f.read_json(protocol)
assert qualified['protocol_sha256']==p.sha(protocol)
cap=spec['final_audit_wall_full_cpu_charge_seconds'];assert cap==qualified['audit_wall_full_cpu_charge_seconds']==15
board=Path(spec['source']);out=ROOT/'.runs/analog-high-cumulative-audit-closure-001';out.mkdir();owner={};h.capture_destination(owner,out)
report={'schema':1,'kind':'shared cumulative audit closure','status':'incomplete','accepted':False,'comparison_eligible':False,'new_native_execution':False,'qualified_result':str(prior/'result.json'),'qualified_result_sha256':p.sha(prior/'result.json'),'audit_allowance_wall_full_cpu_seconds':cap,'prior_audit_cost_items':items,'closure_bootstrap_publication_allowance_seconds':1,'controller_sha256':p.sha(Path(__file__)),'results':qualified['results'],'comparisons':qualified['comparisons'],'all_method_exploration_C_charges':qualified['all_method_exploration_C_charges'],'selection_exposure':qualified['selection_exposure'],'quality_verdict':'Fixed fresh-High C is shorter with equal zero vias than strongest retained B2; exposed development result, no adaptive selector/untouched/physical/general-completion claim.','retained_review_lookup_failure_closed_by_separate_supplement':True,'trial0007':'Actual bound final native report0/0/15/0 exists; rejected after metrics timeout, not promoted.'}
def remaining():return min(cap-wall0-1-(time.monotonic()-START),cap-cpu0-1-(time.process_time()+f.child_cpu()-CPU0))
def stable():
 h.owned_destination(owner);q.verify_freeze(spec['freeze'],board)
 for path,pin in pins.items():
  if p.sha(Path(path))!=pin:raise p.Rejected('cumulative audit basis changed')
 for row in [*qualified['final_candidates'],*qualified['C_trial_candidates']]:
  if 'path' not in row:continue
  candidate=Path(row['path'])
  if p.sha(candidate)!=row['candidate_sha256'] or p.sha(candidate.parent.parent/'final-drc.json')!=row['native_report_sha256']:raise p.Rejected('final native candidate/report changed')
 if remaining()<=0:raise p.Rejected('cumulative audit exceeds unchanged15 allowance')
def account():
 wall=time.monotonic()-START;cpu=time.process_time()+f.child_cpu()-CPU0
 ok=remaining()>0 and all(row['accepted'] for row in report['results'] if row['id'] in ('B1','B2_portfolio','C_feedback'))
 report.update(closure_observed_wall_seconds=wall,closure_observed_full_cpu_seconds=cpu,cumulative_audit_wall_seconds=wall0+1+wall,cumulative_audit_full_cpu_seconds=cpu0+1+cpu,status='completed' if ok else 'audit_budget_exceeded',comparison_eligible=ok,cumulative_audit_closure_passed=ok)
try:stable();account()
except Exception as exc:report.update(status='failed',comparison_eligible=False,reason=type(exc).__name__+': '+str(exc))
f.publish(out,report,stable,account,remaining,owned=lambda:h.owned_destination(owner))
print(json.dumps({k:report.get(k) for k in ('status','comparison_eligible','reason','cumulative_audit_wall_seconds','cumulative_audit_full_cpu_seconds')}))
raise SystemExit(0 if report['comparison_eligible'] else 2)
