"""Bounded disposable review copies; no GUI, native worker or live application."""
from pathlib import Path
import hashlib
import os
import resource
import signal
import stat
import time
import uuid
from . import config as c, floor_route as f, placement_clearance as pc, pipeline as p
from .pipeline import Rejected, check_result, save_json, validation_readback_session
from . import comparison as cmp

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
    """Bind checker/helper source, lock and selected-runtime manifest."""
    try:c.current_native_selection()
    except (ValueError,OSError) as exc:raise Rejected('selected native toolchain changed: '+str(exc)) from exc
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
    manifest=c.ROOT/'runtime-distribution.json'
    if os.path.lexists(manifest):
        result[str(manifest)]=digest(pc.read_bytes(manifest,256*1024))
    return result


def evidence_witness(path):
    files, directories = pc.inventory(path, max_bytes=EVIDENCE_BYTES,
        max_files=4000, max_entries=8000, with_directories=True)
    return {'files': files, 'directories': list(directories)}


class ReviewProjectOpen(Rejected):
    """Observed KiCad lock: closing the review is an operational precondition."""


def require_closed_review(project_hashes):
    # An absent lock is not proof that every editor is closed. Keep the explicit
    # user acknowledgement and all exact material checks, including backups.
    if any(Path(name).suffix.casefold() == '.lck' for name in project_hashes):
        raise ReviewProjectOpen('Close the disposable review PCB and schematic editors, then use '
            'File > Close Project in KiCad project manager before Accept intent. '
            'A KiCad lock file is still present; no acceptance was recorded.')


def delivery_kwargs(native_toolchain=None, experimental_schematic_parity=False):
    """Caller authority only; never construct tools from a delivery receipt."""
    p.experimental_route_record(native_toolchain, experimental_schematic_parity)
    return ({} if native_toolchain is None else
            dict(native_toolchain=native_toolchain,
                 experimental_schematic_parity=experimental_schematic_parity))


def application_kwargs(native_toolchain=None, experimental_schematic_parity=False, comparison_context=None):
    """Application authority stays separate from Native worker arguments."""
    worker=delivery_kwargs(native_toolchain,experimental_schematic_parity)
    cmp.delivery_record(comparison_context,native_toolchain,experimental_schematic_parity)
    return {**worker,**({'comparison_context':comparison_context} if comparison_context is not None else {})}


def check_delivery_context(record, native_toolchain=None, experimental_schematic_parity=False, *, comparison_context=None):
    if cmp.check_delivery(record,comparison_context,native_toolchain,experimental_schematic_parity):return
    expected = p.experimental_route_record(native_toolchain, experimental_schematic_parity)
    if native_toolchain is None:
        if 'native_delivery_context' in record:
            raise Rejected('experimental delivery requires explicit caller toolchain context')
        p.check_experimental_route(record)
    elif f.canonical(record.get('native_delivery_context')) != f.canonical(expected):
        raise Rejected('experimental delivery context differs from caller')


def delivery_record(native_toolchain=None, experimental_schematic_parity=False, *, comparison_context=None):
    expected = p.experimental_route_record(native_toolchain, experimental_schematic_parity)
    return {**({'native_delivery_context': expected} if expected else {}),
        **cmp.delivery_record(comparison_context,native_toolchain,experimental_schematic_parity)}


