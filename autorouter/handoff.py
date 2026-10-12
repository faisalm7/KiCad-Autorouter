"""Bounded disposable review copies; no GUI, native worker or live application."""
from pathlib import Path
import hashlib
import os
import resource
import signal
import time
import uuid
from . import config as c, floor_route as f, placement_clearance as pc
from .pipeline import Rejected, check_result, save_json

SECONDS = 30
PROJECT_BYTES = 32 * 1024 * 1024
EVIDENCE_BYTES = 100 * 1024 * 1024


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def cpu_seconds():
    own = resource.getrusage(resource.RUSAGE_SELF)
    child = resource.getrusage(resource.RUSAGE_CHILDREN)
    return own.ru_utime + own.ru_stime + child.ru_utime + child.ru_stime


def real_path(value, *, existing=True):
    path = Path(value).absolute()
    if '..' in path.parts or any(p.is_symlink() for p in (path, *path.parents)):
        raise Rejected('review paths must be real canonical paths without symlinks')
    return path.resolve(strict=existing)


def runtime_inventory():
    """Bind the checker/helper source and lock, not installed native binaries."""
    result = {}; total = 0
    with os.scandir(c.ROOT / 'autorouter') as entries:
        for count, entry in enumerate(entries, 1):
            if count > 256:
                raise Rejected('review runtime entry ceiling')
            if entry.name.endswith('.py'):
                raw = pc.read_bytes(entry.path, 8 * 1024 * 1024 - total)
                total += len(raw); result[str(Path(entry.path))] = digest(raw)
    for path in (Path(__file__).absolute(), c.ROOT / 'toolchain.lock.json'):
        result[str(path)] = digest(pc.read_bytes(path, PROJECT_BYTES))
    return result


