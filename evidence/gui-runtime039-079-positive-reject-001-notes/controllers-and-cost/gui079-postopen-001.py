"""074 postopen snapshot algorithm; owner supplies role/workspace after observing UI.

This helper records bytes only. It never invents screen observations or new Native validity.
"""
from pathlib import Path
import datetime, json, sys

ROOT = Path(__file__).resolve().parents[1]
runtime = ROOT / '.runs/runtime-directory-039/runtime'
sys.path.insert(0, str(runtime)); sys.dont_write_bytecode = True
from autorouter import pipeline as p, placement_clearance as io

role, workspace = sys.argv[1:]
assert role in ('positive', 'high_budget')
assert workspace == Path(workspace).name and workspace.startswith('autorouter-gui-')
base = runtime / '.runs/gui-session079'; w = base / 'jobs' / workspace
suffix = '-high' if role == 'high_budget' else ''
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
assert p.tree_hash(base / 'project') == json.loads((base / 'prepared-state.json').read_bytes())['source_hashes']
pcb = 'validation/candidate/owned1007-transport.kicad_pcb'
unchanged = before[pcb] == after.get(pcb)
p.save_json(receipt, dict(schema=1, recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    role=role, workspace=str(w), snapshot=str(snapshot), snapshot_hashes=after, changed=changed,
    source_unchanged=True, candidate_PCB_unchanged=unchanged,
    limits='Before-open proof is retained separately. Byte inspection does not establish new Native validity '
        'after editor metadata changes or qualify rendered GUI behavior. Actual UI observations must be '
        'recorded separately by the lead. No human or physical review.'))
print(json.dumps(dict(role=role, changed=list(changed), PCB_unchanged=unchanged, receipt=str(receipt))))