def delivery_guards(receipt, report, native_toolchain, preview=None, destination=None, *, additional=(), material=None, comparison_context=None):
    """Replay existing non-byte guards after all delivery material/tool reads."""
    cmp.delivery_record(comparison_context,native_toolchain)
    comparison=cmp.check_record(Path(receipt).parent,report,comparison_context)
    from . import strategy as pruning
    if pruning.native7_marked(Path(receipt).parent,report):
        if native_toolchain is not None or comparison_context is not None:
            raise Rejected('Improve delivery cannot mix caller authority')
        pairs=[]
        if preview is not None:
            from .review_view import check_native_preview
            pairs=check_native_preview(destination,preview)
        pruning.check_native7_final(Path(receipt).parent,report,additional=additional,
            material=material,pairs=pairs)
        return
    if native_toolchain is None and not comparison:
        if preview is not None:check_delivery_context(preview)
        return
    pairs = []
    if preview is not None:
        from .review_view import check_experimental_preview
        pairs = check_experimental_preview(destination, preview, native_toolchain, native_toolchain is not None,
            comparison_context=comparison_context)
    packets = [(Path(receipt).parent, report), *additional]
    for folder, data in packets:
        if comparison and Path(folder)!=Path(receipt).parent:check_delivery_context(data,comparison_context=comparison_context)
        p.check_experimental_local_settings(folder, data, native_toolchain)
    if material is not None:material()
    if comparison:cmp.require_context(comparison_context)
    from . import local_settings as local
    local.check_final_events(packets, c.CLI if comparison else native_toolchain.cli, pairs=pairs)


def _review_validation_identity():
    from .strategy import _native7_context_identity
    state=p._readback_session.get()
    if state is None:raise Rejected('review validation operation required')
    return _native7_context_identity(state)


def _review_validation_guard(directory,report,identity):
    """Keep the original fully checked Context through pure delivery writes.

    This does not validate a parent or authorize a worker. The caller already
    owes its complete central read, constant byte material and late full
    delivery/preview/PRL guards. No accepted result is stored or returned here.
    """
    from . import strategy
    context=strategy.native7_incumbent_context(directory,report)
    return strategy._native7_context_guard(context,identity)


def review_policy(report, directory, *, native_toolchain=None, experimental_schematic_parity=False, comparison_context=None):
    """Same explicit policy dispatch as the central checker; no inferred downgrade."""
    cmp.delivery_record(comparison_context,native_toolchain,experimental_schematic_parity)
    if not cmp.check_record(directory,report,comparison_context):
        p.check_experimental_route(report, native_toolchain, experimental_schematic_parity)
    from . import placement_strategy as ps
    policy = ps.POLICY if ps.recognize(report, directory) else f.receipt_policy(report, directory)
    schemas = {'native': 1, pc.POLICY: 3, f.SEARCH_POLICY: 4, ps.POLICY: 5}
    if (type(report.get('schema')) is not int or report['schema'] != schemas.get(policy)
            or policy not in schemas or 'diagnostic_schema' in report):
        raise Rejected('guidance-policy GUI handoff is not yet qualified for this receipt')
    return policy


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
    except BaseException:retain()  # No current positive after corrective-write failure.


