"""Reuse075 preopen readers/snapshot for one exact graphical recovery role."""
from pathlib import Path
import json,sys,time
ROOT=Path(__file__).resolve().parents[1]
runtime=ROOT/'.runs/runtime-directory-034/runtime'
sys.path.insert(0,str(runtime));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,review_export as ex,placement_clearance as io,gui
start=time.monotonic();role,workspace=sys.argv[1:]
assert role in ('no-repair','repair') and Path(workspace).name==workspace and workspace.startswith('autorouter-gui-')
base=runtime/'.runs/gui-session075';w=base/'jobs'/workspace
prepared=f.read_json(base/'prepared-state.json');protocol=Path(prepared['recovery_protocol'])
assert p.sha(protocol)==prepared['recovery_protocol_sha256']
plan=f.read_json(protocol);declared=plan['recovery'][role]
assert plan['source_head']==prepared['source_head']=='d64e5f1c9e35552eb2eeca93c71c5683fd09c37c'
assert p.sha(runtime/'runtime-distribution.json')==prepared['runtime_manifest_sha256']=='65aa2eb27ac5c61ce96a771bb6d8a65f923220e464886fb43d789377e4c61d5b'
tools=p.tool_manifest();assert tools==prepared['tools']
source=Path(declared['source']);external=Path(declared['original_source']);hashes=declared['source_hashes']
assert p.tree_hash(source.parent)==p.tree_hash(external.parent)==hashes
settings=f.read_json(w/'settings.json');assert settings==declared['settings'];gui.check_thermal_settings(settings)
parent=f.read_json(w/'route/result.json');exported=f.read_json(w/'export/export.json')
assert parent['source']==str(source) and parent['source_hashes']==hashes and parent['tools']==tools
assert parent['strategy']=='native_validated_thermal_bridge' and parent['thermal_parent_policy']=='native-thermal-parent-selection-v1'
assert parent['scope']=='whole_board_unlocked_routing' and parent['engine_profile']=='standard' and parent['adapter']=='both'
assert parent['budget_seconds']==parent['cpu_budget_seconds']==settings['seconds']==declared['whole_method_seconds']
assert parent['accepted'] is True and parent['invariants_unchanged'] is True
assert parent['schematic_parity']==exported['schematic_parity']=='checked by final native DRC'
assert exported['source_hashes']==hashes and exported['export_accepted'] is True
assert exported['budget_seconds']==exported['cpu_budget_seconds']==declared['additional_export_seconds']
incumbent=Path(parent['incumbent']['receipt']);assert incumbent==w/'route/incumbent/result.json'
assert p.sha(incumbent)==parent['incumbent']['receipt_sha256']
inc=f.read_json(incumbent);assert inc['tools']==tools and inc['source']==str(source) and inc['source_hashes']==hashes
if role=='no-repair':
    assert parent['repair'] is None and parent['recovery_needed'] is False
    assert inc['accepted'] is True and inc['status']=='routing_accepted'
else:
    assert parent['recovery_needed'] is True and parent['repair'] is not None
with p.validation_readback_session():
    route_readback=p.check_result(w/'route/result.json');export_readback=ex.check_export(w/'export/export.json')
assert route_readback['current'] is True and export_readback['current'] is True
control=base/'recovery-controls-001'/role;snapshot=control/'preopen-export';receipt=control/'preopen-001.json'
assert not snapshot.exists() and not receipt.exists();snapshot.mkdir()
for name,raw in io.inventory(w/'export',contents=True).items():
    path=snapshot/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
assert p.tree_hash(snapshot)==p.tree_hash(w/'export')
assert p.tree_hash(source.parent)==p.tree_hash(external.parent)==hashes and p.tool_manifest()==tools
p.save_json(receipt,dict(schema=1,role=role,workspace=str(w),route=route_readback,export=export_readback,
    source=str(source),source_hashes=hashes,source_unchanged=True,settings=settings,settings_sha256=p.sha(w/'settings.json'),
    snapshot=str(snapshot),snapshot_hashes=p.tree_hash(snapshot),incumbent_receipt_sha256=p.sha(incumbent),
    strategy=parent['strategy'],recovery_needed=parent['recovery_needed'],repair=parent['repair'],
    protected_original_locked_items=len(inc['protected_route_import']['matches']),human_review=False,
    scope='Current production readers and exact pre-open export snapshot. Own Native/original proofs retained. '
        'No actual editor opening, new Native execution, electrical or broader quality claim.',wall_seconds=time.monotonic()-start))
print(json.dumps(dict(role=role,route_current=True,export_current=True,snapshot_files=len(p.tree_hash(snapshot)),receipt=str(receipt))))
