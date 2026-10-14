from pathlib import Path
import time
START=time.monotonic();CPU0=time.process_time()
import json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import floor_route as f,pipeline as p,handoff as h
from scripts import experiment_quality as q
CPU0+=f.child_cpu()
prior=ROOT/'.runs/analog-filter-strong-b2-qualification-001';review=ROOT/'.runs/analog-inherited-trial-review-001/checks.json'
qualified=f.read_json(prior/'result.json');audit=f.read_json(review)
assert qualified['status']=='completed' and qualified['cumulative_audit_closure_required'] and audit['passed']
assert audit['strong_qualification_sha256']==p.sha(prior/'result.json') and audit['strong_execution_sha256']==p.sha(prior/'execution.json')
items=[];pins={str(review):p.sha(review),str(prior/'result.json'):p.sha(prior/'result.json')}
for name in ('analog-filter-paired-qualification-001','analog-filter-paired-qualification-002','analog-filter-strong-b2-qualification-001'):
 path=ROOT/'.runs'/name/'execution.json';exe=f.read_json(path);result=path.with_name('result.json');assert exe['result_sha256']==p.sha(result)
 pins[str(path)]=p.sha(path);pins[str(result)]=p.sha(result)
 items.append({'id':name,'wall_seconds':exe['wall_seconds']+1,'full_cpu_seconds':exe['full_cpu_seconds']+1,'startup_publication_allowance_seconds':1,'execution_sha256':p.sha(path),'result_sha256':p.sha(result)})
probe=ROOT/'.runs/analog-inherited-trial-readback-fix-001/actual-trial-readbacks.json';pins[str(probe)]=p.sha(probe)
items.append({'id':'actual-eight-trial-probe','wall_seconds':3.,'full_cpu_seconds':3.,'meaning':'Conservative fixed3 for sum .366518 wall probe bodies, unsampled bootstrap and emission. Single-threaded pure readback/no Native children; detailed body times preserved. This is an allowance, not observed3duration.'})
items.append({'id':'independent-inherited-and-high-review','wall_seconds':audit['observed_wall_seconds_before_emission']+audit['bootstrap_allowance_seconds']+audit['packet_emission_allowance_seconds'],'full_cpu_seconds':audit['lifetime_self_CPU_seconds']+audit['waited_child_CPU_seconds']+audit['bootstrap_allowance_seconds']+audit['packet_emission_allowance_seconds'],'review_sha256':p.sha(review)})
amendpath=ROOT/'.runs/analog-filter-audit-additive-amendment-001-protocol.json';amend=f.read_json(amendpath);failedpath=Path(amend['failed_closure']);failed=f.read_json(failedpath)
assert amend['failed_closure_sha256']==p.sha(failedpath) and failed['status']=='audit_budget_exceeded' and not failed['comparison_eligible']
assert amend['original_qualification_sha256']==p.sha(prior/'result.json') and amend['equal_wall_full_cpu_cap_seconds']==120 and amend['additional_audit_charge_each_arm_seconds']==3
pins[str(amendpath)]=p.sha(amendpath);pins[str(failedpath)]=p.sha(failedpath)
items.append({'id':'failed-original15-cumulative-closure','wall_seconds':failed['closure_observed_wall_seconds']+failed['closure_bootstrap_publication_allowance_seconds'],'full_cpu_seconds':failed['closure_observed_full_cpu_seconds']+failed['closure_bootstrap_publication_allowance_seconds'],'result_sha256':p.sha(failedpath)})
priorwall=sum(row['wall_seconds'] for row in items);priorcpu=sum(row['full_cpu_seconds'] for row in items)
assert qualified['audit_wall_and_full_cpu_charge_seconds']==amend['original_audit_allowance_seconds']==15
cap=amend['new_cumulative_audit_allowance_seconds'];assert cap==18
for row in qualified['results']:
 row['charged_wall_seconds']+=3;row['charged_full_cpu_seconds']+=3
 row['within_equal120_wall_full_cpu_caps']=max(row['charged_wall_seconds'],row['charged_full_cpu_seconds'])<=120
 row['accepted']=row['native_accepted'] and row['within_equal120_wall_full_cpu_caps']
out=ROOT/'.runs/analog-filter-cumulative-audit-additive-001';out.mkdir();owner={};h.capture_destination(owner,out)
frozen=f.read_json(ROOT/'.runs/analog-filter-b2-high-only-001-protocol.json')['freeze'];board=Path(f.read_json(ROOT/'.runs/analog-filter-b2-high-only-001-protocol.json')['source'])
report={'schema':1,'kind':'additive-cumulative-audit-closure','status':'incomplete','comparison_eligible':False,'accepted':False,'new_native_execution':False,'additive_amendment_sha256':p.sha(amendpath),'additional_audit_charge_each_arm_seconds':3,'original15_closure_failed_and_retained':True,'qualified_result_sha256':p.sha(prior/'result.json'),'qualified_result':str(prior/'result.json'),'audit_allowance_wall_full_cpu_seconds':cap,'prior_audit_cost_items':items,'closure_bootstrap_publication_allowance_seconds':1,'quality_verdict':'C shorter but one additional via versus selected zero-via High: tradeoff, no strongB2 domination','claims_limit':qualified['claims_limit'],'results':qualified['results'],'comparisons':qualified['comparisons'],'controller_sha256':p.sha(Path(__file__))}
def remaining():return min(cap-priorwall-1-(time.monotonic()-START),cap-priorcpu-1-(time.process_time()+f.child_cpu()-CPU0))
def stable():
 h.owned_destination(owner);q.verify_freeze(frozen,board)
 for path,pin in pins.items():
  if p.sha(Path(path))!=pin:raise p.Rejected('cumulative audit basis changed')
 for row in [*qualified['final_candidates'],*qualified['C_trial_candidates']]:
  if 'path' not in row:continue
  candidate=Path(row['path'])
  if p.sha(candidate)!=row['candidate_sha256'] or p.sha(candidate.parent.parent/'final-drc.json')!=row['native_report_sha256']:raise p.Rejected('final Native candidate/report changed')
 if remaining()<=0:raise p.Rejected('all cumulative failed/new audit work exceeds charged18 allowance')
def account():
 wall=time.monotonic()-START;cpu=time.process_time()+f.child_cpu()-CPU0
 report.update(closure_observed_wall_seconds=wall,closure_observed_full_cpu_seconds=cpu,cumulative_audit_wall_seconds=priorwall+1+wall,cumulative_audit_full_cpu_seconds=priorcpu+1+cpu)
 ok=remaining()>0 and all(row['accepted'] for row in report['results'] if row['id'] in ('B1','B2_portfolio','C_feedback'))
 report.update(status='completed' if ok else 'audit_budget_exceeded',comparison_eligible=ok,cumulative_audit_closure_passed=ok)
try:stable();account()
except Exception as exc:report.update(status='failed',comparison_eligible=False,reason=type(exc).__name__+': '+str(exc))
f.publish(out,report,stable,account,remaining,owned=lambda:h.owned_destination(owner))
print(json.dumps({k:report.get(k) for k in ('status','comparison_eligible','reason','cumulative_audit_wall_seconds','cumulative_audit_full_cpu_seconds')}))
raise SystemExit(0 if report['comparison_eligible'] else 2)
