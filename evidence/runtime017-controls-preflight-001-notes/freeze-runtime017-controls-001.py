"""Freeze reviewed three-control sources using the completed production context."""
from pathlib import Path
import importlib.util,json,sys,time,resource
START=time.monotonic()
def cpu():return sum(r.ru_utime+r.ru_stime for r in(resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu();ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f
plan=f.read_json(ROOT/'.runs/runtime017-controls-001-protocol-draft.json')
assert p.sha(ROOT/'.runs/runtime017-controls-001-protocol-draft.json')=='e9a24bdee55f8dd457eb41a2b4b1925fb62f34f3c2d42f2d4ddec358bc86107c'and plan['status']=='draft-not-executable'
child=ROOT/'.runs/qualify-runtime017-controls-001.py';outer=ROOT/'.runs/run-runtime017-controls-001.py'
assert p.sha(child)==plan['child_sha256']=='0325f45697825ff10d0d1795b3aeae605a8e5076857555c088e41fabd392e08a'
assert p.sha(outer)==plan['outer_controller_sha256']=='288063ebc20b9fe969e8ba9454670bfa3d25c529d1ecdc0452e459c86a70ebed'
review=ROOT/'.runs/runtime017-controls-source-review-001.json';r=f.read_json(review);assert r['material_findings']==[]and r['Native_executed']is False
spec=importlib.util.spec_from_file_location('reviewed017controls',outer);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
prod=m.production_helper();shared=prod.shared_helpers();prod.frozen(Path(plan['production_protocol']),plan['production_protocol_sha256'],shared)
for path,digest in plan['prerequisite_sha256'].items():assert p.sha(Path(path))==digest,path
plan['prerequisite_sha256'].update({str(review):p.sha(review),str(ROOT/'.runs/runtime017-controls-receipts-001-time.log'):p.sha(ROOT/'.runs/runtime017-controls-receipts-001-time.log'),
 str(ROOT/'.runs/test-runtime017-controls-receipts-001.py'):p.sha(ROOT/'.runs/test-runtime017-controls-receipts-001.py')})
plan['status']='frozen';plan['source_review']=str(review)
plan['preparation_costs']=dict(sample_wall_seconds=time.monotonic()-START,sample_full_cpu_seconds=cpu()-CPU0,Native_executed=False,JVM_executed=False,scope='Static source/context readback and exclusive child copy only; external whole preparation cost separate, no actual control execution.')
runtime=Path(plan['runtime']);target=runtime/'.runs'/plan['installed_child_name']
with target.open('xb')as stream:stream.write(child.read_bytes())
protocol=ROOT/'.runs/runtime017-controls-001-protocol-frozen.json'
with protocol.open('x')as stream:json.dump(plan,stream,indent=2,allow_nan=False);stream.write('\n')
assert m.frozen(protocol,p.sha(protocol),prod,shared)==plan
print(json.dumps(dict(frozen=True,protocol=str(protocol),sha256=p.sha(protocol),Native_executed=False,JVM_executed=False)))
