"""Experimental Mac byte preservation for PRL in owned diagnostic copies.

No PRL field is interpreted or waived. This does not isolate a hostile same-user
process able to clear flags. Interrupted controllers may leave the owned file
immutable; its exact path and flag must be inspected before manual cleanup.
"""
from contextlib import contextmanager
import os
from pathlib import Path
import stat

from autorouter import pipeline as p, handoff as h


@contextmanager
def preserve(path, owned_root, owner, *, cleanup_complete=lambda: True):
    path, owned_root = Path(path), Path(owned_root)
    if h.owned_destination(owner)!=owned_root:
        raise p.Rejected('PRL ownership witness differs')
    if (not path.is_absolute() or not owned_root.is_absolute()
            or path.resolve()!=path or owned_root.resolve()!=owned_root
            or owned_root == p.c.ROOT / '.runs'
            or p.c.ROOT / '.runs' not in owned_root.parents
            or owned_root not in path.parents or path.suffix != '.kicad_prl'
            or any(x.is_symlink() for x in (path, *path.parents))):
        raise p.Rejected('PRL guard requires canonical owned diagnostic copy')
    if not path.exists():
        yield {'policy':'mac-owned-prl-immutable-v1','present':False}
        return
    if not hasattr(os, 'chflags') or not hasattr(stat, 'UF_IMMUTABLE'):
        raise p.Rejected('PRL immutable flag unavailable')
    before = path.stat()
    if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or before.st_flags != 0:
        raise p.Rejected('PRL guard requires ordinary unflagged exclusive file')
    digest, flag = p.sha(path), stat.UF_IMMUTABLE
    event = {'policy':'mac-owned-prl-immutable-v1','present':True,
             'path':str(path),'sha256':digest,'flags_before':0,
             'flags_during':flag,'flags_restored':False,'bytes_unchanged':False}
    if h.owned_destination(owner)!=owned_root:raise p.Rejected('PRL owned output changed')
    os.chflags(path, flag, follow_symlinks=False)
    try:
        frozen = path.stat()
        if ((frozen.st_dev, frozen.st_ino) != (before.st_dev, before.st_ino)
                or frozen.st_flags != flag):
            raise p.Rejected('PRL freeze identity/flag differs')
        yield event
    finally:
        if h.owned_destination(owner)!=owned_root:raise p.Rejected('PRL owned output changed before restoration')
        if cleanup_complete() is not True:
            raise p.Rejected('PRL remains immutable: child cleanup not confirmed: '+str(path))
        current = path.lstat()
        if (not stat.S_ISREG(current.st_mode)
                or (current.st_dev,current.st_ino) != (before.st_dev,before.st_ino)):
            raise p.Rejected('PRL identity changed; refusing unrelated flag edit')
        if current.st_flags != flag:
            raise p.Rejected('PRL immutable flag changed unexpectedly')
        os.chflags(path, 0, follow_symlinks=False)
        event['flags_restored'] = path.stat().st_flags == 0
        event['bytes_unchanged'] = p.sha(path) == digest
        if not event['flags_restored'] or not event['bytes_unchanged']:
            raise p.Rejected('PRL bytes/flags changed during native execution')
