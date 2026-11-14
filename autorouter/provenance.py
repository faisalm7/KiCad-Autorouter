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
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess

MANIFEST = 'runtime-distribution.json'
KIND = 'runtime-directory-v1'
README = 'RUNTIME_README.txt'
# Deliberate runtime reuse, not a recursive copy of experiments or their data.
# Keep these qualified pure modules/native reader at their existing paths so
# historical producers and their exact code pins remain unchanged.
PLACEMENT_FILES = frozenset((
    'experiments/placement_native_evidence.py',  # bounded retained-identity helpers only
    'experiments/placement_native_proposal_v1/__init__.py',
    'experiments/placement_native_proposal_v1/contract.py',
    'experiments/placement_native_proposal_v1/ordinary.py',
    'experiments/placement_native_proposal_v1/ordinary_native.py',
    'experiments/placement_native_proposal_v1/engineering_metadata.py',
    'experiments/placement_native_proposal_v1/worker.py',
    'experiments/native_annotation_geometry_v1/__init__.py',
    'experiments/native_annotation_geometry_v1/ring.py',
    'experiments/native_annotation_geometry_v1/native.py',
    'experiments/selected_unselected_plane_v1/policy.py',
    'experiments/constrained_placement_v1/__init__.py',
    'experiments/constrained_placement_v1/constraints.py',
    'experiments/constrained_placement_v1/prototype.py',
    'experiments/constrained_placement_v1/upstream.json',
    'experiments/constrained_placement_v1/vendor/__init__.py',
    'experiments/constrained_placement_v1/vendor/LICENSE',
    *('experiments/constrained_placement_v1/vendor/' + name + '.py'
      for name in ('anneal', 'blocks', 'edge', 'electrical', 'geom', 'metrics', 'model', 'nets')),
))
FIXED_FILES = frozenset(('LICENSE', 'toolchain.lock.json',
    'scripts/install_gui.py', 'scripts/prepare_gui_plugin.py')) | PLACEMENT_FILES
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



_NATIVE_SUFFIXES = {
    'kicad_cli': 'MacOS/kicad-cli',
    'kicad_python': 'Frameworks/Python.framework/Versions/3.9/bin/python3.9',
    'pcbnew': 'Frameworks/Python.framework/Versions/3.9/lib/python3.9/site-packages/_pcbnew.so',
}
# Exact observed binaries, not a version range or arbitrary tool override.
_NATIVE_HASHES = {
    '10.0.0': ('998aed348399000335b0e29edf747daa18819f2ac417bac066f4216fdc5d90d1',
               '4e2b71c03ac808a6149f4ab7282b8225b3e2ea6d2b9d8710052c355fe08bb813',
               'a7197ed790dbe2f8ab1ef71fc95774069e27eed1142c6fd5d373aec00daf5219'),
    '10.0.7': ('0b9d96dbdac9517e7d85833f926fee07a563549ffe2c55670147bff3f562d01f',
               'fd8c2fa5393bebb9be6789dab8583acee6c5cff90d42696e8c1dbcabe02ec39f',
               '610ae51927809192be637d0de03c32d006332638e2272cbf11a553fe65c75f6e'),
}


def _native_roles(tools, version):
    if type(tools) is not dict or set(tools) != set(_NATIVE_SUFFIXES):
        raise ValueError('exact three native roles required')
    result = {}; bundles = set()
    for (role, suffix), expected_hash in zip(_NATIVE_SUFFIXES.items(), _NATIVE_HASHES[version]):
        pin = tools[role]
        if (type(pin) is not dict or set(pin) != {'path', 'sha256', 'bytes'}
                or type(pin['path']) is not str or type(pin['sha256']) is not str
                or pin['sha256'] != expected_hash or type(pin['bytes']) is not int
                or not 0 < pin['bytes'] <= 128 * 1024**2):
            raise ValueError('known native role hash and bounded positive integer bytes required')
        value = pin['path']; path = PurePosixPath(value); tail = PurePosixPath(suffix).parts
        if (not path.is_absolute() or str(path) != value or value.startswith('//')
                or '\\' in value or any(ord(char) < 32 or ord(char) == 127 for char in value)
                or '..' in path.parts or path.parts[-len(tail):] != tail):
            raise ValueError('canonical absolute native role path and exact suffix required')
        bundle = path.parents[len(tail)-1]
        if bundle.name != 'Contents' or bundle.parent.suffix != '.app':
            raise ValueError('native role must belong to a KiCad app Contents bundle')
        bundles.add(bundle); result[role] = dict(pin)
    if len(bundles) != 1:
        raise ValueError('native roles must share one app Contents bundle')
    return result


