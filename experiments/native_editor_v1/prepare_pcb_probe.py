"""Prepare or open the read-only dock probe in a private KiCad 10.0.8 profile."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

from autorouter import gui, live_move, placement_clearance


ROOT = Path(__file__).resolve().parents[2]
BUNDLE = ROOT / '.tools/kicad-10.0.8-isolated-live-001/KiCad.app'
EDITOR = BUNDLE / 'Contents/Applications/pcbnew.app/Contents/MacOS/pcbnew'
FIXTURE = ROOT / 'examples/owned-placement-routing/source'
PROBE = Path(__file__).with_name('pcb_host_probe.py')


def checked_run(run):
    if run.resolve() != run or not run.is_relative_to(ROOT / '.runs') or run == ROOT / '.runs':
        raise ValueError('Use an exact experiment directory under this checkout’s .runs.')
    return run


def material(run):
    board = run / 'inspection' / (live_move.EXAMPLE_NAME + '.kicad_pcb')
    plugin = run / 'config/10.0/scripting/plugins/copperpath_host_probe.py'
    return board, plugin


def file_digest(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def prepare_profile(run):
    checked_run(run).mkdir(mode=0o700)
    for name in ('cache', 'config', 'documents', 'third-party'):
        (run / name).mkdir(mode=0o700)
    board, _ = material(run)
    placement_clearance.copy_project(FIXTURE, board.parent)
    common_path = run / 'config/10.0/kicad_common.json'
    common_path.parent.mkdir(parents=True, mode=0o700)
    common = dict(meta=dict(filename='kicad_common', version=5), api=dict(enable_server=False),
                  do_not_show_again=dict(data_collection_prompt=True, update_check_prompt=True),
                  system=dict(enable_sentry_reporting=False))
    with common_path.open('x', encoding='utf-8') as stream:
        json.dump(common, stream, indent=2)
        stream.write('\n')
    return board, common_path


def editor_environment(run):
    env = {key: os.environ[key] for key in ('HOME', 'LANG', 'LC_ALL', 'TMPDIR', 'USER', 'PATH')
           if key in os.environ}
    env.update(KICAD_CONFIG_HOME=str(run / 'config'), KICAD_CACHE_HOME=str(run / 'cache'),
               KICAD_DOCUMENTS_HOME=str(run / 'documents'), KICAD10_3RD_PARTY=str(run / 'third-party'),
               PYTHONNOUSERSITE='1', PYTHONDONTWRITEBYTECODE='1')
    return env


def prepare(run):
    board, common_path = prepare_profile(run)
    _, plugin = material(run)
    plugin.parent.mkdir(parents=True, mode=0o700)
    shutil.copyfile(PROBE, plugin)
    data = dict(schema=1, editor='10.0.8', editor_sha256=live_move.PCB_EDITOR_SHA256,
                board_hashes=gui.source_inventory(board), probe_sha256=file_digest(plugin),
                common_sha256=file_digest(common_path))
    with (run / 'prepared.json').open('x', encoding='utf-8') as stream:
        json.dump(data, stream, indent=2)
        stream.write('\n')
    return data


def open_editor(run):
    checked_run(run)
    board, plugin = material(run)
    common = run / 'config/10.0/kicad_common.json'
    data = json.loads((run / 'prepared.json').read_text(encoding='utf-8'))
    if (run.stat().st_uid != os.getuid() or run.stat().st_mode & 0o077
            or board.resolve() != board or plugin.resolve() != plugin
            or common.resolve() != common or file_digest(common) != data['common_sha256']
            or gui.source_inventory(board) != data['board_hashes']
            or file_digest(plugin) != data['probe_sha256']
            or file_digest(PROBE) != data['probe_sha256']):
        raise ValueError('The private fixture or prepared probe changed.')
    receipt = run / 'pcb-host.jsonl'
    launch = run / 'launch.json'
    if os.path.lexists(receipt) or os.path.lexists(launch):
        raise ValueError('Inspect the existing probe attempt before opening another.')
    if EDITOR.resolve() != EDITOR or file_digest(EDITOR) != live_move.PCB_EDITOR_SHA256:
        raise ValueError('The isolated PCB Editor differs from the qualified 10.0.8 binary.')
    subprocess.run(['/usr/bin/codesign', '--verify', '--deep', '--strict', str(BUNDLE)],
                   check=True, timeout=30, capture_output=True)
    env = editor_environment(run)
    env.update(COPPERPATH_PCB_HOST_PROBE_SOURCE=str(board), COPPERPATH_PCB_HOST_PROBE_RECEIPT=str(receipt))
    with launch.open('x', encoding='utf-8') as stream:
        try:
            editor = subprocess.Popen([str(EDITOR), str(board)], cwd=board.parent, env=env,
                                      stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except OSError as error:
            json.dump(dict(status='failed', reason=type(error).__name__), stream, indent=2)
            raise
        json.dump(dict(status='launched', pid=editor.pid, executable=str(EDITOR), source=str(board)),
                  stream, indent=2)
        stream.write('\n')
    return editor.pid


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'open'))
    parser.add_argument('run', type=Path)
    args = parser.parse_args()
    fn = prepare if args.action == 'prepare' else open_editor
    print(json.dumps(fn(args.run.absolute())))
