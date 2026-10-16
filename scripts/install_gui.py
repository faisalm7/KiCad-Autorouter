#!/usr/bin/env python3
"""Prepare a source-bound local .command launcher; no global installation."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from autorouter import config as c, pipeline as p, placement_clearance as pc
from autorouter.local_settings import canonical
from scripts import prepare_gui_plugin as plugin

LIMIT = 1024 * 1024
PLUGIN = 'documents/KiCad/10.0/plugins/org.kicad.autorouter.local/'
IMMUTABLE_FILES = frozenset(('Launch Autorouter.command', 'README.txt', 'initial-kicad_common.json',
    'initial-kicad.json', *(PLUGIN + name for name in ('plugin.json', 'launch-autorouter', 'route24.png', 'route48.png'))))
README = '''Local KiCad Autorouter launcher

Double-click Launch Autorouter.command. This starts the existing KiCad manager
with configuration, documents/plugins and cache in this folder, not globally.
Open a saved project, open PCB Editor and click the green Autorouter toolbar
icon. In the separate router window choose the exact saved PCB/output paths.
Save and CLOSE source PCB/schematic editors and acknowledge before routing.
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
refuse launch. Each home is bounded to 512 MiB, 10,000 files/20,000 entries.
Keep old launcher folders; prepare a fresh one if these limits are exceeded.

The launcher refuses when it observes another KiCad manager/editor for this
user. Close those applications first; it never kills them. This sampled check
cannot prevent simultaneous startup or detect deliberately renamed processes.
Closing Terminal can terminate the manager; cancel active routing in the router
window and wait for its existing cleanup before closing applications.
'''


def digest(path):
    return hashlib.sha256(pc.read_bytes(path, LIMIT)).hexdigest()


def installer_pins():
    return {str(path): digest(path) for path in
            (c.ROOT / 'scripts/install_gui.py', c.ROOT / 'scripts/prepare_gui_plugin.py')}


def prepare(output):
    output = canonical(Path(output).absolute())
    if output.exists() or not output.parent.is_dir():
        raise ValueError('Choose a fresh output folder beneath an existing real directory.')
    tools = p.tool_manifest()
    scripts = installer_pins()
    manager = c.CLI.with_name('kicad')
    if not manager.is_file() or not os.access(manager, os.X_OK):
        raise ValueError('Existing KiCad manager executable required.')
    python = c.ROOT / '.venv/bin/python'
    if not python.is_file() or not os.access(python, os.X_OK):
        raise ValueError('Existing checkout Python environment required.')
    manager_sha256 = p.sha(manager)
    output.mkdir(mode=0o700)
    documents, config, cache = (output / name for name in ('documents', 'config', 'cache'))
    prepared = plugin.prepare(documents)
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
    launch = output / 'Launch Autorouter.command'
    command = ['exec', shlex.quote(str(python)), '-B', shlex.quote(str(c.ROOT / 'scripts/install_gui.py')),
               '--launch', shlex.quote(str(output / 'install.json'))]
    payload = '#!/bin/sh\nset -eu\nunset PYTHONPATH PYTHONHOME KICAD_API_SOCKET KICAD_API_TOKEN\ncd ' + shlex.quote(str(c.ROOT)) + '\n' + ' '.join(command) + '\n'
    with launch.open('x') as stream: stream.write(payload)
    launch.chmod(0o700)
    (output / 'README.txt').write_text(README)
    immutable = {str(path.relative_to(output)): digest(path) for path in
        [launch, output / 'README.txt', output / 'initial-kicad_common.json', output / 'initial-kicad.json',
         *sorted(Path(prepared['plugin']).iterdir())]}
    if set(immutable) != IMMUTABLE_FILES: raise ValueError('Prepared launcher file population differs.')
    record = dict(schema=1, kind='local-gui-bootstrap-v1', root=str(output), checkout=str(c.ROOT),
                  manager=str(manager), manager_sha256=manager_sha256,
                  config_home=str(config), documents_home=str(documents), cache_home=str(cache),
                  tools=tools, installer_sha256=scripts, immutable_files=immutable,
                  installed_globally=False, standalone=False,
                  qualification='Prepared only; actual double-click/IPC/GUI behavior requires qualification.')
    with (output / 'install.json').open('x') as stream:
        json.dump(record, stream, indent=2); stream.write('\n')
    return record



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


def launch(manifest):
    manifest = canonical(Path(manifest).absolute())
    if manifest.name != 'install.json': raise ValueError('Exact prepared install.json required.')
    root = manifest.parent
    record = json.loads(pc.read_bytes(manifest, LIMIT))
    manager = c.CLI.with_name('kicad')
    if (type(record) is not dict or type(record.get('schema')) is not int or record.get('schema') != 1 or record.get('kind') != 'local-gui-bootstrap-v1'
            or record.get('root') != str(root) or record.get('checkout') != str(c.ROOT)
            or record.get('manager') != str(manager) or record.get('installed_globally') is not False
            or record.get('standalone') is not False):
        raise ValueError('Prepared launcher identity differs.')
    expected_homes = {name + '_home': str(root / name) for name in ('config', 'documents', 'cache')}
    if any(record.get(key) != value for key, value in expected_homes.items()):
        raise ValueError('Isolated KiCad homes escaped launcher directory.')
    for value in expected_homes.values():
        if not canonical(Path(value)).is_dir(): raise ValueError('Isolated KiCad home missing.')
    check_live_homes(expected_homes)
    if record.get('tools') != p.tool_manifest() or record.get('installer_sha256') != installer_pins():
        raise ValueError('Checkout or pinned tools changed; prepare a fresh launcher.')
    files = record.get('immutable_files')
    if type(files) is not dict or set(files) != IMMUTABLE_FILES: raise ValueError('Exact prepared launcher files required.')
    for relative, expected in files.items():
        path = canonical(root / relative)
        if root not in path.parents or not path.is_file() or digest(path) != expected:
            raise ValueError('Prepared launcher/plugin file changed.')
    if p.sha(manager) != record.get('manager_sha256') or not os.access(manager, os.X_OK):
        raise ValueError('Prepared KiCad manager changed.')
    env = {key: value for key, value in os.environ.items()
           if key not in ('PYTHONPATH', 'PYTHONHOME', 'KICAD_API_SOCKET', 'KICAD_API_TOKEN')}
    env.update(KICAD_CONFIG_HOME=record['config_home'], KICAD_DOCUMENTS_HOME=record['documents_home'],
               KICAD_CACHE_HOME=record['cache_home'], PYTHONNOUSERSITE='1', PYTHONDONTWRITEBYTECODE='1')
    require_closed_kicad()
    os.chdir(c.ROOT)
    os.execve(manager, [str(manager)], env)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--output'); mode.add_argument('--launch')
    args = parser.parse_args()
    try:
        if args.launch: launch(args.launch)
        else: print(json.dumps(prepare(args.output), indent=2))
    except (ValueError, p.Rejected, OSError) as exc:
        print('Launcher refused: ' + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__': raise SystemExit(main())
