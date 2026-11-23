#!/usr/bin/env python3
"""Prepare a source-bound Finder launcher and isolated KiCad controls."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import plistlib
import shlex
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from autorouter import config as c, pipeline as p, placement_clearance as pc
from autorouter.local_settings import canonical
from scripts import prepare_gui_plugin as plugin

LIMIT = 1024 * 1024
PLUGIN = 'documents/KiCad/10.0/plugins/org.kicad.autorouter.local/'
PCM_ROOT = 'documents/KiCad/10.0/3rdparty'
PCM_ISOLATION_POLICY = 'kicad10-project-pcm-root-v1'
SAVED_APP = 'Copperpath.app'
APP_EXECUTABLE = f'{SAVED_APP}/Contents/MacOS/Copperpath'
APP_INFO = f'{SAVED_APP}/Contents/Info.plist'
APP_ICON = f'{SAVED_APP}/Contents/Resources/Route.icns'
FINDER_REFUSAL_SHOWN = 20
IMMUTABLE_FILES = frozenset(('Open Saved Project.command', 'Launch Autorouter.command', 'README.txt', 'initial-kicad_common.json',
    'initial-kicad.json', APP_EXECUTABLE, APP_INFO, APP_ICON,
    *(PLUGIN + name for name in ('plugin.json', 'launch-autorouter', 'route24.png', 'route48.png'))))
README = '''Copperpath for saved KiCad projects

Double-click Copperpath in Finder. Click Choose project and select the
saved .kicad_pro alongside its matching PCB and schematic. Copperpath inspects
the saved project and displays its board. If it is open in KiCad, save and
close both editors, then choose File > Close Project in KiCad manager. Back in
Copperpath, click Refresh inspection. You can also enter the path and press Return.
If startup checks refuse, the Finder dialog shows the reason. Open Saved
Project.command remains available for Terminal diagnostics.

For the optional PCB toolbar, double-click Launch Autorouter.command. It starts
the existing KiCad manager with configuration, plugins, PCM content and cache
in this folder. Open a project and its PCB Editor, then click the green trace.
With the documented optional IPC client installed, Copperpath verifies and
selects the saved project from that editor. It can also carry the component
selection from launch. Use KiCad selection after closing and inspecting the
saved project. If the handoff cannot be verified, choose the saved project
in Copperpath. Geometry and constraints always come from the inspected files.
KICAD10_3RD_PARTY overrides inherited or saved PCM paths; personal PCM plugins,
libraries and themes are not loaded through that search root. Bundled vendor
plugins are unchanged. This is a cooperative launch boundary, not an OS sandbox.
Acknowledge the reviewed changes before routing.
Candidates/review/export stay separate; no automatic live-board edits.

This is a bootstrap for this exact existing checkout, virtual environment and
pinned tools, not a standalone application, package or dependency installer.
Keep this checkout and tools in place. A changed checkout/tool refuses launch;
prepare a NEW launcher folder after an intentional update. Nothing downloads.

Only this isolated config enables KiCad's local IPC API. Telemetry, KiCad and
package update checks are disabled in the new config. This is not an OS network
sandbox or protection against hostile same-user writers. Standard symbol,
footprint or 3D library warnings may appear if libraries are not installed;
no libraries are fetched and no source project is repaired automatically.
Live config/documents/cache remain mutable, but linked/special files or folders
refuse launch. PCM content shares the documents limit: 512 MiB, 10,000 files/
20,000 entries per home. The prepared PCM directory identity must remain intact;
reconstructed/replaced directories require a fresh launcher. Earlier launchers
without this isolation policy are never upgraded or silently accepted.
Keep old launcher folders; prepare a fresh one if these limits are exceeded.

The optional manager launcher refuses when it observes another KiCad manager
or editor for this user. Close those applications first. This sampled check
cannot prevent simultaneous startup or detect deliberately renamed processes.
Closing Terminal can terminate the manager; cancel active routing in the router
window and wait for its existing cleanup before closing applications.
'''


def digest(path):
    return hashlib.sha256(pc.read_bytes(path, LIMIT)).hexdigest()


def installer_pins():
    return {str(path): digest(path) for path in
            (c.ROOT / 'scripts/install_gui.py', c.ROOT / 'scripts/prepare_gui_plugin.py')}


def launch_command(python, flag, manifest):
    return shlex.join((str(python), '-B', str(c.ROOT / 'scripts/install_gui.py'), flag, str(manifest)))


def finder_refusal(error):
    """Display the checked startup reason as literal text."""
    script = ('on run arguments\n'
              'display alert "Copperpath could not open" message (item 1 of arguments) as warning giving up after 45\n'
              'end run')
    detail = ' '.join(str(error).split())[:500]
    message = (detail + '\n\nOpen Copperpath from its original launcher folder. '
               'If you moved the installation, set up a fresh copy from the verified artifact.')
    try:
        result = subprocess.run(['/usr/bin/osascript', '-e', script, '--', message],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=60)
        return result.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def prepare_saved_app(output, python):
    """Create a small local app around the same pinned saved-project entry."""
    executable, info, icon = (output / name for name in (APP_EXECUTABLE, APP_INFO, APP_ICON))
    executable.parent.mkdir(parents=True, mode=0o700)
    icon.parent.mkdir(mode=0o700)
    properties = dict(CFBundleExecutable='Copperpath', CFBundleIdentifier='org.copperpath.saved-project',
                      CFBundleName='Copperpath', CFBundlePackageType='APPL', CFBundleVersion='1',
                      CFBundleIconFile=icon.name, NSHighResolutionCapable=True, LSUIElement=True)
    with info.open('xb') as stream:
        plistlib.dump(properties, stream)
    png = plugin.icon_png(128)
    image = b'ic07' + (len(png) + 8).to_bytes(4, 'big') + png
    with icon.open('xb') as stream:
        stream.write(b'icns' + (len(image) + 8).to_bytes(4, 'big') + image)
    command = launch_command(python, '--open-saved-finder', output / 'install.json')
    alert = ('display alert "Copperpath could not open" message '
             '"Check that the original installation and its local Python environment are present. '
             'Open Saved Project.command in the launcher folder can show startup diagnostics." as warning giving up after 45')
    with executable.open('x') as stream:
        stream.write('#!/bin/sh\nunset PYTHONPATH PYTHONHOME KICAD_API_SOCKET KICAD_API_TOKEN\n'
                     + command + '\nlauncher_exit=$?\n'
                     + f'case "$launcher_exit" in 0) exit 0;; {FINDER_REFUSAL_SHOWN}) exit 2;; esac\n'
                     + '/usr/bin/osascript -e ' + shlex.quote(alert) + '\nexit 2\n')
    executable.chmod(0o700)
    return executable, info, icon


def prepare(output, *, checked_move_editor=None):
    output = canonical(Path(output).absolute())
    if output.exists() or not output.parent.is_dir():
        raise ValueError('Choose a fresh output folder beneath an existing real directory.')
    tools = p.tool_manifest()
    scripts = installer_pins()
    manager = c.CLI.with_name('kicad')
    example_files = []
    if checked_move_editor is not None:
        from autorouter import live_move
        checked_move_editor = canonical(Path(checked_move_editor).absolute())
        manager = live_move.editor_manager(checked_move_editor, verify_signature=True)
        import kipy  # The optional installation uses the existing pinned IPC client.
        if not Path(kipy.__file__).is_relative_to(c.ROOT / '.venv'):
            raise ValueError('Install the pinned local KiCad IPC client in this runtime first.')
    if not manager.is_file() or not os.access(manager, os.X_OK):
        raise ValueError('Existing KiCad manager executable required.')
    python = c.ROOT / '.venv/bin/python'
    if not python.is_file() or not os.access(python, os.X_OK):
        raise ValueError('Existing checkout Python environment required.')
    manager_sha256 = p.sha(manager)
    output.mkdir(mode=0o700)
    documents, config, cache = (output / name for name in ('documents', 'config', 'cache'))
    prepared = plugin.prepare(documents, checked_launcher=output) if checked_move_editor else plugin.prepare(documents)
    third_party = output / PCM_ROOT
    third_party.mkdir(mode=0o700)
    (third_party / 'plugins').mkdir(mode=0o700)
    third_party_stat = third_party.stat()
    config_version = config / '10.0'; config_version.mkdir(parents=True, mode=0o700)
    cache.mkdir(mode=0o700)
    common = dict(meta=dict(filename='kicad_common', version=5), api=dict(enable_server=True),
                  do_not_show_again=dict(data_collection_prompt=True, update_check_prompt=True),
                  system=dict(enable_sentry_reporting=False))
    manager_config = dict(meta=dict(version=0), system=dict(check_for_kicad_updates=False),
                          pcm=dict(check_for_updates=False))
    for name, value in (('kicad_common.json', common), ('kicad.json', manager_config)):
        data = (json.dumps(value, indent=2) + '\n').encode()
        with (config_version / name).open('xb') as stream: stream.write(data)
        with (output / ('initial-' + name)).open('xb') as stream: stream.write(data)
    launchers = []
    for name, flag in (('Open Saved Project.command', '--open-saved'), ('Launch Autorouter.command', '--launch')):
        launch = output / name
        command = launch_command(python, flag, output / 'install.json')
        payload = ('#!/bin/sh\nset -eu\nunset PYTHONPATH PYTHONHOME KICAD_API_SOCKET KICAD_API_TOKEN\ncd '
                   + shlex.quote(str(c.ROOT)) + '\nexec ' + command + '\n')
        with launch.open('x') as stream: stream.write(payload)
        launch.chmod(0o700)
        launchers.append(launch)
    launchers.extend(prepare_saved_app(output, python))
    description = README
    if checked_move_editor:
        source = live_move.example_source()
        inspection = output / 'inspection'; inspection.mkdir(mode=0o700)
        for name in live_move.EXAMPLE_FILES:
            path = inspection / name
            with path.open('xb') as stream: stream.write(pc.read_bytes(source / name, LIMIT))
            example_files.append(path)
        description += ('\nLaunch Autorouter also opens an owned disposable example in the checked 10.0.8 editor. '
            'Open its PCB Editor, select J1 or J2 and use the green trace toolbar action. '
            'The workspace offers one previewed, approved move and verifies native Undo. '
            'Other boards open the saved-project workspace.\n')
    (output / 'README.txt').write_text(description)
    immutable = {str(path.relative_to(output)): digest(path) for path in
        [*launchers, *example_files, output / 'README.txt', output / 'initial-kicad_common.json', output / 'initial-kicad.json',
         *sorted(Path(prepared['plugin']).iterdir())]}
    if set(immutable) != IMMUTABLE_FILES | {'inspection/' + path.name for path in example_files}:
        raise ValueError('Prepared launcher file population differs.')
    record = dict(schema=1, kind='local-gui-bootstrap-v1', root=str(output), checkout=str(c.ROOT),
                  manager=str(manager), manager_sha256=manager_sha256,
                  config_home=str(config), documents_home=str(documents), cache_home=str(cache),
                  launch_isolation_policy=PCM_ISOLATION_POLICY, third_party_home=str(third_party),
                  third_party_identity=dict(device=third_party_stat.st_dev, inode=third_party_stat.st_ino),
                  tools=tools, installer_sha256=scripts, immutable_files=immutable,
                  installed_globally=False, standalone=False,
                  qualification='Prepared only; actual double-click/IPC/GUI behavior requires qualification.')
    if checked_move_editor: record['checked_move_editor'] = str(checked_move_editor)
    with (output / 'install.json').open('x') as stream:
        json.dump(record, stream, indent=2); stream.write('\n')
    return record


def check_third_party_home(record, root):
    """Bind the PCM search root; its descendants share the documents inventory."""
    expected = root / PCM_ROOT
    if (record.get('launch_isolation_policy') != PCM_ISOLATION_POLICY
            or record.get('third_party_home') != str(expected)):
        raise ValueError('Prepared PCM isolation policy or directory differs; prepare a fresh launcher.')
    path = canonical(expected)
    identity = record.get('third_party_identity')
    if (not path.is_dir() or type(identity) is not dict or set(identity) != {'device', 'inode'}
            or any(type(identity[key]) is not int for key in identity)
            or identity['device'] < 0 or identity['inode'] <= 0):
        raise ValueError('Prepared PCM directory identity missing or invalid.')
    current = path.stat()
    if identity != dict(device=current.st_dev, inode=current.st_ino):
        raise ValueError('Prepared PCM directory replaced; prepare a fresh launcher.')
    return str(path)



def check_live_homes(homes):
    """Reuse bounded snapshot reads; reject pre-existing links without resetting config.

    This is a cooperative pre-exec consistency check, not an atomic defense
    against a hostile same-user writer or simultaneous application startup.
    """
    for value in homes.values():
        root = canonical(Path(value))
        files = pc.inventory(root, max_bytes=512 * 1024**2,
                             max_files=10000, max_entries=20000)
        for name in files:
            path = canonical(root / name)
            if path.stat().st_nlink != 1:
                raise ValueError('Linked file in isolated KiCad home; prepare a fresh launcher folder.')


def require_closed_kicad():
    """Current-user, PID-only sampled precondition; never terminate other applications."""
    try:
        result = subprocess.run(['/usr/bin/pgrep', '-U', str(os.getuid()), '-x',
                                 '(kicad|pcbnew|eeschema)'], capture_output=True,
                                timeout=3, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ValueError('Could not check existing KiCad applications; launch refused.') from exc
    if len(result.stdout) > 128 * 1024 or len(result.stderr) > 128 * 1024:
        raise ValueError('Existing KiCad application check exceeded its output bound.')
    if result.returncode == 1 and result.stdout == b'':
        return
    rows = result.stdout.splitlines()
    if result.returncode == 0 and rows and all(row.isdigit() and int(row) > 0 for row in rows):
        raise ValueError('Close other KiCad managers, PCB and schematic editors, then launch again. No application was closed.')
    raise ValueError('Could not verify closed KiCad applications; launch refused.')


def read_manifest(manifest):
    """Check the launcher and pinned inputs without starting any process."""
    manifest = canonical(Path(manifest).absolute())
    if manifest.name != 'install.json': raise ValueError('Exact prepared install.json required.')
    root = manifest.parent
    record = json.loads(pc.read_bytes(manifest, LIMIT))
    if type(record) is not dict: raise ValueError('Prepared launcher identity differs.')
    manager = c.CLI.with_name('kicad')
    immutable = IMMUTABLE_FILES
    if 'checked_move_editor' in record:
        from autorouter import live_move
        editor = record['checked_move_editor']
        if type(editor) is not str or not Path(editor).is_absolute():
            raise ValueError('Prepared checked editor path differs.')
        manager = live_move.editor_manager(editor)
        immutable = immutable | {'inspection/' + name for name in live_move.EXAMPLE_FILES}
    if (type(record.get('schema')) is not int or record.get('schema') != 1 or record.get('kind') != 'local-gui-bootstrap-v1'
            or record.get('root') != str(root) or record.get('checkout') != str(c.ROOT)
            or record.get('manager') != str(manager) or record.get('installed_globally') is not False
            or record.get('standalone') is not False):
        raise ValueError('Prepared launcher identity differs.')
    expected_homes = {name + '_home': str(root / name) for name in ('config', 'documents', 'cache')}
    if any(record.get(key) != value for key, value in expected_homes.items()):
        raise ValueError('Isolated KiCad homes escaped launcher directory.')
    for value in expected_homes.values():
        if not canonical(Path(value)).is_dir(): raise ValueError('Isolated KiCad home missing.')
    check_third_party_home(record, root)
    check_live_homes(expected_homes)
    if record.get('tools') != p.tool_manifest() or record.get('installer_sha256') != installer_pins():
        raise ValueError('Checkout or pinned tools changed; prepare a fresh launcher.')
    files = record.get('immutable_files')
    if type(files) is not dict or set(files) != immutable: raise ValueError('Exact prepared launcher files required.')
    for relative, expected in files.items():
        path = canonical(root / relative)
        if root not in path.parents or not path.is_file() or digest(path) != expected:
            raise ValueError('Prepared launcher/plugin file changed.')
    if p.sha(manager) != record.get('manager_sha256') or not os.access(manager, os.X_OK):
        raise ValueError('Prepared KiCad manager changed.')
    return record


def launch_material(manifest):
    record = read_manifest(manifest)
    root = Path(record['root'])
    third_party = check_third_party_home(record, root)
    env = {key: value for key, value in os.environ.items()
           if key not in ('PYTHONPATH', 'PYTHONHOME', 'KICAD_API_SOCKET', 'KICAD_API_TOKEN')}
    env.update(KICAD_CONFIG_HOME=record['config_home'], KICAD_DOCUMENTS_HOME=record['documents_home'],
               KICAD_CACHE_HOME=record['cache_home'], KICAD10_3RD_PARTY=third_party,
               PYTHONNOUSERSITE='1', PYTHONDONTWRITEBYTECODE='1')
    return record, root, env


def prepare_new_project_manager(manifest):
    """Prepare the native manager without opening an example or writing CAD files."""
    require_closed_kicad()
    record, root, env = launch_material(manifest)
    if 'checked_move_editor' in record:
        from autorouter import live_move
        live_move.editor_manager(record['checked_move_editor'], verify_signature=True)
    check_third_party_home(record, root)
    return [record['manager']], env


def launch(manifest, *, direct=False):
    record, root, env = launch_material(manifest)
    manager = Path(record['manager'])
    if not direct:
        require_closed_kicad()
    check_third_party_home(record, root)
    os.chdir(c.ROOT)
    if direct:
        os.execve(c.PYTHON, [str(c.PYTHON), '-B', '-m', 'autorouter.gui', '--workspace',
                            '--workspace-launcher', str(root / 'install.json')], env)
    else:
        argv = [str(manager)]
        if 'checked_move_editor' in record:
            from autorouter import live_move
            live_move.editor_manager(record['checked_move_editor'], verify_signature=True)
            argv.append(str(root / 'inspection' / (live_move.EXAMPLE_NAME + '.kicad_pro')))
        os.execve(manager, argv, env)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--output'); mode.add_argument('--launch'); mode.add_argument('--open-saved')
    mode.add_argument('--open-saved-finder', help=argparse.SUPPRESS)
    parser.add_argument('--checked-move-editor', help='Existing signed KiCad 10.0.8 app for the isolated example')
    args = parser.parse_args()
    if args.checked_move_editor is not None and args.output is None:
        parser.error('Use --checked-move-editor only when preparing a new output folder.')
    try:
        if args.launch: launch(args.launch)
        elif args.open_saved or args.open_saved_finder:
            launch(args.open_saved or args.open_saved_finder, direct=True)
        else: print(json.dumps(prepare(args.output, checked_move_editor=args.checked_move_editor), indent=2))
    except (ValueError, p.Rejected, OSError, ImportError) as exc:
        print('Launcher refused: ' + str(exc), file=sys.stderr)
        if args.open_saved_finder and finder_refusal(exc):
            return FINDER_REFUSAL_SHOWN
        return 2
    return 0


if __name__ == '__main__': raise SystemExit(main())
