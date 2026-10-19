"""Hierarchy/high-budget079 byte/proof adapter; no Native or screen observation.

Usage: exact039 Python -B THIS preopen|postopen autorouter-gui-WORKSPACE_HEX
Preopen uses existing production readers; postopen records bytes without retrying
those readers or claiming fresh validity after editor metadata changes.
"""
from pathlib import Path
import hashlib, json, os, sys, time

ROOT = Path(__file__).resolve().parents[1]
# Exact immutable preparation/prerequisite binding; no validation is inferred.
import hashlib as _hashlib
_EXPECTED_PREPARED_SHA = 'a0ee6588cdaf5594c1baaf4564a79b86ff9117484f642eadfe4cc253ca6cd3ff'
_EXPECTED_HEAD = 'f7524d7bbfb4824640c8ca51dc978769b2fab98b'
_EXPECTED_MANIFEST = '3d1f5200848cec85a1d7fd0666dfcf3634f4aaa02caeeec66575f99df9a46399'
def _bind_prepared(base):
    raw = (base / 'prepared-state.json').read_bytes()
    assert _hashlib.sha256(raw).hexdigest() == _EXPECTED_PREPARED_SHA
    frozen = json.loads(raw)
    assert frozen['source_head'] == _EXPECTED_HEAD
    assert frozen['runtime_manifest_sha256'] == _EXPECTED_MANIFEST
    runtime = base.parents[1]
    assert _hashlib.sha256((runtime / 'runtime-distribution.json').read_bytes()).hexdigest() == _EXPECTED_MANIFEST
    for name, digest in frozen['prerequisites_sha256'].items():
        path = Path(name)
        assert path.is_absolute() and not path.is_symlink() and path.is_file()
        assert _hashlib.sha256(path.read_bytes()).hexdigest() == digest
    protocol = Path(frozen['recovery_protocol'])
    assert protocol == base / 'recovery-controls-001/protocol-required-001.json'
    assert _hashlib.sha256(protocol.read_bytes()).hexdigest() == frozen['recovery_protocol_sha256']
    return frozen

RUNTIME = ROOT / '.runs/runtime-directory-041/runtime'
BASE = RUNTIME / '.runs/gui-session080'
CONTROL = BASE / 'ordinary-controls-002'
PROTOCOL = CONTROL / 'protocol-frozen-001.json'
PROTOCOL_SHA = 'd45085ece2515ce4e1d8ad0cdd69122fad4fc77fd749bbd570ad05386ae4cd97'
MANIFEST_SHA = '3d1f5200848cec85a1d7fd0666dfcf3634f4aaa02caeeec66575f99df9a46399'
SETTINGS_SHA = '54da1de9cf1c6a52b5c30865bf92a63518fb5454569e42a0a13bd5a0563633cd'
ROLE = 'hierarchy_high_budget'
sys.path.insert(0, str(RUNTIME)); sys.dont_write_bytecode = True
from autorouter import config as c, pipeline as p, floor_route as f
from autorouter import review_export as ex, placement_clearance as io, handoff as h, sexpr as sx

start = time.monotonic()
mode, workspace = sys.argv[1:]
assert mode in ('preopen', 'postopen')
assert workspace == Path(workspace).name and workspace.startswith('autorouter-gui-')
assert c.ROOT == RUNTIME and c.NATIVE_VERSION == '10.0.7'
assert Path(sys.prefix).resolve() == RUNTIME / '.venv'
assert p.sha(PROTOCOL) == PROTOCOL_SHA
plan = f.read_json(PROTOCOL)
source = Path(plan['source']); settings_path = Path(plan['settings_path'])
assert source == BASE / 'hierarchy-project/owned_hierarchy_native.kicad_pcb'
assert settings_path == CONTROL / 'route-settings420.json'
assert plan['runtime'] == str(RUNTIME) and plan['runtime_manifest_sha256'] == MANIFEST_SHA
assert plan['settings_sha256'] == SETTINGS_SHA
assert plan['settings'] == dict(schema=1, scope='whole_board_unlocked_routing', seconds=420,
    adapter='both', profile='standard', guidance='native', layers='source_all', scoring_preference=None)
assert plan['expected_protected_count'] == 0 and plan['no_positive_protection_claim'] is True
w = BASE / 'jobs' / workspace; assert h.real_path(w) == w
paths = {key: Path(value) for key, value in plan['helper_plan']['planned_material'].items()}
assert paths == dict(preopen_receipt=CONTROL/'preopen-001.json', preopen_snapshot=CONTROL/'preopen-export-001',
    postopen_receipt=CONTROL/'postopen-001.json', postopen_snapshot=CONTROL/'postopen-export-001')

def stable():
    assert p.sha(PROTOCOL) == PROTOCOL_SHA and p.sha(RUNTIME/'runtime-distribution.json') == MANIFEST_SHA
    assert p.sha(settings_path) == SETTINGS_SHA and f.read_json(settings_path) == plan['settings']
    assert io.inventory(source.parent) == plan['source_hashes']
    for key in ('original_protocol', 'prepared_state'):
        assert p.sha(Path(plan[key]['path'])) == plan[key]['sha256']