def native_selection(lock, version=None):
    """Pure selection of known pins; callers still verify actual tool bytes."""
    if type(lock) is not dict or lock.get('kicad') != '10.0.0':
        raise ValueError('original exact10.0.0 default lock required')
    tools = lock.get('tools')
    if type(tools) is not dict or set(tools) != set(_NATIVE_SUFFIXES) | {'java','freerouting'}:
        raise ValueError('known default tool roles required')
    choices = {'10.0.0': _native_roles({role: tools[role] for role in _NATIVE_SUFFIXES}, '10.0.0')}
    if 'native_profiles' in lock:
        profiles = lock['native_profiles']
        if type(profiles) is not dict or set(profiles) != {'10.0.7'}:
            raise ValueError('only the exact optional10.0.7 native profile is supported')
        choices['10.0.7'] = _native_roles(profiles['10.0.7'], '10.0.7')
    selected = lock['kicad'] if version is None else version
    if type(selected) is not str or selected not in choices:
        raise ValueError('known explicitly pinned native version required')
    return {'version': selected, 'tools': {role: dict(pin) for role, pin in choices[selected].items()}}


def _binding_path(value, *, check_aliases=True):
    if (type(value) is not str or not value or '\\' in value
            or any(ord(char)<32 or ord(char)==127 for char in value)):
        raise ValueError('canonical absolute host tool path required')
    path=PurePosixPath(value)
    if (not path.is_absolute() or str(path)!=value or value.startswith('//')
            or any(part in ('.','..') for part in value.split('/'))):
        raise ValueError('canonical absolute host tool path required')
    local=Path(value)
    if check_aliases and (local.resolve()!=local or any(p.is_symlink() for p in (local,*local.parents))):
        raise ValueError('host tool alias refused')
    return value


def bound_tool_selection(lock, version, paths):
    """Pure known profile plus explicit locations; actual bytes remain mandatory.

    Empty paths preserves original role locations. Nonempty input must specify
    all four roles, preventing partial/default location combinations.
    """
    return _bound_tool_selection(lock,version,paths,check_aliases=True)


def _bound_tool_selection(lock, version, paths, *, check_aliases):
    """Recorded transport locations are lexical provenance, never live tools."""
    selected=native_selection(lock,version)
    roles=set(_NATIVE_SUFFIXES)|{'java'}
    if type(paths) is not dict or (paths and set(paths)!=roles):
        raise ValueError('exact four host tool locations required')
    java=lock['tools']['java']
    if (type(java) is not dict or set(java)!={'path','sha256','bytes'}
            or type(java['sha256']) is not str or _DIGEST.fullmatch(java['sha256']) is None
            or type(java['bytes']) is not int or not 0<java['bytes']<=MAX_ENGINE_BYTES):
        raise ValueError('original pinned Java role required')
    pins={**selected['tools'],'java':dict(java)}
    for role,pin in pins.items():
        pin['path']=_binding_path(paths[role] if paths else pin['path'],check_aliases=check_aliases)
    native=_native_roles({role:pins[role] for role in _NATIVE_SUFFIXES},selected['version'])
    return {'version':selected['version'],'tools':native,'java':pins['java']}


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


def _git(root, *arguments, limit=256 * 1024, input_bytes=None):
    if input_bytes is not None and (type(input_bytes) is not bytes
                                   or len(input_bytes) > MAX_FILES * 65):
        raise ValueError('Git source identity input ceiling exceeded')
    # Inherited redirection and local replacement refs must not supply identity.
    env = {key: value for key, value in os.environ.items() if not key.startswith('GIT_')}
    env.update(GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull)
    try:
        result = subprocess.run(['git', '--no-optional-locks', '--no-replace-objects',
                                 '-C', str(root), *arguments],
            input=input_bytes, capture_output=True, check=True, timeout=5, env=env)
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
        oid = object_id.decode('ascii')
        if _HEAD.fullmatch(oid) is None or relative in blobs:
            raise ValueError('invalid or duplicate committed source blob identity')
        blobs[relative] = oid
    if set(blobs) != set(snapshot):
        raise ValueError('complete selected runtime population must exist at source HEAD')
    # Check every declared size before requesting any content: assume-unchanged
    # index entries must not hide an oversized HEAD blob behind a tiny worktree
    # file. Then read the same immutable OIDs in one ordered raw-object batch.
    # Never request filters, text conversion, links or the whole object store.
    requested = b''.join(blobs[name].encode('ascii') + b'\n' for name in paths)
    expected_headers = [blobs[name].encode('ascii') + b' blob '
                        + str(len(snapshot[name])).encode('ascii') for name in paths]
    checked = _git(root, 'cat-file', '--batch-check', input_bytes=requested,
                   limit=128 * len(paths))
    if checked != b''.join(header + b'\n' for header in expected_headers):
        raise ValueError('selected source identity/type/size differs from HEAD blob')
    packed = _git(root, 'cat-file', '--batch', input_bytes=requested,
                  limit=sum(len(raw) for raw in snapshot.values()) + 128 * len(paths))
    cursor = 0
    for relative, expected in zip(paths, expected_headers):
        raw = snapshot[relative]
        end = packed.find(b'\n', cursor)
        if end < 0 or packed[cursor:end] != expected:
            raise ValueError('selected source identity/type/size differs from HEAD blob')
        cursor = end + 1
        end = cursor + len(raw)
        if packed[cursor:end] != raw or packed[end:end + 1] != b'\n':
            raise ValueError('selected source bytes differ from HEAD blob')
        cursor = end + 1
    if cursor != len(packed):
        raise ValueError('extra Git source identity output')
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
    """Ordinary live runtime verification always enforces its exact root."""
    return _distribution_identity(root,implementation,declared_root=str(root))


