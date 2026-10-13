def evidence_witness(path):
    files, directories = pc.inventory(path, max_bytes=EVIDENCE_BYTES,
        max_files=4000, max_entries=8000, with_directories=True)
    return {'files': files, 'directories': list(directories)}

def review_policy(report, directory):
    """Same explicit policy dispatch as the central checker; no inferred downgrade."""
    from . import placement_strategy as ps
    policy = ps.POLICY if ps.recognize(report, directory) else f.receipt_policy(report, directory)
    schemas = {'native': 1, pc.POLICY: 3, f.SEARCH_POLICY: 4, ps.POLICY: 5}
    if (type(report.get('schema')) is not int or report['schema'] != schemas.get(policy)
            or policy not in schemas or 'diagnostic_schema' in report):
        raise Rejected('guidance-policy GUI handoff is not yet qualified for this receipt')
    return policy

def finish_session(record, output, start, cpu_start, name):
    """Include memo cleanup in delivery caps; retain any over-cap publication."""
    wall, cpu = time.monotonic() - start, cpu_seconds() - cpu_start
    if wall <= SECONDS and cpu <= SECONDS:return record
    destination = real_path(output)
    for filename in (name, 'preview.html' if name == 'review.json' else None):
        if filename is not None and (destination / filename).exists():
            (destination / filename).rename(destination / ('invalidated-session-' + uuid.uuid4().hex + '-' + filename))
    record.update(status='rejected', choice_recorded=False, within_budget=False,
                  wall_seconds=wall, total_cpu_seconds=cpu, error='session cleanup exceeded delivery budget')
    save_json(destination / name, record)
    raise Rejected('session cleanup exceeded delivery budget')

def review_copy(receipt, output, *, render=False):
    """Create one new disposable project from centrally verified captured bytes."""
    start = time.monotonic(); cpu_start = cpu_seconds()
    previous = {sig: signal.getsignal(sig) for sig in (signal.SIGINT, signal.SIGTERM)}

    def interrupted(*_):
        raise KeyboardInterrupt

    try:
        for sig in previous:
            signal.signal(sig, interrupted)
        if type(render) is not bool:
            raise Rejected('render must be a Boolean')
        with validation_readback_session():
            record = _review_copy(receipt, output, start, cpu_start, render)
        return finish_session(record, output, start, cpu_start, 'review.json')
    finally:
        for sig, handler in previous.items():
            signal.signal(sig, handler)

def review_choice(review, output, choice):
    """Persist accept/reject intent with stale checks; no PCB application/approval."""
    start = time.monotonic(); cpu_start = cpu_seconds()
    previous = {sig: signal.getsignal(sig) for sig in (signal.SIGINT, signal.SIGTERM)}
    def interrupted(*_): raise KeyboardInterrupt
    try:
        for sig in previous: signal.signal(sig, interrupted)
        with validation_readback_session():
            record = _review_choice(review, output, choice, start, cpu_start)
        return finish_session(record, output, start, cpu_start, 'choice.json')
    finally:
        for sig, handler in previous.items(): signal.signal(sig, handler)
