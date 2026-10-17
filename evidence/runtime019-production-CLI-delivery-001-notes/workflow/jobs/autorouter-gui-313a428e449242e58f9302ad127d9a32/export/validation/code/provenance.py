"""Fresh source identity for exact Git checkouts or curated local runtimes.

A distribution manifest is an integrity record, not a signature or independent
proof of its declared source commit. Mutable job/venv contents are not attested.
No pipeline import: this provider is used by the pipeline itself.
"""
from __future__ import annotations

from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess

MANIFEST = 'runtime-distribution.json'
KIND = 'runtime-directory-v1'
README = 'RUNTIME_README.txt'
FIXED_FILES = frozenset(('LICENSE', 'toolchain.lock.json',
    'scripts/install_gui.py', 'scripts/prepare_gui_plugin.py'))
MUTABLE_DIRECTORIES = ('.runs', '.venv')
ENGINE_PATH = '.tools/freerouting-2.5.0.jar'
MAX_FILE_BYTES = 2 * 1024**2
MAX_OWNED_BYTES = 16 * 1024**2
MAX_ENGINE_BYTES = 128 * 1024**2
MAX_FILES = 256
MAX_MANIFEST_BYTES = 256 * 1024
_DIGEST = re.compile(r'[0-9a-f]{64}')
_HEAD = re.compile(r'[0-9a-f]{40}')
_MODULE = re.compile(r'autorouter/[A-Za-z_][A-Za-z_0-9]*\.py')


def canonical(path):
    """Require a real absolute path, including every existing ancestor."""
    path = Path(path)
    if (not path.is_absolute() or '..' in path.parts or path.resolve() != path
            or any(item.is_symlink() for item in (path, *path.parents))):
        raise ValueError('runtime provenance requires canonical paths without symlinks')
    return path


def _directory(path):
    path = canonical(path)
    if not stat.S_ISDIR(path.lstat().st_mode):
        raise ValueError('runtime provenance requires a real directory')
    return path


def _identity(info):
    return (info.st_dev, info.st_ino, info.st_mode, info.st_nlink,
            info.st_size, info.st_mtime_ns, info.st_ctime_ns)


@contextmanager
def _regular(path, limit):
    path = canonical(path)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as stream:
        before = os.fstat(stream.fileno())
        if (not stat.S_ISREG(before.st_mode) or before.st_nlink != 1
                or not 0 <= before.st_size <= limit):
            raise ValueError('runtime provenance requires bounded single-link regular files')
        yield stream, before.st_size
        if (_identity(before) != _identity(os.fstat(stream.fileno()))
                or _identity(before) != _identity(path.lstat())):
            raise ValueError('runtime provenance file changed while reading')


def read_bytes(path, limit=MAX_FILE_BYTES):
    """Small cycle-free bounded reader; placement_clearance imports pipeline."""
    with _regular(path, limit) as (stream, size):
        raw = stream.read(size + 1)
        if len(raw) != size:
            raise ValueError('runtime provenance file changed or exceeded read bound')
    return raw


def file_digest(path, limit=MAX_FILE_BYTES):
    with _regular(path, limit) as (stream, size):
        digest = hashlib.sha256(); count = 0
        while True:
            chunk = stream.read(min(1024**2, size - count + 1))
            if not chunk:
                break
            count += len(chunk)
            if count > size:
                raise ValueError('runtime provenance file exceeded read bound')
            digest.update(chunk)
        if count != size:
            raise ValueError('runtime provenance file changed while hashing')
    return digest.hexdigest(), size


def module_paths(root):
    """Only inspect the direct product module directory, never the archive."""
    directory = _directory(Path(root) / 'autorouter'); names = []
    with os.scandir(directory) as entries:
        for index, item in enumerate(entries):
            if index >= MAX_FILES * 2:
                raise ValueError('runtime module entry ceiling exceeded')
            if item.name.endswith('.py'):
                relative = 'autorouter/' + item.name
                if _MODULE.fullmatch(relative) is None:
                    raise ValueError('noncanonical runtime module name')
                names.append(relative)
                if len(names) > MAX_FILES - len(FIXED_FILES) - 1:
                    raise ValueError('runtime module population ceiling exceeded')
    if 'autorouter/__init__.py' not in names or 'autorouter/provenance.py' not in names:
        raise ValueError('complete runtime module population required')
    return tuple(sorted(names))


