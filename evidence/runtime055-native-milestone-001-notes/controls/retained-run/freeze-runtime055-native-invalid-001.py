"""Freeze fresh invalid controls from the completed owned NPTH positive."""
from pathlib import Path
import copy,json,shutil,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f
runtime=ROOT/'.runs/runtime-directory-055/runtime';base=ROOT/'.runs/runtime055-native-controls-001/invalid';assert not base.exists()
positive=ROOT/'.runs/runtime055-native-qualification-002/ordinary-npth2Cu/execution.json';ex=f.read_json(positive);assert ex['controls_passed'] and ex['workflow_delivered']
child_path=Path(ex['child_receipt']);child=f.read_json(child_path);route=Path(child['workspace'])/'route/result.json';record=f.read_json(route)
assert record['accepted'] and record['source_hashes']==p.tree_hash(Path(record['source']).parent)
controller=ROOT/'.runs/qualify-runtime055-hole-safety-001.py';copy_to=runtime/'.runs'/controller.name;assert not copy_to.exists();shutil.copyfile(controller,copy_to)
plan=copy.deepcopy(f.read_json(ROOT/'.runs/runtime050-native-controls-001/invalid/protocol.json'))
encloser=ROOT/'.runs/enclose-runtime030-independent-control-001.py'
plan.update(kind='runtime055-ordinary-NPTH-three-invalid-controls-v1',runtime=str(runtime),runtime_manifest_sha256=p.sha(runtime/'runtime-distribution.json'),source_head='38e193cdf94a814ee50baacb786e7f64214f02b8',controller=str(copy_to),controller_sha256=p.sha(copy_to),enclosure_sha256=p.sha(encloser),output=str(runtime/'.runs/native7-comparison-control-runtime055-npth-invalid-001'),receipt=str(route),source=record['source'],source_hashes=record['source_hashes'],scope=plan['scope'].replace('ordinary050','ordinary055'))
plan['prerequisites']={str(q):p.sha(q) for q in (positive,child_path,route,controller)}
assert not Path(plan['output']).exists();base.mkdir(parents=True,mode=0o700);p.save_json(base/'protocol.json',plan)
p.save_json(base/'frozen.json',dict(schema=1,protocol_sha256=p.sha(base/'protocol.json'),controller_sha256=p.sha(Path(__file__)),executed=False,source_head=plan['source_head'],scope='Fresh control plan only; reuses completed055 positive with own actual Native proof. No control Native or engine execution occurred during freezing. Same120/135caps and three mutations.'))
print(json.dumps(dict(protocol=str(base/'protocol.json'),sha256=p.sha(base/'protocol.json'),executed=False)))
