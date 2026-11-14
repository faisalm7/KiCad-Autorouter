"""Explicit, project-scoped tool paths; installed application is never changed."""
import json
import os
from pathlib import Path, PurePosixPath
import stat
ROOT = Path(__file__).resolve().parents[1]
from autorouter.provenance import (_NATIVE_SUFFIXES, _NATIVE_HASHES,
                                    native_selection, bound_tool_selection)


def _strict_json(path, limit):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result: raise ValueError('duplicate JSON key')
            result[key] = value
        return result
    def nonfinite(value): raise ValueError('nonfinite JSON value')
    if any(part.is_symlink() for part in (path, *path.parents)):
        raise ValueError('symlink selection file refused')
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        before = os.fstat(descriptor)
        if (not stat.S_ISREG(before.st_mode) or before.st_nlink != 1
                or not 0 < before.st_size <= limit):
            raise ValueError('bounded regular selection JSON required')
        with os.fdopen(descriptor, 'rb', closefd=False) as stream: raw = stream.read(limit + 1)
        after = os.fstat(descriptor); named = path.lstat()
        identity = lambda info: (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)
        if (len(raw) != before.st_size or len(raw) > limit
                or any(not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 for info in (after, named))
                or identity(before) != identity(after) or identity(before) != identity(named)):
            raise ValueError('selection JSON changed during read')
    finally:
        os.close(descriptor)
    result = json.loads(raw.decode('utf-8'), object_pairs_hook=pairs, parse_constant=nonfinite)
    if type(result) is not dict or not result: raise ValueError('nonempty selection JSON object required')
    return result


def _read_native_selection(root):
    lock = _strict_json(root / 'toolchain.lock.json', 64 * 1024)
    manifest = root / 'runtime-distribution.json'; version = None; manifest_selection = None
    if os.path.lexists(manifest):
        record = _strict_json(manifest, 256 * 1024)
        schema = record.get('schema')
        if (type(schema) is not int or schema not in (1, 2, 3)
                or record.get('kind') != 'runtime-directory-v1' or record.get('root') != str(root)):
            raise ValueError('runtime selection manifest identity differs')
        if schema == 1:
            if 'native_version' in record: raise ValueError('v1 runtime cannot select a native version')
        else:
            version = record.get('native_version')
            if type(version) is not str or version not in _NATIVE_HASHES:
                raise ValueError('v2 runtime requires an exact known native version')
        manifest_selection = (schema, version)
        if schema==3:
            paths=record.get('host_paths')
            selected=bound_tool_selection(lock,version,paths)
            manifest_selection=(schema,version,tuple(sorted(paths.items())))
            return selected,manifest_selection
    return native_selection(lock, version), manifest_selection


def _selection_signature(selection):
    return (selection['version'], tuple((role, pin['path'], pin['sha256'], pin['bytes'])
            for role, pin in selection['tools'].items()),
            tuple(selection['java'].items()) if 'java' in selection else None)


_INITIAL_NATIVE, _INITIAL_NATIVE_MANIFEST = _read_native_selection(ROOT)
NATIVE_VERSION = _INITIAL_NATIVE['version']
CLI, PYTHON, PCBNEW = (Path(_INITIAL_NATIVE['tools'][role]['path']) for role in _NATIVE_SUFFIXES)
KICAD = CLI.parent.parent
_INITIAL_NATIVE_SIGNATURE = _selection_signature(_INITIAL_NATIVE)
JAVA = Path(_INITIAL_NATIVE['java']['path']) if 'java' in _INITIAL_NATIVE else Path('/Library/Java/JavaVirtualMachines/temurin-25.jdk/Contents/Home/bin/java')
_INITIAL_NATIVE_GLOBALS = (ROOT, NATIVE_VERSION, KICAD, CLI, PYTHON, PCBNEW, JAVA)


def current_native_selection():
    """Recheck local selection; full runtime provenance is a separate guard."""
    current, manifest_selection = _read_native_selection(ROOT)
    if (_selection_signature(current) != _INITIAL_NATIVE_SIGNATURE
            or manifest_selection != _INITIAL_NATIVE_MANIFEST
            or (ROOT, NATIVE_VERSION, KICAD, CLI, PYTHON, PCBNEW, JAVA) != _INITIAL_NATIVE_GLOBALS):
        raise ValueError('native selection or cached role globals changed')
    return current


JAR = ROOT / '.tools/freerouting-2.5.0.jar'
JAR_SHA256 = 'f6f51bb02245e8e717f9359bd260cc9c5c0b1bc0acc8b7cb2cd5b8ffeb5de3c7'


def resolve_tool_path(value):
    """Resolve a lock path; project-relative pins cannot escape this checkout.

    Installed application pins remain absolute, including their OS-managed path
    layout. Relative pins must be canonical and contain no symlink components.
    Resolving a path does not replace the caller's mandatory digest check.
    """
    if not isinstance(value, str) or not value or '\\' in value:
        raise ValueError('invalid tool pin path')
    path = Path(value)
    if path.is_absolute():
        return path
    if str(path) != value or any(part in ('.', '..') for part in value.split('/')):
        raise ValueError('noncanonical or escaping relative tool pin')
    result = ROOT / path
    if result == ROOT or not result.resolve().is_relative_to(ROOT.resolve()):
        raise ValueError('relative tool pin escapes project')
    current = ROOT
    for part in path.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError('symlink in project-relative tool pin')
    return result
