"""Prospective bounded-readiness freeze; no Native/engine/test execution."""
import time,resource
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import sys,json,hashlib,subprocess
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f
from scripts import experiment_quality as q
source,_=q.selected_source('ir-obstacle');freeze=q.freeze(source)
spec=f.read_json(ROOT/'.local-backups/ir-native-connected-baseline-prep-001/protocol.template.json')
prior='.runs/ir-obstacle-corrected300-readback-execution-003/execution.json';old=f.read_json(ROOT/prior);assert old['passed'] and old['source_current'] and old['whole_delivery_within_budget']
spec.update(status='frozen',tools=p.tool_manifest(),freeze=freeze,prior_execution=prior,prior_rows=old['final_charged_results'],source=str(source),source_hashes=p.tree_hash(source.parent),actor_sha256=p.sha(ROOT/'experiments/ir_native_connected_baseline_v1/actor.py'),outer_sha256=p.sha(ROOT/'.runs/run-ir-native-connected-baseline-001.py'),reader_sha256=p.sha(ROOT/'.runs/read-ir-native-connected-baseline-001.py'),control_execution='.runs/ir-native-connected-baseline-integration-001/execution.json')
for n in [prior,'.runs/ir-obstacle-corrected300-readback-003/result.json','evidence/ir-native300-003.json','.runs/ir-obstacle-original-native-001/result.json','.runs/run-ir-native-connected-baseline-001.py','.runs/read-ir-native-connected-baseline-001.py',spec['control_execution'],'.runs/ir-native-connected-baseline-integration-001/checks.json']:
 spec['pins'][n]=p.sha(ROOT/n)
for n in spec['pins']:spec['pins'][n]=p.sha(ROOT/n)
# Retain old certification and verify byte witnesses only; no old semantic checker or solver.
for row in old['final_charged_results']:
 path=Path(row['result']);assert p.sha(path)==row['result_sha256'];spec['pins'][str(path.relative_to(ROOT))]=p.sha(path)
for item in f.read_json(ROOT/'.runs/ir-obstacle-corrected300-readback-003/result.json')['final_candidates']:
 receipt=Path(item['receipt']);data=f.read_json(receipt)
 for path,expected in [(receipt,None),(Path(data['candidate']) if data.get('candidate') else receipt.parent/'candidate'/source.name,item['candidate_sha256']),(receipt.parent/'final-drc.json',item['native_report_sha256'])]:
  actual=p.sha(path);assert expected is None or actual==expected;spec['pins'][str(path.relative_to(ROOT))]=actual
assert all(max(r['charged_wall_seconds'],r['charged_cpu_seconds'])+40+(95 if r['id']=='B2_portfolio' else 0)<=300 for r in spec['prior_rows'])
spec['delivery_accounting'].update(maximum_new_B2_wall_seconds=next(r['charged_wall_seconds'] for r in spec['prior_rows'] if r['id']=='B2_portfolio')+135,maximum_retained_C_wall_seconds=next(r['charged_wall_seconds'] for r in spec['prior_rows'] if r['id']=='C_feedback')+40,definition='New common includes whole enclosing overhead, fresh integration control plus2, and this preflight whole cost plus1; cap10wall/fullCPU. Add actor actual whole max95 only to B2, pure reader whole max25 and bootstrap/outerpub/readerpub5 equally to every row. Prior001/002/003 costs and candidates retained unchanged. No old semantic Native/engine repeat. Development full085/source research recorded separately; no all-development CPU or speedup claim.')
protocol=ROOT/'.runs/ir-native-connected-baseline-protocol-001.json';assert not protocol.exists();p.save_json(protocol,spec)
out=ROOT/'.runs/ir-native-connected-baseline-preflight-001';out.mkdir();wall,full=time.monotonic()-START,cpu()-CPU0
r=dict(schema=1,passed=max(wall,full)+1<=4,tools=spec['tools'],wall_seconds=wall,full_cpu_seconds=full,publication_allowance_seconds=1,protocol_sha256=p.sha(protocol),controller_sha256=p.sha(Path(__file__)),new_native=False,new_engine=False)
p.save_json(out/'execution.json',r);print(json.dumps({k:r[k] for k in ('passed','wall_seconds','full_cpu_seconds','protocol_sha256')}));raise SystemExit(0 if r['passed'] else 2)
