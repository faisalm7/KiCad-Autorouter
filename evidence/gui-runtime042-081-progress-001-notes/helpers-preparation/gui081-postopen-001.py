"""074 postopen snapshot algorithm; owner supplies role/workspace after observing UI.

This helper records bytes only. It never invents screen observations or new Native validity.
"""
from pathlib import Path
import datetime, json, sys

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
from autorouter import pipeline as p, placement_clearance as io

role, workspace = sys.argv[1:]
assert role in ('positive', 'alias_positive')
assert workspace == Path(workspace).name and workspace.startswith('autorouter-gui-')
base = runtime / '.runs/gui-session081'; w = base / 'jobs' / workspace
prepared = _bind_prepared(base)
suffix = '-alias' if role == 'alias_positive' else ''
pre = json.loads((base / ('preopen' + suffix + '-001.json')).read_bytes())
assert pre['role'] == role and Path(pre['workspace']) == w
before = pre['snapshot_hashes']; after = p.tree_hash(w / 'export')
snapshot = base / ('postopen' + suffix + '-snapshot-001'); snapshot.mkdir()
receipt = base / ('postopen' + suffix + '-001.json'); assert not receipt.exists()
for name, raw in io.inventory(w / 'export', contents=True).items():
    target = snapshot / name; target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(raw)
assert p.tree_hash(snapshot) == after
changed = {key: dict(before=before.get(key), after=after.get(key))
           for key in sorted(set(before) | set(after)) if before.get(key) != after.get(key)}
source = Path(prepared['alias_required']['source']).parent if role == 'alias_positive' else base / 'project'
expected_hashes = prepared['alias_required']['source_hashes'] if role == 'alias_positive' else prepared['source_hashes']
assert p.tree_hash(source) == expected_hashes == pre['source_hashes']
pcb = 'validation/candidate/owned1007-transport.kicad_pcb'
unchanged = before[pcb] == after.get(pcb)
p.save_json(receipt, dict(schema=1, recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    role=role, workspace=str(w), snapshot=str(snapshot), snapshot_hashes=after, changed=changed,
    source_unchanged=True, candidate_PCB_unchanged=unchanged,
    limits='Before-open proof is retained separately. Byte inspection does not establish new Native validity '
        'after editor metadata changes or qualify rendered GUI behavior. Actual UI observations must be '
        'recorded separately by the lead. No human or physical review.'))
print(json.dumps(dict(role=role, changed=list(changed), PCB_unchanged=unchanged, receipt=str(receipt))))
