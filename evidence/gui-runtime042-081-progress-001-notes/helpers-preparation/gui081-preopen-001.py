"""Existing shared preopen algorithm with an explicit081 role and workspace basename.

Usage: gui081-preopen-001.py positive|alias_positive|source|settings|export WORKSPACE
Hierarchy/high requires a separately prepared helper; no Native is run here.
Uses existing production readers and bounded inventory; never runs Native.
"""
from pathlib import Path
import json, sys, time

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

runtime = ROOT / '.runs/runtime-directory-042/runtime'
sys.path.insert(0, str(runtime)); sys.dont_write_bytecode = True
from autorouter import config as c, pipeline as p, review_export as ex, placement_clearance as io

start = time.monotonic()
role, workspace = sys.argv[1:]
assert role in ('positive', 'alias_positive', 'source', 'settings', 'export')
assert workspace == Path(workspace).name and workspace.startswith('autorouter-gui-')
assert c.ROOT == runtime and c.NATIVE_VERSION == '10.0.7'
base = runtime / '.runs/gui-session081'
w = base / 'jobs' / workspace
prepared = _bind_prepared(base)
assert p.sha(runtime / 'runtime-distribution.json') == prepared['runtime_manifest_sha256']
if role in ('source', 'settings', 'export'):
    control = base / 'freshness-controls-001' / role
    protocol = json.loads((control.parent / 'protocol-frozen-001.json').read_bytes())
    source = control / 'project'
    snapshot, receipt = control / 'preopen-export', control / 'preopen-001.json'
    assert protocol['source_hashes'] == prepared['source_hashes']
    assert protocol['prepared_state_sha256'] == _EXPECTED_PREPARED_SHA
    assert protocol['helper_sha256'][str(Path(__file__).relative_to(ROOT))] == p.sha(Path(__file__))
elif role == 'alias_positive':
    source = Path(prepared['alias_required']['source']).parent
    snapshot, receipt = base / 'preopen-alias-snapshot-001', base / 'preopen-alias-001.json'
else:
    source = base / 'project'
    snapshot = base / ('preopen-high-snapshot-001' if role == 'high_budget' else 'preopen-snapshot-001')
    receipt = base / ('preopen-high-001.json' if role == 'high_budget' else 'preopen-001.json')
expected_hashes = prepared['alias_required']['source_hashes'] if role == 'alias_positive' else prepared['source_hashes']
expected_settings = prepared['alias_required']['settings'] if role == 'alias_positive' else prepared['settings']
assert p.tree_hash(source) == expected_hashes and not receipt.exists() and not snapshot.exists()
assert json.loads((w / 'settings.json').read_bytes()) == expected_settings
with p.validation_readback_session():
    route = p.check_result(w / 'route/result.json')
    exported = ex.check_export(w / 'export/export.json')
assert route['current'] is True and exported['current'] is True
assert Path(json.loads((w / 'route/result.json').read_bytes())['source']).parent == source
snapshot.mkdir()
for name, raw in io.inventory(w / 'export', contents=True).items():
    target = snapshot / name; target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(raw)
assert p.tree_hash(snapshot) == p.tree_hash(w / 'export')
p.save_json(receipt, dict(schema=1, role=role, workspace=str(w), route=route, export=exported,
    snapshot=str(snapshot), snapshot_hashes=p.tree_hash(snapshot), source_hashes=expected_hashes,
    settings_sha256=p.sha(w / 'settings.json'), export_receipt_sha256=p.sha(w / 'export/export.json'),
    source_unchanged=True, human_review=False, wall_seconds=time.monotonic()-start))
print(json.dumps(dict(role=role, workspace=workspace, route_current=True, export_current=True,
    snapshot_files=len(p.tree_hash(snapshot)), receipt=str(receipt))))
