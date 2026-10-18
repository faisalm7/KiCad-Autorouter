"""Bind the unchanged finite cancellation control to newly installed031."""
from pathlib import Path
import argparse,json,sys
ROOT=Path(__file__).resolve().parents[1]
runtime=ROOT/'.runs/runtime-directory-031/runtime';sys.path.insert(0,str(runtime));sys.dont_write_bytecode=True
from autorouter import pipeline as p,config as c
assert c.ROOT==runtime and Path(sys.prefix).resolve()==runtime/'.venv'
install=json.loads((ROOT/'.runs/install-distribution-native-004/execution.json').read_text());assert install['passed'] and install['source_unchanged']
prior=json.loads((ROOT/'.runs/runtime030-comparison-engine-cancel-001/protocol.json').read_text())
assert p.tree_hash(Path(prior['source']).parent)==prior['source_hashes']
manifest=p.sha(runtime/'runtime-distribution.json');tools=p.tool_manifest()
assert tools['git_head']=='4f8307ba024304685720e95ac960a717602cf34c'
for name in ['qualify-native7-comparison-route-child-001.py','cancel-runtime030-comparison-engine-001.py','owned-child-path-observer-001.py']:
 target=runtime/'.runs'/name;assert not target.exists();target.parent.mkdir(exist_ok=True);target.write_bytes((ROOT/'.runs'/name).read_bytes())
base=ROOT/'.runs/runtime031-comparison-engine-cancel-001';base.mkdir()
parent=runtime/'.runs/native7-comparison-cancel-attempt-001';out=runtime/'.runs/native7-comparison-cancellation-control-001';assert not parent.exists() and not out.exists()
child=runtime/'.runs/qualify-native7-comparison-route-child-001.py';driver=runtime/'.runs/cancel-runtime030-comparison-engine-001.py'
child_plan=dict(runtime=str(runtime),runtime_manifest_sha256=manifest,tools=tools,source=prior['source'],source_hashes=prior['source_hashes'],source_rights=prior['source_rights'],profile='tuned',route_seconds=420,mode='cancel',output=str(parent),child_sha256=p.sha(child),whole_wall_full_cpu_seconds=220)
q=base/'child-protocol.json'
with q.open('x') as stream:json.dump(child_plan,stream,indent=2);stream.write('\n')
plan=dict(prior,runtime=str(runtime),runtime_manifest_sha256=manifest,source_head=tools['git_head'],tools=tools,output=str(out),route_parent=str(parent),controller=str(driver),controller_args=['--runtime',str(runtime)],child=str(child),child_protocol=str(q),child_protocol_sha256=p.sha(q))
assert p.sha(driver)==plan['controller_sha256'] and p.sha(child)==plan['child_sha256']
assert p.sha(runtime/'.runs/owned-child-path-observer-001.py')==plan['observer_sha256']
q=base/'protocol.json'
with q.open('x') as stream:json.dump(plan,stream,indent=2);stream.write('\n')
print(json.dumps(dict(protocol=str(q),sha256=p.sha(q),runtime_manifest_sha256=manifest,preparation_only=True)))
