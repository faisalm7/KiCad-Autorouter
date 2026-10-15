import time,resource
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,sexpr as sx,routing_scope as rs,board_floor as g
from scripts import experiment_quality as q
spec=f.read_json(ROOT/'.local-backups/ir-native-connected-repair-prep-001/protocol.template.json');source,family=q.selected_source('ir-obstacle');tools=p.tool_manifest()
actor=ROOT/'.runs/ir-native-connected-repair-actor-001.py';reader=ROOT/'.runs/read-ir-native-connected-repair-001.py';outer=ROOT/'.runs/run-ir-native-connected-repair-001.py';warm=ROOT/'.runs/ir-native-connected-baseline-001/route/candidate/IR_Sensor.kicad_pcb'
spec.update(status='frozen',source=str(source),source_hashes=p.tree_hash(source.parent),tools=tools,freeze=q.freeze(source),actor_sha256=p.sha(actor),reader_sha256=p.sha(reader),outer_sha256=p.sha(outer),repair_source=str(warm),original_report='.runs/ir-obstacle-original-native-001/job/original-final.json',prior_execution='.runs/ir-native-connected-cumulative-001.json')
spec['retained_material']['.runs/ir-native-connected-classifier-001']=None
spec['retained_material']={n:p.tree_hash(ROOT/n)for n in spec['retained_material']}
for path in [actor,reader,outer,ROOT/'.runs/run-ir-native-connected-repair-readback-001.py',Path(__file__)]:spec['pins'][str(path.relative_to(ROOT))]=p.sha(path)
assert all(p.sha(ROOT/n)==pin for n,pin in spec['pins'].items())
prior=f.read_json(ROOT/spec['prior_execution']);assert prior['comparison_eligible'] and spec['prior_rows']==[{k:r[k]for k in ('id','accepted','charged_wall_seconds','charged_cpu_seconds')}for r in prior['final_charged_results']]
assert all(max(r['charged_wall_seconds'],r['charged_cpu_seconds'])+17+(63 if r['id']=='B2_portfolio'else 0)<=300 for r in spec['prior_rows'])
# Actual Native-reported same-zone UUID, original net identity and protected copper.
findings=f.read_json(ROOT/'.runs/ir-native-connected-negative-child-tail-002/checks.json')['unconnected_items'];ids={x['uuid']for x in findings[0]['items']};tree=sx.read(warm);zones=[z for z in sx.children(tree,'zone')if rs._uuid(sx.one(z,'uuid'))[1]in ids];_,resolve=g.source_net_identity(tree);assert len(ids)==len(zones)==1 and [resolve(sx.one(zones[0],'net'),owner=zones[0])]==['/GND'] and rs.protected_routes(tree,['/GND'])
protocol=ROOT/'.runs/ir-native-connected-repair-protocol-001.json';assert not protocol.exists();p.save_json(protocol,spec)
out=ROOT/'.runs/ir-native-connected-repair-preflight-001';out.mkdir();wall,full=time.monotonic()-START,cpu()-CPU0
record=dict(schema=1,passed=max(wall,full)+1<=3,wall_seconds=wall,full_cpu_seconds=full,publication_allowance_seconds=1,protocol_sha256=p.sha(protocol),tools=tools,controller_sha256=p.sha(Path(__file__)),new_native=False,new_engine=False)
p.save_json(out/'execution.json',record);print(json.dumps({k:record[k]for k in ('passed','wall_seconds','full_cpu_seconds','protocol_sha256')}));raise SystemExit(0 if record['passed']else 2)