def _review_copy(receipt, output, start, cpu_start, render=False, lifecycle=None, *, native_toolchain=None, experimental_schematic_parity=False, comparison_context=None):
    ctx = application_kwargs(native_toolchain, experimental_schematic_parity, comparison_context)
    destination = None; created = False; before_created = False; preview = None
    validation_guard=None
    record = {'schema': 1, 'status': 'rejected', 'native_validation_performed': False,
              'budget_seconds': SECONDS, 'cpu_budget_seconds': SECONDS,
              'accounting_point': 'Stored totals precede final publication checks; final wall and parent-plus-waited-child CPU caps include them. These are observed acceptance ceilings, not OS quotas.'}
    record.update(delivery_record(native_toolchain, experimental_schematic_parity, comparison_context=comparison_context))
    if lifecycle is not None:lifecycle.update(record=record,name='review.json')

    def cap():
        if time.monotonic() - start > SECONDS or cpu_seconds() - cpu_start > SECONDS:
            raise Rejected('review copy exceeded 30-second wall or full CPU ceiling')

    def inventory(path, *, contents=False, evidence=False):
        cap()
        value = evidence_witness(path) if evidence else pc.inventory(path, contents=contents,
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
        cmp.delivery_path(receipt.parent,comparison_context,'route');cmp.delivery_path(Path(output).absolute(),comparison_context,'review')
        raw = pc.read_bytes(receipt, PROJECT_BYTES); receipt_digest = digest(raw)
        report = f.read_json(receipt)
        report_canonical=f.canonical(report)
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
        policy = review_policy(report, receipt.parent, **ctx)
        identity = {'candidate': str(candidate), 'candidate_sha256': report['candidate_sha256'],
                    'input_policy': policy}
        if candidate_hashes.get(candidate.name) != identity['candidate_sha256']:
            raise Rejected('captured candidate differs from receipt')
        project = destination / 'project'

        def byte_material():
            cap()
            if f.canonical(report)!=report_canonical:
                raise Rejected('in-memory review routing receipt changed')
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
                if native_toolchain is None and sha(c.CLI) != preview['plotter_sha256']:
                    raise Rejected('review plotter changed after rendering')
                for name, expected in preview.get('input_trees', {}).items():
                    if inventory(destination / name) != expected:
                        raise Rejected('review preview input file set changed after rendering')
                for name, expected in preview['files'].items():
                    if digest(pc.read_bytes(destination / name, PROJECT_BYTES)) != expected:
                        raise Rejected('review preview changed after rendering')
            if validation_guard is not None:validation_guard()
            cap()

        def material():
            byte_material()
            delivery_guards(receipt, report, native_toolchain, preview, destination, material=byte_material, comparison_context=comparison_context)

        def central_check():
            material()
            verified = check_result(receipt, **ctx); cap()
            if (verified.get('current') is not True or verified.get('applied') is not False
                    or any(verified.get(key, 'native' if key == 'input_policy' else None) != value
                           for key, value in identity.items())):
                raise Rejected('central receipt policy or candidate identity changed')
            # No subprocess-bearing check follows this material sample.
            material()

        validation_identity=_review_validation_identity()
        central_check()
        # Only a fully checked, source-derived selected7 parent uses the
        # narrower render callbacks below. A receipt marker grants no reuse.
        from .strategy import native7_parent
        native7_review = (native_toolchain is None and comparison_context is None
                          and native7_parent(receipt.parent, report) is not None)
        if native7_review:
            if _review_validation_identity()!=validation_identity:
                raise Rejected('review validation policy changed during initial check')
            validation_guard=_review_validation_guard(receipt.parent,report,validation_identity)
        copy_material=byte_material if native7_review else material
        destination.mkdir(parents=True, exist_ok=False); created = True
        capture_destination(lifecycle,destination)
        project.mkdir()
        for relative, payload in captured.items():
            cap(); target = project / relative; target.parent.mkdir(parents=True, exist_ok=True)
            with target.open('xb') as stream:
                stream.write(payload)
        del captured
        copy_material()
        if render:
            before = destination / 'before'; before.mkdir()
            for relative, payload in original_capture.items():
                cap(); target = before / relative; target.parent.mkdir(parents=True, exist_ok=True)
                with target.open('xb') as stream:
                    stream.write(payload)
            before_created = True; del original_capture
            copy_material()
            from .review_view import render as render_view
            remaining = lambda: max(0, min(SECONDS - (time.monotonic() - start), SECONDS - (cpu_seconds() - cpu_start)))
            # Plot workers already preserve/check their own input and completed
            # output bytes. Keep every captured byte witness between plots;
            # replay the full parent/tool/worker/PRL fence immediately after.
            render_material = byte_material if native7_review else material
            preview = render_view(destination, before / source.name, project / candidate.name, report, remaining, render_material, **ctx)
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
                      limits='Disposable complete project files for manual review only; no fresh native check, applied result, GUI opening or live-editor approval. Saving/editing invalidates the original validation claim. Local bounded inventories are finite samples, not atomic authentication or protection against hostile concurrent writers, abrupt termination or power loss. Optional rendering checks the pinned plotter binary; this copy command does not rerun native validation or revalidate other installed native tools.')
        # The selected7 parent was fully read before any copy or plot. Its
        # captured bytes and original authority/policy stay constant; the full
        # delivery guard above checks the current preview and metadata. Pure
        # copies/record construction need no second child/trial replay.
        if native7_review:
            if render:byte_material()
            else:material()
        else:central_check()
        account(); cap()
        expected = f.canonical(record)
        save_json(destination / 'review.json', record)
        if f.canonical(record) != expected or f.canonical(f.read_json(destination / 'review.json')) != expected:
            raise Rejected('ready review metadata changed during publication')
        if native7_review:
            # After the checked pure copy/render, only this separate JSON was
            # written. Recheck current bytes, authority, Native/plot/PRL guards.
            material()
        else:
            central_check()
        if f.canonical(record) != expected or f.canonical(f.read_json(destination / 'review.json')) != expected:
            raise Rejected('ready review metadata changed after validation')
        if not native7_review:material()
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


