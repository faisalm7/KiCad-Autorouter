"""Pure replay of the actual refused038 map; no Native or routing execution."""
from pathlib import Path
import sys,time,hashlib,json
START=time.monotonic();ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import schematic_hierarchy as q,pipeline as p,preferences
route=ROOT/'.runs/runtime-directory-038/runtime/.runs/ordinary-hierarchy-whole2Cu-001/autorouter-gui-a678fb8855c74ac09f272d7f6a54e473/route'
board=route/'candidate/owned_hierarchy_native.kicad_pcb';project=board.with_suffix('.kicad_pro');native=route/'export-netclasses.json'
paths=[board,project,native,route/'result.json',*sorted(board.parent.glob('*.kicad_sch'))]
pins={str(path.relative_to(ROOT)):p.sha(path) for path in paths};old=json.loads((route/'result.json').read_bytes())
assert old['accepted'] is False and old['reason']=='ValueError: hierarchy parity: native class map source/schema differs'
raw_board=board.read_bytes();raw_project=project.read_bytes();raw_native=native.read_bytes()
req=q.source_requirement(raw_board,raw_project,source=str(board),schematics={x.name:x.read_bytes() for x in board.parent.glob('*.kicad_sch')},native_version='10.0.7')
partitions={name:{tuple(v) for v in rows} for name,rows in req['partitions'].items()}
classes=q._classes(raw_native,str(board),raw_board,raw_project,preferences._parse(raw_project,q.MAX_BYTES),partitions,'10.0.7')
assert len(classes)==5 and all(p.sha(ROOT/name)==digest for name,digest in pins.items())
record=dict(schema=1,kind='pure-current-reader-replay-actual038-native-map',passed=True,Native_executed=False,routing_executed=False,accepted=False,full_schematic_parity_performed=False,source_unchanged=True,input_sha256=pins,reader_sha256={name:p.sha(ROOT/name) for name in ('autorouter/schematic_hierarchy.py','autorouter/schematic_classes.py','autorouter/netclass_native.py','autorouter/default_targets.py')},rows=classes,scope='Only actual retained PCB class map preliminary schema/scalar/parent/floor check, before any SCH netlist worker. Does not qualify038 or039 delivery or assert a new Native observation.',wall_seconds=time.monotonic()-START)
p.save_json(ROOT/'.runs/native-map-floor-schema-replay-001.json',record);print(json.dumps(dict(passed=True,rows=len(classes),Native_executed=False,inputs_unchanged=True)))
