"""Explicit Mac protection of unchanged PRL bytes in fresh owned Job copies.

This guards actual Native input, never restores bytes or waives any PRL field.
It is not isolation from a hostile same-user process that can clear file flags.
"""
from contextlib import contextmanager
import os
from pathlib import Path
import stat
from . import pipeline as p,handoff as h
POLICY='mac-owned-prl-immutable-v1'
JOB_POLICY='job-owned-prl-immutable-v1'

def canonical(value):
    path=Path(value)
    if (not path.is_absolute() or '..' in path.parts or path.resolve()!=path
            or any(x.is_symlink() for x in (path,*path.parents))):
        raise p.Rejected('PRL requires canonical owned paths')
    return path

@contextmanager
def preserve(path,owned_root,owner,*,cleanup_complete=lambda:True):
    path,owned_root=canonical(path),canonical(owned_root)
    if h.owned_destination(owner)!=owned_root:raise p.Rejected('PRL ownership witness differs')
    if owned_root not in path.parents or path.suffix!='.kicad_prl':raise p.Rejected('PRL must belong to captured owned root')
    if not path.exists():
        yield {'policy':POLICY,'present':False};return
    if not hasattr(os,'chflags') or not hasattr(stat,'UF_IMMUTABLE'):raise p.Rejected('PRL immutable flag unavailable')
    before=path.lstat()
    if not stat.S_ISREG(before.st_mode) or before.st_nlink!=1 or before.st_flags!=0:raise p.Rejected('PRL guard requires ordinary unflagged exclusive file')
    digest,flag=p.sha(path),stat.UF_IMMUTABLE
    event={'policy':POLICY,'present':True,'path':str(path),'sha256':digest,'flags_before':0,'flags_during':flag,'flags_restored':False,'bytes_unchanged':False}
    if h.owned_destination(owner)!=owned_root:raise p.Rejected('PRL owned output changed')
    os.chflags(path,flag,follow_symlinks=False)
    try:
        frozen=path.stat()
        if (frozen.st_dev,frozen.st_ino)!=(before.st_dev,before.st_ino) or frozen.st_flags!=flag:raise p.Rejected('PRL freeze identity/flag differs')
        yield event
    finally:
        if h.owned_destination(owner)!=owned_root:raise p.Rejected('PRL owned output changed before restoration')
        if cleanup_complete() is not True:raise p.Rejected('PRL remains immutable: child cleanup not confirmed: '+str(path))
        current=path.lstat()
        if not stat.S_ISREG(current.st_mode) or (current.st_dev,current.st_ino)!=(before.st_dev,before.st_ino):raise p.Rejected('PRL identity changed; refusing unrelated flag edit')
        if current.st_flags!=flag:raise p.Rejected('PRL immutable flag changed unexpectedly')
        os.chflags(path,0,follow_symlinks=False)
        event['flags_restored']=path.stat().st_flags==0;event['bytes_unchanged']=p.sha(path)==digest
        if not event['flags_restored'] or not event['bytes_unchanged']:raise p.Rejected('PRL bytes/flags changed during native execution')

def drc_step(job,name,argv):
    """Journal real worker and guard outcomes even if step/cleanup rejects."""
    start=len(job.steps);state={'complete':False};event=None;native_error=None
    def worker():
        matches=[s for s in job.steps[start:] if s.get('name')==name and s.get('cwd')==str(job.out)]
        return matches[0] if len(matches)==1 else None
    try:
        with preserve(Path(argv[-1]).with_suffix('.kicad_prl'),job.out,job._local_settings_owner,cleanup_complete=lambda:state['complete']) as event:
            try:result=job.step(name,argv,allowed=(0,5))
            except (Exception,KeyboardInterrupt) as exc:
                native_error=type(exc).__name__+': '+str(exc);raise
            finally:
                result=worker();state['complete']=result is not None and result.get('cleanup_complete') is True
        if not state['complete']:raise p.Rejected('PRL Native child cleanup not confirmed')
        return result
    except (Exception,KeyboardInterrupt) as exc:
        if event is not None:
            event['guard_error']=type(exc).__name__+': '+str(exc)
            if native_error is not None:event['native_error']=native_error
        raise
    finally:
        result=worker()
        if result is not None:
            if h.owned_destination(job._local_settings_owner)!=job.out:raise p.Rejected('PRL Job root changed before worker journal')
            result['local_settings_policy']=JOB_POLICY;result['local_settings_protection']=event
            p.save_json(job.out/(name+'-process.json'),result)

def check_event(directory,binding,process):
    """Strict opt-in marker/event replay; legacy unmarked receipts unchanged."""
    marker=binding.get('local_settings_policy');worker_marker=process.get('local_settings_policy')
    if marker is None and worker_marker is None:return
    if marker!=JOB_POLICY or worker_marker!=JOB_POLICY:raise p.Rejected('PRL Job policy marker differs')
    root=canonical(Path(directory));board=canonical(Path(binding['input']));path=board.with_suffix('.kicad_prl')
    if root not in board.parents:raise p.Rejected('PRL validation input outside Job root')
    if process.get('cleanup_complete') is not True:raise p.Rejected('PRL child cleanup not confirmed')
    event=process.get('local_settings_protection');before=binding['before']
    if path.exists():
        canonical(path)
        if not stat.S_ISREG(path.lstat().st_mode) or path.stat().st_nlink!=1 or path.stat().st_flags!=0:raise p.Rejected('PRL retained current file/flags differ')
    if path.name not in before:
        expected={'policy':POLICY,'present':False}
    else:
        if (not hasattr(stat,'UF_IMMUTABLE') or not path.exists() or not stat.S_ISREG(path.lstat().st_mode)
                or path.stat().st_nlink!=1 or path.stat().st_flags!=0 or p.sha(path)!=before[path.name]):
            raise p.Rejected('PRL current retained bytes/flags differ')
        expected={'policy':POLICY,'present':True,'path':str(path),'sha256':before[path.name],'flags_before':0,'flags_during':stat.UF_IMMUTABLE,'flags_restored':True,'bytes_unchanged':True}
    if (type(event) is not dict or set(event)!=set(expected)
            or any(type(event[k]) is not type(v) or event[k]!=v for k,v in expected.items())):
        raise p.Rejected('PRL guard event differs from exact Native input')