def transport_identity(root, implementation, *, expected_manifest_sha256):
    """Installer-only pinned payload check; old root is recorded provenance.

    No Git fallback, dependency execution or mutation is authorized here. The
    result does not authorize ordinary execution at the transported location.
    """
    root=_directory(root)
    if type(expected_manifest_sha256) is not str or _DIGEST.fullmatch(expected_manifest_sha256) is None:
        raise ValueError('exact source runtime manifest SHA256 required')
    raw=read_bytes(root/MANIFEST,MAX_MANIFEST_BYTES)
    if hashlib.sha256(raw).hexdigest()!=expected_manifest_sha256:
        raise ValueError('source runtime manifest SHA256 differs')
    try:
        record=json.loads(raw,object_pairs_hook=_strict_object,
            parse_constant=lambda value: (_ for _ in ()).throw(ValueError('invalid JSON constant')))
    except RecursionError as exc:
        raise ValueError('malformed transported manifest') from exc
    if type(record) is not dict:
        raise ValueError('source runtime manifest object required')
    declared=_binding_path(record.get('root'),check_aliases=False)
    identity=_distribution_identity(root,implementation,declared_root=declared,transport_record=True)
    if (read_bytes(root/MANIFEST,MAX_MANIFEST_BYTES)!=raw
            or identity['manifest_sha256']!=expected_manifest_sha256):
        raise ValueError('transported source manifest changed')
    return identity


def _distribution_identity(root, implementation, *, declared_root, transport_record=False):
    raw = read_bytes(root / MANIFEST, MAX_MANIFEST_BYTES)
    try:
        record = json.loads(raw, object_pairs_hook=_strict_object,
            parse_constant=lambda value: (_ for _ in ()).throw(ValueError('invalid JSON constant')))
    except (UnicodeError, json.JSONDecodeError, RecursionError) as exc:
        raise ValueError('malformed runtime distribution manifest') from exc
    fields={'schema', 'kind', 'root', 'build_source',
            'immutable_files_sha256', 'mutable_directories', 'local_engine'}
    if (type(record) is not dict or type(record.get('schema')) is not int
            or record['schema'] not in (1,2,3)
            or set(record) != fields | ({'native_version'} if record['schema']>=2 else set()) | ({'host_paths'} if record['schema']==3 else set())
            or record['kind'] != KIND or record['root'] != declared_root
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
    # Enumerate only the parents of the exact selected files. In particular,
    # selected placement modules do not authorize a recursive experiment-tree
    # copy or an unbounded history scan. Every intermediate directory has an
    # exact child population; mutable roots alone may contain unattested state.
    folders = {}
    for name in (*expected, MANIFEST, *([ENGINE_PATH] if engine is not None else [])):
        path = Path(name)
        folders.setdefault(path.parent, set()).add(path.name)
        for parent in path.parents:
            if parent == Path('.'):
                break
            folders.setdefault(parent.parent, set()).add(parent.name)
    for folder, names in sorted(folders.items()):
        mutable = set(MUTABLE_DIRECTORIES) if folder == Path('.') else set()
        allowed = names | mutable
        with os.scandir(_directory(root / folder)) as entries:
            actual = set()
            for index, item in enumerate(entries):
                if index >= len(allowed) or item.name not in allowed or item.is_symlink():
                    raise ValueError('runtime directory file population differs')
                if item.name in mutable:
                    _directory(Path(item.path))  # Contents are explicitly mutable/unattested.
                else:
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
    if record['schema']>=2:
        # Selection is part of the manifest hash and must name a committed,
        # exact known profile. It never rewrites the copied source or lock.
        lock=json.loads(read_bytes(root / 'toolchain.lock.json'))
        native_selection(lock,record['native_version'])
        if record['schema']==3:
            # Only the installer transport reader treats old absolute locations
            # as recorded provenance. Live runtime callers retain alias checks.
            _bound_tool_selection(lock,record['native_version'],record['host_paths'],
                                  check_aliases=not transport_record)
    if engine is not None:
        if file_digest(root / ENGINE_PATH, MAX_ENGINE_BYTES) != (engine['sha256'], engine['bytes']):
            raise ValueError('local runtime engine changed')
        lock = json.loads(read_bytes(root / 'toolchain.lock.json'))
        if lock.get('tools', {}).get('freerouting') != {key: engine[key] for key in ('path', 'sha256', 'bytes')}:
            raise ValueError('local runtime engine differs from original tool lock')
    return {'kind': KIND, 'git_head': build['git_head'], 'build_source': build,
            'manifest_sha256': hashlib.sha256(raw).hexdigest(),
            **({'native_version':record['native_version']} if record['schema']>=2 else {})}


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
