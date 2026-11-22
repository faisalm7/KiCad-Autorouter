#!/usr/bin/env python3
"""Prepare a curated local Mac runtime from committed source or a pinned artifact.

No downloads, virtual-environment copying, package/release publication or GUI
installation. Optional engine copying is a local-only existing-cache action.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from autorouter import provenance as pv

README = '''Local KiCad Autorouter runtime directory

This is a curated, path-bound Mac runtime directory, not a standalone app.
It requires the selected pinned KiCad app and Java 25.0.2 installation,
plus a new local Python 3.11 environment at .venv. Nothing is downloaded here.
The original toolchain.lock.json remains authoritative. If the local Freerouting
JAR was not explicitly copied at preparation, routing remains unavailable.

Create the environment with Python 3.11: python3.11 -m venv --copies .venv
Use copies so strict local artifact backups can retain regular interpreter files.
Check dependencies with: .venv/bin/python -B -m autorouter doctor
Prepare a NEW separate GUI launcher directory with:
  .venv/bin/python -B scripts/install_gui.py --output /absolute/new-launcher
Use that launcher's README for the save/close/route/review/export workflow.
Candidates remain separate from the saved source project. Native acceptance,
whole-project DRC, and physical/electrical review are distinct checks.

Keep this installed directory at its recorded path. A transported artifact is
installation input, not a runnable relocated installation. Import it into a new
directory with --install-existing --import-artifact and its exact manifest SHA256.
For a compatible current build, --host-paths-json can explicitly bind all four
known KiCad/Java roles to existing locations. Versions, architecture, hashes,
permissions and original lock requirements remain mandatory; no tool is downloaded.
Default installation preserves its recorded dependency locations. Run doctor and
the applicable Native qualification after installation; import alone proves neither.
The manifest records build-source HEAD, not a live Git checkout. Immutable
product files are checked afresh. Only .runs and .venv are reserved mutable
directories: their contents are not pinned by this manifest or copied from the
source checkout. Do not add research archives, datasets, .git or other files.
Use -B / PYTHONDONTWRITEBYTECODE=1; generated __pycache__ is outside the curated
population and will refuse. Legacy placement-guidance research modes require source-checkout proof and
remain separate. The selected-placement interface uses the curated contract,
Native observer and attributed MIT search; support is limited to its exact
qualified geometry. A changed product requires a new directory.

This local artifact is not publication authorization. A copied Freerouting JAR
remains an external local cache artifact; binary redistribution and release
compliance have not been qualified. GPL project license is retained in LICENSE.
Qualification and source history stay in the original source repository.
'''


INSTALL_RECEIPT = '.runs/install-existing-runtime-001.json'
SETUP_PEAK_BYTES = 512 * 1024**2


def _new_destination(destination):
    destination = pv.canonical(Path(destination).absolute())
    if os.path.lexists(destination):
        raise ValueError('Use a new runtime directory; existing paths are never overwritten.')
    parent = pv._directory(destination.parent)
    if parent.stat().st_uid != os.getuid():
        raise ValueError('Runtime destination parent must be owned by the current user.')
    return destination


def _write_runtime(engine_source, destination, payloads, record):
    # Both entry points use the same exclusive, bounded writer and engine copy.
    destination = _new_destination(destination)
    engine = record['local_engine']
    destination.mkdir(mode=0o700)
    # Saved-project inspection creates an owned job inside this private root.
    (destination / '.runs').mkdir(mode=0o700)
    for relative, raw in sorted(payloads.items()):
        path = destination / relative
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        with path.open('xb') as stream:
            stream.write(raw)
        path.chmod(0o600)
    if engine is not None:
        target = destination / pv.ENGINE_PATH; target.parent.mkdir(mode=0o700)
        # Descriptor-bounded source checks before/after copying, then target hash.
        with pv._regular(engine_source, pv.MAX_ENGINE_BYTES) as (incoming, size):
            with target.open('xb') as outgoing:
                count = 0
                while True:
                    chunk = incoming.read(min(1024**2, size - count + 1))
                    if not chunk:
                        break
                    count += len(chunk)
                    if count > size:
                        raise ValueError('Local engine changed during copy.')
                    outgoing.write(chunk)
                if count != size:
                    raise ValueError('Local engine changed during copy.')
        target.chmod(0o600)
        if pv.file_digest(target, pv.MAX_ENGINE_BYTES) != (engine['sha256'], engine['bytes']):
            raise ValueError('Copied local engine hash differs.')
    with (destination / pv.MANIFEST).open('x') as stream:
        json.dump(record, stream, indent=2, sort_keys=True); stream.write('\n')
    return pv._runtime_identity(destination, {key: value for key, value in
        record['immutable_files_sha256'].items() if key.startswith('autorouter/')})


def verified_host_tools(lock, version, host_paths, *, payloads):
    """Bind explicit locations to the same pinned binaries and permissions."""
    implementation = pv.canonical(Path(__file__).absolute()).parents[1]
    for name in ('autorouter/config.py', 'autorouter/provenance.py', 'autorouter/pipeline.py'):
        if payloads.get(name) != pv.read_bytes(implementation / name):
            raise ValueError('Host binding requires a compatible reviewed product build.')
    bound = pv.bound_tool_selection(lock, version, host_paths)
    for role, pin in {**bound['tools'], 'java': bound['java']}.items():
        path = Path(pin['path'])
        if (role != 'pcbnew' and not os.access(path, os.X_OK)
                or pv.file_digest(path, pv.MAX_ENGINE_BYTES) != (pin['sha256'], pin['bytes'])):
            raise ValueError(f'The pinned host tool changed or is unavailable: {role}.')
    return bound


def prepare(source, destination, *, copy_local_engine=False, native_version=None,
            freerouting_jar=None, host_paths=None):
    source = pv.canonical(Path(source).absolute())
    destination = _new_destination(destination)
    if copy_local_engine and freerouting_jar is not None:
        raise ValueError('Choose the project-local engine or one explicit Freerouting JAR.')
    head, snapshot = pv.committed_snapshot(source)
    source_hashes = {name: hashlib.sha256(raw).hexdigest() for name, raw in snapshot.items()}
    lock = json.loads(snapshot['toolchain.lock.json'])
    if native_version is not None:
        pv.native_selection(lock, native_version)
    engine = None
    engine_source = None
    if copy_local_engine or freerouting_jar is not None:
        engine_source = (source / pv.ENGINE_PATH if freerouting_jar is None else
                         pv.canonical(Path(freerouting_jar).absolute()))
        pin = lock.get('tools', {}).get('freerouting')
        if (type(pin) is not dict or set(pin) != {'path', 'sha256', 'bytes'}
                or pin['path'] != pv.ENGINE_PATH or type(pin['bytes']) is not int
                or not 0 < pin['bytes'] <= pv.MAX_ENGINE_BYTES
                or type(pin['sha256']) is not str or pv._DIGEST.fullmatch(pin['sha256']) is None):
            raise ValueError('Existing project-local engine pin required.')
        digest, size = pv.file_digest(engine_source, pv.MAX_ENGINE_BYTES)
        if pin != {'path': pv.ENGINE_PATH, 'sha256': digest, 'bytes': size}:
            raise ValueError('Existing local engine does not match original lock.')
        engine = {**pin, 'publication_authorized': False}
    payloads = {**snapshot, pv.README: README.encode('utf-8')}
    record = {'schema': 1, 'kind': pv.KIND, 'root': str(destination),
        'build_source': {'kind': 'git-checkout', 'git_head': head, 'files_sha256': source_hashes},
        'immutable_files_sha256': {name: hashlib.sha256(raw).hexdigest() for name, raw in payloads.items()},
        'mutable_directories': list(pv.MUTABLE_DIRECTORIES), 'local_engine': engine}
    if native_version is not None:
        record.update(schema=2,native_version=native_version)
    if host_paths is not None:
        native_version = native_version or '10.0.0'
        bound = verified_host_tools(lock, native_version, host_paths, payloads=payloads)
        host_paths = dict(host_paths)
        record.update(schema=3, native_version=native_version, host_paths=host_paths)
    identity = _write_runtime(engine_source, destination, payloads, record)
    if host_paths is not None and verified_host_tools(lock, native_version, host_paths, payloads=payloads) != bound:
        raise ValueError('Host tool bindings changed during setup.')
    return {'root': str(destination), 'source_provenance': identity,
            'local_engine_copied': engine is not None, 'standalone': False, 'published': False}


def installed_tool_paths(kicad_app, java_executable):
    """Resolve two supplied tool locations into the existing four pinned roles."""
    if kicad_app is None or java_executable is None:
        raise ValueError('Supply both --kicad-app and --java-executable to use different tool locations.')
    app = pv._directory(Path(kicad_app).absolute())
    if app.suffix != '.app':
        raise ValueError('Select the installed KiCad .app bundle.')
    java = pv.canonical(Path(java_executable).absolute())
    return {'java': str(java), **{role: str(app / 'Contents' / suffix)
                                 for role, suffix in pv._NATIVE_SUFFIXES.items()}}


def install_existing(source, destination, *, expected_manifest_sha256, import_artifact=False, host_paths=None):
    """Install a pinned artifact at a new root, without rebuilding its payload.

    Default mode requires a still-bound source; explicit import accepts only an
    externally manifest-pinned transported payload. Optional host paths bind known
    identical tools; no mutable state/venv/launcher/tool download or Native work.
    Failure retains the exclusive partial destination, which must not be reused.
    The receipt may remain on late refusal; it is a non-authoritative record,
    not a completion marker. Only a return means this installation finished.
    Fresh doctor and Native qualification remain separate required operations.
    """
    if (type(expected_manifest_sha256) is not str or
            pv._DIGEST.fullmatch(expected_manifest_sha256) is None):
        raise ValueError('Exact source runtime manifest SHA256 required.')
    if type(import_artifact) is not bool:raise ValueError('explicit artifact import boolean required')
    source = pv._directory(Path(source).absolute())
    destination = _new_destination(destination)
    if source in destination.parents or destination in source.parents:
        raise ValueError('Source and destination runtimes must be disjoint.')
    if source.stat().st_uid != os.getuid():
        raise ValueError('Source runtime must be owned by the current user.')
    raw_manifest = pv.read_bytes(source / pv.MANIFEST, pv.MAX_MANIFEST_BYTES)
    if hashlib.sha256(raw_manifest).hexdigest() != expected_manifest_sha256:
        raise ValueError('Source runtime manifest SHA256 differs.')
    try:
        record = json.loads(raw_manifest, object_pairs_hook=pv._strict_object,
            parse_constant=lambda value: (_ for _ in ()).throw(ValueError('Invalid JSON constant.')))
    except RecursionError as exc:
        raise ValueError('Malformed source runtime manifest.') from exc
    if type(record) is not dict:
        raise ValueError('Source runtime manifest object required.')
    expected = pv._file_map(record.get('immutable_files_sha256'))
    implementation = {name: value for name, value in expected.items()
                      if name.startswith('autorouter/')}
    # Deliberately no Git fallback, including if the source manifest disappears.
    def source_identity():
        if import_artifact:
            return pv.transport_identity(source,implementation,expected_manifest_sha256=expected_manifest_sha256)
        return pv._runtime_identity(source,implementation)
    identity = source_identity()
    if identity['manifest_sha256'] != expected_manifest_sha256:
        raise ValueError('Source runtime manifest changed.')
    if record.get('local_engine') is None:
        raise ValueError('Install-existing requires the verified local-only engine.')
    payloads = {}; total = 0
    for name, digest in sorted(expected.items()):
        raw = pv.read_bytes(source / name, min(pv.MAX_FILE_BYTES, pv.MAX_OWNED_BYTES - total))
        total += len(raw)
        if hashlib.sha256(raw).hexdigest() != digest:
            raise ValueError('Source runtime payload changed: ' + name)
        payloads[name] = raw
    installer = pv.canonical(Path(__file__).absolute())
    installer_pin = pv.file_digest(installer)

    def source_stable():
        if (pv.read_bytes(source / pv.MANIFEST, pv.MAX_MANIFEST_BYTES) != raw_manifest
                or source_identity() != identity
                or pv.file_digest(installer) != installer_pin):
            raise ValueError('Source runtime or installer changed during installation.')

    source_stable()
    # Payload/lock/source maps remain exact. Explicit locations are local metadata.
    installed_record = {**record, 'root': str(destination)}
    bound=None
    if host_paths is not None:
        version=record.get('native_version','10.0.0')
        bound=verified_host_tools(json.loads(payloads['toolchain.lock.json']),version,host_paths,payloads=payloads)
        installed_record.update(schema=3,native_version=version,host_paths=dict(host_paths))

    def bindings_stable():
        if bound is None:return
        fresh=verified_host_tools(json.loads(payloads['toolchain.lock.json']),bound['version'],host_paths,payloads=payloads)
        if fresh!=bound:raise ValueError('host tool bindings changed during installation')

    installed_identity = _write_runtime(source / pv.ENGINE_PATH, destination, payloads, installed_record)
    source_stable()
    receipt = {'schema': 1, 'kind': 'existing-runtime-installation-record-v1',
        'source_root': str(source), 'source_manifest_sha256': expected_manifest_sha256,
        'destination_root': str(destination),
        'destination_manifest_sha256': installed_identity['manifest_sha256'],
        'installer': {'path': str(installer), 'sha256': installer_pin[0], 'bytes': installer_pin[1]},
        'immutable_files': len(expected), 'local_engine': record['local_engine'],
        'record_is_authoritative': False, 'receipt_may_remain_on_refusal': True,
        'mutable_state_copied': False, 'venv_created': False, 'launcher_created': False,
        'native_qualification_performed': False, 'same_mac_dependency_locations_required': not bool(installed_record.get('host_paths')),
        'standalone': False, 'published': False,
        'artifact_import_mode':import_artifact,'explicit_host_paths':host_paths is not None}
    receipt_raw = (json.dumps(receipt, indent=2, sort_keys=True) + '\n').encode('utf-8')
    receipt_path = destination / INSTALL_RECEIPT
    with receipt_path.open('xb') as stream:
        stream.write(receipt_raw)
    receipt_path.chmod(0o600)
    source_stable()
    bindings_stable()
    if (pv._runtime_identity(destination, implementation) != installed_identity
            or pv.read_bytes(receipt_path, pv.MAX_MANIFEST_BYTES) != receipt_raw):
        raise ValueError('Installed runtime or receipt changed before completion.')
    return {'root': str(destination), 'source_provenance': installed_identity,
        'installation_receipt': str(receipt_path),
        'installation_receipt_sha256': hashlib.sha256(receipt_raw).hexdigest(),
        'local_engine_copied': True, 'standalone': False, 'published': False}


def prepare_workspace_launcher(root):
    """Finish a fresh local install using its own files and existing pinned tools."""
    from autorouter.runner import run
    from scripts.install_gui import APP_EXECUTABLE, SAVED_APP

    root = pv._directory(Path(root))
    jobs = pv._directory(root / '.runs')
    launcher = jobs / 'Copperpath Launcher'
    if os.path.lexists(root / '.venv') or os.path.lexists(launcher):
        raise ValueError('Launcher setup requires a fresh runtime without an existing environment or launcher.')
    setup = jobs / 'launcher-setup'
    setup.mkdir(mode=0o700)
    python = root / '.venv' / 'bin' / 'python'
    env = {name: value for name, value in os.environ.items()
           if name not in ('PYTHONPATH', 'PYTHONHOME', 'KICAD_API_SOCKET', 'KICAD_API_TOKEN')}
    env.update(PYTHONDONTWRITEBYTECODE='1', PYTHONNOUSERSITE='1')
    commands = (
        ('environment', [sys.executable, '-B', '-m', 'venv', '--copies', '--without-pip', str(root / '.venv')]),
        ('doctor', [str(python), '-B', '-m', 'autorouter', 'doctor']),
        ('launcher', [str(python), '-B', 'scripts/install_gui.py', '--output', str(launcher)]),
    )
    for stage, argv in commands:
        log = setup / (stage + '.log')
        outcome = run(argv, cwd=root, log=log, timeout=55, env=env,
                      max_log_bytes=256 * 1024, max_group_rss_bytes=1024**3, max_workdir_bytes=SETUP_PEAK_BYTES)
        with (setup / (stage + '.json')).open('x') as stream:
            json.dump(outcome, stream, indent=2); stream.write('\n')
        if (outcome['status'] != 'success' or outcome['exit_code'] != 0
                or outcome['log_truncated'] or not outcome['cleanup_complete']):
            raise ValueError('Local setup stopped at ' + stage + '. Details are in ' + str(log))
        if stage == 'doctor':
            checked = json.loads(pv.read_bytes(log, 256 * 1024))
            if type(checked) is not dict or checked.get('ready') is not True:
                raise ValueError('Installed dependencies did not pass doctor. Details are in ' + str(log))
    prepared = json.loads(pv.read_bytes(launcher / 'install.json', 1024 * 1024))
    if APP_EXECUTABLE in prepared['immutable_files']:
        app = pv.canonical(launcher / SAVED_APP)
        executable = pv.canonical(launcher / APP_EXECUTABLE)
        if not app.is_dir():
            raise ValueError('Saved-project application is missing.')
    else:  # An older verified artifact prepares its original command launcher.
        app = executable = pv.canonical(launcher / 'Open Saved Project.command')
    if not executable.is_file() or not os.access(executable, os.X_OK):
        raise ValueError('Saved-project launcher is missing or unavailable.')
    return {'workspace_launcher': str(app), 'setup_records': str(setup)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument('--output', required=True)
    parser.add_argument('--copy-local-engine', action='store_true',
        help='Copy only the existing lock-matching project JAR, as a local artifact; never download.')
    parser.add_argument('--freerouting-jar',
        help='Use an existing lock-matching Freerouting JAR at the supplied path for first setup; never download.')
    parser.add_argument('--native-version',choices=['10.0.0','10.0.7'],
        help='Explicit committed native tool profile; requires separate qualification. No app is installed or changed.')
    parser.add_argument('--install-existing', action='store_true',
        help='Install a still-bound, manifest-pinned local runtime at a new root; no rebuild.')
    parser.add_argument('--import-artifact',action='store_true',help='Explicitly import manifest-pinned transported source; installed runtime remains root-bound.')
    parser.add_argument('--host-paths-json',help='Explicit bounded JSON object with all four existing known tool role locations; no downloads.')
    parser.add_argument('--kicad-app', help='Existing pinned KiCad .app bundle at this Mac’s location. Pair with --java-executable.')
    parser.add_argument('--java-executable', help='Existing pinned Java executable. Pair with --kicad-app.')
    parser.add_argument('--expected-manifest-sha256',
        help='Required source manifest SHA256 for --install-existing only.')
    parser.add_argument('--with-launcher', action='store_true',
        help='Create a fresh local Python environment, check dependencies and prepare the saved-project launcher on macOS.')
    args = parser.parse_args()
    try:
        direct_paths = args.kicad_app is not None or args.java_executable is not None
        if direct_paths and args.host_paths_json is not None:
            raise ValueError('Choose either the KiCad and Java paths or --host-paths-json.')
        if args.install_existing and (args.copy_local_engine or args.freerouting_jar is not None
                                      or args.native_version is not None):
            raise ValueError('Install-existing preserves engine and native selection; build flags refuse.')
        host_paths = installed_tool_paths(args.kicad_app, args.java_executable) if direct_paths else None
        if args.with_launcher:
            from scripts.backup import BackupError, require_headroom

            if sys.platform != 'darwin' or sys.version_info[:2] != (3, 11):
                raise ValueError('Launcher preparation requires macOS and the existing Python 3.11.')
            if not args.install_existing and not (args.copy_local_engine or args.freerouting_jar is not None):
                raise ValueError('Launcher preparation requires the existing pinned engine. Give its location with --freerouting-jar.')
            try:
                require_headroom(_new_destination(args.output).parent, SETUP_PEAK_BYTES, 'fresh local workspace setup')
            except BackupError as exc:
                raise ValueError(str(exc)) from exc
        if args.install_existing:
            if args.host_paths_json is not None:
                host_paths=json.loads(pv.read_bytes(Path(args.host_paths_json).absolute(),64*1024),
                    object_pairs_hook=pv._strict_object,
                    parse_constant=lambda value: (_ for _ in ()).throw(ValueError('invalid JSON constant')))
            result = install_existing(args.source, args.output,
                expected_manifest_sha256=args.expected_manifest_sha256,
                import_artifact=args.import_artifact,host_paths=host_paths)
        else:
            if args.expected_manifest_sha256 is not None or args.import_artifact or args.host_paths_json is not None:
                raise ValueError('Artifact pin/import/JSON host paths require --install-existing.')
            result = prepare(args.source, args.output, copy_local_engine=args.copy_local_engine,
                             native_version=args.native_version, freerouting_jar=args.freerouting_jar,
                             host_paths=host_paths)
        if args.with_launcher:
            result.update(prepare_workspace_launcher(result['root']))
        print(json.dumps(result, indent=2))
    except (ValueError, OSError) as exc:
        print('Runtime preparation refused: ' + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
