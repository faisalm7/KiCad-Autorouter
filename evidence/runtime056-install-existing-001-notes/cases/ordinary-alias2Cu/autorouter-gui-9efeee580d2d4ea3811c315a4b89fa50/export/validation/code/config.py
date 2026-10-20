"""Explicit, project-scoped tool paths; installed application is never changed."""
import json
import os
from pathlib import Path, PurePosixPath
import stat
ROOT = Path(__file__).resolve().parents[1]
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
        if (type(schema) is not int or schema not in (1, 2)
                or record.get('kind') != 'runtime-directory-v1' or record.get('root') != str(root)):
            raise ValueError('runtime selection manifest identity differs')
        if schema == 1:
            if 'native_version' in record: raise ValueError('v1 runtime cannot select a native version')
        else:
            version = record.get('native_version')
            if type(version) is not str or version not in _NATIVE_HASHES:
                raise ValueError('v2 runtime requires an exact known native version')
        manifest_selection = (schema, version)
    return native_selection(lock, version), manifest_selection


def _selection_signature(selection):
    return (selection['version'], tuple((role, pin['path'], pin['sha256'], pin['bytes'])
            for role, pin in selection['tools'].items()))


_INITIAL_NATIVE, _INITIAL_NATIVE_MANIFEST = _read_native_selection(ROOT)
NATIVE_VERSION = _INITIAL_NATIVE['version']
CLI, PYTHON, PCBNEW = (Path(_INITIAL_NATIVE['tools'][role]['path']) for role in _NATIVE_SUFFIXES)
KICAD = CLI.parent.parent
_INITIAL_NATIVE_SIGNATURE = _selection_signature(_INITIAL_NATIVE)
_INITIAL_NATIVE_GLOBALS = (ROOT, NATIVE_VERSION, KICAD, CLI, PYTHON, PCBNEW)


def current_native_selection():
    """Recheck local selection; full runtime provenance is a separate guard."""
    current, manifest_selection = _read_native_selection(ROOT)
    if (_selection_signature(current) != _INITIAL_NATIVE_SIGNATURE
            or manifest_selection != _INITIAL_NATIVE_MANIFEST
            or (ROOT, NATIVE_VERSION, KICAD, CLI, PYTHON, PCBNEW) != _INITIAL_NATIVE_GLOBALS):
        raise ValueError('native selection or cached role globals changed')
    return current


JAVA = Path('/Library/Java/JavaVirtualMachines/temurin-25.jdk/Contents/Home/bin/java')
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
