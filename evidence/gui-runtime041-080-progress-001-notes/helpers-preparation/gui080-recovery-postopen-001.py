"""074 postopen snapshot algorithm; owner supplies role/workspace after observing UI.

This helper records bytes only. It never invents screen observations or new Native validity.
"""
from pathlib import Path
import datetime, json, sys

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

runtime = ROOT / '.runs/runtime-directory-041/runtime'
sys.path.insert(0, str(runtime)); sys.dont_write_bytecode = True
from autorouter import pipeline as p, placement_clearance as io

role, workspace = sys.argv[1:]
assert role in ('no-repair', 'repair')
assert workspace == Path(workspace).name and workspace.startswith('autorouter-gui-')
base = runtime / '.runs/gui-session080'; w = base / 'jobs' / workspace
prepared=_bind_prepared(base)
control = base / 'recovery-controls-001' / role
pre = json.loads((control / 'preopen-001.json').read_bytes())
assert pre['role'] == role and Path(pre['workspace']) == w
before = pre['snapshot_hashes']; after = p.tree_hash(w / 'export')
snapshot = control / 'postopen-snapshot-001'; snapshot.mkdir()
receipt = control / 'postopen-001.json'; assert not receipt.exists()
for name, raw in io.inventory(w / 'export', contents=True).items():
    target = snapshot / name; target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(raw)
assert p.tree_hash(snapshot) == after
changed = {key: dict(before=before.get(key), after=after.get(key))
           for key in sorted(set(before) | set(after)) if before.get(key) != after.get(key)}
assert p.tree_hash(Path(pre['source']).parent) == pre['source_hashes']
pcb = 'validation/candidate/' + Path(pre['source']).name
unchanged = before[pcb] == after.get(pcb)
p.save_json(receipt, dict(schema=1, recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    role=role, workspace=str(w), snapshot=str(snapshot), snapshot_hashes=after, changed=changed,
    source_unchanged=True, candidate_PCB_unchanged=unchanged,
    limits='Before-open proof is retained separately. Byte inspection does not establish new Native validity '
        'after editor metadata changes or qualify rendered GUI behavior. Actual UI observations must be '
        'recorded separately by the lead. No human or physical review.'))
print(json.dumps(dict(role=role, changed=list(changed), PCB_unchanged=unchanged, receipt=str(receipt))))