def hashes(contents):
    return {name: hashlib.sha256(raw).hexdigest() for name, raw in contents.items()}

def snapshot(contents, destination):
    assert not os.path.lexists(destination)
    destination.mkdir()
    for name, raw in contents.items():
        target = destination / name; target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as stream: stream.write(raw)
    assert io.inventory(destination) == hashes(contents)

_bind_prepared(BASE)
stable()
receipt = paths[mode+'_receipt']; assert not os.path.lexists(receipt)
if mode == 'preopen':
    route_path = w/'route/result.json'; export_path = w/'export/export.json'
    with p.validation_readback_session():
        checked_route = p.check_result(route_path); checked_export = ex.check_export(export_path)
    assert checked_route['current'] is True and checked_export['current'] is True
    route = f.read_json(route_path); exported = f.read_json(export_path)
    assert route['source'] == exported['inputs']['source'] == str(source)
    assert route['source_hashes'] == exported['source_hashes'] == plan['source_hashes']
    assert f.read_json(w/'settings.json') == plan['settings']
    assert route['budget_seconds'] == route['cpu_budget_seconds'] == 420
    assert exported['budget_seconds'] == exported['cpu_budget_seconds'] == 120
    assert route['schematic_parity'] == exported['schematic_parity'] == 'checked by final native DRC'
    assert all([item['native'][key] for key in ('opens','blocking','warnings','exclusions')]
        == plan['expected_final_Native_counts'] for item in (route, exported))
    assert len(p.protected_for_record(route, sx.read(source))) == 0
    candidate_relative = str(Path(exported['candidate']).relative_to(w/'export'))
    assert candidate_relative == 'validation/candidate/' + source.name
    contents = io.inventory(w/'export', contents=True); before = hashes(contents)
    assert before[candidate_relative] == exported['candidate_sha256'] == route['candidate_sha256']
    snapshot(contents, paths['preopen_snapshot'])
    assert io.inventory(w/'export') == before
    record = dict(route=checked_route, export=checked_export, snapshot=str(paths['preopen_snapshot']),
        snapshot_hashes=before, candidate_relative_path=candidate_relative,
        candidate_sha256=exported['candidate_sha256'], protected_count=0, no_positive_protection_claim=True,
        settings_sha256=p.sha(w/'settings.json'), route_receipt_sha256=p.sha(route_path),
        export_receipt_sha256=p.sha(export_path), production_readers_executed=True,
        scope='Production current-proof readback before opening only; no new Native or screen observation.')
else:
    pre_path = paths['preopen_receipt']; pre = f.read_json(pre_path)
    assert pre['role'] == ROLE and pre['workspace'] == str(w) and pre['protocol_sha256'] == PROTOCOL_SHA
    assert pre['source_hashes'] == plan['source_hashes'] and pre['settings_input_sha256'] == SETTINGS_SHA
    assert pre['snapshot'] == str(paths['preopen_snapshot'])
    before = pre['snapshot_hashes']; assert io.inventory(paths['preopen_snapshot']) == before
    candidate_relative = pre['candidate_relative_path']
    assert candidate_relative == 'validation/candidate/' + source.name
    assert before[candidate_relative] == pre['candidate_sha256']
    contents = io.inventory(w/'export', contents=True); after = hashes(contents)
    snapshot(contents, paths['postopen_snapshot'])
    assert io.inventory(w/'export') == after
    changed = {key: dict(before=before.get(key), after=after.get(key))
        for key in sorted(set(before)|set(after)) if before.get(key) != after.get(key)}
    record = dict(preopen_receipt_sha256=p.sha(pre_path), snapshot=str(paths['postopen_snapshot']),
        snapshot_hashes=after, changed=changed, candidate_relative_path=candidate_relative,
        candidate_PCB_unchanged=before[candidate_relative] == after.get(candidate_relative),
        production_readers_executed=False, current_posteditor_validity='not_assessed',
        scope='Bytes only; saved preopen proof keeps its original scope. No stale-reader retry, screen '
            'observation, renewed Native validity or actual-opening qualification is inferred.')
stable()
record.update(schema=1, mode=mode, role=ROLE, workspace=str(w), protocol_sha256=PROTOCOL_SHA,
    runtime_manifest_sha256=MANIFEST_SHA, source=str(source), source_hashes=plan['source_hashes'],
    settings_input_sha256=SETTINGS_SHA, source_unchanged=True, Native_executed=False,
    screen_observed=False, human_review=False, wall_seconds=time.monotonic()-start)
with receipt.open('x') as stream: stream.write(json.dumps(record, indent=2, sort_keys=True)+'\n')
print(json.dumps(dict(mode=mode, role=ROLE, workspace=workspace, receipt=str(receipt),
    snapshot_files=len(record['snapshot_hashes']), Native_executed=False, screen_observed=False)))
