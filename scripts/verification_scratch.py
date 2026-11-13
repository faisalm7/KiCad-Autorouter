"""One new-owned verification slot; never a collector for historical folders.

The caller supplies independently reconstructed expected contents.  Success
records and the compact disposal receipt live outside the disposable slot.
This detects ordinary concurrent edits, not hostile administrator/kernel races.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import subprocess
import sys
import uuid


class ScratchError(RuntimeError):
    pass


_LIVE_LEASES = {}


def _regular_bytes(path, *, dir_fd=None):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=dir_fd)
    with os.fdopen(fd, 'rb') as stream:
        before = os.fstat(stream.fileno())
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
            raise ScratchError('Only single-link regular scratch files are supported')
        h = hashlib.sha256()
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
        after = os.fstat(stream.fileno())
    identity = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
    if identity(before) != identity(after):
        raise ScratchError('Scratch file changed while read')
    return {'size': before.st_size, 'sha256': h.hexdigest()}, identity(before)


def _json(path, value):
    with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'w') as out:
        json.dump(value, out, sort_keys=True, indent=2)
        out.write('\n')


def _path(path):
    path = Path(path).absolute()
    if '..' in path.parts:
        raise ScratchError('Parent traversal in owned scratch path')
    for parent in [*reversed(path.parents), path]:
        if parent.is_symlink():
            raise ScratchError('Symlink in owned scratch path')
    return path


def _name(name):
    p = PurePosixPath(name)
    if not name or p.is_absolute() or '..' in p.parts or str(p) != name or '\\' in name:
        raise ScratchError('Out-of-scope scratch member')
    return p


def manifest(path, *, max_files=1_000_000):
    """No-follow exact member inventory; callers must not treat this as coverage."""
    path = _path(path)
    files, dirs, identities = {}, set(), {}
    root_stat = path.lstat()
    for current, children, names in os.walk(path, followlinks=False):
        current = Path(current)
        current_stat = current.lstat()
        if not stat.S_ISDIR(current_stat.st_mode) or current_stat.st_dev != root_stat.st_dev:
            raise ScratchError('Changed or cross-device scratch directory')
        current_name = current.relative_to(path).as_posix()
        identities['dir:' + current_name] = (current_stat.st_dev, current_stat.st_ino)
        if current != path:
            dirs.add(current.relative_to(path).as_posix())
        for name in children + names:
            target = current / name
            st = target.lstat()
            rel = target.relative_to(path).as_posix()
            if st.st_dev != root_stat.st_dev:
                raise ScratchError('Cross-device scratch member')
            if stat.S_ISDIR(st.st_mode):
                continue
            if not stat.S_ISREG(st.st_mode) or len(files) >= max_files:
                raise ScratchError('Linked/special or oversized scratch tree')
            files[rel], identities[rel] = _regular_bytes(_path(target))
    return {'files': files, 'directories': sorted(dirs)}, identities


@dataclass(frozen=True)
class Lease:
    path: Path
    records: Path
    token: str
    device: int
    inode: int
    owner_pid: int


def claim(root, purpose):
    """Exclusive fixed slot: failed/unreviewed work blocks the next verification."""
    root = _path(root)
    if root == Path(root.anchor) or '.local-backups' in root.parts:
        raise ScratchError('Out-of-scope nested verification root')
    base = _path(root / '.local-backups')
    base.mkdir(mode=0o700, exist_ok=True)
    records = _path(base / 'verification-records')
    records.mkdir(mode=0o700, exist_ok=True)
    path = _path(base / 'verification-workspace')
    try:
        path.mkdir(mode=0o700)
    except FileExistsError as exc:
        raise ScratchError('Existing verification slot retained; inspect/pin it before another job') from exc
    st = path.lstat()
    lease = Lease(path, records, uuid.uuid4().hex, st.st_dev, st.st_ino, os.getpid())
    _json(records / (lease.token + '-ownership.json'), {
        'schema': 1, 'token': lease.token, 'path': str(path), 'purpose': purpose,
        'device': st.st_dev, 'inode': st.st_ino, 'pid': os.getpid(),
        'created_utc': datetime.now(timezone.utc).isoformat(),
        'historical_scope': False, 'automatic_removal': 'only successful independently covered contents'})
    _LIVE_LEASES[lease.token] = lease
    return lease


def active_users_many(paths):
    """One fresh owned-process snapshot for a bounded batch at this boundary.

    Keys are absolute no-symlink path strings; each value is the sorted matching
    PID list. Exact paths and descendants match, never a similarly named sibling.
    No snapshot survives this call; separate boundaries must query again. Like
    active_users, this detects cooperative ordinary users, not hostile races.
    No process command lines, unrelated paths or file contents are returned.
    """
    if isinstance(paths, (str, bytes, os.PathLike)):
        raise ScratchError('Activity batch requires an iterable of paths')
    targets = {}
    for count, path in enumerate(paths, 1):
        if count > 4096:
            raise ScratchError('Activity batch exceeds path bound')
        path = str(_path(path))
        if any(char in path for char in ('\n', '\r', '\0')):
            raise ScratchError('Unsupported control character in activity path')
        targets.setdefault(path, set())
    if not targets:
        raise ScratchError('Activity batch must not be empty')

    prefixes = {path: path.rstrip('/') + '/' for path in targets}
    def observe(name, pid):
        for path in targets:
            if name == path or name.startswith(prefixes[path]):
                targets[path].add(pid)

    if sys.platform == 'darwin':
        exe = shutil.which('lsof') or '/usr/sbin/lsof'
        try:
            result = subprocess.run([exe, '-nP', '-a', '-u', str(os.getuid()), '-Fpn'],
                                    capture_output=True, text=True, timeout=30)
        except (OSError, subprocess.SubprocessError, UnicodeError) as exc:
            raise ScratchError('Process-use inspection unavailable or incomplete') from exc
        if result.returncode != 0 or result.stderr or len(result.stdout) > 16 * 1024 ** 2:
            raise ScratchError('Process-use inspection unavailable or incomplete')
        pid = None
        for line in result.stdout.splitlines():
            if line.startswith('p'):
                pid = line[1:]
                if not pid or not pid.isascii() or not pid.isdigit() or int(pid) <= 0:
                    raise ScratchError('Process-use inspection malformed')
            if line.startswith('n'):
                if pid is None:
                    raise ScratchError('Process-use inspection missing process identity')
                observe(line[1:], pid)
        if pid is None:
            raise ScratchError('Process-use inspection missing process identity')
    elif sys.platform.startswith('linux'):
        try:
            for process in Path('/proc').iterdir():
                if not process.name.isdigit(): continue
                try:
                    if process.stat().st_uid != os.getuid(): continue
                    links = [process / 'cwd', *list((process / 'fd').iterdir())]
                    for target in links:
                        try: name = os.readlink(target)
                        except FileNotFoundError: continue
                        observe(name, process.name)
                except FileNotFoundError: continue
        except PermissionError as exc:
            raise ScratchError('Process-use inspection denied') from exc
        except OSError as exc:
            raise ScratchError('Process-use inspection unavailable or incomplete') from exc
    else:
        raise ScratchError('Automatic verification cleanup is not qualified on this platform')
    return {path: sorted(found) for path, found in targets.items()}


def active_users(path):
    """Fresh one-path compatibility API; no shared snapshot or cached result."""
    path = str(_path(path))
    return active_users_many([path])[path]


def _preserve_macos_metadata(lease, expected, identities, stable=None):
    """Supplement only this owned slot; independent content coverage is prior."""
    try:
        from scripts import retirement_metadata as metadata
    except ModuleNotFoundError:  # Direct scripts/backup.py entry point.
        import retirement_metadata as metadata
    files, directories = {}, {}
    for name, row in expected['files'].items():
        target = _path(lease.path / name)
        observed = target.lstat()
        identity = (observed.st_dev, observed.st_ino, observed.st_size,
                    observed.st_mtime_ns, observed.st_ctime_ns)
        if (not stat.S_ISREG(observed.st_mode) or observed.st_nlink != 1
                or identity != identities[name]):
            raise ScratchError('Scratch changed before metadata preservation: ' + name)
        files[name] = {'sha256': row['sha256'], 'stat': metadata._stamp(observed)}
    for name in ['.', *expected['directories']]:
        observed = _path(lease.path / name).lstat()
        if (not stat.S_ISDIR(observed.st_mode)
                or (observed.st_dev, observed.st_ino) != identities['dir:' + name]):
            raise ScratchError('Scratch directory changed before metadata preservation: ' + name)
        directories[name] = metadata._stamp(observed)
    output = _path(lease.records / (lease.token + '-metadata.json.gz'))
    try:
        saved = metadata.capture(lease.path, files, directories, output)
        if stable is not None: stable()
        metadata.verify_current(lease.path, output, saved['sha256'])
    except metadata.MetadataError as exc:
        raise ScratchError('Scratch metadata preservation refused: ' + str(exc)) from exc
    return saved


def dispose(lease, expected, *, success_record, reconstruction, required_paths=(), stable=None):
    """Delete only this process's new slot after independent caller coverage.

    `expected` must come from verified recovery sources, not merely inventory of
    whatever currently occupies the slot.  Failed checks retain all material.
    """
    if (not isinstance(lease, Lease) or lease.owner_pid != os.getpid()
            or _LIVE_LEASES.get(lease.token) is not lease):
        raise ScratchError('Only the live creating process may dispose its new slot')
    def require_owner_access(observed, directory):
        required = stat.S_IWUSR | stat.S_IXUSR
        if observed.st_uid != os.getuid() or observed.st_mode & required != required:
            raise ScratchError('Directory owner write/execute permissions required before disposal: ' + str(directory))

    # Check the entry's parent before traversing into a possibly non-searchable
    # workspace. Refusal must precede proof reads, coverage and unlinking.
    parent = _path(lease.path.parent)
    fd = os.open(parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        require_owner_access(os.fstat(fd), parent)
    finally:
        os.close(fd)
    path = _path(lease.path)
    if path.name != 'verification-workspace' or path.parent.name != '.local-backups':
        raise ScratchError('Out-of-scope disposal path')
    st = path.lstat()
    if (st.st_dev, st.st_ino) != (lease.device, lease.inode) or not stat.S_ISDIR(st.st_mode):
        raise ScratchError('Owned scratch directory identity changed')
    require_owner_access(st, path)
    proof = _path(success_record)
    if proof == path or path in proof.parents or not proof.is_file() or not reconstruction:
        raise ScratchError('Durable successful proof and reconstruction coverage required outside scratch')
    with os.fdopen(os.open(proof, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK), 'rb') as stream:
        before = os.fstat(stream.fileno())
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or before.st_size > 1024 ** 2:
            raise ScratchError('Compact successful verification record required')
        raw = stream.read(1024 ** 2 + 1)
        after = os.fstat(stream.fileno())
    identity = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
    proof_identity = identity(before)
    proof_expected = {'size': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}
    if len(raw) != before.st_size or proof_identity != identity(after):
        raise ScratchError('Successful verification record changed while read')
    result = json.loads(raw)
    if type(result) is not dict or not (result.get('verified') is True or result.get('integrity_checked') is True):
        raise ScratchError('Successful verification record required')
    for dependency in required_paths:
        # A lexical outside path may alias a required file inside the slot.
        # Reject every symlink component rather than following it silently.
        dep = _path(dependency)
        if dep == path or path in dep.parents or dep in path.parents:
            raise ScratchError('Scratch is a required recovery dependency')
        # Case-insensitive filesystems can provide another spelling without a
        # symlink. Compare directory identities as well as lexical ancestry.
        required_stat = dep.lstat()
        required_identity = (required_stat.st_dev, required_stat.st_ino)
        for parent in [dep, *dep.parents]:
            observed = parent.lstat()
            if (observed.st_dev, observed.st_ino) == (lease.device, lease.inode):
                raise ScratchError('Scratch alias is a required recovery dependency')
        for parent in [path, *path.parents]:
            observed = parent.lstat()
            if (observed.st_dev, observed.st_ino) == required_identity:
                raise ScratchError('Scratch ancestor is a required recovery dependency')
    # Reuse the same no-follow descriptor traversal for an early permission
    # preflight and the actual unlink operations. Owner bits are a conservative
    # prerequisite, not proof against ACL denies, filesystem errors or races.
    identities = None
    def parent_fd(name, *, directory=False):
        fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            root_now = os.fstat(fd)
            if (root_now.st_dev, root_now.st_ino) != (lease.device, lease.inode):
                raise ScratchError('Owned root changed during disposal')
            require_owner_access(root_now, path)
            relative = []
            components = PurePosixPath(name).parts
            for component in components if directory else components[:-1]:
                next_fd = os.open(component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
                relative.append(component)
                try:
                    observed = os.fstat(next_fd)
                    if (observed.st_dev != lease.device or identities is not None
                            and (observed.st_dev, observed.st_ino) != identities['dir:' + '/'.join(relative)]):
                        raise ScratchError('Scratch ancestor directory identity changed')
                    require_owner_access(observed, path.joinpath(*relative))
                except BaseException:
                    os.close(next_fd)
                    raise
                os.close(fd); fd = next_fd
            return fd
        except BaseException:
            os.close(fd)
            raise

    def preflight_directories():
        # The workspace entry itself is removed from its owned parent last.
        fd = os.open(_path(path.parent), os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            require_owner_access(os.fstat(fd), path.parent)
        finally:
            os.close(fd)
        for name in ['.', *expected['directories']]:
            fd = parent_fd(name, directory=True)
            os.close(fd)

    for name in list(expected['files']) + list(expected['directories']): _name(name)
    preflight_directories()
    current, identities = manifest(path)
    if current != expected:
        raise ScratchError('Unique/modified/unexpected scratch contents; retained')
    if stable is not None: stable()
    if active_users(path):
        raise ScratchError('Active process uses verification workspace; retained')
    # Recheck after dependency/process callbacks before changing any content.
    again, again_ids = manifest(path)
    if again != expected or identities != again_ids:
        raise ScratchError('Scratch changed before disposal; retained')
    proof_data, current_proof_identity = _regular_bytes(proof)
    if proof_data != proof_expected or current_proof_identity != proof_identity:
        raise ScratchError('Successful verification record changed before disposal')
    metadata_supplement = None
    if sys.platform == 'darwin':
        metadata_supplement = _preserve_macos_metadata(lease, expected, identities, stable=stable)
        # Native metadata inspection can take time; activity must be checked
        # again after it, with every descriptor closed. Failure keeps the slot
        # and its already durable supplement for inspection.
        if active_users(path):
            raise ScratchError('Active process uses verification workspace after metadata preservation; retained')
        proof_data, current_proof_identity = _regular_bytes(proof)
        if proof_data != proof_expected or current_proof_identity != proof_identity:
            raise ScratchError('Successful verification record changed after metadata preservation')
    receipt = {'schema': 1, 'token': lease.token, 'path': str(path),
               'success_record': str(proof), 'success_record_sha256': proof_data['sha256'],
               'reconstruction': reconstruction, 'files': len(expected['files']),
               'logical_bytes': sum(row['size'] for row in expected['files'].values()),
               'tree_manifest_sha256': hashlib.sha256(json.dumps(expected, sort_keys=True).encode()).hexdigest(),
               'scope': 'new creating-process slot only; no historical deletion',
               'threat_model': 'cooperative processes and ordinary edits; no hostile administrator/kernel guarantee'}
    if metadata_supplement is not None:
        receipt['metadata_supplement'] = metadata_supplement
    # Check all directories again after callbacks/metadata/activity inspection,
    # before a covered receipt or the first unlink. Never chmod to force removal.
    preflight_directories()
    _json(lease.records / (lease.token + '-covered.json'), receipt)
    # Exact member deletion, with no wildcard, no symlink traversal, and only
    # the previously validated regular files. Failures preserve unknown work.
    for name in sorted(expected['files']):
        fd = parent_fd(name)
        try:
            leaf = PurePosixPath(name).name
            row, identity = _regular_bytes(leaf, dir_fd=fd)
            if row != expected['files'][name] or identity != identities[name]:
                raise ScratchError('File changed during disposal; remaining material retained')
            os.unlink(leaf, dir_fd=fd)
        finally:
            os.close(fd)
    for name in sorted(expected['directories'], key=lambda n: (-len(PurePosixPath(n).parts), n)):
        fd = parent_fd(name)
        try:
            observed = os.stat(PurePosixPath(name).name, dir_fd=fd, follow_symlinks=False)
            if not stat.S_ISDIR(observed.st_mode) or (observed.st_dev, observed.st_ino) != identities['dir:' + name]:
                raise ScratchError('Scratch directory identity changed before removal')
            os.rmdir(PurePosixPath(name).name, dir_fd=fd)
        finally: os.close(fd)
    final = path.lstat()
    if (final.st_dev, final.st_ino) != (lease.device, lease.inode):
        raise ScratchError('Owned scratch root changed before final removal')
    path.rmdir()
    _json(lease.records / (lease.token + '-removed.json'), {**receipt, 'removed': True,
          'removed_utc': datetime.now(timezone.utc).isoformat()})
    _LIVE_LEASES.pop(lease.token)
    return lease.records / (lease.token + '-removed.json')
