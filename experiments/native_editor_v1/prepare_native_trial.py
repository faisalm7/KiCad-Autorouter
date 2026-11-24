"""Prepare a private owned-board trial for the local KiCad source build."""

import argparse
import json
import os
from pathlib import Path
import stat
import subprocess
import sys

from autorouter import gui, placement_clearance, provenance
from .prepare_pcb_probe import (BUNDLE, ROOT, checked_run, editor_environment, material,
                                prepare_profile)
from .stage_kicad_source import UPSTREAM_REVISION


SOURCE = ROOT / '.tools/kicad-copperpath-10.0.8'
WX_CONFIG = ROOT / '.tools/wx-ki-0bb586c9-dev/bin/wx-config'
CHECKER = Path(__file__).with_name('review_move.py')
CORE = ROOT / 'experiments/live_editor_v1/probe.py'
PROFILE_DIRS = ('cache', 'config', 'documents', 'third-party', 'inspection', 'tmp')


def _private(path):
    info = provenance.canonical(path).lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise ValueError('The native trial requires private, owned directories.')


def _profile_record(run, runtime):
    _private(run)
    for directory in PROFILE_DIRS:
        _private(run / directory)
    board, _ = material(run)
    return dict(schema=1, kind='native-pcb-trial', runtime=runtime,
                project=gui.source_inventory(board),
                config=placement_clearance.inventory(run / 'config', max_bytes=512*1024,
                                                     max_files=16, max_entries=24),
                checker_sha256=provenance.file_digest(CHECKER)[0],
                core_sha256=provenance.file_digest(CORE)[0])


def _validation_runtime(runtime):
    runtime = provenance.canonical(checked_run(runtime))
    manifest = json.loads(provenance.read_bytes(runtime / provenance.MANIFEST, provenance.MAX_MANIFEST_BYTES),
                          object_pairs_hook=provenance._strict_object)
    pins = manifest['immutable_files_sha256']
    identity = provenance.source_identity(runtime,
        {name: pins[name] for name in provenance.module_paths(runtime)})
    if identity.get('native_version') != '10.0.7':
        raise ValueError('Select the verified KiCad 10.0.7 validation runtime.')
    return dict(path=str(runtime), git_head=identity['git_head'],
                manifest_sha256=identity['manifest_sha256'])


def prepare(run, runtime):
    run = provenance.canonical(checked_run(run))
    validated = _validation_runtime(runtime)
    _, common = prepare_profile(run)
    (run / 'tmp').mkdir(mode=0o700)
    templates = BUNDLE / 'Contents/SharedSupport/template'
    for name in ('fp-lib-table', 'sym-lib-table'):
        raw = provenance.read_bytes(templates / name, 128 * 1024)
        with (common.parent / name).open('xb') as target:
            target.write(raw)
    record = _profile_record(run, validated)
    with (run / 'prepared.json').open('x', encoding='utf-8') as stream:
        json.dump(record, stream, indent=2)
        stream.write('\n')
    return record


def _build_files(build):
    build = provenance.canonical(checked_run(build))
    cache = provenance.read_bytes(build / 'CMakeCache.txt').decode('utf-8').splitlines()
    if (f'CMAKE_HOME_DIRECTORY:INTERNAL={SOURCE}' not in cache
            or f'wxWidgets_CONFIG_EXECUTABLE:FILEPATH={WX_CONFIG}' not in cache):
        raise ValueError('Use the pinned KiCad build configured with the built private wxWidgets prefix.')
    revision = subprocess.run(['/usr/bin/git', '-C', str(SOURCE), 'rev-parse', 'HEAD'],
                              check=True, timeout=8, capture_output=True, text=True).stdout.strip()
    if revision != UPSTREAM_REVISION:
        raise ValueError('Use the isolated KiCad 10.0.8 source revision.')
    editor = build / 'pcbnew/pcbnew.app/Contents/MacOS/pcbnew'
    module = build / 'kicad/KiCad.app/Contents/PlugIns/_pcbnew.kiface'
    files = {}
    for role, path in (('editor', editor), ('module', module)):
        sha, size = provenance.file_digest(path, 512 * 1024**2)
        subprocess.run(['/usr/bin/lipo', '-verify_arch', 'arm64', str(path)],
                       check=True, timeout=8, capture_output=True)
        files[role] = dict(path=str(path), sha256=sha, bytes=size)
    return files


def open_editor(run, build):
    """Start only the prepared project. Call from the ordinary admission lane."""
    run = provenance.canonical(checked_run(run))
    _private(run)
    prepared = json.loads(provenance.read_bytes(run / 'prepared.json'),
                          object_pairs_hook=provenance._strict_object)
    runtime = _validation_runtime(Path(prepared['runtime']['path']))
    if prepared != _profile_record(run, runtime):
        raise ValueError('The prepared project, profile or validator changed.')
    launch = run / 'launch.json'
    if os.path.lexists(launch) or os.path.lexists(run / 'native-jobs'):
        raise ValueError('This profile already has a trial. Verify it or prepare a fresh profile.')
    files = _build_files(build)
    board, _ = material(run)
    env = editor_environment(run)
    env.update(TMPDIR=str(run / 'tmp'), KICAD_RUN_FROM_BUILD_DIR='1',
               COPPERPATH_NATIVE_DOCUMENT=str(board), COPPERPATH_NATIVE_PROOF_WRITES='1',
               COPPERPATH_NATIVE_SESSION=str(run), COPPERPATH_NATIVE_PYTHON=sys.executable,
               COPPERPATH_NATIVE_RUNTIME=runtime['path'], COPPERPATH_NATIVE_CHECKER=str(CHECKER))
    with launch.open('x', encoding='utf-8') as stream:
        receipt = dict(schema=1, status='starting', files=files, project=str(board), runtime=runtime)
        try:
            process = subprocess.Popen([files['editor']['path'], str(board)], cwd=board.parent, env=env,
                                       stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                       stderr=subprocess.DEVNULL)
            receipt.update(status='launched', pid=process.pid)
        except OSError:
            receipt['status'] = 'launch_failed'
            raise
        finally:
            json.dump(receipt, stream, indent=2)
            stream.write('\n')
    return process.pid


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run', type=Path)
    parser.add_argument('--runtime', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.run.absolute(), args.runtime.absolute())))
