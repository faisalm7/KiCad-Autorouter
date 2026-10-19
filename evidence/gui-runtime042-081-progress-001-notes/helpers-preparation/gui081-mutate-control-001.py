"""Existing080 algorithm on one explicit081 owned copy after saved preopen proof.

Export changes typed true to integer1 only. A separately observed reader boundary
is caller-controlled; this helper never proves a queued CallAfter interval.
"""
from pathlib import Path
import datetime, hashlib, json, sys

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

role, workspace = sys.argv[1:]
assert role in ('source', 'settings', 'export')
assert workspace == Path(workspace).name and workspace.startswith('autorouter-gui-')
base = ROOT / '.runs/runtime-directory-042/runtime/.runs/gui-session081'
control = base / 'freshness-controls-001' / role
w = base / 'jobs' / workspace
prepared = _bind_prepared(base)
protocol = json.loads((control.parent / 'protocol-frozen-001.json').read_bytes())
assert protocol['prepared_state_sha256'] == _EXPECTED_PREPARED_SHA
assert protocol['helper_sha256'][str(Path(__file__).relative_to(ROOT))] == hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
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
receipt = control / 'mutation-001.json'; assert not receipt.exists() and not receipt.is_symlink()
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
