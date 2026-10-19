"""One 15-second owned GUI080 export-opening opportunity; never run by preparation.

Pause only the verified GUI after its exact direct CLI reader is observed. Mutate
the owned export only after that same reader becomes a zombie, then resume the
GUI in finally. Worker adoption is delayed too: CallAfter already queued is NOT
established. This replaces no reader, validator, router or application setting.
"""
from pathlib import Path
import datetime, hashlib, json, os, signal, subprocess, sys, time

ROOT = Path(__file__).resolve().parents[1]
runtime = ROOT / '.runs/runtime-directory-041/runtime'
base = runtime / '.runs/gui-session080'
workspace = 'autorouter-gui-b1ac68eceb0e41cebae84faeba4a6c09'
job = base / 'jobs' / workspace
control = base / 'freshness-controls-001/export'
receipt = control / 'open-boundary-001.json'
helper = ROOT / '.runs/gui080-mutate-control-001.py'
preopen_helper = ROOT / '.runs/gui080-preopen-001.py'
expected_manifest = '3d1f5200848cec85a1d7fd0666dfcf3634f4aaa02caeeec66575f99df9a46399'
expected_prepared = 'a0ee6588cdaf5594c1baaf4564a79b86ff9117484f642eadfe4cc253ca6cd3ff'
expected_helper = 'cb22a20586bce4614a4cf7445f93db183e62a9f26be84a465982a34e6a258af4'
expected_preopen_helper = '32d2b538c55fff241fcdab92f0d2a72d896f244362bcdade1b781a593c87699d'
gui_python = str(ROOT / '.tools/kicad-10.0.7-local-001/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/Resources/Python.app/Contents/MacOS/Python')
expected_gui = gui_python + ' -B -m autorouter.gui'
reader_tail = ' -B -m autorouter review-export-check ' + str(job / 'export/export.json')
expected_readers = {str(runtime / '.venv/bin/python') + reader_tail,
                    gui_python + reader_tail}
assert not receipt.exists() and not receipt.is_symlink(), 'Boundary receipt already exists'
started = time.monotonic()
deadline = started + 15
record = dict(schema=1, recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    workspace=str(job), GUI_command=expected_gui, GUI_cwd=str(runtime),
    expected_reader_commands=sorted(expected_readers), limit_seconds=15,
    paused=False, resumed=False, mutated=False, mutation_attempted=False,
    Native_executed_by_controller=False, signals_target_GUI_only=True,
    CallAfter_already_queued_proved=False,
    scope='Existing CLI readback completes while the owned GUI is paused. Worker adoption '
          'is also delayed; this cannot establish that CallAfter was already queued, '
          'Native interruption, all-phase safety or hostile-writer isolation.')
stopped = False
pid = birth = None

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def remaining():
    left = deadline - time.monotonic()
    assert left > 0, '15-second opportunity ended; no further mutation or pause'
    return left

def command(argv, *, cleanup=False):
    timeout = 2 if cleanup else min(1.5, remaining())
    return subprocess.run(argv, capture_output=True, text=True, timeout=timeout)

def query(target, column, *, cleanup=False):
    result = command(['/bin/ps', '-p', str(target), '-o', column + '='], cleanup=cleanup)
    return result.stdout.strip() if result.returncode == 0 else None

def rows():
    result = command(['/bin/ps', '-axo', 'pid=,ppid=,stat=,command='])
    assert result.returncode == 0, 'Process inventory failed'
    return [row for line in result.stdout.splitlines()
            if len(row := line.strip().split(None, 3)) == 4]

def gui_identity(*, cleanup=False):
    return (query(pid, 'lstart', cleanup=cleanup) == birth
            and query(pid, 'command', cleanup=cleanup) == expected_gui)

def gui_cwd():
    result = command(['/usr/sbin/lsof', '-a', '-p', str(pid), '-d', 'cwd', '-Fn'])
    assert result.returncode == 0
    assert '\nn' + str(runtime) + '\n' in '\n' + result.stdout, 'GUI cwd differs'

