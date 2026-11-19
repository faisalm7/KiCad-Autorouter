"""Prepare an isolated launcher for the reproducible owned-board experiment."""
import argparse
import json
from pathlib import Path
import shlex
import sys

from probe import FIXTURE, ROOT


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--diagnostics', action='store_true')
    parser.add_argument('--direct-1008-trial', action='store_true')
    args = parser.parse_args()
    runtime, run = args.runtime.absolute(), args.run.absolute()
    if runtime.resolve() != runtime or run.resolve() != run or run.parent != ROOT / '.runs' or run.exists():
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
    print(launcher / 'Launch Autorouter.command')
    print(run / 'inspection')


if __name__ == '__main__':
    main()
