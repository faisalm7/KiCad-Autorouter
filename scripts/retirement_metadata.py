"""Private macOS metadata supplement for an already content-checked catalog.

No file payloads are copied or hashed here. The caller owns authorization,
content/recovery checks, activity checks and deletion. Capture never modifies
the source. Provenance is retained as readable bytes but deliberately not
replayed. Other xattrs, including resource forks, are data, not decoration.
"""
import base64
from contextlib import contextmanager
import ctypes
import errno
from functools import lru_cache
import gzip
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import sys
import time


MAX_ATTRIBUTE_BYTES = 1024 ** 2
MAX_TOTAL_ATTRIBUTE_BYTES = 16 * 1024 ** 2
MAX_RECORD_BYTES = 384 * 1024 ** 2
MAX_COMPRESSED_RECORD_BYTES = 32 * 1024 ** 2
MAX_ENTRIES = 750000  # Combined existing file AND directory catalogs.
MAX_ACL_BYTES = 1024 ** 2
PROVENANCE = 'com.apple.provenance'
KIND = 'macos-retirement-metadata-v1'


class MetadataError(RuntimeError):
    pass


def _error(path, attribute, message):
    return MetadataError(f'{path}: {attribute}: {message}')


@lru_cache(maxsize=1)
def _native():
    if sys.platform != 'darwin':
        raise MetadataError('Metadata capture is qualified on macOS only')
    lib = ctypes.CDLL('/usr/lib/libSystem.B.dylib', use_errno=True)
    declarations = {
        'flistxattr': ([ctypes.c_int, ctypes.c_void_p, ctypes.c_size_t, ctypes.c_int], ctypes.c_ssize_t),
        'fgetxattr': ([ctypes.c_int, ctypes.c_char_p, ctypes.c_void_p, ctypes.c_size_t,
                       ctypes.c_uint32, ctypes.c_int], ctypes.c_ssize_t),
        'fsetxattr': ([ctypes.c_int, ctypes.c_char_p, ctypes.c_void_p, ctypes.c_size_t,
                       ctypes.c_uint32, ctypes.c_int], ctypes.c_int),
        'acl_get_fd_np': ([ctypes.c_int, ctypes.c_int], ctypes.c_void_p),
        'acl_init': ([ctypes.c_int], ctypes.c_void_p),
        'acl_to_text': ([ctypes.c_void_p, ctypes.POINTER(ctypes.c_ssize_t)], ctypes.c_void_p),
        'acl_from_text': ([ctypes.c_char_p], ctypes.c_void_p),
        'acl_set_fd_np': ([ctypes.c_int, ctypes.c_void_p, ctypes.c_int], ctypes.c_int),
        'acl_free': ([ctypes.c_void_p], ctypes.c_int),
        'fchflags': ([ctypes.c_int, ctypes.c_uint32], ctypes.c_int),
    }
    for name, (args, result) in declarations.items():
        function = getattr(lib, name)
        function.argtypes, function.restype = args, result
    return lib


def _checked(value, path, attribute):
    if value == -1 or value is None:
        code = ctypes.get_errno()
        raise _error(path, attribute, f'native operation failed errno {code}: {os.strerror(code)}')
    return value


def _stamp(s):
    return (s.st_dev, s.st_ino, s.st_mode, s.st_nlink, s.st_size, s.st_mtime_ns, s.st_ctime_ns)


def _identity(s):
    return {key: getattr(s, 'st_' + key) for key in
            ('dev', 'ino', 'mode', 'nlink', 'size', 'mtime_ns', 'ctime_ns', 'uid', 'gid', 'flags')}


def _absolute(path):
    path = Path(path).absolute()
    if '..' in path.parts:
        raise MetadataError('Parent traversal is not supported: ' + str(path))
    return path


def _name(name):
    p = PurePosixPath(name)
    if not name or p.is_absolute() or '..' in p.parts or str(p) != name or '\\' in name:
        raise MetadataError('Noncanonical catalog member: ' + repr(name))
    return p


