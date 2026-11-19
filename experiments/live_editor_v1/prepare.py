"""Prepare an isolated launcher for the reproducible owned-board experiment."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys

from probe import FIXTURE, ROOT

EDITOR_1008 = ROOT / '.tools/kicad-10.0.8-isolated-live-001/KiCad.app'
MANAGER_1008_SHA256 = '9962d3c69819eaf3da623090208c86159d50ea840bfb3ee36beb271dfabce435'


def run_checked_launcher(launcher, runtime, run):
    """Start the exact qualified editor with a fresh, private project home."""
    from scripts import install_gui

    manifest = json.loads((launcher / 'install.json').read_bytes())
    homes = {name: launcher / name for name in ('config', 'cache', 'documents')}
    if (manifest['root'] != str(launcher) or manifest['checkout'] != str(runtime)
            or any(manifest[key + '_home'] != str(path) for key, path in homes.items())):
        raise ValueError('The prepared live companion homes differ.')
    install_gui.check_live_homes({name: str(path) for name, path in homes.items()})
    third_party = install_gui.check_third_party_home(manifest, launcher)
    manager = EDITOR_1008 / 'Contents/MacOS/kicad'
    if manager.resolve() != manager or hashlib.sha256(manager.read_bytes()).hexdigest() != MANAGER_1008_SHA256:
        raise ValueError('Use the verified isolated KiCad 10.0.8 installation.')
    subprocess.run(['/usr/bin/codesign', '--verify', '--deep', '--strict', str(EDITOR_1008)],
                   check=True, timeout=30)
    install_gui.require_closed_kicad()
    env = {key: value for key, value in os.environ.items() if key not in
           ('PYTHONPATH', 'PYTHONHOME', 'KICAD_API_SOCKET', 'KICAD_API_TOKEN')}
    env.update({f'KICAD_{key.upper()}_HOME': str(path) for key, path in homes.items()})
    env.update(KICAD10_3RD_PARTY=third_party, PYTHONNOUSERSITE='1', PYTHONDONTWRITEBYTECODE='1')
    project = run / 'inspection' / 'owned-placement-ordinary.kicad_pro'
    os.chdir(project.parent)
    os.execve(manager, [str(manager), str(project)], env)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--diagnostics', action='store_true')
    parser.add_argument('--direct-1008-trial', action='store_true')
    parser.add_argument('--open', action='store_true', help='Open a prepared owned checked-move project.')
    args = parser.parse_args()
    runtime, run = args.runtime.absolute(), args.run.absolute()
    if (runtime.resolve() != runtime or run.resolve() != run or run.parent != ROOT / '.runs'
            or args.open != run.is_dir() or (not args.open and run.exists())):
        parser.error('Choose an existing canonical runtime and a fresh directory directly under .runs.')

    sys.path.insert(0, str(runtime))
    from autorouter import config, placement_clearance
    from scripts import install_gui, prepare_gui_plugin
    import kipy

    python = runtime / '.venv/bin/python'
    if config.ROOT != runtime or config.NATIVE_VERSION != '10.0.7' or not python.is_file():
        parser.error('Use the pinned KiCad 10.0.7 runtime with its official IPC client installed.')
    if not Path(kipy.__file__).is_relative_to(runtime):
        parser.error('Run this with the selected runtime’s .venv/bin/python.')

    if args.open:
        if not args.direct_1008_trial:
            parser.error('Checked live moves require the exact isolated 10.0.8 editor.')
        run_checked_launcher(run / 'launcher', runtime, run)
        return

    run.mkdir(mode=0o700)
    placement_clearance.copy_project(FIXTURE, run / 'inspection')
    launcher = run / 'launcher'
    install_gui.prepare(launcher)
    plugins = launcher / 'documents/KiCad/10.0/plugins'
    plugin = plugins / 'org.copperpath.owned-live-check'
    plugin.mkdir(mode=0o700)
    for size in (24, 48):
        (plugin / f'move{size}.png').write_bytes(prepare_gui_plugin.icon_png(size))
    manifest = dict(identifier=plugin.name, name='Copperpath live PCB check',
        description='Preview a move on the exact owned disposable PCB.',
        runtime=dict(type='exec'), actions=[dict(identifier='check-open-board',
        name='Copperpath: open board', description='Open the owned-board experiment.',
        entrypoint='launch-live-check', scopes=['pcb'], **{
            'show-button': True, 'icons-light': ['move24.png', 'move48.png'],
            'icons-dark': ['move24.png', 'move48.png']})])
    (plugin / 'plugin.json').write_text(json.dumps(manifest, indent=2) + '\n')
    command = [python, '-B', Path(__file__).with_name('probe.py').resolve(),
               '--runtime', runtime, '--run', run]
    if args.diagnostics:
        command.append('--diagnostics')
    if args.direct_1008_trial:
        command.append('--direct-1008-trial')
    script = plugin / 'launch-live-check'
    script.write_text('#!/bin/sh\nset -eu\nunset PYTHONPATH PYTHONHOME\nexport PYTHONNOUSERSITE=1\n'
        + 'cd ' + shlex.quote(str(run)) + '\nexec ' + shlex.join(map(str, command)) + '\n')
    script.chmod(0o700)
    if args.direct_1008_trial:
        launch = run / 'Launch Checked Live Move.command'
        args_open = [python, '-B', Path(__file__).resolve(), '--runtime', runtime, '--run', run,
                     '--direct-1008-trial', '--open']
        launch.write_text('#!/bin/sh\nset -eu\nexec ' + shlex.join(map(str, args_open)) + '\n')
        launch.chmod(0o700)
        print(launch)
    else:
        print(launcher / 'Launch Autorouter.command')
    print(run / 'inspection')


if __name__ == '__main__':
    main()
