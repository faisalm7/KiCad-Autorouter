"""074 shared preopen algorithm with an explicit075 role and workspace basename.

Usage: gui075-preopen-001.py positive|high_budget|source|settings|export WORKSPACE
Uses existing production readers and bounded inventory; never runs Native.
"""
from pathlib import Path
import json, sys, time

ROOT = Path(__file__).resolve().parents[1]
runtime = ROOT / '.runs/runtime-directory-034/runtime'
sys.path.insert(0, str(runtime)); sys.dont_write_bytecode = True
from autorouter import config as c, pipeline as p, review_export as ex, placement_clearance as io

start = time.monotonic()
role, workspace = sys.argv[1:]
assert role in ('positive', 'high_budget', 'source', 'settings', 'export')
assert workspace == Path(workspace).name and workspace.startswith('autorouter-gui-')
assert c.ROOT == runtime and c.NATIVE_VERSION == '10.0.7'
base = runtime / '.runs/gui-session075'
w = base / 'jobs' / workspace
prepared = json.loads((base / 'prepared-state.json').read_bytes())
assert p.sha(runtime / 'runtime-distribution.json') == prepared['runtime_manifest_sha256']
if role in ('source', 'settings', 'export'):
    control = base / 'freshness-controls-001' / role
    protocol = json.loads((control.parent / 'protocol-frozen-001.json').read_bytes())
    source = control / 'project'
    snapshot, receipt = control / 'preopen-export', control / 'preopen-001.json'
    assert protocol['source_hashes'] == prepared['source_hashes']
else:
    source = base / 'project'
    snapshot = base / ('preopen-high-snapshot-001' if role == 'high_budget' else 'preopen-snapshot-001')
    receipt = base / ('preopen-high-001.json' if role == 'high_budget' else 'preopen-001.json')
assert p.tree_hash(source) == prepared['source_hashes'] and not receipt.exists()
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
    snapshot=str(snapshot), snapshot_hashes=p.tree_hash(snapshot), source_hashes=prepared['source_hashes'],
    settings_sha256=p.sha(w / 'settings.json'), export_receipt_sha256=p.sha(w / 'export/export.json'),
    source_unchanged=True, human_review=False, wall_seconds=time.monotonic()-start))
print(json.dumps(dict(role=role, workspace=workspace, route_current=True, export_current=True,
    snapshot_files=len(p.tree_hash(snapshot)), receipt=str(receipt))))
