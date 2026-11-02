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


def active_users(path):
    """Owned-process path check; private0700 slot excludes other ordinary users.

    No process command lines or file contents are inspected or recorded.
    Unsupported/inaccessible process inspection fails closed.
    """
    path = str(_path(path))
    if sys.platform == 'darwin':
        exe = shutil.which('lsof') or '/usr/sbin/lsof'
        result = subprocess.run([exe, '-nP', '-a', '-u', str(os.getuid()), '-Fpn'],
                                capture_output=True, text=True, timeout=30)
        if result.returncode != 0 or result.stderr or len(result.stdout) > 16 * 1024 ** 2:
            raise ScratchError('Process-use inspection unavailable or incomplete')
        pid = None; found = []
        for line in result.stdout.splitlines():
            if line.startswith('p'): pid = line[1:]
            if line.startswith('n') and (line[1:] == path or line[1:].startswith(path + '/')):
                found.append(pid)
        return sorted(set(found))
    if sys.platform.startswith('linux'):
        found = []
        for process in Path('/proc').iterdir():
            if not process.name.isdigit(): continue
            try:
                if process.stat().st_uid != os.getuid(): continue
                targets = [process / 'cwd', *list((process / 'fd').iterdir())]
                for target in targets:
                    try: name = os.readlink(target)
                    except FileNotFoundError: continue
                    if name == path or name.startswith(path + '/'): found.append(process.name)
            except FileNotFoundError: continue
            except PermissionError as exc: raise ScratchError('Process-use inspection denied') from exc
        return sorted(set(found))
    raise ScratchError('Automatic verification cleanup is not qualified on this platform')


def dispose(lease, expected, *, success_record, reconstruction, required_paths=(), stable=None):
    """Delete only this process's new slot after independent caller coverage.

    `expected` must come from verified recovery sources, not merely inventory of
    whatever currently occupies the slot.  Failed checks retain all material.
    """
    if (not isinstance(lease, Lease) or lease.owner_pid != os.getpid()
            or _LIVE_LEASES.get(lease.token) is not lease):
        raise ScratchError('Only the live creating process may dispose its new slot')
    path = _path(lease.path)
    if path.name != 'verification-workspace' or path.parent.name != '.local-backups':
        raise ScratchError('Out-of-scope disposal path')
    st = path.lstat()
    if (st.st_dev, st.st_ino) != (lease.device, lease.inode) or not stat.S_ISDIR(st.st_mode):
        raise ScratchError('Owned scratch directory identity changed')
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
    for name in list(expected['files']) + list(expected['directories']): _name(name)
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
    receipt = {'schema': 1, 'token': lease.token, 'path': str(path),
               'success_record': str(proof), 'success_record_sha256': proof_data['sha256'],
               'reconstruction': reconstruction, 'files': len(expected['files']),
               'logical_bytes': sum(row['size'] for row in expected['files'].values()),
               'tree_manifest_sha256': hashlib.sha256(json.dumps(expected, sort_keys=True).encode()).hexdigest(),
               'scope': 'new creating-process slot only; no historical deletion',
               'threat_model': 'cooperative processes and ordinary edits; no hostile administrator/kernel guarantee'}
    _json(lease.records / (lease.token + '-covered.json'), receipt)
    # Exact member deletion, with no wildcard, no symlink traversal, and only
    # the previously validated regular files. Failures preserve unknown work.
    def parent_fd(name):
        fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        root_now = os.fstat(fd)
        if (root_now.st_dev, root_now.st_ino) != (lease.device, lease.inode):
            os.close(fd)
            raise ScratchError('Owned root changed during disposal')
        try:
            relative = []
            for component in PurePosixPath(name).parts[:-1]:
                next_fd = os.open(component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
                relative.append(component)
                observed = os.fstat(next_fd)
                if (observed.st_dev, observed.st_ino) != identities['dir:' + '/'.join(relative)]:
                    os.close(next_fd)
                    raise ScratchError('Scratch ancestor directory identity changed')
                os.close(fd); fd = next_fd
            return fd
        except BaseException:
            os.close(fd)
            raise
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
