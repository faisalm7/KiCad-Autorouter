"""Fixed copy-only disallowed-layer control through shared native and layer checks."""
from pathlib import Path
import json,shutil,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from autorouter import pipeline as p,sexpr as sx,preferences as pref
from scripts.native_class_controls import OfflineJob,cpu_total
started=time.monotonic();cpu_started=cpu_total()
receipt=ROOT/'.runs/layers-native-front-001/result.json';verified=p.check_result(receipt)
prior=json.loads(receipt.read_text());source=Path(prior['source']);accepted=Path(verified['candidate'])
source_before=p.tree_hash(source.parent);run_before=p.tree_hash(receipt.parent);tools=p.tool_manifest()
effective=pref.readback((receipt.parent/'routing-preferences.json').read_bytes());assert effective['layers']==['F.Cu']
contract=p.layer_contract(receipt.parent,source,effective,prior['layer_binding'])
out=ROOT/'.runs/layer-negative-native-001';job=OfflineJob(out,max(5,60-(time.monotonic()-started)))
shutil.copytree(accepted.parent,out/'candidate');candidate=out/'candidate'/source.name
original=sx.read(source);changed=sx.read(candidate);mutations=[]
for route in p.routes(changed):
 if sx.unquote(sx.one(route,'net')[1])!='SIGNAL_A':continue
 assert route[0]=='segment' and sx.one(route,'layer')==['layer','"F.Cu"']
 mutations.append(sx.one(route,'uuid')[1]);sx.one(route,'layer')[1]='"B.Cu"'
assert mutations and p.immutable(changed)==p.immutable(original)
sx.write(candidate,changed)
summary={'schema':1,'control':'move every generated SIGNAL_A segment to B.Cu on a separate front-only accepted-project copy',
 'routing_accepted':False,'passed':False,'solver_executed':False,'mocked_native_execution':False,
 'source':str(source),'source_hashes':source_before,'accepted_receipt_sha256':p.sha(receipt),
 'accepted_candidate_sha256':verified['candidate_sha256'],'moved_uuid_atoms':mutations,'candidate_sha256':p.sha(candidate),
 'tools':tools,'script_sha256':p.sha(Path(__file__)),'budget_seconds':60,'cpu_budget_seconds':60}
try:
 summary['native']=job.drc('disallowed-layer-drc',candidate)
 summary['native_report_sha256']=p.sha(out/'disallowed-layer-drc.json')
 count=len(job.steps)
 try:p.validate_candidate(job,original,candidate,source_before,[],layer_contract=contract)
 except (ValueError,p.Rejected) as exc:summary['guard_rejection']=str(exc)
 summary['guard_ran_no_extra_native']=len(job.steps)==count
 summary['source_unchanged']=p.tree_hash(source.parent)==source_before
 summary['accepted_run_unchanged']=p.tree_hash(receipt.parent)==run_before
 summary['runtime_unchanged']=p.tool_manifest()==tools
 summary['positive_readback']=p.check_result(receipt)
 summary['candidate_unchanged']=p.sha(candidate)==summary['candidate_sha256']
 summary['passed']=(summary.get('guard_rejection','').startswith('new route uses disallowed copper layer:')
  and p.native_accepted(summary['native']) and all(summary[k] for k in ('guard_ran_no_extra_native','source_unchanged','accepted_run_unchanged','runtime_unchanged','candidate_unchanged')))
except (Exception,KeyboardInterrupt) as exc:summary.update(passed=False,error=type(exc).__name__+': '+str(exc))
summary.update(steps=job.steps,wall_seconds=time.monotonic()-started,total_cpu_seconds=cpu_total()-cpu_started)
if max(summary['wall_seconds'],summary['total_cpu_seconds'])>60:summary.update(passed=False,error='budget exceeded')
p.save_json(out/'summary.json',summary)
print(json.dumps({k:summary.get(k) for k in ('passed','guard_rejection','native','wall_seconds','total_cpu_seconds','error')}))
raise SystemExit(0 if summary['passed'] else 2)
