"""Identity port of074: copy three owned sources and freeze seven GUI roles only."""
from pathlib import Path
import datetime, hashlib, json, shutil

ROOT = Path(__file__).resolve().parents[1]
base = ROOT / '.runs/runtime-directory-034/runtime/.runs/gui-session075'
prepared_path = base / 'prepared-state.json'
prepared_raw = prepared_path.read_bytes()
prep = json.loads(prepared_raw)
assert prep['source_head'] == 'd64e5f1c9e35552eb2eeca93c71c5683fd09c37c'
assert prep['runtime_manifest_sha256'] == '65aa2eb27ac5c61ce96a771bb6d8a65f923220e464886fb43d789377e4c61d5b'
assert Path(prep['source']) == base / 'project/owned1007-transport.kicad_pcb'
assert hashlib.sha256((base.parents[1] / 'runtime-distribution.json').read_bytes()).hexdigest() == prep['runtime_manifest_sha256']
pins = lambda directory: {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in directory.iterdir()}
assert pins(base / 'project') == prep['source_hashes']
controls = base / 'freshness-controls-001'
controls.mkdir()
for label in ('source', 'settings', 'export'):
    destination = controls / label
    destination.mkdir()
    shutil.copytree(base / 'project', destination / 'project')
    assert pins(destination / 'project') == prep['source_hashes']
helpers = {}
for name in ('gui075-preopen-001.py', 'gui075-mutate-control-001.py', 'gui075-postopen-001.py'):
    path = ROOT / '.runs' / name
    helpers[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
protocol = dict(schema=1, recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    runtime_manifest_sha256=prep['runtime_manifest_sha256'], source_head=prep['source_head'],
    prepared_state_sha256=hashlib.sha256(prepared_raw).hexdigest(), source_hashes=prep['source_hashes'],
    settings=prep['settings'], declared_jobs=['positive90', 'high420-export120', 'source-freshness',
        'settings-freshness', 'typed-export-freshness', 'cancel', 'reject'],
    scope='Actual new034 normal1007 GUI075 controls on an exposed owned partial fixture, not breadth, '
        'human review, all-phase cancellation or forced queued-race timing. Fresh outputs each. '
        'All positive Route/export proof must remain retained. Mutate copied sources only after '
        'current preopen proof; original projects and033/074 remain unchanged. Preparation does not qualify any GUI role.',
    limits=dict(heavy_workers=1, native_execution_sequential=True, routing_seconds=90,
        high_routing_seconds=420, export_seconds=90, high_export_seconds=120),
    mutations=dict(source='append newline to copied source PRO only after frozen positive proof',
        settings='append newline to own captured settings only after proof',
        export='change typed export_accepted true to integer1 only after proof'),
    helper_sha256=helpers, originals_preserved=True, GUI_qualified=False, Native_run_by_preparation=False)
assert prepared_path.read_bytes() == prepared_raw and pins(base / 'project') == prep['source_hashes']
with (controls / 'protocol-frozen-001.json').open('x') as stream:
    json.dump(protocol, stream, indent=2)
    stream.write('\n')
print(json.dumps(dict(prepared=True, freshness_copies=3, declared_jobs=protocol['declared_jobs'],
    protocol=str(controls / 'protocol-frozen-001.json'), GUI_qualified=False, Native_run=False)))
