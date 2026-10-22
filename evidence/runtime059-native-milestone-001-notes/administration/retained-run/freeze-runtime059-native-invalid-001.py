"""DRAFT: freeze the same three invalid controls after export replay repair.

Requires the completed current058 high-via whole2Cu positive; no old result
provides current authority. Existing120s child/135s outer limits are unchanged.
"""
from pathlib import Path
import copy,json,shutil,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f
runtime=ROOT/'.runs/runtime-directory-059/runtime';base=ROOT/'.runs/runtime059-native-controls-001/invalid';assert not base.exists()
positive=ROOT/'.runs/runtime059-native-qualification-001/via-high-whole2Cu/execution.json';ex=f.read_json(positive);assert ex['controls_passed'] and ex['workflow_delivered']
child_path=Path(ex['child_receipt']);child=f.read_json(child_path);route=Path(child['workspace'])/'route/result.json';record=f.read_json(route)
assert record['accepted'] and record['source_hashes']==p.tree_hash(Path(record['source']).parent)
controller=ROOT/'.runs/qualify-runtime059-hole-safety-001.py';copy_to=runtime/'.runs'/controller.name;assert not copy_to.exists();shutil.copyfile(controller,copy_to)
prior=ROOT/'.runs/runtime058-native-controls-001/invalid/protocol.json'
assert p.sha(prior)=='fa50b60b80fcfb4553b832814d1dd000bcb840025e93d867d1057f9c954fe22d'
plan=copy.deepcopy(f.read_json(prior))
encloser=ROOT/'.runs/enclose-runtime030-independent-control-001.py'
plan.update(kind='runtime059-via-high-NPTH-three-invalid-controls-v1',expected_scoring='via_high',runtime=str(runtime),runtime_manifest_sha256=p.sha(runtime/'runtime-distribution.json'),source_head='50f63338a67cdbdb81e0392fff7dda5dceaf5b4d',controller=str(copy_to),controller_sha256=p.sha(copy_to),enclosure_sha256=p.sha(encloser),output=str(runtime/'.runs/native7-comparison-control-runtime059-npth-invalid-001'),receipt=str(route),source=record['source'],source_hashes=record['source_hashes'],scope=plan['scope'].replace('ordinary058','ordinary059'))
plan['prerequisites']={str(q):p.sha(q) for q in (positive,child_path,route,controller)}
assert not Path(plan['output']).exists();base.mkdir(parents=True,mode=0o700);p.save_json(base/'protocol.json',plan)
p.save_json(base/'frozen.json',dict(schema=1,protocol_sha256=p.sha(base/'protocol.json'),controller_sha256=p.sha(Path(__file__)),executed=False,source_head=plan['source_head'],scope='Fresh control plan only; reuses completed058 positive with own actual Native proof. No control Native or engine execution occurred during freezing. Explicit high-cost positive; same120/135caps and three mutations.'))
print(json.dumps(dict(protocol=str(base/'protocol.json'),sha256=p.sha(base/'protocol.json'),executed=False)))
