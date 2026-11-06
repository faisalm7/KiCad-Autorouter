"""Qualify an explicitly reviewed translation with the shared Native core.

Proposals and inspection are independent of a model. This operation writes only
a new isolated candidate; successful qualification is still not route acceptance.
The reused observer, FloorJob, process controller and publication guards retain
the same original-design, local-settings, cancellation and freshness boundaries.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import signal
import sys
import time

if __package__ in (None, ''):
    # Fixed owned entry permits the resource controller's cwd to be one job,
    # rather than scanning the installation's historical .runs.
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    __package__ = 'autorouter'

from . import config as c, floor_route as f, gui, handoff as h, pipeline as p
from . import local_settings, placement_clearance as pc, placement_intent as intent, provenance
from experiments.placement_native_proposal_v1 import contract
from experiments import placement_native_evidence as retained

KIND = 'autorouter.reviewed-placement-qualification.v1'
TOTAL_SECONDS, WORKER_SECONDS = 120, 105
DISK_BYTES, RSS_BYTES = 512 * 1024**2, 2 * 1024**3
AUTHORITY = ('accepted', 'routing_accepted', 'execution_authorized', 'approval_granted',
             'warning_acknowledged', 'human_PCB_approval', 'original_mutated')


def need(value, reason):
    if not value: raise ValueError('Placement qualification: ' + reason)


def code_pins():
    return {name: provenance.file_digest(c.ROOT / name)[0]
        for name in sorted(provenance.PLACEMENT_FILES)
        if name.startswith(('experiments/placement_native_proposal_v1/', 'experiments/constrained_placement_v1/'))}


def native_worker():
    return c.ROOT / 'experiments/placement_native_proposal_v1/worker.py'


def material(binding):
    need(c.NATIVE_VERSION == '10.0.7' and binding['runtime'] == str(c.ROOT), 'exact selected KiCad10.0.7 runtime required')
    def local():
        need(p.sha(c.ROOT / provenance.MANIFEST) == binding['runtime_manifest_sha256'], 'runtime changed')
        need(code_pins() == binding['code_sha256'], 'placement dependencies changed')
        need(p.sha(Path(binding['draft'])) == binding['draft_sha256'], 'reviewed draft changed')
        need(p.sha(c.PCBNEW.with_name('pcbnew.py')) == binding['wrapper_sha256'], 'Native wrapper changed')
        intent.current(binding['inspection'])
    local()
    need(p.tool_manifest() == binding['tools'], 'actual runtime/tool files changed')
    local()


def _binding(draft_path, digest):
    path = h.real_path(draft_path)
    raw = pc.read_bytes(path, 64 * 1024)
    need(type(digest) is str and len(digest) == 64 and hashlib.sha256(raw).hexdigest() == digest,
         'explicit unchanged draft SHA256 required')
    draft = intent.preferences._parse(raw, 64 * 1024)
    inspection = intent.inspect_saved(draft.get('source'))
    intent.validate_draft(inspection, draft)
    source = Path(inspection['source'])
    h.require_closed_review(inspection['source_hashes'])
    p.preflight(source)
    need(c.NATIVE_VERSION == '10.0.7' and (c.ROOT / provenance.MANIFEST).is_file(),
         'a curated selected10.0.7 runtime is required')
    value = dict(schema=1, kind=KIND, draft=str(path), draft_sha256=digest, intent=draft,
        inspection=inspection, runtime=str(c.ROOT), runtime_manifest_sha256=p.sha(c.ROOT / provenance.MANIFEST),
        wrapper_sha256=p.sha(c.PCBNEW.with_name('pcbnew.py')), code_sha256=code_pins(), tools=p.tool_manifest())
    material(value)
    return value


def _paths(output, binding):
    work = output / 'work'; name = Path(binding['inspection']['source']).name
    return work, {role: work / role / name for role in ('snapshot', 'candidate', 'refill-preimage', 'refill-native')}


def _options(binding):
    value = intent.validate_settings(binding['intent']['settings'])
    return contract.scope_options(scope=contract.MULTIPAD_SCOPE, selected=value['selected'], region_nm=value['region_nm'])


def _request(binding, work, name, board, candidate, hashes):
    st = work.stat(); options = _options(binding)
    translating = name == 'translate'
    return dict(schema=1, mode='translate' if translating else 'capture', board=str(board), source_hashes=hashes,
        candidate=str(candidate) if translating else None, moves_nm=binding['intent']['moves_nm'] if translating else {},
        job=str(work), job_identity=[st.st_dev, st.st_ino], application_policy='source-translation-v1',
        runtime_manifest_sha256=binding['runtime_manifest_sha256'], wrapper_sha256=binding['wrapper_sha256'],
        code_sha256=binding['code_sha256'], placement_scope=options['scope'], selected_footprints=options['selected'],
        allowed_region_nm=options['region_nm'])


def _argv(work, name):
    return [str(c.PYTHON), str(native_worker()), '--runtime', str(c.ROOT),
            '--request', str(work / (name + '-request.json')), '--output', str(work / (name + '-observation.json'))]


def _findings(native):
    need(native['blocking'] == native['exclusions'] == 0, 'blocking/excluded Native findings remain')
    for row in native['findings']:
        need(not row.get('excluded', False) and row['type'] in p.KNOWN_CHECKS | {'padstack_invalid'},
             'unknown or excluded Native finding')
        if row['type'] != 'unconnected_items':
            need(row['severity'] != 'error' and row['type'] not in p.CRITICAL_FINDINGS, 'critical Native finding remains')
    return sorted(f.canonical(row) for row in native['findings'] if row['type'] != 'unconnected_items')


def _metadata(paths, source):
    expected = source.with_suffix('.kicad_prl').exists()
    for board in (source, *paths):
        present = local_settings.check_current_metadata(board.with_suffix('.kicad_prl'))
        need(present or not expected, 'required local settings disappeared')


def proof(output, binding, data, *, replay=False):
    """Read actual request/process/Native/immutable proofs, not success flags."""
    need(type(replay) is bool, 'explicit replay mode required')
    work, paths = _paths(output, binding); source = Path(binding['inspection']['source'])
    need(type(data['schema']) is int and data['schema'] == 1 and data['kind'] == KIND and data['status'] == 'pending_candidate'
         and data['placement_qualified'] is True and data['external_exit_required'] is True, 'pending qualification absent')
    need(all(data.get(k) is False for k in AUTHORITY), 'unexpected approval authority')
    need(data['tools'] == binding['tools'] and data['binding_sha256'] == p.sha(output / 'binding.json')
         and data['budget_seconds'] == data['cpu_budget_seconds'] == WORKER_SECONDS, 'worker binding/budget differs')
    p.check_resource_accounting(data)
    hashes = binding['inspection']['source_hashes']; snapshot, candidate = paths['snapshot'], paths['candidate']
    need(gui.source_inventory(snapshot) == hashes, 'snapshot differs')
    before, after = pc.read_bytes(snapshot, contract.MAX_BYTES), pc.read_bytes(candidate, contract.MAX_BYTES)
    moves = binding['intent']['moves_nm']; options = _options(binding)
    immutable = contract.check_translation(before, after, moves, **options)
    need(immutable == data['immutable_check'], 'immutable design differs')
    preimage, refill = paths['refill-preimage'], paths['refill-native']
    pre_raw = pc.read_bytes(preimage, contract.MAX_BYTES)
    expected_raw = (contract.sx.dump(contract.translated_tree(before, moves, **options)) + '\n').encode()
    need(pre_raw == expected_raw, 'translated source bytes differ')
    expected = dict(hashes); expected[source.name] = hashlib.sha256(after).hexdigest()
    pre_hashes = dict(hashes); pre_hashes[source.name] = hashlib.sha256(pre_raw).hexdigest()
    need(gui.source_inventory(candidate) == data['candidate_hashes'] == expected
         and data['candidate'] == str(candidate) and gui.source_inventory(preimage) == pre_hashes, 'candidate/sidecars differ')
    need(contract.check_refill_reconstruction(pre_raw, pc.read_bytes(refill, contract.MAX_BYTES), after)
         == data['refill_transplant'], 'derived-fill reconstruction differs')
    history = None; details = None
    for name, board, captured, observed_raw in (('capture', snapshot, hashes, before),
            ('translate', snapshot, hashes, before), ('final-capture', candidate, expected, after)):
        request = f.read_json(work / (name + '-request.json'))
        expected_request = _request(binding, work, name, board, candidate, captured)
        if replay:
            st = work.stat()
            history = retained.retained_request_identity(request.get('job_identity'), (st.st_dev, st.st_ino), history)
            expected_request['job_identity'] = history
        need(f.canonical(request) == f.canonical(expected_request), 'Native request differs: ' + name)
        retained._success(f.process_check(work, data, name, [*f.SANDBOX, *_argv(work, name)]))
        observed = f.read_json(work / (name + '-observation.json')); translating = name == 'translate'
        need(type(observed['schema']) is int and observed['schema'] == 1 and observed['status'] == ('translated_copy' if translating else 'observed')
             and observed['native_version'] == '10.0.7' and observed['actual_native_observation'] is True
             and observed['request_sha256'] == p.sha(work / (name + '-request.json'))
             and observed['source'] == str(board) and observed['source_hashes'] == captured
             and observed['accepted'] is False and observed['routing_accepted'] is False
             and observed['native_save_board_called'] is False and observed['board_saved'] is translating
             and observed['application_policy'] == 'source-translation-v1'
             and observed['placement_scope'] == options['scope'] and observed['selected_footprints'] == options['selected']
             and observed['allowed_region_nm'] == options['region_nm']
             and observed['candidate'] == (str(candidate) if translating else None)
             and observed['observation'] == contract.inspect_board(observed_raw, scope=contract.MULTIPAD_SCOPE),
             'Native observation differs: ' + name)
        if details is None: details = observed['details']
        need(observed['details'] == details, 'Native connectivity/area identity changed')
        if translating:
            need(observed['candidate_hashes_before'] == hashes and observed['candidate_hashes_after'] == pre_hashes
                 and observed['saved_candidate_sha256'] == pre_hashes[source.name]
                 and observed['immutable_check'] == contract.check_translation(before, pre_raw, moves, **options), 'translation differs')
    natives = {}; drc_inputs = []
    for name, board, saved, captured in (('source-drc', snapshot, False, hashes),
            ('refill-drc', refill, True, pre_hashes), ('final-drc', candidate, False, expected)):
        target = board if saved else work / (name + '-input') / source.name
        native = f.check_drc_stage(work, data, name, board, target, saved, captured, schematic_parity=True)
        need(native == data[name.replace('-', '_')], 'Native DRC readback differs')
        natives[name] = native; drc_inputs.append(target)
    for native in natives.values():
        need(_findings(native) == _findings(natives['source-drc'])
             and native['ignored_checks'] == natives['source-drc']['ignored_checks'], 'warning/check policy changed')
    material(binding); _metadata([*paths.values(), *drc_inputs], source)
    return dict(candidate=str(candidate), candidate_sha256=expected[source.name], source_hashes=expected,
                original_source=str(source), original_source_hashes=hashes, findings=natives['final-drc'])


def _worker(output, binding_sha):
    started, cpu_start, children = time.monotonic(), time.process_time(), f.child_cpu()
    output = h.real_path(output)
    need(output.parent == c.ROOT/'.runs' and not (output/'work').exists(), 'fresh owned runtime worker directory required')
    binding = f.read_json(output / 'binding.json')
    need(p.sha(output / 'binding.json') == binding_sha, 'binding changed')
    need(f.canonical(_binding(binding['draft'], binding['draft_sha256'])) == f.canonical(binding), 'binding differs')
    work, paths = _paths(output, binding); source = Path(binding['inspection']['source'])
    need(source.parent != output and source.parent not in output.parents, 'worker output overlaps original source')
    def remaining():
        return min(WORKER_SECONDS - (time.monotonic()-started), WORKER_SECONDS - (time.process_time()-cpu_start + f.child_cpu()-children))
    job = f.FloorJob(work, WORKER_SECONDS, remaining, protect_local_settings=True)
    record = dict(schema=1, kind=KIND, status='failed', placement_qualified=False,
        **{key: False for key in AUTHORITY}, binding_sha256=binding_sha, tools=binding['tools'],
        budget_seconds=WORKER_SECONDS, cpu_budget_seconds=WORKER_SECONDS, steps=job.steps, external_exit_required=True)
    def stable():
        h.owned_destination(job._local_settings_owner)
        need(p.sha(output/'binding.json') == binding_sha, 'binding changed'); material(binding)
    def account():
        record.update(wall_seconds=time.monotonic()-started,
            **p.sequential_cpu_components(time.process_time()-cpu_start, f.child_cpu()-children, job.steps))
        if record['status'] != 'pending_candidate' or remaining() <= 0:
            record['placement_qualified'] = False
            if remaining() <= 0: record['status'] = 'budget_exhausted'
    def final():
        stable()
        if record['placement_qualified']: proof(output, binding, record)
    def native(name, board):
        stable(); spec = _request(binding, work, name, board, paths['candidate'], gui.source_inventory(board))
        p.save_json(work/(name+'-request.json'), spec); job.step(name, _argv(work, name)); stable()
    def drc(name, board, saved=False):
        stable(); before = gui.source_inventory(board)
        value = job.drc(name, board, save=saved, schematic_parity=True)
        checked = f.check_drc_stage(work, record, name, board,
            board if saved else work/(name+'-input')/board.name, saved, before, schematic_parity=True)
        need(value == checked, 'DRC stage differs'); record[name.replace('-', '_')] = value; stable()
    try:
        stable(); pc.copy_project(source.parent, paths['snapshot'].parent)
        drc('source-drc', paths['snapshot']); _findings(record['source_drc'])
        native('capture', paths['snapshot'])
        pc.copy_project(paths['snapshot'].parent, paths['candidate'].parent)
        native('translate', paths['snapshot'])
        pc.copy_project(paths['candidate'].parent, paths['refill-preimage'].parent)
        pc.copy_project(paths['refill-preimage'].parent, paths['refill-native'].parent)
        drc('refill-drc', paths['refill-native'], True)
        need(_findings(record['refill_drc']) == _findings(record['source_drc']), 'refill warning change')
        stable()
        before = pc.read_bytes(paths['refill-preimage'], contract.MAX_BYTES)
        need(pc.read_bytes(paths['candidate'], contract.MAX_BYTES) == before, 'candidate changed before refill')
        filled = pc.read_bytes(paths['refill-native'], contract.MAX_BYTES)
        paths['candidate'].write_bytes(contract.transplant_refill(before, filled))
        after = pc.read_bytes(paths['candidate'], contract.MAX_BYTES)
        record['refill_transplant'] = contract.check_refill_reconstruction(before, filled, after)
        record['immutable_check'] = contract.check_translation(pc.read_bytes(paths['snapshot'], contract.MAX_BYTES),
            after, binding['intent']['moves_nm'], **_options(binding))
        drc('final-drc', paths['candidate']); native('final-capture', paths['candidate'])
        record.update(status='pending_candidate', placement_qualified=True, candidate=str(paths['candidate']),
                      candidate_hashes=gui.source_inventory(paths['candidate']))
        account(); proof(output, binding, record); account()
    except (Exception, KeyboardInterrupt) as exc:
        record.update(status='cancelled' if isinstance(exc, KeyboardInterrupt) else 'failed',
                      placement_qualified=False, reason=type(exc).__name__ + ': ' + str(exc)); account()
    return f.publish(work, record, stable, account, remaining,
                     owned=lambda: h.owned_destination(job._local_settings_owner), final_check=final)


def _worker_argv(output, digest):
    return [str(c.ROOT / '.venv/bin/python'), '-B', str(c.ROOT/'autorouter/placement.py'),
            '--worker', str(output), '--binding-sha256', digest]


def _process_cost(process):
    retained._success(process)
    for key in ('wall_seconds', 'cpu_seconds', 'monitor_cpu_seconds'):
        value = process.get(key)
        need(type(value) in (int, float) and math.isfinite(value) and 0 <= value <= WORKER_SECONDS,
             'invalid complete process cost: ' + key)


def qualify(draft, draft_sha256, output, *, confirmed=False):
    """Explicit execution only; ordinary controls and CLI share this operation."""
    from .runner import run
    import shutil
    started, cpu_start = time.monotonic(), h.cpu_seconds()
    need(confirmed is True, 'explicit qualification action required')
    binding = _binding(draft, draft_sha256)
    output = h.real_path(output, existing=False); source = Path(binding['inspection']['source'])
    need(output.parent == c.ROOT/'.runs' and not output.exists() and source.parent not in output.parents,
         'fresh runtime .runs output outside the source project required')
    required = DISK_BYTES + 3 * 1024**3; free = shutil.disk_usage(output.parent).free
    need(free >= required, 'insufficient measured space for512MiB peak plus3GiB reserve')
    p.check_storage(active_root=output); material(binding)
    output.mkdir(mode=0o700); owner = {}; h.capture_destination(owner, output)
    p.save_json(output/'binding.json', binding); digest = p.sha(output/'binding.json')
    process = run(_worker_argv(output, digest), cwd=output, env=gui.child_environment(), log=output/'command.log',
        timeout=max(.001, min(WORKER_SECONDS, TOTAL_SECONDS-8-(time.monotonic()-started))),
        max_log_bytes=512*1024, max_group_rss_bytes=RSS_BYTES, max_workdir_bytes=DISK_BYTES)
    h.owned_destination(owner); p.save_json(output/'process.json', process)
    record = dict(schema=1, kind=KIND, status='failed', placement_qualified=False,
        **{key: False for key in AUTHORITY}, binding_sha256=digest, process_sha256=p.sha(output/'process.json'),
        total_seconds=TOTAL_SECONDS, worker_seconds=WORKER_SECONDS, measured_free_bytes=free, required_free_bytes=required,
        controller_exit_not_measured=True, publication_allowance_seconds=1)
    def remaining(): return min(TOTAL_SECONDS-(time.monotonic()-started), TOTAL_SECONDS-(h.cpu_seconds()-cpu_start))
    def stable():
        h.owned_destination(owner); need(p.sha(output/'binding.json') == digest, 'binding changed'); material(binding)
        need(p.sha(output/'process.json') == record['process_sha256'], 'process receipt changed')
        if record['placement_qualified']:
            need(pc.inventory(output/'work', max_bytes=DISK_BYTES) == record['worker_artifact_hashes'], 'worker evidence changed')
            work, boards = _paths(output, binding)
            _metadata([*boards.values(), *(work/(name+'-input')/source.name for name in ('source-drc','final-drc'))], source)
    def account():
        record.update(wall_seconds=time.monotonic()-started, full_cpu_seconds=h.cpu_seconds()-cpu_start)
        if record['status'] != 'pending_candidate' or remaining() < 1:
            record['placement_qualified'] = False
            if remaining() < 1: record['status'] = 'budget_exhausted'
    try:
        _process_cost(process); need(process['resource_guards']['max_group_rss_bytes'] == RSS_BYTES
            and process['resource_guards']['max_workdir_bytes'] == DISK_BYTES, 'resource guards differ')
        data = f.read_json(output/'work/result.json'); result = proof(output, binding, data)
        record.update(status='pending_candidate', placement_qualified=True, result=result,
            worker_artifact_hashes=pc.inventory(output/'work', max_bytes=DISK_BYTES))
    except (Exception, KeyboardInterrupt) as exc:
        record.update(status='cancelled' if isinstance(exc, KeyboardInterrupt) or process['status']=='cancelled' else 'failed',
                      reason=type(exc).__name__ + ': ' + str(exc))
    account()
    return f.publish(output, record, stable, account, remaining, owned=lambda: h.owned_destination(owner), final_check=stable)


def check(output):
    """Full read-only proof at use; never grants approval or runs Native."""
    output = h.real_path(output)
    need(output.parent == c.ROOT/'.runs', 'exact runtime job required')
    identity = retained.retained_tree_identity(output, c.ROOT); artifacts = h.evidence_witness(output)
    outer = f.read_json(output/'result.json'); binding = f.read_json(output/'binding.json')
    need(f.canonical(_binding(binding['draft'], binding['draft_sha256'])) == f.canonical(binding), 'binding stale')
    need(type(outer['schema']) is int and outer['schema'] == 1 and outer['kind'] == KIND
         and outer['status'] == 'pending_candidate' and outer['placement_qualified'] is True
         and all(outer.get(key) is False for key in AUTHORITY), 'completed pending placement required')
    need(outer['total_seconds'] == TOTAL_SECONDS and outer['worker_seconds'] == WORKER_SECONDS
         and outer['controller_exit_not_measured'] is True and outer['publication_allowance_seconds'] == 1
         and all(type(outer[k]) in (int, float) and 0 <= outer[k] <= TOTAL_SECONDS-1 for k in ('wall_seconds','full_cpu_seconds')),
         'complete resource evidence differs')
    process = f.read_json(output/'process.json'); _process_cost(process)
    digest = p.sha(output/'binding.json')
    need(outer['binding_sha256'] == digest and outer['process_sha256'] == p.sha(output/'process.json')
         and process['argv'] == _worker_argv(output, digest) and process['cwd'] == str(output)
         and max(process['wall_seconds'],process['cpu_seconds']) <= WORKER_SECONDS
         and process['wall_seconds'] <= outer['wall_seconds'] and process['cpu_seconds'] <= outer['full_cpu_seconds'],
         'outer process/binding differs')
    need(process['resource_guards']['max_group_rss_bytes'] == RSS_BYTES
         and process['resource_guards']['max_workdir_bytes'] == DISK_BYTES
         and process['resource_guards']['os_enforced'] is False
         and pc.inventory(output/'work', max_bytes=DISK_BYTES) == outer['worker_artifact_hashes'], 'worker contents/limits changed')
    actual = proof(output, binding, f.read_json(output/'work/result.json'), replay=True)
    need(actual == outer['result'], 'placement result differs')
    material(binding)
    need(h.evidence_witness(output) == artifacts and retained.retained_tree_identity(output, c.ROOT) == identity,
         'evidence changed during readback')
    return dict(actual, current=True, placement_qualified=True, **{key:False for key in AUTHORITY},
                evidence=str(output), evidence_hashes=artifacts, binding=binding)


def source_guard(output, witness, *, verify_review=None):
    """Internal handoff after off-thread check(); never a model/preset input.

    The caller retains this checked witness and a review-lifecycle fence. All
    material is reread at the normal GUI actions/adoption edges, without repeating
    Native validation or rerunning search. Closing/editing/rejecting the placement
    review must make verify_review raise. No return value grants authority.
    """
    output = h.real_path(output); expected = copy.deepcopy(witness)
    need(expected.get('current') is True and expected.get('placement_qualified') is True
         and expected.get('evidence') == str(output) and output.parent == c.ROOT/'.runs'
         and all(expected.get(k) is False for k in AUTHORITY), 'a checked pending placement witness is required')
    need(verify_review is None or callable(verify_review), 'trusted review-lifecycle callback required')
    work, boards = _paths(output, expected['binding'])
    source = Path(expected['binding']['inspection']['source'])
    def fresh():
        if verify_review is not None:
            need(verify_review() is None, 'review lifecycle must grant no result authority')
        need(h.evidence_witness(output) == expected['evidence_hashes'], 'checked placement evidence changed')
        material(expected['binding'])
        _metadata([*boards.values(), *(work/(name+'-input')/source.name for name in ('source-drc','final-drc'))], source)
        need(h.evidence_witness(output) == expected['evidence_hashes'], 'placement evidence changed during origin check')
        if verify_review is not None:
            need(verify_review() is None, 'review lifecycle changed')
    return gui.SourceGuard(Path(expected['candidate']), fresh)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--draft'); parser.add_argument('--draft-sha256'); parser.add_argument('--output')
    parser.add_argument('--qualify', action='store_true'); parser.add_argument('--check')
    parser.add_argument('--worker', help=argparse.SUPPRESS); parser.add_argument('--binding-sha256', help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    def interrupted(*_): raise KeyboardInterrupt
    handlers = {sig:signal.getsignal(sig) for sig in (signal.SIGINT,signal.SIGTERM)}
    try:
        for sig in handlers: signal.signal(sig, interrupted)
        if args.worker:
            need(not any((args.qualify,args.check,args.draft,args.output)), 'mixed worker action')
            result = _worker(h.real_path(args.worker), args.binding_sha256)
        elif args.check:
            need(not any((args.qualify,args.draft,args.output,args.binding_sha256)), 'mixed readback action')
            result = check(args.check)
        else:
            need(args.qualify and args.draft and args.draft_sha256 and args.output and args.binding_sha256 is None,
                 'explicit draft/hash/fresh output and --qualify required')
            result = qualify(args.draft, args.draft_sha256, args.output, confirmed=True)
        print(json.dumps(result, sort_keys=True))
        return 0 if result.get('placement_qualified') is True else 2
    finally:
        for sig, handler in handlers.items(): signal.signal(sig, handler)


if __name__ == '__main__': raise SystemExit(main())
