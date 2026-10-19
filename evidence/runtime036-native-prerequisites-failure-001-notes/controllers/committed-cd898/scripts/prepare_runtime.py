#!/usr/bin/env python3
"""Build a curated local Mac runtime directory from exact committed source.

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


def prepare(source, destination, *, copy_local_engine=False, native_version=None):
    source = pv.canonical(Path(source).absolute())
    destination = pv.canonical(Path(destination).absolute())
    if os.path.lexists(destination):
        raise ValueError('Use a new runtime directory; existing paths are never overwritten.')
    parent = pv._directory(destination.parent)
    if parent.stat().st_uid != os.getuid():
        raise ValueError('Runtime destination parent must be owned by the current user.')
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
    record = {'schema': 1, 'kind': pv.KIND, 'root': str(destination),
        'build_source': {'kind': 'git-checkout', 'git_head': head, 'files_sha256': source_hashes},
        'immutable_files_sha256': {name: hashlib.sha256(raw).hexdigest() for name, raw in payloads.items()},
        'mutable_directories': list(pv.MUTABLE_DIRECTORIES), 'local_engine': engine}
    if native_version is not None:
        record.update(schema=2,native_version=native_version)
    with (destination / pv.MANIFEST).open('x') as stream:
        json.dump(record, stream, indent=2, sort_keys=True); stream.write('\n')
    identity = pv.source_identity(destination,
        {key: value for key, value in source_hashes.items() if key.startswith('autorouter/')})
    return {'root': str(destination), 'source_provenance': identity,
            'local_engine_copied': engine is not None, 'standalone': False, 'published': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument('--output', required=True)
    parser.add_argument('--copy-local-engine', action='store_true',
        help='Copy only the existing lock-matching project JAR, as a local artifact; never download.')
    parser.add_argument('--native-version',choices=['10.0.0','10.0.7'],
        help='Explicit committed native tool profile; requires separate qualification. No app is installed or changed.')
    args = parser.parse_args()
    try:
        result = prepare(args.source, args.output, copy_local_engine=args.copy_local_engine,
                         native_version=args.native_version)
        print(json.dumps(result, indent=2))
    except (ValueError, OSError) as exc:
        print('Runtime preparation refused: ' + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
