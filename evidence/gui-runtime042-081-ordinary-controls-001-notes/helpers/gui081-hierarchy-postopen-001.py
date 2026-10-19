"""081 hierarchy/high-budget postopen bytes, ported from080.

Usage: exact042 Python -B THIS autorouter-gui-WORKSPACE_HEX
Uses saved preopen candidate filename/hash; no production-reader retry, Native,
new validity, rendered-screen or actual-opening qualification is inferred.
"""
from pathlib import Path
import hashlib, json, os, sys, time

ROOT = Path(__file__).resolve().parents[1]
# Exact immutable preparation/prerequisite binding; no validation is inferred.
import hashlib as _hashlib
_EXPECTED_PREPARED_SHA = '7ea7e874fe2781e1c915f024a6a72edc05f7d631887d0cd9e744ea32a23242a3'
_EXPECTED_HEAD = '82aaa3b750007ef2ffaafd367ffcb718aa93865e'
_EXPECTED_MANIFEST = '1dc25cf5133b7a0e0562704008b62bea328e46b61ec159a2bd326c3bf279aa2e'
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

RUNTIME = ROOT / '.runs/runtime-directory-042/runtime'
BASE = RUNTIME / '.runs/gui-session081'
CONTROL = BASE / 'ordinary-controls-002'
PROTOCOL = BASE / 'recovery-controls-001/protocol-required-001.json'
PROTOCOL_SHA = 'f4119835b72ef3b74b7cffcca50f0854ec499a95698d55e26be5bfeb67012851'
MANIFEST_SHA = _EXPECTED_MANIFEST
SETTINGS_SHA = '54da1de9cf1c6a52b5c30865bf92a63518fb5454569e42a0a13bd5a0563633cd'
ROLE = 'hierarchy_high_budget'
sys.path.insert(0, str(RUNTIME)); sys.dont_write_bytecode = True
from autorouter import config as c, pipeline as p, floor_route as f
from autorouter import review_export as ex, placement_clearance as io, handoff as h, sexpr as sx

start = time.monotonic()
workspace, = sys.argv[1:]
assert workspace == Path(workspace).name and workspace.startswith('autorouter-gui-')
assert c.ROOT == RUNTIME and c.NATIVE_VERSION == '10.0.7'
assert Path(sys.prefix).resolve() == RUNTIME / '.venv'
prepared = _bind_prepared(BASE)
assert p.sha(PROTOCOL) == PROTOCOL_SHA
protocol = f.read_json(PROTOCOL)
assert protocol['source_head'] == _EXPECTED_HEAD and protocol['runtime_manifest_sha256'] == MANIFEST_SHA
repair = protocol['recovery']['repair']
source = Path(prepared['hierarchy_source']); settings_path = Path(repair['settings_path'])
assert source == BASE / 'hierarchy-project/owned_hierarchy_native.kicad_pcb'
assert settings_path == BASE / 'recovery-controls-001/repair/route-settings.json'
assert repair['settings_sha256'] == SETTINGS_SHA
assert repair['whole_method_seconds'] == 420 and repair['additional_export_seconds'] == 120
assert repair['settings'] == dict(schema=1, scope='whole_board_unlocked_routing', seconds=420,
    adapter='both', profile='standard', guidance='native', layers='source_all', scoring_preference=None)
# Reuse the frozen structured settings only. The required GUI method is ordinary
# Route on the prepared hierarchy source, never Recover on the repair source.
plan = dict(source_hashes=prepared['hierarchy_source_hashes'], settings=repair['settings'],
            expected_final_Native_counts=[0, 0, 0, 0])
w = BASE / 'jobs' / workspace; assert h.real_path(w) == w
paths = dict(preopen_receipt=CONTROL/'preopen-001.json', preopen_snapshot=CONTROL/'preopen-export-001',
    postopen_receipt=CONTROL/'postopen-001.json', postopen_snapshot=CONTROL/'postopen-export-001')

def stable():
    assert p.sha(PROTOCOL) == PROTOCOL_SHA and p.sha(RUNTIME/'runtime-distribution.json') == MANIFEST_SHA
    assert p.sha(settings_path) == SETTINGS_SHA and f.read_json(settings_path) == plan['settings']
    assert io.inventory(source.parent) == plan['source_hashes']
    assert p.sha(BASE/'prepared-state.json') == _EXPECTED_PREPARED_SHA

def hashes(contents):
    return {name: hashlib.sha256(raw).hexdigest() for name, raw in contents.items()}

def snapshot(contents, destination):
    assert not os.path.lexists(destination)
    destination.mkdir()
    for name, raw in contents.items():
        target = destination / name; target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as stream: stream.write(raw)
    assert io.inventory(destination) == hashes(contents)

PREOPEN_HELPER_SHA = '7157eecf85d329b5cce392cffafa7bc895cf8c3ee28276bdd936c3f3535531c3'
mode = 'postopen'
stable()
receipt = paths[mode+'_receipt']; assert not os.path.lexists(receipt)
assert CONTROL.is_dir() and h.real_path(CONTROL) == CONTROL
pre_path = paths['preopen_receipt']; pre = f.read_json(pre_path)
assert p.sha(ROOT/'.runs/gui081-hierarchy-preopen-001.py') == PREOPEN_HELPER_SHA
assert pre['helper_sha256'] == PREOPEN_HELPER_SHA
assert pre['prepared_state_sha256'] == _EXPECTED_PREPARED_SHA
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
    settings_input_sha256=SETTINGS_SHA, prepared_state_sha256=_EXPECTED_PREPARED_SHA,
    helper_sha256=p.sha(Path(__file__)), required_GUI_method='route',
    source_unchanged=True, Native_executed=False,
    screen_observed=False, human_review=False, wall_seconds=time.monotonic()-start)
with receipt.open('x') as stream: stream.write(json.dumps(record, indent=2, sort_keys=True)+'\n')
print(json.dumps(dict(mode=mode, role=ROLE, workspace=workspace, receipt=str(receipt),
    snapshot_files=len(record['snapshot_hashes']), Native_executed=False, screen_observed=False)))
