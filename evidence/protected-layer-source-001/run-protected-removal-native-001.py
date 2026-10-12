"""Preselected removal control, reusing actual Job DRC and production guard."""
from pathlib import Path
import datetime,json,resource,shutil,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from autorouter import pipeline as p,sexpr as sx
from scripts.native_class_controls import OfflineJob,cpu_total
started=time.monotonic();cpu_started=cpu_total()
receipt=ROOT/'.runs/preferences-native-partial-002/result.json'
verified=p.check_result(receipt);prior=json.loads(receipt.read_text());source=Path(prior['source']);accepted=Path(verified['candidate'])
source_before=p.tree_hash(source.parent);run_before=p.tree_hash(receipt.parent);tools=p.tool_manifest()
original=sx.read(source);protected=p.routes(original)
assert prior['scope']=='partial_completion' and len(protected)==2
selected=[r for r in protected if sx.one(r,'uuid')[1]=='"938c1c14-f4a8-48c1-a41b-b4e3e79fc5bf"'];assert len(selected)==1
out=ROOT/'.runs/protected-removal-native-001';job=OfflineJob(out,max(5,60-(time.monotonic()-started)))
shutil.copytree(accepted.parent,out/'candidate');candidate=out/'candidate'/source.name
before=sx.read(candidate);changed=sx.read(candidate);assert changed.count(selected[0])==1;changed.remove(selected[0]);sx.write(candidate,changed)
assert p.immutable(changed)==p.immutable(original) and len(p.routes(before))-len(p.routes(changed))==1
summary={'schema':1,'control':'remove exactly one original protected 5mm SIGNAL_A segment from a separate accepted-project copy','routing_accepted':False,'passed':False,'solver_executed':False,'mocked_native_execution':False,'source':str(source),'source_hashes':source_before,'accepted_receipt_sha256':p.sha(receipt),'accepted_candidate_sha256':verified['candidate_sha256'],'removed_route':selected[0],'candidate_sha256':p.sha(candidate),'tools':tools,'script_sha256':p.sha(Path(__file__)),'budget_seconds':60,'cpu_budget_seconds':60}
try:
 summary['native']=job.drc('removal-drc',candidate)
 summary['native_report_sha256']=p.sha(out/'removal-drc.json')
 try:p.validate_candidate(job,original,candidate,source_before,protected)
 except p.Rejected as exc:summary['guard_rejection']=str(exc)
 summary['source_unchanged']=p.tree_hash(source.parent)==source_before
 summary['accepted_run_unchanged']=p.tree_hash(receipt.parent)==run_before
 summary['runtime_unchanged']=p.tool_manifest()==tools
 summary['positive_readback']=p.check_result(receipt)
 summary['candidate_unchanged']=p.sha(candidate)==summary['candidate_sha256']
 summary['passed']=(summary['guard_rejection']=='protected route changed' and summary['native']['opens']==1 and summary['native']['blocking']==0 and summary['native']['exclusions']==0 and all(summary[k] for k in ('source_unchanged','accepted_run_unchanged','runtime_unchanged','candidate_unchanged')))
except (Exception,KeyboardInterrupt) as exc:summary.update(passed=False,error=type(exc).__name__+': '+str(exc))
summary.update(steps=job.steps,wall_seconds=time.monotonic()-started,total_cpu_seconds=cpu_total()-cpu_started)
if max(summary['wall_seconds'],summary['total_cpu_seconds'])>60:summary.update(passed=False,error='budget exceeded')
p.save_json(out/'summary.json',summary)
print(json.dumps({k:summary.get(k) for k in ('passed','guard_rejection','native','wall_seconds','total_cpu_seconds','error')}))
raise SystemExit(0 if summary['passed'] else 2)
