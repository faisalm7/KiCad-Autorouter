"""Freeze fresh invalid controls from the completed owned NPTH positive."""
from pathlib import Path
import copy,json,shutil,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f
runtime=ROOT/'.runs/runtime-directory-056/runtime';base=ROOT/'.runs/runtime056-native-controls-001/invalid';assert not base.exists()
positive=ROOT/'.runs/runtime056-native-qualification-001/via-high-whole2Cu/execution.json';ex=f.read_json(positive);assert ex['controls_passed'] and ex['workflow_delivered']
child_path=Path(ex['child_receipt']);child=f.read_json(child_path);route=Path(child['workspace'])/'route/result.json';record=f.read_json(route)
assert record['accepted'] and record['source_hashes']==p.tree_hash(Path(record['source']).parent)
controller=ROOT/'.runs/qualify-runtime056-hole-safety-001.py';copy_to=runtime/'.runs'/controller.name;assert not copy_to.exists();shutil.copyfile(controller,copy_to)
plan=copy.deepcopy(f.read_json(ROOT/'.runs/runtime050-native-controls-001/invalid/protocol.json'))
encloser=ROOT/'.runs/enclose-runtime030-independent-control-001.py'
plan.update(kind='runtime056-via-high-NPTH-three-invalid-controls-v1',expected_scoring='via_high',runtime=str(runtime),runtime_manifest_sha256=p.sha(runtime/'runtime-distribution.json'),source_head='a03b5e8b6ae523d9f099cf211815900053629fe3',controller=str(copy_to),controller_sha256=p.sha(copy_to),enclosure_sha256=p.sha(encloser),output=str(runtime/'.runs/native7-comparison-control-runtime056-npth-invalid-001'),receipt=str(route),source=record['source'],source_hashes=record['source_hashes'],scope=plan['scope'].replace('ordinary050','ordinary056'))
plan['prerequisites']={str(q):p.sha(q) for q in (positive,child_path,route,controller)}
assert not Path(plan['output']).exists();base.mkdir(parents=True,mode=0o700);p.save_json(base/'protocol.json',plan)
p.save_json(base/'frozen.json',dict(schema=1,protocol_sha256=p.sha(base/'protocol.json'),controller_sha256=p.sha(Path(__file__)),executed=False,source_head=plan['source_head'],scope='Fresh control plan only; reuses completed056 positive with own actual Native proof. No control Native or engine execution occurred during freezing. Explicit high-cost positive; same120/135caps and three mutations.'))
print(json.dumps(dict(protocol=str(base/'protocol.json'),sha256=p.sha(base/'protocol.json'),executed=False)))
