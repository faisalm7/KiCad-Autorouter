"""The checked single-move entry from the ordinary PCB toolbar."""
from __future__ import annotations

import json
import os
from pathlib import Path
import stat
import subprocess
import uuid

from . import config as c, gui, pipeline as p
from .local_settings import canonical


MANAGER_SHA256 = '9962d3c69819eaf3da623090208c86159d50ea840bfb3ee36beb271dfabce435'
PCB_EDITOR_SHA256 = '003e268aeb96cb23f660c4cc81c839addbea9ab638daf9a5fa16f05023f08a9d'
EXAMPLE_NAME = 'owned-placement-ordinary'
EXAMPLE_FILES = tuple(EXAMPLE_NAME + suffix for suffix in ('.kicad_pcb', '.kicad_pro', '.kicad_sch'))


def editor_manager(bundle, *, verify_signature=False):
    """Bind both executables of the qualified isolated Mac editor."""
    bundle = canonical(Path(bundle).absolute())
    if c.NATIVE_VERSION != '10.0.7' or bundle.name != 'KiCad.app':
        raise ValueError('The checked move needs the approved 10.0.8 editor and 10.0.7 validation tools.')
    manager = canonical(bundle / 'Contents/MacOS/kicad')
    editor = canonical(bundle / 'Contents/Applications/PCBNew.app/Contents/MacOS/pcbnew')
    for path, expected in ((manager, MANAGER_SHA256), (editor, PCB_EDITOR_SHA256)):
        if not os.access(path, os.X_OK) or p.sha(path) != expected:
            raise ValueError('The isolated KiCad 10.0.8 editor no longer matches the checked installation.')
    if verify_signature:
        try:
            subprocess.run(['/usr/bin/codesign', '--verify', '--deep', '--strict', str(bundle)],
                           check=True, timeout=30, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except (OSError, subprocess.SubprocessError) as exc:
            raise ValueError('The isolated KiCad editor signature could not be verified.') from exc
    return manager


def example_source():
    return c.ROOT / 'examples' / 'owned-placement-routing' / 'source'


def start(launcher, board, connection):
    """Check exact product scope before opening any write-capable IPC session."""
    import fcntl
    from scripts import install_gui
    from experiments.live_editor_v1.probe import Session

    manifest = canonical(Path(launcher) / 'install.json')
    record = install_gui.read_manifest(manifest)
    if not record.get('checked_move_editor'):
        raise ValueError('This launcher has no checked live move capability.')
    source = manifest.parent / 'inspection'
    if board != canonical(source / (EXAMPLE_NAME + '.kicad_pcb')):
        raise ValueError('Checked live moves are available on the prepared example only.')
    path = manifest.parent / '.checked-live-move-lock'
    lease = os.fdopen(os.open(path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600), 'r+')
    try:
        info = os.fstat(lease.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_nlink != 1:
            raise ValueError('The checked move needs a private workspace lock.')
        fcntl.flock(lease.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        run = canonical(c.ROOT / '.runs') / ('checked-live-move-' + uuid.uuid4().hex)
        run.mkdir(mode=0o700)
        session = Session(run, c.ROOT, direct_trial=True, source=source, connection=connection)
    except BaseException:
        lease.close()
        raise
    return session, lease


def workspace(session):
    """Own the private worker and its checked operations for one workspace."""
    from experiments.live_editor_v1.probe import EditorContextChanged

    operations = {'inspect': lambda: session.inspect(board_view=True),
                  'preview': lambda request=None: session.preview(request, board_view=True), 'discard': session.reject,
                  'validate': session.validate, 'apply_direct': lambda proposal: session.apply_direct_trial(proposal, board_view=True),
                  'undo': lambda: session.check_undo(board_view=True)}
    argv = [str(c.PYTHON), '-B', '-m', 'experiments.live_editor_v1.panel', '--workspace', '--direct-1008-trial',
            '--saved-project', str(session.path.with_suffix('.kicad_pro'))]
    view = subprocess.Popen(argv, cwd=c.ROOT, env=gui.child_environment(),
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE, encoding='utf-8')
    try:
        for line in iter(lambda: view.stdout.readline(4096), ''):
            if not line.endswith('\n'):
                raise ValueError('Invalid Copperpath IPC request size.')
            command = None
            try:
                request = json.loads(line)
                if type(request) is not dict or set(request) != {'command', 'args'} or type(request['args']) is not list:
                    raise ValueError('Unrecognized Copperpath command.')
                command = request['command']
                result = dict(ok=True, value=operations[command](*request['args']))
            except Exception as exc:
                # Never send an endpoint or token from transport exceptions.
                message = str(exc) if type(exc) in (ValueError, EditorContextChanged) else 'The KiCad operation could not be verified. Check the editor.'
                result = dict(ok=False, message=message)
                if type(exc) is EditorContextChanged:
                    result['read_selection'] = True
                if command == 'apply_direct' and session.applied is not None:
                    result.update(verify_undo=True, message=(
                        'The move outcome is uncertain. In KiCad, check for the named Copperpath Undo. '
                        'If present, use it and then verify the board here. A further move is disabled.'))
            print(json.dumps(result), file=view.stdin, flush=True)
    finally:
        view.stdin.close()
        view.stdout.close()
        try:
            view.wait(timeout=4)
        except subprocess.TimeoutExpired:
            view.terminate()
            view.wait(timeout=4)
