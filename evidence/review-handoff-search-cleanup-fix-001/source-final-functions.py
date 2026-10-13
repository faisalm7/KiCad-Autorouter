def owned_destination(lifecycle):
    """A saved pathname alone cannot authorize corrections after replacement."""
    path=real_path(lifecycle['destination'])
    current=path.lstat()
    if not stat.S_ISDIR(current.st_mode) or (current.st_dev,current.st_ino)!=lifecycle['directory_identity']:
        raise Rejected('owned review output directory was replaced')
    return path

def capture_destination(lifecycle,destination):
    if lifecycle is not None:
        info=destination.lstat()
        lifecycle.update(created=True,destination=destination,directory_identity=(info.st_dev,info.st_ino))

def finish_session(record, output, start, cpu_start, name, lifecycle=None):
    """Include memo cleanup in delivery caps; retain any over-cap publication."""
    destination=owned_destination(lifecycle) if lifecycle is not None else real_path(output)
    wall, cpu = time.monotonic() - start, cpu_seconds() - cpu_start
    if wall <= SECONDS and cpu <= SECONDS:return record
    for filename in (name, 'preview.html' if name == 'review.json' else None):
        if filename is not None and (destination / filename).exists():
            (destination / filename).rename(destination / ('invalidated-session-' + uuid.uuid4().hex + '-' + filename))
    record.update(status='rejected', choice_recorded=False, within_budget=False,
                  wall_seconds=wall, total_cpu_seconds=cpu, error='session cleanup exceeded delivery budget')
    save_json(destination / name, record)
    raise Rejected('session cleanup exceeded delivery budget')

def failed_session(lifecycle, exc):
    """Correct only a positive publication created by this invocation."""
    if not lifecycle.get('created'):return
    record=lifecycle['record']
    if not lifecycle.get('completed') and record.get('status') not in {'ready_for_manual_review','disposition_recorded'}:return
    destination=owned_destination(lifecycle);name=lifecycle['name']
    def retain():
        for filename in (name,name+'.partial','preview.html' if name=='review.json' else None):
            if filename is not None:
                path=destination/filename
                if path.exists() or path.is_symlink():path.rename(destination/('invalidated-session-'+uuid.uuid4().hex+'-'+filename))
    retain()
    record.update(status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'rejected',
                  choice_recorded=False,error=type(exc).__name__+': '+str(exc))
    expected=f.canonical(record)
    try:
        save_json(destination/name,record)
        if f.canonical(record)!=expected or f.canonical(f.read_json(destination/name))!=expected:
            raise Rejected('corrective session publication changed')
    except BaseException:retain()

def review_copy(receipt, output, *, render=False):
    """Create one new disposable project from centrally verified captured bytes."""
    start = time.monotonic(); cpu_start = cpu_seconds()
    previous = {sig: signal.getsignal(sig) for sig in (signal.SIGINT, signal.SIGTERM)}
    lifecycle={}

    def interrupted(*_):
        raise KeyboardInterrupt

    try:
        for sig in previous:
            signal.signal(sig, interrupted)
        if type(render) is not bool:
            raise Rejected('render must be a Boolean')
        with validation_readback_session():
            record = _review_copy(receipt, output, start, cpu_start, render, lifecycle)
            lifecycle['completed']=True
        return finish_session(record, output, start, cpu_start, 'review.json',lifecycle)
    except BaseException as exc:
        try:failed_session(lifecycle,exc)
        except BaseException as correction:
            raise Rejected('review cleanup could not safely invalidate owned output: '+str(correction)) from exc
        if isinstance(exc,KeyboardInterrupt):raise Rejected('review copy cancelled during session cleanup') from exc
        raise
    finally:
        for sig, handler in previous.items():
            signal.signal(sig, handler)

def review_choice(review, output, choice):
    """Persist accept/reject intent with stale checks; no PCB application/approval."""
    start = time.monotonic(); cpu_start = cpu_seconds()
    previous = {sig: signal.getsignal(sig) for sig in (signal.SIGINT, signal.SIGTERM)}
    lifecycle={}
    def interrupted(*_): raise KeyboardInterrupt
    try:
        for sig in previous: signal.signal(sig, interrupted)
        with validation_readback_session():
            record = _review_choice(review, output, choice, start, cpu_start,lifecycle)
            lifecycle['completed']=True
        return finish_session(record, output, start, cpu_start, 'choice.json',lifecycle)
    except BaseException as exc:
        try:failed_session(lifecycle,exc)
        except BaseException as correction:
            raise Rejected('choice cleanup could not safely invalidate owned output: '+str(correction)) from exc
        if isinstance(exc,KeyboardInterrupt):raise Rejected('review choice cancelled during session cleanup') from exc
        raise
    finally:
        for sig, handler in previous.items(): signal.signal(sig, handler)