def owned_snapshot(root):
    """Capture only selected product bytes, with finite file/aggregate bounds."""
    root = _directory(root); result = {}; total = 0
    for relative in sorted((*FIXED_FILES, *module_paths(root))):
        raw = read_bytes(root / relative, min(MAX_FILE_BYTES, MAX_OWNED_BYTES - total))
        result[relative] = raw; total += len(raw)
    return result


def _git(root, *arguments, limit=256 * 1024):
    # Inherited GIT_DIR/WORK_TREE/config redirection must not supply identity.
    env = {key: value for key, value in os.environ.items() if not key.startswith('GIT_')}
    env.update(GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull)
    try:
        result = subprocess.run(['git', '--no-optional-locks', '-C', str(root), *arguments],
            capture_output=True, check=True, timeout=5, env=env)
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raise ValueError('exact local Git source identity unavailable') from exc
    if len(result.stdout) > limit or len(result.stderr) > 64 * 1024:
        raise ValueError('Git source identity output ceiling exceeded')
    return result.stdout


def git_head(root):
    root = _directory(root)
    # A parent checkout must never lend its identity to an unpacked artifact.
    _directory(root / '.git')
    if _git(root, 'rev-parse', '--show-toplevel').decode().strip() != str(root):
        raise ValueError('runtime source is not the exact local Git top-level')
    head = _git(root, 'rev-parse', '--verify', 'HEAD').decode().strip()
    if _HEAD.fullmatch(head) is None:
        raise ValueError('invalid Git source HEAD')
    return head


def committed_snapshot(root):
    """Builder-only exact HEAD/index/worktree proof for the curated population."""
    root = _directory(root)
    if os.path.lexists(root / MANIFEST):
        raise ValueError('build source must be a source checkout, not a runtime artifact')
    head = git_head(root); snapshot = owned_snapshot(root); paths = sorted(snapshot)
    if _git(root, 'status', '--porcelain=v1', '--untracked-files=all', '--', *paths):
        raise ValueError('commit exact selected runtime sources before building')
    # Derive HEAD's complete product population independently of the worktree.
    # Restricting the pathspec to currently existing files would hide deletions.
    rows = _git(root, 'ls-tree', '-r', '-z', head, '--', 'autorouter',
                *sorted(FIXED_FILES)).split(b'\0')
    blobs = {}
    for row in rows:
        if not row:
            continue
        metadata, name = row.split(b'\t', 1); mode, kind, object_id = metadata.split(b' ')
        relative = name.decode('utf-8')
        if relative not in FIXED_FILES:
            if not (relative.startswith('autorouter/') and relative.count('/') == 1
                    and relative.endswith('.py')):
                continue
            if _MODULE.fullmatch(relative) is None:
                raise ValueError('noncanonical committed runtime module name')
        if mode not in (b'100644', b'100755') or kind != b'blob':
            raise ValueError('selected source must be an ordinary committed blob')
        blobs[relative] = object_id.decode('ascii')
    if set(blobs) != set(snapshot):
        raise ValueError('complete selected runtime population must exist at source HEAD')
    for relative, raw in snapshot.items():
        object_id = blobs[relative]
        size = _git(root, 'cat-file', '-s', object_id, limit=64).decode().strip()
        if not size.isdigit() or int(size) != len(raw):
            raise ValueError('selected source size differs from HEAD blob')
        if _git(root, 'cat-file', 'blob', object_id, limit=MAX_FILE_BYTES) != raw:
            raise ValueError('selected source bytes differ from HEAD blob')
    if git_head(root) != head or owned_snapshot(root) != snapshot:
        raise ValueError('selected source changed during runtime preparation')
    return head, snapshot


def _strict_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate runtime manifest key')
        result[key] = value
    return result


def _file_map(value):
    if type(value) is not dict or not 1 <= len(value) <= MAX_FILES:
        raise ValueError('bounded complete runtime file map required')
    for name, digest in value.items():
        if (type(name) is not str or name not in FIXED_FILES | {README}
                and _MODULE.fullmatch(name) is None):
            raise ValueError('unexpected or escaping runtime file path')
        if type(digest) is not str or _DIGEST.fullmatch(digest) is None:
            raise ValueError('invalid runtime file digest')
    return value


