"""074 mutation algorithm on one explicit075 owned control after saved proof."""
from pathlib import Path
import datetime, hashlib, json, sys

ROOT = Path(__file__).resolve().parents[1]
role, workspace = sys.argv[1:]
assert role in ('source', 'settings', 'export')
assert workspace == Path(workspace).name and workspace.startswith('autorouter-gui-')
base = ROOT / '.runs/runtime-directory-039/runtime/.runs/gui-session079'
control = base / 'freshness-controls-001' / role
w = base / 'jobs' / workspace
prepared = json.loads((base / 'prepared-state.json').read_bytes())
pins = lambda directory: {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in directory.iterdir()}
assert pins(base / 'project') == prepared['source_hashes']
preopen = control / 'preopen-001.json'
proof = json.loads(preopen.read_bytes())
assert proof['route']['current'] is True and proof['export']['current'] is True
assert proof['role'] == role and Path(proof['workspace']) == w
path = (control / 'project/owned1007-transport.kicad_pro' if role == 'source'
        else w / 'settings.json' if role == 'settings' else w / 'export/export.json')
raw = path.read_bytes(); before = hashlib.sha256(raw).hexdigest()
expected = (proof['source_hashes'][path.name] if role == 'source'
            else proof['settings_sha256'] if role == 'settings' else proof['export_receipt_sha256'])
assert before == expected
if role in ('source', 'settings'):
    altered = raw + b'\n'
    kind = 'append newline to owned source PRO' if role == 'source' else 'append newline to own captured settings'
else:
    data = json.loads(raw); assert data['export_accepted'] is True
    data['export_accepted'] = 1
    altered = (json.dumps(data, indent=2) + '\n').encode()
    kind = 'typed export_accepted true changed to integer1'
receipt = control / 'mutation-001.json'; assert not receipt.exists()
path.write_bytes(altered)
assert pins(base / 'project') == prepared['source_hashes']
with receipt.open('x') as stream:
    json.dump(dict(schema=1, recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        kind=role, workspace=str(w), path=str(path), before_sha256=before,
        after_sha256=hashlib.sha256(path.read_bytes()).hexdigest(), mutation=kind,
        original_source_untouched=True, positive_proof_before_mutation='preopen-001.json',
        preopen_receipt=str(preopen), preopen_sha256=hashlib.sha256(preopen.read_bytes()).hexdigest()), stream, indent=2)
    stream.write('\n')
print(json.dumps(dict(role=role, workspace=workspace, mutated_owned_copy=True)))