@contextmanager
def _directory(path):
    """Open each absolute component without following a symlink."""
    path = _absolute(path)
    fd = os.open(path.anchor, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for part in path.parts[1:]:
            following = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = following
        yield fd
    finally:
        os.close(fd)


@contextmanager
def _member(rootfd, name, kind, path):
    parts = _name(name).parts
    fd = os.dup(rootfd)
    device = os.fstat(rootfd).st_dev
    try:
        for i, part in enumerate(parts):
            directory = i < len(parts) - 1 or kind == 'directory'
            flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
            if directory:
                flags |= os.O_DIRECTORY
            following = os.open(part, flags, dir_fd=fd)
            os.close(fd)
            fd = following
            s = os.fstat(fd)
            if s.st_dev != device:
                raise _error(path, 'filesystem', 'unexpected device/mount')
            if directory and not stat.S_ISDIR(s.st_mode):
                raise _error(path, 'type', 'expected a directory')
        s = os.fstat(fd)
        if kind == 'file' and not stat.S_ISREG(s.st_mode):
            raise _error(path, 'type', 'expected a regular file')
        yield fd
    finally:
        os.close(fd)


def _acl(fd, path):
    lib = _native()
    ctypes.set_errno(0)
    acl = lib.acl_get_fd_np(fd, 0x100)
    if acl is None and ctypes.get_errno() == errno.ENOENT and os.fstat(fd).st_nlink:
        # Actual APFS no-ACL behavior: an open, still-linked descriptor returns
        # NULL/ENOENT. Positive ACL and absent/empty controls exercise this.
        return None
    acl = _checked(acl, path, 'ACL')
    try:
        size = ctypes.c_ssize_t()
        text = _checked(lib.acl_to_text(acl, ctypes.byref(size)), path, 'ACL')
        try:
            if not 0 <= size.value <= MAX_ACL_BYTES:
                raise _error(path, 'ACL', 'text exceeds bounded ACL size')
            try:
                value = ctypes.string_at(text, size.value).decode('utf-8')
            except UnicodeDecodeError as exc:
                raise _error(path, 'ACL', 'native text is not readable UTF-8') from exc
            return value if len(value.splitlines()) > 1 else None
        finally:
            lib.acl_free(text)
    finally:
        lib.acl_free(acl)


def _xattrs(fd, path):
    lib = _native()
    # SHOWCOMPRESSION also exposes compression data hidden by default listings.
    size = _checked(lib.flistxattr(fd, None, 0, 0x20), path, 'xattr names')
    if size > 65536:
        raise _error(path, 'xattr names', 'name list exceeds 65536 bytes')
    buffer = ctypes.create_string_buffer(max(1, size))
    count = _checked(lib.flistxattr(fd, buffer, size, 0x20), path, 'xattr names')
    if count != size:
        raise _error(path, 'xattr names', 'changed during capture')
    raw = buffer.raw[:count]
    if raw and not raw.endswith(b'\0'):
        raise _error(path, 'xattr names', 'unterminated native name list')
    names = raw[:-1].split(b'\0') if raw else []
    if len(set(names)) != len(names) or any(not n or len(n) > 127 for n in names):
        raise _error(path, 'xattr names', 'invalid or duplicate native names')
    result = {}
    for name in sorted(names):
        display = os.fsdecode(name)
        size = _checked(lib.fgetxattr(fd, name, None, 0, 0, 0x20), path, display)
        if size > MAX_ATTRIBUTE_BYTES:
            raise _error(path, display, f'{size} bytes exceeds {MAX_ATTRIBUTE_BYTES}-byte attribute cap')
        value = ctypes.create_string_buffer(max(1, size))
        count = _checked(lib.fgetxattr(fd, name, value, size, 0, 0x20), path, display)
        if count != size:
            raise _error(path, display, 'changed during capture')
        result[display] = base64.b64encode(value.raw[:count]).decode('ascii')
    return result


def _metadata(fd, path):
    before = _identity(os.fstat(fd))
    result = {'identity': before, 'acl': _acl(fd, path), 'xattrs_base64': _xattrs(fd, path)}
    if _identity(os.fstat(fd)) != before:
        raise _error(path, 'metadata', 'changed during capture')
    return result


def _collect(root, catalogfiles, catalogdirs):
    root = _absolute(root)
    if '.' not in catalogdirs or set(catalogfiles) & set(catalogdirs):
        raise MetadataError('Complete disjoint file/directory catalogs including root dot required')
    kinds = {**dict.fromkeys(catalogfiles, 'file'), **dict.fromkeys(catalogdirs, 'directory')}
    if len(kinds) > MAX_ENTRIES:
        raise MetadataError('Metadata entry cap exceeded')
    children = {name: set() for name in catalogdirs}
    for name in kinds:
        p = _name(name)
        if name != '.':
            parent = str(p.parent)
            if parent not in children:
                raise _error(root / name, 'catalog', 'missing parent directory')
            children[parent].add(p.name)
    rows, total, encoded_bytes = {}, 0, 0
    with _directory(root) as rootfd:
        rootstat = os.fstat(rootfd)
        for name, kind in sorted(kinds.items()):
            path = root / name
            expected = catalogfiles[name]['stat'] if kind == 'file' else catalogdirs[name]
            with _member(rootfd, name, kind, path) as fd:
                if _stamp(os.fstat(fd)) != tuple(expected):
                    raise _error(path, 'catalog identity', 'changed after content catalog')
                row = _metadata(fd, path)
                if kind == 'directory' and set(os.listdir(fd)) != children[name]:
                    raise _error(path, 'catalog members', 'extra, missing or changed children')
                if _stamp(os.fstat(fd)) != tuple(expected):
                    raise _error(path, 'catalog identity', 'changed during metadata capture')
                if kind == 'file':
                    digest = catalogfiles[name]['sha256']
                    if not isinstance(digest, str) or re.fullmatch('[0-9a-f]{64}', digest) is None:
                        raise _error(path, 'catalog content', 'content-checked SHA256 required')
                    row['content_sha256'] = digest
                for attribute, encoded in row['xattrs_base64'].items():
                    total += len(base64.b64decode(encoded, validate=True))
                    if total > MAX_TOTAL_ATTRIBUTE_BYTES:
                        raise _error(path, attribute, f'total xattr payload exceeds {MAX_TOTAL_ATTRIBUTE_BYTES} bytes')
                rows[name] = {'kind': kind, **row}
                encoded_bytes += len(json.dumps({name: rows[name]}, sort_keys=True, separators=(',', ':')))
                if encoded_bytes > MAX_RECORD_BYTES - 4096:
                    raise _error(path, 'metadata record', 'decoded record size cap exceeded')
        if _identity(os.fstat(rootfd)) != _identity(rootstat):
            raise _error(root, 'root', 'changed during metadata capture')
        with _directory(root) as current:
            if _identity(os.fstat(current)) != _identity(rootstat):
                raise _error(root, 'root', 'path changed during metadata capture')
    return rows, total


def _outside(root, parentfd, parent, identity=None):
    if root == parent or root in parent.parents:
        raise MetadataError('Supplement/destination must be outside captured root')
    if identity is None:
        with _directory(root) as fd:
            s = os.fstat(fd)
            identity = (s.st_dev, s.st_ino)
    for path in [parent, *parent.parents]:
        with _directory(path) as fd:
            s = os.fstat(fd)
            if (s.st_dev, s.st_ino) == identity:
                raise MetadataError('Supplement/destination must be outside captured root')
    if os.fstat(parentfd).st_uid != os.getuid():
        raise MetadataError('Supplement/destination parent must be owned by current user')


def read_record(path, expected_sha256):
    """Read back a separately hash-bound, bounded, single-link private record."""
    path = _absolute(path)
    with _directory(path.parent) as parent:
        fd = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
        with os.fdopen(fd, 'rb') as stream:
            before = os.fstat(stream.fileno())
            if (not stat.S_ISREG(before.st_mode) or before.st_nlink != 1
                    or before.st_size > MAX_COMPRESSED_RECORD_BYTES):
                raise _error(path, 'record', 'unsupported file or size')
            digest = hashlib.sha256()
            for chunk in iter(lambda: stream.read(1024 ** 2), b''):
                digest.update(chunk)
            if digest.hexdigest() != expected_sha256:
                raise _error(path, 'record', 'SHA256 differs')
            stream.seek(0)
            with gzip.GzipFile(fileobj=stream, mode='rb') as compressed:
                raw = compressed.read(MAX_RECORD_BYTES + 1)
            if len(raw) > MAX_RECORD_BYTES:
                raise _error(path, 'record', 'decoded record exceeds size cap')
            if _identity(os.fstat(stream.fileno())) != _identity(before):
                raise _error(path, 'record', 'changed during read')
    def unique(pairs):
        value = {}
        for key, entry in pairs:
            if key in value:
                raise _error(path, 'record', 'duplicate JSON key')
            value[key] = entry
        return value
    record = json.loads(raw, object_pairs_hook=unique)
    if (record.get('schema') != 1 or record.get('kind') != KIND
            or record.get('record_only_xattrs') != [PROVENANCE]
            or not isinstance(record.get('members'), dict) or len(record['members']) > MAX_ENTRIES):
        raise _error(path, 'record', 'unsupported schema')
    return record


class _RecordWriter:
    def __init__(self, stream, path):
        self.stream, self.path = stream, path
        self.size, self.digest = 0, hashlib.sha256()

    def write(self, data):
        if self.size + len(data) > MAX_COMPRESSED_RECORD_BYTES:
            raise _error(self.path, 'record', 'compressed supplement exceeds size cap; partial record retained')
        written = self.stream.write(data)
        if written != len(data):
            raise _error(self.path, 'record', 'short output write; partial record retained')
        self.size += written
        self.digest.update(data)
        return written

    def flush(self):
        return self.stream.flush()


def capture(root, catalogfiles, catalogdirs, output):
    """Capture every catalog member's metadata; source content stays untouched.

    Catalogs use legacy helper shapes files[name]={sha256,stat}, dirs[name]=stat,
    where stat=(dev,ino,mode,nlink,size,mtime_ns,ctime_ns). Output must be outside
    this root AND, as enforced by the caller, outside every deletion candidate.
    """
    root, output = _absolute(root), _absolute(output)
    with _directory(output.parent) as parent:
        _outside(root, parent, output.parent)
        members, total = _collect(root, catalogfiles, catalogdirs)
        record = {'schema': 1, 'kind': KIND, 'root': str(root), 'created_ns': time.time_ns(),
                  'record_only_xattrs': [PROVENANCE], 'members': members,
                  'xattr_payload_bytes': total, 'source_content_verified_by_this_helper': False,
                  'limits': {'attribute_bytes': MAX_ATTRIBUTE_BYTES,
                             'total_attribute_bytes': MAX_TOTAL_ATTRIBUTE_BYTES,
                             'decoded_record_bytes': MAX_RECORD_BYTES,
                             'compressed_record_bytes': MAX_COMPRESSED_RECORD_BYTES,
                             'entries': MAX_ENTRIES}}
        raw = json.dumps(record, sort_keys=True, separators=(',', ':')).encode('ascii') + b'\n'
        if len(raw) > MAX_RECORD_BYTES:
            raise _error(output, 'record', 'serialized supplement exceeds size cap')
        fd = os.open(output.name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=parent)
        with os.fdopen(fd, 'wb') as stream:
            writer = _RecordWriter(stream, output)
            with gzip.GzipFile(filename='', fileobj=writer, mode='wb', compresslevel=1, mtime=0) as compressed:
                compressed.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
            size = os.fstat(stream.fileno()).st_size
            if size != writer.size:
                raise _error(output, 'record', 'output size differs; retained')
    digest = writer.digest.hexdigest()
    if read_record(output, digest) != record:
        raise _error(output, 'record', 'independent read-back differs')
    return {'path': str(output), 'sha256': digest, 'bytes': size, 'decoded_bytes': len(raw),
            'members': len(members),
            'xattr_payload_bytes': total, 'readback_verified': True,
            'provenance_recorded_not_replayed': True}


def verify_current(root, record_path, expected_sha256):
    record = read_record(record_path, expected_sha256)
    if record['root'] != str(_absolute(root)):
        raise MetadataError('Supplement source root differs')
    catalogfiles, catalogdirs = {}, {}
    for name, row in record['members'].items():
        identity = row['identity']
        stamp = tuple(identity[k] for k in ('dev', 'ino', 'mode', 'nlink', 'size', 'mtime_ns', 'ctime_ns'))
        if row['kind'] == 'file':
            catalogfiles[name] = {'stat': stamp, 'sha256': row['content_sha256']}
        elif row['kind'] == 'directory':
            catalogdirs[name] = stamp
        else:
            raise MetadataError('Unsupported supplemental member kind')
    members, total = _collect(root, catalogfiles, catalogdirs)
    if members != record['members'] or total != record['xattr_payload_bytes']:
        raise MetadataError('Current metadata differs from retained supplement')
    return True


def recover_small(record_path, expected_sha256, destination, file_contents):
    """Replay supported metadata only into a NEW tiny caller-owned test tree.

    This is a qualification probe, not a historical environment installer. It
    never edits a captured path, strips xattrs, or removes a failed destination.
    Callers supply <=1MiB known fixture bytes; at most256 entries are supported.
    """
    record = read_record(record_path, expected_sha256)
    members = record['members']
    if len(members) > 256 or sum(len(v) for v in file_contents.values()) > 1024 ** 2:
        raise MetadataError('Small recovery probe exceeds fixture bounds')
    files = {name: row for name, row in members.items() if row['kind'] == 'file'}
    dirs = {name: row for name, row in members.items() if row['kind'] == 'directory'}
    if set(files) != set(file_contents) or '.' not in dirs:
        raise MetadataError('Exact small fixture payload map required')
    for name, row in members.items():
        _name(name)
        if name != '.' and str(PurePosixPath(name).parent) not in dirs:
            raise MetadataError('Recovery member omits directory parent')
        if row['kind'] not in ('file', 'directory'):
            raise MetadataError('Unsupported recovery member kind')
    destination = _absolute(destination)
    with _directory(destination.parent) as parent:
        source = members['.']['identity']
        _outside(Path(record['root']), parent, destination.parent, (source['dev'], source['ino']))
        os.mkdir(destination.name, 0o700, dir_fd=parent)
    with _directory(destination) as rootfd:
        for name in sorted(set(dirs) - {'.'}, key=lambda n: (len(PurePosixPath(n).parts), n)):
            os.mkdir(name, 0o700, dir_fd=rootfd)
        groups = {}
        for name, row in sorted(files.items()):
            raw = file_contents[name]
            if hashlib.sha256(raw).hexdigest() != row['content_sha256']:
                raise _error(destination / name, 'fixture content', 'SHA256 differs')
            key = (row['identity']['dev'], row['identity']['ino'])
            if key in groups:
                os.link(groups[key], name, src_dir_fd=rootfd, dst_dir_fd=rootfd, follow_symlinks=False)
            else:
                fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=rootfd)
                with os.fdopen(fd, 'wb') as stream:
                    stream.write(raw)
                groups[key] = name
        for name, row in sorted(members.items(), key=lambda item: (-len(PurePosixPath(item[0]).parts), item[0])):
            path = destination / name
            with _member(rootfd, name, row['kind'], path) as fd:
                identity = row['identity']
                if row['kind'] == 'file' and os.fstat(fd).st_nlink != identity['nlink']:
                    raise _error(path, 'link information', 'links outside fixture cannot be reconstructed')
                current = os.fstat(fd)
                if (current.st_uid, current.st_gid) != (identity['uid'], identity['gid']):
                    os.fchown(fd, identity['uid'], identity['gid'])
                os.fchmod(fd, stat.S_IMODE(identity['mode']))
                acl = (_native().acl_init(0) if row['acl'] is None else
                       _native().acl_from_text(row['acl'].encode('utf-8')))
                acl = _checked(acl, path, 'ACL')
                try:
                    _checked(_native().acl_set_fd_np(fd, acl, 0x100), path, 'ACL')
                finally:
                    _native().acl_free(acl)
                for attribute, encoded in row['xattrs_base64'].items():
                    if attribute == PROVENANCE:
                        continue
                    raw = base64.b64decode(encoded, validate=True)
                    value = ctypes.create_string_buffer(raw)
                    _checked(_native().fsetxattr(fd, os.fsencode(attribute), value, len(raw), 0, 0), path, attribute)
                _checked(_native().fchflags(fd, identity['flags']), path, 'flags')
        for name, row in members.items():
            path = destination / name
            with _member(rootfd, name, row['kind'], path) as fd:
                actual = _metadata(fd, path)
            keys = ('uid', 'gid', 'flags', 'mode', 'nlink')
            if any(actual['identity'][k] != row['identity'][k] for k in keys) or actual['acl'] != row['acl']:
                raise _error(path, 'recovered metadata', 'mode/ownership/flags/links/ACL differs')
            for attribute, encoded in row['xattrs_base64'].items():
                if attribute != PROVENANCE and actual['xattrs_base64'].get(attribute) != encoded:
                    raise _error(path, attribute, 'recovered bytes differ')
    return {'verified': True, 'destination': str(destination), 'members': len(members),
            'provenance_replayed': False, 'existing_attributes_stripped': False,
            'qualification': 'tiny same-Mac metadata fixture only; not historical venv/OS recovery'}
