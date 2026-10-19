"""Pure diagnostic replay of retained failed001; no fresh Native qualification."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p, floor_route as f, schematic_hierarchy as q
base=ROOT/'.runs/runtime-directory-036/runtime/.runs/native7-comparison-hierarchy-controls-001/positive'
binding=f.read_json(base/'task-classes-binding.json');board=Path(binding['source']);copied=Path(binding['input'])
paths=[base/'task-classes.net',base/'export-netclasses.json',*sorted(board.parent.iterdir()),*sorted(copied.parent.iterdir())]
before={str(path.relative_to(ROOT)):p.sha(path) for path in paths if path.is_file()}
assert p.tree_hash(board.parent)==binding['before'] and p.tree_hash(copied.parent)==binding['after']
proof=q.derive((base/'task-classes.net').read_bytes(),board.read_bytes(),board.with_suffix('.kicad_pro').read_bytes(),(base/'export-netclasses.json').read_bytes(),source=str(board),schematic_source=str(copied.with_suffix('.kicad_sch')),schematics={path.name:path.read_bytes() for path in board.parent.glob('*.kicad_sch')})
assert (proof['components'],proof['terminals'],proof['nets'],proof['instances'],len(proof['unconnected_pads']))==(5,11,5,3,4)
assert all(p.sha(ROOT/name)==digest for name,digest in before.items())
result=dict(schema=1,kind='pure-retained-native001-stamp-v2-diagnostic',passed=True,accepted=False,routing_accepted=False,production_qualified=False,Native_executed=False,original_result_unchanged=True,original_source_head='cd898bf3c1c97e988a820c2bf1b783ab6f44864d',original_runtime_manifest_sha256=p.sha(ROOT/'.runs/runtime-directory-036/runtime/runtime-distribution.json'),policy=q.POLICY,comparator_sha256=p.sha(ROOT/'autorouter/schematic_hierarchy.py'),inputs=before,proof=proof,scope='New pure comparator replay of the completed two Native workers only. Does not turn failed001 into a pass or qualify v2 Native routing.')
out=ROOT/'.runs/hierarchy-stamp-v2-replay-001.json';assert not out.exists();p.save_json(out,result)
print({k:proof[k] for k in ('policy','components','terminals','nets','instances','class_parity_qualified','accepted')})