def _runtime_identity(root, implementation):
    raw = read_bytes(root / MANIFEST, MAX_MANIFEST_BYTES)
    try:
        record = json.loads(raw, object_pairs_hook=_strict_object,
            parse_constant=lambda value: (_ for _ in ()).throw(ValueError('invalid JSON constant')))
    except (UnicodeError, json.JSONDecodeError, RecursionError) as exc:
        raise ValueError('malformed runtime distribution manifest') from exc
    if (type(record) is not dict or set(record) != {'schema', 'kind', 'root', 'build_source',
            'immutable_files_sha256', 'mutable_directories', 'local_engine'}
            or type(record['schema']) is not int or record['schema'] != 1
            or record['kind'] != KIND or record['root'] != str(root)
            or record['mutable_directories'] != list(MUTABLE_DIRECTORIES)):
        raise ValueError('runtime distribution identity or schema differs')
    expected = _file_map(record['immutable_files_sha256'])
    modules = module_paths(root)
    if set(expected) != FIXED_FILES | {README} | set(modules):
        raise ValueError('runtime immutable file population differs')
    build = record['build_source']
    if (type(build) is not dict or set(build) != {'kind', 'git_head', 'files_sha256'}
            or build['kind'] != 'git-checkout' or type(build['git_head']) is not str
            or _HEAD.fullmatch(build['git_head']) is None
            or _file_map(build['files_sha256']) != {key: value for key, value in expected.items() if key != README}):
        raise ValueError('runtime build-source provenance differs')
    engine = record['local_engine']
    if engine is not None:
        if (type(engine) is not dict or set(engine) != {'path', 'sha256', 'bytes', 'publication_authorized'}
                or engine['path'] != ENGINE_PATH or type(engine['sha256']) is not str
                or _DIGEST.fullmatch(engine['sha256']) is None or type(engine['bytes']) is not int
                or not 0 < engine['bytes'] <= MAX_ENGINE_BYTES or engine['publication_authorized'] is not False):
            raise ValueError('invalid local-only engine record')
    allowed = {'autorouter', 'scripts', 'LICENSE', 'toolchain.lock.json', README, MANIFEST,
               *MUTABLE_DIRECTORIES, *({'.tools'} if engine is not None else set())}
    with os.scandir(root) as entries:
        for index, item in enumerate(entries):
            if index >= len(allowed) or item.name not in allowed or item.is_symlink():
                raise ValueError('unexpected or linked runtime root entry')
            if item.name in MUTABLE_DIRECTORIES:
                _directory(Path(item.path))  # Contents are explicitly mutable/unattested.
    for folder, names in [('autorouter', {Path(name).name for name in modules}),
                          ('scripts', {'install_gui.py', 'prepare_gui_plugin.py'}),
                          *([('.tools', {Path(ENGINE_PATH).name})] if engine is not None else [])]:
        with os.scandir(_directory(root / folder)) as entries:
            actual = set()
            for index, item in enumerate(entries):
                if index >= MAX_FILES or item.name not in names or item.is_symlink():
                    raise ValueError('runtime directory file population differs')
                actual.add(item.name)
            if actual != names:
                raise ValueError('runtime directory missing declared files')
    total = 0
    for relative, digest in expected.items():
        current, size = file_digest(root / relative, min(MAX_FILE_BYTES, MAX_OWNED_BYTES - total))
        total += size
        if current != digest:
            raise ValueError('runtime immutable file changed: ' + relative)
    actual_implementation = {relative: expected[relative] for relative in modules}
    if implementation != actual_implementation:
        raise ValueError('runtime implementation census differs')
    if engine is not None:
        if file_digest(root / ENGINE_PATH, MAX_ENGINE_BYTES) != (engine['sha256'], engine['bytes']):
            raise ValueError('local runtime engine changed')
        lock = json.loads(read_bytes(root / 'toolchain.lock.json'))
        if lock.get('tools', {}).get('freerouting') != {key: engine[key] for key in ('path', 'sha256', 'bytes')}:
            raise ValueError('local runtime engine differs from original tool lock')
    return {'kind': KIND, 'git_head': build['git_head'], 'build_source': build,
            'manifest_sha256': hashlib.sha256(raw).hexdigest()}


def source_identity(root: Path, implementation: dict[str, str]) -> dict:
    """Check current bytes on every call; never inherit an ancestor Git HEAD.

    Source checkouts retain their historical dirty-worktree behavior. Builders
    separately require the selected product files to match committed HEAD blobs.
    """
    root = _directory(root)
    if os.path.lexists(root / MANIFEST):
        return _runtime_identity(root, implementation)
    head = git_head(root)
    modules = module_paths(root)
    actual = {relative: file_digest(root / relative)[0] for relative in modules}
    if implementation != actual:
        raise ValueError('live source implementation census differs')
    return {'kind': 'git-checkout', 'git_head': head, 'build_source': None, 'manifest_sha256': None}