def _review_copy(receipt, output, start, cpu_start, render=False):
    destination = None; created = False; before_created = False; preview = None
    record = {'schema': 1, 'status': 'rejected', 'native_validation_performed': False,
              'budget_seconds': SECONDS, 'cpu_budget_seconds': SECONDS,
              'accounting_point': 'Stored totals precede final publication checks; final wall and parent-plus-waited-child CPU caps include them. These are observed acceptance ceilings, not OS quotas.'}

    def cap():
        if time.monotonic() - start > SECONDS or cpu_seconds() - cpu_start > SECONDS:
            raise Rejected('review copy exceeded 30-second wall or full CPU ceiling')

    def inventory(path, *, contents=False, evidence=False):
        cap()
        value = pc.inventory(path, contents=contents,
                             max_bytes=EVIDENCE_BYTES if evidence else PROJECT_BYTES,
                             max_files=4000 if evidence else 2000, max_entries=8000 if evidence else 4000)
        cap(); return value

    def account():
        record.update(wall_seconds=time.monotonic() - start,
                      total_cpu_seconds=cpu_seconds() - cpu_start)
        record['within_budget'] = record['wall_seconds'] <= SECONDS and record['total_cpu_seconds'] <= SECONDS

    def invalidate():
        # Only metadata in this invocation's new directory is moved. Keep the
        # disposable project and all interrupted/ready bytes as evidence.
        for path in (destination / 'review.json', destination / 'review.json.partial', destination / 'preview.html'):
            if path.exists() or path.is_symlink():
                path.rename(destination / ('invalidated-review-' + uuid.uuid4().hex + '-' + path.name))

    try:
        cap(); receipt = real_path(receipt)
        raw = pc.read_bytes(receipt, PROJECT_BYTES); receipt_digest = digest(raw)
        report = f.read_json(receipt)
        if digest(pc.read_bytes(receipt, PROJECT_BYTES)) != receipt_digest:
            raise Rejected('receipt changed while reading review input')
        if not isinstance(report, dict):
            raise Rejected('review receipt must be an object')
        source = real_path(report['source'])
        candidate = real_path(report['candidate'])
        if candidate != receipt.parent / 'candidate' / source.name:
            raise Rejected('review candidate does not belong to receipt')
        destination = real_path(output, existing=False)
        if destination.exists():
            raise Rejected('review output already exists')
        for protected in (source.parent, receipt.parent):
            if destination == protected or protected in destination.parents:
                raise Rejected('review copy must be outside source and evidence directories')

        # Bound complete trees before calling legacy check_result, whose own
        # reads remain sampled rather than race-free. Never adopt later trees.
        evidence_hashes = inventory(receipt.parent, evidence=True)
        source_hashes = inventory(source.parent)
        original_capture = inventory(source.parent, contents=True) if render else None
        if render and {name: digest(value) for name, value in original_capture.items()} != source_hashes:
            raise Rejected('source changed during preview capture')
        captured = inventory(candidate.parent, contents=True)
        candidate_hashes = {name: digest(value) for name, value in captured.items()}
        runtime_hashes = runtime_inventory(); cap()
        policy = f.receipt_policy(report, receipt.parent)
        if ((policy == 'native' and (type(report.get('schema')) is not int or report['schema'] != 1))
                or (policy == pc.POLICY and report.get('schema') != 3)
                or policy not in {'native', pc.POLICY}
                or 'diagnostic_schema' in report):
            raise Rejected('guidance-policy GUI handoff is not yet qualified for this receipt')
        identity = {'candidate': str(candidate), 'candidate_sha256': report['candidate_sha256'],
                    'input_policy': policy}
        if candidate_hashes.get(candidate.name) != identity['candidate_sha256']:
            raise Rejected('captured candidate differs from receipt')
        project = destination / 'project'

        def material():
            cap()
            if runtime_inventory() != runtime_hashes:
                raise Rejected('review runtime source or toolchain lock changed')
            if digest(pc.read_bytes(receipt, PROJECT_BYTES)) != receipt_digest:
                raise Rejected('receipt changed while preparing review copy')
            if inventory(source.parent) != source_hashes:
                raise Rejected('source project changed while preparing review copy')
            if inventory(receipt.parent, evidence=True) != evidence_hashes:
                raise Rejected('routing evidence changed while preparing review copy')
            if inventory(candidate.parent) != candidate_hashes:
                raise Rejected('candidate project changed while preparing review copy')
            if created and inventory(project) != candidate_hashes:
                raise Rejected('copied project changed while preparing review copy')
            if before_created and inventory(destination / 'before') != source_hashes:
                raise Rejected('copied original changed while preparing review preview')
            if preview is not None:
                from .pipeline import sha
                if sha(c.CLI) != preview['plotter_sha256']:
                    raise Rejected('review plotter changed after rendering')
                for name, expected in preview['files'].items():
                    if digest(pc.read_bytes(destination / name, PROJECT_BYTES)) != expected:
                        raise Rejected('review preview changed after rendering')
            cap()

        def central_check():
            material()
            verified = check_result(receipt); cap()
            if (verified.get('current') is not True or verified.get('applied') is not False
                    or any(verified.get(key, 'native' if key == 'input_policy' else None) != value
                           for key, value in identity.items())):
                raise Rejected('central receipt policy or candidate identity changed')
            # No subprocess-bearing check follows this material sample.
            material()

        central_check()
        destination.mkdir(parents=True, exist_ok=False); created = True
        project.mkdir()
        for relative, payload in captured.items():
            cap(); target = project / relative; target.parent.mkdir(parents=True, exist_ok=True)
            with target.open('xb') as stream:
                stream.write(payload)
        del captured
        material()
        if render:
            before = destination / 'before'; before.mkdir()
            for relative, payload in original_capture.items():
                cap(); target = before / relative; target.parent.mkdir(parents=True, exist_ok=True)
                with target.open('xb') as stream:
                    stream.write(payload)
            before_created = True; del original_capture
            material()
            from .review_view import render as render_view
            remaining = lambda: max(0, min(SECONDS - (time.monotonic() - start), SECONDS - (cpu_seconds() - cpu_start)))
            preview = render_view(destination, before / source.name, project / candidate.name, report, remaining, material)
            material(); record['preview'] = preview
        record.update(status='ready_for_manual_review', input_policy=policy,
                      source_receipt_schema=report['schema'], receipt=str(receipt),
                      receipt_sha256=receipt_digest, verified_candidate_sha256=identity['candidate_sha256'],
                      candidate_sha256=candidate_hashes[candidate.name], project=str(project),
                      board=str(project / candidate.name),
                      project_file=str(project / candidate.with_suffix('.kicad_pro').name),
                      review_instructions='Open project_file in KiCad project manager, then Tools > PCB Editor. Run DRC with zone refill and all severities visible. Review every warning. Close and discard to reject; originals remain unchanged.',
                      initial_project_hashes=candidate_hashes,
                      source_project_hashes=source_hashes, routing_evidence_hashes=evidence_hashes,
                      runtime_source_sha256=runtime_hashes,
                      limits='Disposable complete project files for manual review only; no fresh native check, applied result, GUI opening or live-editor approval. Saving/editing invalidates the original validation claim. Local bounded inventories are finite samples, not atomic authentication or protection against hostile concurrent writers, abrupt termination or power loss. Installed native tool binaries are not revalidated by this copy command.')
        central_check(); account(); cap()
        expected = f.canonical(record)
        save_json(destination / 'review.json', record)
        if f.canonical(record) != expected or f.canonical(f.read_json(destination / 'review.json')) != expected:
            raise Rejected('ready review metadata changed during publication')
        central_check()
        if f.canonical(record) != expected or f.canonical(f.read_json(destination / 'review.json')) != expected:
            raise Rejected('ready review metadata changed after validation')
        material()
        if f.canonical(record) != expected or f.canonical(f.read_json(destination / 'review.json')) != expected:
            raise Rejected('ready review metadata changed during final material check')
        cap(); return record
    except (Exception, KeyboardInterrupt) as exc:
        if created:
            invalidate()
            record.update(status='cancelled' if isinstance(exc, KeyboardInterrupt) else 'rejected',
                          error=type(exc).__name__ + ': ' + str(exc))
            account()
            try:
                save_json(destination / 'review.json', record)
                if f.canonical(f.read_json(destination / 'review.json')) != f.canonical(record):
                    raise Rejected('corrective review metadata differs')
            except (Exception, KeyboardInterrupt):
                invalidate()
        if isinstance(exc, KeyboardInterrupt):
            raise Rejected('review copy cancelled') from exc
        raise


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
        return _review_copy(receipt, output, start, cpu_start, render)
    finally:
        for sig, handler in previous.items():
            signal.signal(sig, handler)
