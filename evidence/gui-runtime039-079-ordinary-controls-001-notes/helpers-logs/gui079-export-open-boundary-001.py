"""One finite fault injection in the owned GUI; no router/validator replacement.

After the actual Open button, pause only its live GUI parent while the existing
CLI reader finishes. The existing declared mutation helper changes the copied
export, then finally resumes the GUI. Abort without mutation if timing is missed.
This delays worker adoption too; it does not prove a CallAfter was already queued.
"""
from pathlib import Path
import datetime, hashlib, json, os, signal, subprocess, sys, time

ROOT = Path(__file__).resolve().parents[1]
runtime = ROOT / '.runs/runtime-directory-039/runtime'
base = runtime / '.runs/gui-session079'
workspace = 'autorouter-gui-f73a05fb499949cda0e013eb45ad526e'
job = base / 'jobs' / workspace
receipt = base / 'freshness-controls-001/export/open-boundary-001.json'
assert not receipt.exists()
helper = ROOT / '.runs/gui079-mutate-control-001.py'
assert json.loads((base/'freshness-controls-001/export/preopen-001.json').read_text())['export']['current'] is True
expected = str(ROOT / '.tools/kicad-10.0.7-local-001/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/Resources/Python.app/Contents/MacOS/Python') + ' -B -m autorouter.gui'
def query(pid, column):
    result = subprocess.run(['/bin/ps', '-p', str(pid), '-o', column+'='], capture_output=True, text=True)
    return result.stdout.strip() if result.returncode == 0 else None
def rows():
    raw = subprocess.check_output(['/bin/ps', '-axo', 'pid=,ppid=,stat=,command='], text=True)
    return [line.strip().split(None, 3) for line in raw.splitlines() if len(line.strip().split(None, 3)) == 4]
owned = [row for row in rows() if row[3] == expected]
assert len(owned) == 1, 'One current owned GUI is required'
pid = int(owned[0][0]); birth = query(pid, 'lstart')
assert birth and query(pid, 'command') == expected
cwd = subprocess.check_output(['/usr/sbin/lsof','-a','-p',str(pid),'-d','cwd','-Fn'], text=True)
assert '\nn'+str(runtime)+'\n' in '\n'+cwd
children = [row for row in rows() if int(row[1]) == pid and
            ' -B -m autorouter review-export-check ' in row[3] and str(job/'export/export.json') in row[3] and 'Z' not in row[2]]
record = dict(schema=1, recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    workspace=str(job), GUI_pid=pid, GUI_birth=birth, GUI_command=expected, GUI_cwd=str(runtime),
    mutation_helper_sha256=hashlib.sha256(helper.read_bytes()).hexdigest(),
    child_before=children, paused=False, resumed=False, mutated=False,
    limit_seconds=15, Native_executed_by_controller=False,
    scope='Existing CLI readback completed while owned GUI paused; worker adoption was also delayed. '
          'Not evidence that a CallAfter was already queued, all-phase safety or hostile-writer isolation.')
started = time.monotonic(); stopped = False
try:
    assert len(children) == 1, 'Reader interval missed; no mutation or pause'
    child = int(children[0][0]); child_birth = query(child, 'lstart')
    assert query(pid,'lstart') == birth and query(pid,'command') == expected
    os.kill(pid, signal.SIGSTOP); stopped = True; record['paused'] = True
    deadline = time.monotonic()+15
    while True:
        state = query(child,'stat')
        assert state is not None, 'Reader was already reaped; interval missed, no mutation'
        if 'Z' in state:
            record['child_completion_state'] = state
            record['child_completion_birth'] = query(child,'lstart')
            assert record['child_completion_birth'] == child_birth
            break
        assert time.monotonic() < deadline, 'Reader did not finish in finite pause; no mutation'
        time.sleep(0.1)
    assert query(pid,'lstart') == birth and query(pid,'command') == expected
    result = subprocess.run([str(ROOT/'.venv/bin/python'),'-B',str(helper),'export',workspace],
                            capture_output=True,text=True,timeout=5)
    record['mutation_helper_exit'] = result.returncode
    record['mutation_helper_output'] = result.stdout+result.stderr
    assert result.returncode == 0
    record['mutated'] = True
except BaseException as error:
    record['error'] = type(error).__name__+': '+str(error)
finally:
    if stopped:
        if query(pid,'lstart') == birth and query(pid,'command') == expected:
            os.kill(pid, signal.SIGCONT); record['resumed'] = True
        else:
            record['resume_refused_identity_changed'] = True
    record['wall_seconds'] = time.monotonic()-started
    with receipt.open('x') as stream:
        json.dump(record,stream,indent=2,sort_keys=True);stream.write('\n')
print(json.dumps(record))
sys.exit(0 if record['mutated'] and record['resumed'] else 2)
