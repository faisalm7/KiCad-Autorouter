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

Keep this directory and pinned external applications at their prepared paths.
The manifest records build-source HEAD, not a live Git checkout. Immutable
product files are checked afresh. Only .runs and .venv are reserved mutable
directories: their contents are not pinned by this manifest or copied from the
source checkout. Do not add research archives, datasets, .git or other files.
Use -B / PYTHONDONTWRITEBYTECODE=1; generated __pycache__ is outside the curated
population and will refuse. Placement-guidance modes require source checkout
proof and remain unsupported here. A changed product requires a new directory.

This local artifact is not publication authorization. A copied Freerouting JAR
remains an external local cache artifact; binary redistribution and release
compliance have not been qualified. GPL project license is retained in LICENSE.
Qualification and source history stay in the original source repository.
'''


INSTALL_RECEIPT = '.runs/install-existing-runtime-001.json'


def _new_destination(destination):
    destination = pv.canonical(Path(destination).absolute())
    if os.path.lexists(destination):
        raise ValueError('Use a new runtime directory; existing paths are never overwritten.')
    parent = pv._directory(destination.parent)
    if parent.stat().st_uid != os.getuid():
        raise ValueError('Runtime destination parent must be owned by the current user.')
    return destination


def _write_runtime(source, destination, payloads, record):
    # Both entry points use the same exclusive, bounded writer and engine copy.
    destination = _new_destination(destination)
    engine = record['local_engine']
    destination.mkdir(mode=0o700)
    for relative, raw in sorted(payloads.items()):
        path = destination / relative
        path.parent.mkdir(mode=0o700, exist_ok=True)
        with path.open('xb') as stream:
            stream.write(raw)
        path.chmod(0o600)
    if engine is not None:
        target = destination / pv.ENGINE_PATH; target.parent.mkdir(mode=0o700)
        # Descriptor-bounded source checks before/after copying, then target hash.
        with pv._regular(source / pv.ENGINE_PATH, pv.MAX_ENGINE_BYTES) as (incoming, size):
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


def prepare(source, destination, *, copy_local_engine=False, native_version=None):
    source = pv.canonical(Path(source).absolute())
    destination = _new_destination(destination)
    head, snapshot = pv.committed_snapshot(source)
    source_hashes = {name: hashlib.sha256(raw).hexdigest() for name, raw in snapshot.items()}
    if native_version is not None:
        from autorouter.config import native_selection
        native_selection(json.loads(snapshot['toolchain.lock.json']),native_version)
    engine = None
    if copy_local_engine:
        lock = json.loads(snapshot['toolchain.lock.json'])
        pin = lock.get('tools', {}).get('freerouting')
        if (type(pin) is not dict or set(pin) != {'path', 'sha256', 'bytes'}
                or pin['path'] != pv.ENGINE_PATH or type(pin['bytes']) is not int
                or not 0 < pin['bytes'] <= pv.MAX_ENGINE_BYTES
                or type(pin['sha256']) is not str or pv._DIGEST.fullmatch(pin['sha256']) is None):
            raise ValueError('Existing project-local engine pin required.')
        digest, size = pv.file_digest(source / pv.ENGINE_PATH, pv.MAX_ENGINE_BYTES)
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
    identity = _write_runtime(source, destination, payloads, record)
    return {'root': str(destination), 'source_provenance': identity,
            'local_engine_copied': engine is not None, 'standalone': False, 'published': False}


def install_existing(source, destination, *, expected_manifest_sha256):
    """Install a still-bound, pinned artifact at a new root, without rebuilding.

    This does not repair a moved artifact, copy mutable state, create a venv or
    launcher, relocate external dependencies, or perform Native qualification.
    Failure retains the exclusive partial destination, which must not be reused.
    The receipt may remain on late refusal; it is a non-authoritative record,
    not a completion marker. Only a return means this installation finished.
    Fresh doctor and Native qualification remain separate required operations.
    """
    if (type(expected_manifest_sha256) is not str or
            pv._DIGEST.fullmatch(expected_manifest_sha256) is None):
        raise ValueError('Exact source runtime manifest SHA256 required.')
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
    identity = pv._runtime_identity(source, implementation)
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
                or pv._runtime_identity(source, implementation) != identity
                or pv.file_digest(installer) != installer_pin):
            raise ValueError('Source runtime or installer changed during installation.')

    source_stable()
    # Preserve schema, source HEAD, lock/version, maps and engine record exactly.
    installed_record = {**record, 'root': str(destination)}
    installed_identity = _write_runtime(source, destination, payloads, installed_record)
    source_stable()
    receipt = {'schema': 1, 'kind': 'existing-runtime-installation-record-v1',
        'source_root': str(source), 'source_manifest_sha256': expected_manifest_sha256,
        'destination_root': str(destination),
        'destination_manifest_sha256': installed_identity['manifest_sha256'],
        'installer': {'path': str(installer), 'sha256': installer_pin[0], 'bytes': installer_pin[1]},
        'immutable_files': len(expected), 'local_engine': record['local_engine'],
        'record_is_authoritative': False, 'receipt_may_remain_on_refusal': True,
        'mutable_state_copied': False, 'venv_created': False, 'launcher_created': False,
        'native_qualification_performed': False, 'same_mac_dependency_locations_required': True,
        'standalone': False, 'published': False}
    receipt_raw = (json.dumps(receipt, indent=2, sort_keys=True) + '\n').encode('utf-8')
    (destination / '.runs').mkdir(mode=0o700)
    receipt_path = destination / INSTALL_RECEIPT
    with receipt_path.open('xb') as stream:
        stream.write(receipt_raw)
    receipt_path.chmod(0o600)
    source_stable()
    if (pv._runtime_identity(destination, implementation) != installed_identity
            or pv.read_bytes(receipt_path, pv.MAX_MANIFEST_BYTES) != receipt_raw):
        raise ValueError('Installed runtime or receipt changed before completion.')
    return {'root': str(destination), 'source_provenance': installed_identity,
        'installation_receipt': str(receipt_path),
        'installation_receipt_sha256': hashlib.sha256(receipt_raw).hexdigest(),
        'local_engine_copied': True, 'standalone': False, 'published': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument('--output', required=True)
    parser.add_argument('--copy-local-engine', action='store_true',
        help='Copy only the existing lock-matching project JAR, as a local artifact; never download.')
    parser.add_argument('--native-version',choices=['10.0.0','10.0.7'],
        help='Explicit committed native tool profile; requires separate qualification. No app is installed or changed.')
    parser.add_argument('--install-existing', action='store_true',
        help='Install a still-bound, manifest-pinned local runtime at a new root; no rebuild.')
    parser.add_argument('--expected-manifest-sha256',
        help='Required source manifest SHA256 for --install-existing only.')
    args = parser.parse_args()
    try:
        if args.install_existing:
            if args.copy_local_engine or args.native_version is not None:
                raise ValueError('Install-existing preserves engine and native selection; build flags refuse.')
            result = install_existing(args.source, args.output,
                expected_manifest_sha256=args.expected_manifest_sha256)
        else:
            if args.expected_manifest_sha256 is not None:
                raise ValueError('--expected-manifest-sha256 requires --install-existing.')
            result = prepare(args.source, args.output, copy_local_engine=args.copy_local_engine,
                             native_version=args.native_version)
        print(json.dumps(result, indent=2))
    except (ValueError, OSError) as exc:
        print('Runtime preparation refused: ' + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
