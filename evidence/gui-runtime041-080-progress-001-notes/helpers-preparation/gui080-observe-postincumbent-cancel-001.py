"""Finite read-only observer for one actual GUI cancellation control.

No Native execution or signals: the lead uses the actual Cancel button after
this captures a saved accepted incumbent and a live owned final Native worker.
"""
from pathlib import Path
import datetime, hashlib, json, subprocess, sys, time

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

base = ROOT/'.runs/runtime-directory-041/runtime/.runs/gui-session080'
name = sys.argv[1]
assert Path(name).name == name and name.startswith('autorouter-gui-')
w = base/'jobs'/name
out = base/'recovery-controls-001/no-repair/postincumbent-cancel-observed-001.json'
assert not out.exists() and not out.is_symlink() and w.is_dir()
prepared=_bind_prepared(base)
plan=json.loads(Path(prepared['recovery_protocol']).read_bytes())['recovery']['no-repair']
source=Path(plan['source'])
assert {p.name:_hashlib.sha256(p.read_bytes()).hexdigest() for p in source.parent.iterdir()}==plan['source_hashes']
assert json.loads((w/'settings.json').read_bytes())==plan['settings']
expected_cli=' '.join([str(base.parents[1]/'.venv/bin/python'),'-B','-m','autorouter','recover',str(source),'--seconds','90','--output',str(w/'route')])
started = time.monotonic(); deadline = started+120
record = dict(schema=1, workspace=str(w), started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    maximum_wait_seconds=120, observed=False, signals_sent=False, Native_executed_by_observer=False,
    scope='One actual GUI recovery schedule; accepted incumbent plus live final Native worker. '
          'Observer is not independent Native validation, all-phase cancellation or Improve qualification.')
try:
    while time.monotonic() < deadline:
        incumbent = w/'route/incumbent/result.json'
        if incumbent.is_file():
            raw = incumbent.read_bytes(); saved = json.loads(raw)
            assert saved['source']==str(source) and saved['source_hashes']==plan['source_hashes']
            assert saved['tools']==prepared['tools']
            assert saved['accepted'] is True and saved['status'] == 'routing_accepted'
            assert saved['invariants_unchanged'] is True
            assert [saved['native'][k] for k in ('opens','blocking','warnings','exclusions')] == [0,0,0,0]
            text = subprocess.check_output(['/bin/ps','-axo','pid=,ppid=,stat=,command='], text=True)
            rows = [line.strip().split(None,3) for line in text.splitlines() if len(line.strip().split(None,3)) == 4]
            parents=[r for r in rows if r[3]==expected_cli and 'Z' not in r[2]]
            assert len(parents)<=1
            workers = [r for r in rows if parents and r[1]==parents[0][0] and str(w/'route') in r[3] and str(w/'route/incumbent') not in r[3]
                       and '.tools/kicad-10.0.7-local-001/KiCad.app/' in r[3]
                       and ('/kicad-cli ' in r[3] or '/bin/python3.9 ' in r[3]) and 'Z' not in r[2]]
            if workers:
                ancestry = []
                for worker in workers:
                    row = worker
                    for _ in range(8):
                        ancestry.append(row)
                        parent = next((r for r in rows if r[0] == row[1]), None)
                        if parent is None: break
                        row = parent
                        if row[3].endswith(' -B -m autorouter.gui'):
                            ancestry.append(row); break
                assert any(r[3].endswith(' -B -m autorouter.gui') for r in ancestry)
                candidate = Path(saved['candidate'])
                assert hashlib.sha256(candidate.read_bytes()).hexdigest() == saved['candidate_sha256']
                record.update(observed=True, observed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    incumbent_receipt=str(incumbent), incumbent_sha256=hashlib.sha256(raw).hexdigest(),
                    incumbent_candidate=str(candidate), incumbent_candidate_sha256=saved['candidate_sha256'],
                    incumbent_accepted=True, live_final_workers=workers, ancestry=ancestry)
                break
        if (w/'route/result.json').exists():
            raise ValueError('Recovery finished before required live interval; timing not passed')
        time.sleep(.25)
    assert record['observed'], 'No required live interval within120 seconds; timing not passed'
except BaseException as exc:
    record['error'] = type(exc).__name__+': '+str(exc)
_bind_prepared(base)
assert {p.name:_hashlib.sha256(p.read_bytes()).hexdigest() for p in source.parent.iterdir()}==plan['source_hashes']
record['observer_wall_seconds'] = time.monotonic()-started
with out.open('x') as stream:
    json.dump(record,stream,indent=2,sort_keys=True);stream.write('\n')
print(json.dumps(record),flush=True)
sys.exit(0 if record['observed'] else 2)