try:
    assert sha(helper) == expected_helper and sha(preopen_helper) == expected_preopen_helper
    assert sha(runtime / 'runtime-distribution.json') == expected_manifest
    assert sha(base / 'prepared-state.json') == expected_prepared
    prepared = json.loads((base / 'prepared-state.json').read_bytes())
    assert prepared['source_head'] == 'f7524d7bbfb4824640c8ca51dc978769b2fab98b'
    assert prepared['runtime_manifest_sha256'] == expected_manifest
    proof = json.loads((control / 'preopen-001.json').read_bytes())
    assert proof['role'] == 'export' and Path(proof['workspace']) == job
    assert proof['route']['current'] is True and proof['export']['current'] is True
    assert sha(job / 'export/export.json') == proof['export_receipt_sha256']
    assert not (control / 'mutation-001.json').exists()
    record.update(mutation_helper_sha256=sha(helper), preopen_helper_sha256=sha(preopen_helper),
                  preopen_receipt_sha256=sha(control / 'preopen-001.json'),
                  export_receipt_before_sha256=proof['export_receipt_sha256'])
    owned = [row for row in rows() if row[3] == expected_gui and 'Z' not in row[2]]
    assert len(owned) == 1, 'Exactly one current owned GUI is required'
    pid = int(owned[0][0]); birth = query(pid, 'lstart')
    assert birth and gui_identity()
    gui_cwd()
    record.update(GUI_pid=pid, GUI_birth=birth)
    children = []
    while not children:
        remaining()
        assert gui_identity(), 'GUI identity changed while waiting'
        children = [row for row in rows() if int(row[1]) == pid
                    and row[3] in expected_readers and 'Z' not in row[2]]
        assert len(children) <= 1, 'More than one exact reader; no pause or mutation'
        if not children:
            time.sleep(min(0.1, remaining()))
    child = int(children[0][0]); child_command = children[0][3]
    child_birth = query(child, 'lstart')
    assert child_birth and query(child, 'command') == child_command
    assert query(child, 'ppid') == str(pid)
    assert gui_identity()
    gui_cwd()
    record.update(child_before=children, child_pid=child, child_birth=child_birth,
                  child_command=child_command, child_observed_wall_seconds=time.monotonic()-started)
    remaining()
    os.kill(pid, signal.SIGSTOP); stopped = True; record['paused'] = True
    while True:
        state = query(child, 'stat')
        assert state is not None, 'Reader reaped; interval missed, no mutation'
        assert query(child, 'lstart') == child_birth and query(child, 'ppid') == str(pid)
        if 'Z' in state:
            record.update(child_completion_state=state, child_completion_birth=child_birth,
                          child_completion_wall_seconds=time.monotonic()-started)
            break
        assert query(child, 'command') == child_command, 'Live reader command changed'
        time.sleep(min(0.1, remaining()))
    assert gui_identity()
    gui_cwd()
    assert sha(helper) == expected_helper
    record['mutation_attempted'] = True
    result = subprocess.run([str(ROOT / '.venv/bin/python'), '-B', str(helper), 'export', workspace],
                            capture_output=True, text=True, timeout=min(5, remaining()))
    record.update(mutation_helper_exit=result.returncode,
                  mutation_helper_output=(result.stdout + result.stderr)[:16384])
    assert result.returncode == 0
    record['mutated'] = True
except BaseException as error:
    record['error'] = type(error).__name__ + ': ' + str(error)
finally:
    if stopped:
        try:
            # Cleanup has a separate finite allowance: never leave a verified owned
            # GUI stopped merely because the injection opportunity expired.
            assert gui_identity(cleanup=True), 'Resume refused: GUI identity changed'
            os.kill(pid, signal.SIGCONT); record['resumed'] = True
        except BaseException as error:
            record['resume_error'] = type(error).__name__ + ': ' + str(error)
    record['wall_seconds'] = time.monotonic() - started
    record['cleanup_can_extend_opportunity'] = True
    if (control / 'mutation-001.json').is_file():
        record['mutation_receipt_sha256'] = sha(control / 'mutation-001.json')
        record['export_receipt_after_sha256'] = sha(job / 'export/export.json')
    with receipt.open('x') as stream:
        json.dump(record, stream, indent=2, sort_keys=True); stream.write('\n')
print(json.dumps(record))
sys.exit(0 if record['mutated'] and record['resumed'] else 2)