def review_copy(receipt, output, *, render=False, native_toolchain=None, experimental_schematic_parity=False, comparison_context=None):
    """Create one new disposable project from centrally verified captured bytes."""
    start = time.monotonic(); cpu_start = cpu_seconds()
    ctx = application_kwargs(native_toolchain, experimental_schematic_parity, comparison_context)
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
            record = _review_copy(receipt, output, start, cpu_start, render, lifecycle, **ctx)
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


def _review_choice(review_path, output, choice, start, cpu_start, lifecycle=None, *, native_toolchain=None, experimental_schematic_parity=False, comparison_context=None):
    """Record a design choice; it never approves/applies a PCB or invokes KiCad."""
    ctx = application_kwargs(native_toolchain, experimental_schematic_parity, comparison_context)
    destination = None; created = False
    validation_guard=None
    record = {'schema': 1, 'status': 'rejected', 'choice_recorded': False,
              'routing_accepted': False, 'applied': False,
              'native_validation_performed': False, 'human_pcb_approval_observed': False,
              'fresh_native_validation_required': True,
              'budget_seconds': SECONDS, 'cpu_budget_seconds': SECONDS}
    record.update(delivery_record(native_toolchain, experimental_schematic_parity, comparison_context=comparison_context))
    if lifecycle is not None:lifecycle.update(record=record,name='choice.json')
    def cap():
        if time.monotonic() - start > SECONDS or cpu_seconds() - cpu_start > SECONDS:
            raise Rejected('review choice exceeded 30-second wall or full CPU ceiling')
    def inventory(path, *, evidence=False):
        cap(); value = evidence_witness(path) if evidence else pc.inventory(path, max_bytes=EVIDENCE_BYTES if evidence else PROJECT_BYTES,
                max_files=4000 if evidence else 2000, max_entries=8000 if evidence else 4000)
        cap(); return value
    def account():
        record.update(wall_seconds=time.monotonic() - start,
                      total_cpu_seconds=cpu_seconds() - cpu_start)
        record['within_budget'] = record['wall_seconds'] <= SECONDS and record['total_cpu_seconds'] <= SECONDS
    def invalidate():
        for name in ('choice.json', 'choice.json.partial'):
            path = destination / name
            if path.exists() or path.is_symlink():
                path.rename(destination / ('invalidated-choice-' + uuid.uuid4().hex + '-' + name))
    try:
        if type(choice) is not str or choice not in {'accept', 'reject'}:
            raise Rejected('review choice must be accept or reject')
        cmp.delivery_path(Path(review_path).absolute().parent,comparison_context,'review');cmp.delivery_path(Path(output).absolute(),comparison_context,'choice')
        review_path = real_path(review_path); review_hash = digest(pc.read_bytes(review_path, PROJECT_BYTES))
        review = f.read_json(review_path)
        check_delivery_context(review, native_toolchain, experimental_schematic_parity, comparison_context=comparison_context)
        if (type(review.get('schema')) is not int or review['schema'] != 1
                or review.get('status') != 'ready_for_manual_review'):
            raise Rejected('current ready review record required')
        receipt = real_path(review['receipt']); receipt_hash = digest(pc.read_bytes(receipt, PROJECT_BYTES))
        if receipt_hash != review['receipt_sha256']:
            raise Rejected('reviewed routing receipt changed')
        report = f.read_json(receipt); report_canonical=f.canonical(report)
        review_canonical=f.canonical(review);policy = review_policy(report, receipt.parent, **ctx)
        source = real_path(report['source']); candidate = real_path(report['candidate'])
        project = real_path(review['project'])
        if (candidate != receipt.parent / 'candidate' / source.name
                or project != review_path.parent / 'project'
                or review.get('board') != str(project / source.name)
                or review.get('input_policy') != policy
                or review.get('source_receipt_schema') != report['schema']
                or review.get('verified_candidate_sha256') != report['candidate_sha256']):
            raise Rejected('review/receipt/candidate identity differs')
        source_hashes = inventory(source.parent); evidence_hashes = inventory(receipt.parent, evidence=True)
        candidate_hashes = inventory(candidate.parent); project_hashes = inventory(project)
        if (source_hashes != review['source_project_hashes']
                or evidence_hashes != review['routing_evidence_hashes']
                or candidate_hashes != review['initial_project_hashes']
                or candidate_hashes.get(source.name) != report['candidate_sha256']):
            raise Rejected('reviewed source, candidate or routing evidence changed')
        board_same = project_hashes.get(source.name) == report['candidate_sha256']
        if choice == 'accept': require_closed_review(project_hashes)
        if choice == 'accept' and not board_same:
            raise Rejected('reviewed board changed; obtain a newly validated review before accepting')
        runtime = runtime_inventory(); preview = review.get('preview')
        if (review_path.parent / 'preview.html').exists() and not isinstance(preview, dict):
            raise Rejected('preview binding missing')
        def preview_material():
            if preview is None: return
            from .pipeline import sha
            if native_toolchain is None and sha(c.CLI) != preview['plotter_sha256']:
                raise Rejected('review plotter pin changed')
            if inventory(review_path.parent / 'before') != source_hashes:
                raise Rejected('reviewed original preview changed')
            for name, expected in preview['input_trees'].items():
                path = real_path(review_path.parent / name)
                if not path.is_relative_to(review_path.parent) or inventory(path) != expected:
                    raise Rejected('review preview input changed')
            for name, expected in preview['files'].items():
                path = real_path(review_path.parent / name)
                if not path.is_relative_to(review_path.parent) or digest(pc.read_bytes(path, PROJECT_BYTES)) != expected:
                    raise Rejected('review preview changed')
        identity = {'candidate': str(candidate), 'candidate_sha256': report['candidate_sha256'], 'input_policy': policy}
        def byte_material():
            cap()
            if f.canonical(report)!=report_canonical or f.canonical(review)!=review_canonical:
                raise Rejected('in-memory review choice input changed')
            if (digest(pc.read_bytes(review_path, PROJECT_BYTES)) != review_hash
                    or digest(pc.read_bytes(receipt, PROJECT_BYTES)) != receipt_hash
                    or runtime_inventory() != runtime):
                raise Rejected('review/receipt/runtime changed during choice')
            if (inventory(source.parent) != source_hashes or inventory(receipt.parent, evidence=True) != evidence_hashes
                    or inventory(candidate.parent) != candidate_hashes or inventory(project) != project_hashes):
                raise Rejected('review choice material changed')
            preview_material()
            if validation_guard is not None:validation_guard()
            cap()
        def material():
            byte_material()
            delivery_guards(receipt, report, native_toolchain, preview, review_path.parent, material=byte_material, comparison_context=comparison_context)
        def central_check():
            material(); verified = check_result(receipt, **ctx); cap()
            if (verified.get('current') is not True or verified.get('applied') is not False
                    or any(verified.get(key, 'native' if key == 'input_policy' else None) != value for key, value in identity.items())):
                raise Rejected('central reviewed candidate identity changed')
            material()
        destination = real_path(output, existing=False)
        if destination.exists(): raise Rejected('review choice output already exists')
        for protected in (source.parent, receipt.parent, review_path.parent):
            if destination == protected or protected in destination.parents:
                raise Rejected('choice output must be outside source, routing evidence and review')
        validation_identity=_review_validation_identity()
        central_check()
        from .strategy import native7_parent
        native7_choice = (native_toolchain is None and comparison_context is None
                          and native7_parent(receipt.parent, report) is not None)
        if native7_choice:
            if _review_validation_identity()!=validation_identity:
                raise Rejected('review validation policy changed during initial check')
            validation_guard=_review_validation_guard(receipt.parent,report,validation_identity)
        destination.mkdir(parents=True, exist_ok=False); created = True
        capture_destination(lifecycle,destination)
        names = set(candidate_hashes) | set(project_hashes)
        changes = {'added': sorted(set(project_hashes) - set(candidate_hashes)),
                   'removed': sorted(set(candidate_hashes) - set(project_hashes)),
                   'changed': sorted(name for name in names & set(candidate_hashes) & set(project_hashes)
                                     if candidate_hashes[name] != project_hashes[name])}
        record.update(status='disposition_recorded', choice_recorded=True, choice=choice,
            meaning='Separate-project design choice only. No candidate application, native acceptance, human PCB approval or electrical/manufacturing approval is recorded.',
            review=str(review_path), review_sha256=review_hash, receipt=str(receipt), receipt_sha256=receipt_hash,
            input_policy=policy, source_receipt_schema=report['schema'], validated_candidate=str(candidate),
            validated_candidate_sha256=report['candidate_sha256'], review_project=str(project),
            observed_review_project_hashes=project_hashes, candidate_board_unchanged=board_same,
            review_project_matches_recorded_candidate=project_hashes == candidate_hashes, review_project_changes=changes,
            original_source_hashes=source_hashes, routing_evidence_hashes=evidence_hashes, runtime_source_sha256=runtime,
            saved_native_findings=report['native'], saved_metrics=report['metrics'],
            next_action=('Freshly validate the bound original candidate against its unchanged original complete project before exporting any separate accepted project. Edited GUI rules/metadata are not authoritative.'
                         if choice == 'accept' else 'Keep the original project. The review copy and evidence remain available; this command deletes nothing.'),
            accounting_point='Stored totals precede final publication. Whole wall/parent-plus-waited-child CPU caps and all material checks include final readback; observed ceilings, not OS quotas.')
        (byte_material if native7_choice else central_check)()
        account(); cap(); expected = f.canonical(record)
        save_json(destination / 'choice.json', record)
        if f.canonical(f.read_json(destination / 'choice.json')) != expected or f.canonical(record) != expected:
            raise Rejected('review choice changed during publication')
        if native7_choice:
            # Only pure disposition construction and this separate write
            # follow the full central read. Keep current authority/preview/PRL.
            material()
        else:
            central_check()
        if f.canonical(f.read_json(destination / 'choice.json')) != expected or f.canonical(record) != expected:
            raise Rejected('review choice changed during final readback')
        cap(); return record
    except (Exception, KeyboardInterrupt) as exc:
        if created:
            invalidate(); record.update(status='cancelled' if isinstance(exc, KeyboardInterrupt) else 'rejected',
                choice_recorded=False, error=type(exc).__name__ + ': ' + str(exc))
            account()
            try:
                save_json(destination / 'choice.json', record)
                if f.canonical(f.read_json(destination / 'choice.json')) != f.canonical(record): invalidate()
            except (Exception, KeyboardInterrupt): invalidate()
        if isinstance(exc, KeyboardInterrupt): raise Rejected('review choice cancelled') from exc
        raise


def review_choice(review, output, choice, *, native_toolchain=None, experimental_schematic_parity=False, comparison_context=None):
    """Persist accept/reject intent with stale checks; no PCB application/approval."""
    start = time.monotonic(); cpu_start = cpu_seconds()
    ctx = application_kwargs(native_toolchain, experimental_schematic_parity, comparison_context)
    previous = {sig: signal.getsignal(sig) for sig in (signal.SIGINT, signal.SIGTERM)}
    lifecycle={}
    def interrupted(*_): raise KeyboardInterrupt
    try:
        for sig in previous: signal.signal(sig, interrupted)
        with validation_readback_session():
            record = _review_choice(review, output, choice, start, cpu_start,lifecycle, **ctx)
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
