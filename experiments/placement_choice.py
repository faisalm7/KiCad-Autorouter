"""Qualify one exact reviewed placement draft on a fresh copy, never route/apply it.

Explicit --qualify is required. Retained source DRC/capture are dependencies;
translation, refill, final full-schematic DRC and final capture are new checks.
check(output, expected_runtime=...) replays retained proofs without executing Native or granting approval.
"""
import argparse
import copy
import fcntl
import hashlib
import json
import os
from pathlib import Path
import resource
import signal
import stat
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / 'experiments/placement_native_proposal_v1'
KIND = 'reviewed-placement-choice-v1'
TOTAL, INNER, DISK, RSS = 120, 110, 512 * 1024**2, 2 * 1024**3
ENTRY = time.monotonic()
PARENT_CPU = time.process_time()
CHILD_CPU = sum((resource.getrusage(resource.RUSAGE_CHILDREN).ru_utime,
                 resource.getrusage(resource.RUSAGE_CHILDREN).ru_stime))
AUTHORITY = ('accepted', 'execution_authorized', 'routing_accepted', 'human_approval',
             'warning_acknowledged', 'routing_performed', 'original_mutated')


def need(condition, reason):
    if not condition: raise ValueError('Placement choice: ' + reason)


def canonical(value): return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)
def digest(value): return hashlib.sha256(canonical(value).encode()).hexdigest()
def equal(left, right): return canonical(left) == canonical(right)
def cpu():
    return sum(row.ru_utime + row.ru_stime for row in
               (resource.getrusage(resource.RUSAGE_SELF), resource.getrusage(resource.RUSAGE_CHILDREN)))


def json_bytes(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            need(key not in result, 'duplicate JSON field')
            result[key] = value
        return result
    def constant(_): raise ValueError('Placement choice: nonfinite JSON')
    value = json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)
    canonical(value)  # Also reject exponent overflow such as 1e999.
    return value


def read_binding(path):
    # Bootstrap only: the installed context cannot be selected before this read.
    path = Path(path)
    need(not any(p.is_symlink() for p in (path, *path.parents)), 'linked binding')
    with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK), 'rb') as stream:
        before = os.fstat(stream.fileno())
        need(stat.S_ISREG(before.st_mode) and before.st_size <= 2 * 1024**2, 'bounded regular binding required')
        raw = stream.read(before.st_size + 1); after = os.fstat(stream.fileno())
    need(len(raw) == before.st_size and (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
         == (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns), 'binding changed while reading')
    return json_bytes(raw)


def code_pins():
    names = ('experiments/placement_choice.py', 'experiments/placement_review.py',
             'experiments/placement_native_evidence.py')
    return {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in names}


def validate_draft(review, draft):
    """Regenerate every field; a digest is a byte binding, not proof of human origin."""
    need(type(draft) is dict and type(draft.get('revision')) is int
         and 1 <= draft['revision'] <= 256, 'exact bounded draft revision required')
    candidate = copy.copy(review)
    candidate.pose = candidate.contract.validate_moves(candidate.observation, draft.get('moves_nm'), **candidate.options)
    candidate.moves = copy.deepcopy(draft['moves_nm']); candidate.revision = draft['revision']
    expected = candidate.decision(acknowledged=True, accepted=True, current_witness=review.witness)
    need(equal(draft, expected), 'draft fields, authority, witness, facts, options or pose differ')
    return candidate


def prepare(runtime, evidence, protocol, draft, draft_sha256):
    from experiments.placement_native_proposal_v1 import driver
    c, p, f, gui, h, pc = driver.context(Path(runtime))
    from experiments.placement_native_proposal_v1 import contract
    from experiments import placement_review
    from autorouter.preferences import _parse
    runtime, evidence, protocol, draft = (h.real_path(Path(x)) for x in (runtime, evidence, protocol, draft))
    need(type(draft_sha256) is str and len(draft_sha256) == 64
         and all(ch in '0123456789abcdef' for ch in draft_sha256), 'explicit lowercase draft SHA256 required')
    raw = pc.read_bytes(draft, 64 * 1024)
    need(hashlib.sha256(raw).hexdigest() == draft_sha256, 'draft bytes changed')
    review = placement_review.load(runtime, evidence, protocol)
    need(review.options['scope'] == contract.MULTIPAD_SCOPE
         and review.witness['application_policy'] == 'source-translation-v1'
         and review.witness['derivation']['removed_routes'] == [], 'unaltered multipad source required')
    choice = validate_draft(review, _parse(raw, 64 * 1024))
    spec = f.read_json(protocol)
    binding = dict(schema=1, kind=KIND, runtime=str(runtime), evidence=str(evidence), protocol=str(protocol),
        draft=str(draft), draft_sha256=draft_sha256, retained_witness_sha256=digest(review.witness),
        source=review.witness['original_source'], source_hashes=review.witness['original_source_hashes'],
        options=review.options, moves_nm=choice.moves, pose_sha256=digest(choice.pose),
        bridge_code_sha256=code_pins(), native_code_sha256=driver.code_pins(),
        protocol_sha256=p.sha(protocol), runtime_manifest_sha256=spec['runtime_manifest_sha256'],
        wrapper_sha256=spec['wrapper_sha256'], tools=p.tool_manifest(),
        total_seconds=TOTAL, inner_seconds=INNER, disk_bytes=DISK, group_rss_bytes=RSS)
    material(binding, review)
    return binding, review, choice


def material(binding, review):
    """Cheap late fence after the complete retained proof was read, no Native."""
    from experiments.placement_native_proposal_v1 import driver
    c, p, f, gui, h, pc = driver.context(Path(binding['runtime']))
    from autorouter import local_settings
    def local():
        need(code_pins() == binding['bridge_code_sha256'] and driver.code_pins() == binding['native_code_sha256'], 'code changed')
        need(p.sha(Path(binding['draft'])) == binding['draft_sha256']
             and p.sha(Path(binding['protocol'])) == binding['protocol_sha256'], 'draft/protocol changed')
        need(pc.inventory(Path(binding['evidence']), max_bytes=DISK) == review.witness['artifact_hashes'], 'retained evidence changed')
        source = Path(binding['source'])
        need(gui.source_inventory(source) == binding['source_hashes'], 'original source changed')
        spec = f.read_json(Path(binding['protocol']))
        need(driver.source_manifest_unchanged(spec, p), 'original provenance changed')
        local_settings.check_current_metadata(source.with_suffix('.kicad_prl'))
    local()
    need(driver.runtime_unchanged(Path(binding['runtime']), c.PCBNEW.with_name('pcbnew.py'), binding, binding['tools'], p), 'runtime/tools changed')
    local()




def work_prl(output, binding):
    """Last metadata fence after all tool/material reads; byte hashes cannot see flags."""
    from autorouter import local_settings
    source = Path(binding['source']); name = source.with_suffix('.kicad_prl').name
    boards = [source, *(Path(output) / 'work' / role / source.name for role in
              ('snapshot', 'candidate', 'refill-preimage', 'refill-native', 'final-drc-input'))]
    for board in boards:
        present = local_settings.check_current_metadata(board.with_suffix('.kicad_prl'))
        need(present or name not in binding['source_hashes'], 'required retained local settings disappeared')


def loaded(output, expected_runtime):
    # A retained file may name a runtime, never choose executable/import code.
    expected_runtime = Path(expected_runtime).absolute()
    binding = read_binding(Path(output) / 'binding.json')
    need(binding.get('runtime') == str(expected_runtime), 'binding runtime differs from caller-trusted runtime')
    fresh, review, choice = prepare(binding['runtime'], binding['evidence'], binding['protocol'],
                                    binding['draft'], binding['draft_sha256'])
    need(equal(binding, fresh), 'binding changed or stale')
    return binding, review, choice


def request(binding, work, name, source, candidate, hashes, moves):
    identity = work.stat()
    return dict(schema=1, mode='translate' if name == 'translate' else 'capture', board=str(source),
        source_hashes=hashes, candidate=str(candidate) if name == 'translate' else None,
        moves_nm=moves if name == 'translate' else {}, job=str(work), job_identity=[identity.st_dev, identity.st_ino],
        application_policy='source-translation-v1', runtime_manifest_sha256=binding['runtime_manifest_sha256'],
        wrapper_sha256=binding['wrapper_sha256'], code_sha256=binding['native_code_sha256'],
        placement_scope=binding['options']['scope'], selected_footprints=binding['options']['selected'],
        allowed_region_nm=binding['options']['region_nm'])


def native_argv(c, runtime, work, name):
    return [str(c.PYTHON), str(HERE / 'worker.py'), '--runtime', str(runtime),
            '--request', str(work / (name + '-request.json')), '--output', str(work / (name + '-observation.json'))]


def check_native_request(actual, expected, *, retained=False, previous=None):
    """Live requests keep exact current identity; only closed replay permits remount."""
    need(type(retained) is bool, 'explicit retained replay mode required')
    historical = None
    if retained:
        from experiments import placement_native_evidence as old
        historical = old.retained_request_identity(actual.get('job_identity'), expected['job_identity'], previous)
        expected = dict(expected, job_identity=historical)
    need(equal(actual, expected), 'Native request differs')
    return historical


def proof(output, binding, review, choice, data, *, retained=False):
    """Read actual new Native/PRL/process/immutable proofs, never a prior pass flag."""
    from experiments.placement_native_proposal_v1 import driver
    c, p, f, gui, h, pc = driver.context(Path(binding['runtime']))
    from experiments.placement_native_proposal_v1 import contract
    from experiments import placement_native_evidence as old
    from autorouter import local_settings
    need(type(retained) is bool, 'explicit retained replay mode required')
    work = h.real_path(output / 'work'); source = Path(binding['source'])
    snapshot = work / 'snapshot' / source.name; candidate = work / 'candidate' / source.name
    preimage = work / 'refill-preimage' / source.name; refill = work / 'refill-native' / source.name
    need(type(data.get('schema')) is int and data['schema'] == 1 and data['kind'] == KIND and data['status'] == 'pending_candidate' and data['placement_qualified'] is True,
         'worker did not qualify a pending candidate')
    old._false(data, *AUTHORITY)
    need(data['binding_sha256'] == p.sha(output / 'binding.json') and data['tools'] == binding['tools']
         and data['budget_seconds'] == data['cpu_budget_seconds'] == INNER
         and data['native_save_board_called'] is False and data['external_exit_required'] is True
         and data['refill_save_board_requested'] is True,
         'worker binding, budgets or authority differ')
    p.check_resource_accounting(data)
    need(data['source'] == str(source) and data['source_hashes'] == binding['source_hashes']
         and gui.source_inventory(snapshot) == binding['source_hashes'], 'snapshot/source differs')
    raw = pc.read_bytes(snapshot, contract.MAX_BYTES); candidate_raw = pc.read_bytes(candidate, contract.MAX_BYTES)
    preimage_raw = pc.read_bytes(preimage, contract.MAX_BYTES)
    need(preimage_raw == (contract.sx.dump(contract.translated_tree(raw, choice.moves, **choice.options)) + '\n').encode(),
         'exact source translation differs')
    candidate_hashes = dict(binding['source_hashes']); candidate_hashes[source.name] = p.sha(candidate)
    preimage_hashes = dict(binding['source_hashes']); preimage_hashes[source.name] = p.sha(preimage)
    need(data['candidate'] == str(candidate) and gui.source_inventory(candidate) == data['candidate_hashes'] == candidate_hashes,
         'candidate or sidecars changed')
    need(gui.source_inventory(preimage) == data['refill_preimage_hashes'] == preimage_hashes
         and gui.source_inventory(refill) == data['refill_native_hashes'], 'refill copies changed')
    need(contract.check_translation(raw, candidate_raw, choice.moves, **choice.options) == data['immutable_check'],
         'immutable AST differs')
    need(contract.check_refill_reconstruction(preimage_raw, pc.read_bytes(refill, contract.MAX_BYTES), candidate_raw)
         == data['refill_transplant'], 'fill-only exact reconstruction differs')
    base_work = Path(binding['evidence']) / 'work'
    base_capture = f.read_json(base_work / 'capture-observation.json')
    reused = dict(evidence=binding['evidence'], witness_sha256=binding['retained_witness_sha256'],
                  source_drc_receipt_sha256=review.witness['receipt_sha256'],
                  capture_sha256=p.sha(base_work / 'capture-observation.json'), new_initial_native_checks=False)
    need(equal(data['reused_initial'], reused) and base_capture['observation'] == review.observation
         == contract.inspect_board(raw, scope=choice.options['scope']), 'reused source provenance differs')
    historical_identity = None
    for name, board, hashes, expected in (
            ('translate', snapshot, binding['source_hashes'], review.observation),
            ('final-capture', candidate, candidate_hashes, contract.inspect_board(candidate_raw, scope=choice.options['scope']))):
        spec = request(binding, work, name, board, candidate, hashes, choice.moves)
        actual = f.read_json(work / (name + '-request.json'))
        historical_identity = check_native_request(actual, spec, retained=retained, previous=historical_identity)
        observed = f.read_json(work / (name + '-observation.json'))
        old._success(f.process_check(work, data, name, [*f.SANDBOX, *native_argv(c, Path(binding['runtime']), work, name)]))
        old._false(observed, 'accepted', 'routing_accepted', 'native_save_board_called')
        old._scoped(observed, choice.options)
        translated = name == 'translate'
        need(observed['schema'] == 1 and observed['status'] == ('translated_copy' if translated else 'observed')
             and observed['request_sha256'] == p.sha(work / (name + '-request.json'))
             and observed['native_version'] == c.NATIVE_VERSION and observed['actual_native_observation'] is True
             and observed['application_policy'] == 'source-translation-v1' and observed['source'] == str(board)
             and observed['source_hashes'] == hashes and observed['candidate'] == (str(candidate) if translated else None)
             and observed['board_saved'] is translated and observed['observation'] == expected
             and observed['details'] == base_capture['details'], 'Native capture/translation differs: ' + name)
        if translated:
            need(observed['candidate_hashes_before'] == binding['source_hashes']
                 and observed['candidate_hashes_after'] == preimage_hashes
                 and observed['saved_candidate_sha256'] == preimage_hashes[source.name]
                 and observed['immutable_check'] == contract.check_translation(raw, preimage_raw, choice.moves, **choice.options),
                 'translation readback differs')
    source_native = review.witness['Native_findings']['source_native']
    inputs = []
    for name, board, path, saved, before, key in (
            ('refill-drc', refill, refill, True, preimage_hashes, 'refill_native'),
            ('final-drc', candidate, work / 'final-drc-input' / source.name, False, candidate_hashes, 'final_native')):
        native = f.check_drc_stage(work, data, name, board, path, saved, before, schematic_parity=True)
        need(native == data[key], 'new full-SCH Native proof differs')
        need(driver.placement_findings(native, p) == driver.placement_findings(source_native, p)
             and native['ignored_checks'] == source_native['ignored_checks'], 'warnings or ignored checks changed')
        inputs.append(path)
    for board in [source, snapshot, candidate, preimage, refill, *inputs]:
        local_settings.check_current_metadata(board.with_suffix('.kicad_prl'))
    material(binding, review)
    work_prl(output, binding)
    return candidate_hashes


def worker(output, expected_binding_sha, runtime):
    from experiments.placement_native_proposal_v1 import driver
    binding, review, choice = loaded(output, runtime)
    c, p, f, gui, h, pc = driver.context(Path(runtime))
    from experiments.placement_native_proposal_v1 import contract
    binding_path = output / 'binding.json'
    need(p.sha(binding_path) == expected_binding_sha, 'worker binding changed')
    source = Path(binding['source'])
    def remaining(): return min(INNER - (time.monotonic() - ENTRY), INNER - (cpu() - PARENT_CPU - CHILD_CPU))
    job = f.FloorJob(output / 'work', INNER, remaining, protect_local_settings=True)
    snapshot = job.out / 'snapshot' / source.name; candidate = job.out / 'candidate' / source.name
    preimage = job.out / 'refill-preimage' / source.name; refill = job.out / 'refill-native' / source.name
    data = dict(schema=1, kind=KIND, status='failed', placement_qualified=False, **{key: False for key in AUTHORITY},
        source=str(source), source_hashes=binding['source_hashes'], binding_sha256=expected_binding_sha,
        tools=binding['tools'], budget_seconds=INNER, cpu_budget_seconds=INNER, steps=job.steps,
        external_exit_required=True, native_save_board_called=False, refill_save_board_requested=False, whole_project_drc_clean=False)
    def fresh():
        h.owned_destination(job._local_settings_owner)
        need(remaining() > 0 and p.sha(binding_path) == expected_binding_sha, 'budget exhausted or binding changed')
        material(binding, review)
        if data['placement_qualified']: work_prl(output, binding)
    def account():
        data.update(wall_seconds=time.monotonic() - ENTRY,
            **p.sequential_cpu_components(time.process_time() - PARENT_CPU, f.child_cpu() - CHILD_CPU, job.steps))
        if data['status'] != 'pending_candidate' or remaining() <= 0:
            data['placement_qualified'] = False
            if remaining() <= 0: data['status'] = 'budget_exhausted'
    def final():
        fresh()
        if data['placement_qualified']: proof(output, binding, review, choice, data)
        fresh()
    def native(name, board):
        fresh()
        spec = request(binding, job.out, name, board, candidate, gui.source_inventory(board), choice.moves)
        p.save_json(job.out / (name + '-request.json'), spec)
        job.step(name, native_argv(c, Path(binding['runtime']), job.out, name))
        fresh()
        return f.read_json(job.out / (name + '-observation.json'))
    def drc(name, board, saved=False):
        fresh(); before = gui.source_inventory(board)
        actual = job.drc(name, board, save=saved, schematic_parity=True)
        checked = f.check_drc_stage(job.out, data, name, board,
            board if saved else job.out / (name + '-input') / board.name, saved, before, schematic_parity=True)
        need(actual == checked, 'Native stage readback differs'); fresh()
        return actual
    try:
        fresh(); pc.copy_project(source.parent, snapshot.parent); pc.copy_project(snapshot.parent, candidate.parent)
        need(gui.source_inventory(snapshot) == gui.source_inventory(candidate) == binding['source_hashes'], 'copy differs')
        base_capture = Path(binding['evidence']) / 'work/capture-observation.json'
        data['reused_initial'] = dict(evidence=binding['evidence'], witness_sha256=binding['retained_witness_sha256'],
            source_drc_receipt_sha256=review.witness['receipt_sha256'], capture_sha256=p.sha(base_capture), new_initial_native_checks=False)
        translated = native('translate', snapshot)
        need(translated['status'] == 'translated_copy' and translated['native_save_board_called'] is False, 'translation failed')
        contract.check_translation(pc.read_bytes(snapshot), pc.read_bytes(candidate), choice.moves, **choice.options)
        pc.copy_project(candidate.parent, preimage.parent); pc.copy_project(preimage.parent, refill.parent)
        data['refill_preimage_hashes'] = gui.source_inventory(preimage)
        data['refill_save_board_requested'] = True
        data['refill_native'] = drc('refill-drc', refill, True)
        data['refill_native_hashes'] = gui.source_inventory(refill)
        fresh(); need(gui.source_inventory(candidate) == data['refill_preimage_hashes'], 'candidate changed before transplant')
        candidate.write_bytes(contract.transplant_refill(pc.read_bytes(preimage), pc.read_bytes(refill)))
        data['refill_transplant'] = contract.check_refill_reconstruction(pc.read_bytes(preimage), pc.read_bytes(refill), pc.read_bytes(candidate))
        data['immutable_check'] = contract.check_translation(pc.read_bytes(snapshot), pc.read_bytes(candidate), choice.moves, **choice.options)
        data['final_native'] = drc('final-drc', candidate)
        native('final-capture', candidate)
        data.update(status='pending_candidate', placement_qualified=True, candidate=str(candidate), candidate_hashes=gui.source_inventory(candidate))
        account(); proof(output, binding, review, choice, data); fresh(); account()
        p.check_resource_accounting(data)
    except (Exception, KeyboardInterrupt) as exc:
        data.update(status='cancelled' if isinstance(exc, KeyboardInterrupt) else 'failed', placement_qualified=False,
                    reason=type(exc).__name__ + ': ' + str(exc)); account()
    return f.publish(job.out, data, fresh, account, remaining,
                     owned=lambda: h.owned_destination(job._local_settings_owner), final_check=final)


def worker_argv(binding, output, binding_sha):
    return [str(Path(binding['runtime']) / '.venv/bin/python'), '-B', str(Path(__file__)),
            '--runtime', binding['runtime'], '--evidence', binding['evidence'], '--protocol', binding['protocol'],
            '--draft', binding['draft'], '--draft-sha256', binding['draft_sha256'], '--output', str(output),
            '--qualify', '--worker', '--binding-sha256', binding_sha]


def outer_proof(process, outer, data):
    from experiments import placement_native_evidence as old
    old._success(process); old._false(outer, *AUTHORITY)
    need(type(outer.get('schema')) is int and outer['schema'] == 1 and outer['kind'] == KIND and outer['placement_qualified'] is True and outer['status'] == 'pending_candidate'
         and outer['process'] == process and outer['total_limit_seconds'] == TOTAL
         and outer['publication_allowance_seconds'] == 1 and outer['controller_exit_not_measured'] is True,
         'outer qualification differs')
    wall = old._number(outer['complete_worker_exit_wall_seconds']); spent = old._number(outer['parent_plus_waited_child_cpu_seconds'])
    need(max(wall, spent) + 1 <= TOTAL and max(old._number(process['wall_seconds']), old._number(process['cpu_seconds'])) <= INNER
         and process['wall_seconds'] <= wall and process['cpu_seconds'] <= spent, 'complete cost exceeds bound')
    guards = process['resource_guards']
    need(guards['max_group_rss_bytes'] == RSS and guards['max_workdir_bytes'] == DISK and guards['os_enforced'] is False,
         'resource guards differ')
    need(data['placement_qualified'] is True and data['external_exit_required'] is True, 'worker qualification absent')


def stable_work(output, expected, pc):
    need(pc.inventory(output / 'work', max_bytes=DISK) == expected, 'closed worker artifacts changed')


def check(output, *, expected_runtime):
    """Fresh pending witness, with a caller-trusted runtime; no Native or routing.

    The canonical outer receipt is output/result.json; work/result.json belongs
    to the completed child. Current proof bytes, rather than saved pass flags,
    are read independently. Call from the explicit installed runtime interpreter.
    """
    output = Path(output).absolute()
    from experiments import placement_native_evidence as old
    need(output.parent == ROOT / '.runs', 'choice output must be an owned .runs child')
    current_tree = old.retained_tree_identity(output, ROOT)
    binding, review, choice = loaded(output, expected_runtime)
    from experiments.placement_native_proposal_v1 import driver
    c, p, f, gui, h, pc = driver.context(Path(binding['runtime']))
    output = h.real_path(output)
    need(output.parent == ROOT / '.runs', 'choice output must be an owned .runs child')
    inventory = pc.inventory(output, max_bytes=DISK)
    outer = f.read_json(output / 'result.json'); process = f.read_json(output / 'process.json')
    data = f.read_json(output / 'work/result.json'); binding_sha = p.sha(output / 'binding.json')
    outer_proof(process, outer, data)
    stable_work(output, outer['worker_artifact_hashes'], pc)
    need(outer['binding_sha256'] == binding_sha and outer['child_receipt_sha256'] == p.sha(output / 'work/result.json')
         and process['argv'] == worker_argv(binding, output, binding_sha) and process['cwd'] == str(output), 'process/receipt binding differs')
    candidate_hashes = proof(output, binding, review, choice, data, retained=True)
    material(binding, review)
    need(pc.inventory(output, max_bytes=DISK) == inventory, 'choice artifacts changed during readback')
    work_prl(output, binding)
    need(old.retained_tree_identity(output, ROOT) == current_tree, 'choice filesystem identity changed during readback')
    return dict(schema=1, kind=KIND, current=True, placement_qualified=True, status='pending_candidate',
        **{key: False for key in AUTHORITY}, artifact_hashes=inventory, binding_sha256=binding_sha,
        draft_sha256=binding['draft_sha256'], original_source=binding['source'], original_source_hashes=binding['source_hashes'],
        candidate=data['candidate'], candidate_sha256=candidate_hashes[Path(data['candidate']).name], source_hashes=candidate_hashes,
        moves_nm=choice.moves, pose_sha256=digest(choice.pose), options=choice.options, Native_findings=data['final_native'],
        reused_initial=data['reused_initial'], new_native_stages=['translate','refill-drc','final-drc','final-capture'],
        complete_worker_exit_wall_seconds=outer['complete_worker_exit_wall_seconds'],
        parent_plus_waited_child_cpu_seconds=outer['parent_plus_waited_child_cpu_seconds'], controller_exit_not_measured=True)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    for name in ('runtime','evidence','protocol','draft','draft-sha256','output'): ap.add_argument('--' + name, required=True)
    ap.add_argument('--qualify', action='store_true'); ap.add_argument('--worker', action='store_true', help=argparse.SUPPRESS)
    ap.add_argument('--binding-sha256', help=argparse.SUPPRESS)
    args = ap.parse_args(argv)
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(ROOT))
    need(args.qualify, 'explicit --qualify required; nothing was executed')
    from experiments.placement_native_proposal_v1 import driver
    c, p, f, gui, h, pc = driver.context(Path(args.runtime).absolute())
    need(Path(sys.prefix).resolve() == Path(args.runtime).absolute() / '.venv', 'installed runtime interpreter required')
    output = h.real_path(Path(args.output).absolute(), existing=args.worker)
    need(output.parent == ROOT / '.runs', 'fresh owned .runs output required')
    if args.worker:
        binding = read_binding(output / 'binding.json')
        need([binding[k] for k in ('runtime','evidence','protocol','draft','draft_sha256')]
             == [args.runtime,args.evidence,args.protocol,args.draft,args.draft_sha256], 'worker arguments differ')
        value = worker(output, args.binding_sha256, Path(args.runtime))
        return 0 if value['placement_qualified'] and value['status'] == 'pending_candidate' else 2
    need(not output.exists() and args.binding_sha256 is None, 'fresh output required')
    from scripts.backup import require_headroom
    from autorouter.runner import run
    binding, review, choice = prepare(Path(args.runtime).absolute(), Path(args.evidence).absolute(), Path(args.protocol).absolute(),
                                      Path(args.draft).absolute(), args.draft_sha256)
    fd = os.open(ROOT / '.runs/quality-experiment.lock', os.O_RDWR | os.O_NOFOLLOW)
    with os.fdopen(fd, 'r+') as lane:
        mode = os.fstat(lane.fileno()); need(stat.S_ISREG(mode.st_mode) and mode.st_nlink == 1, 'invalid worker lane')
        fcntl.flock(lane, fcntl.LOCK_EX | fcntl.LOCK_NB)
        space = require_headroom(ROOT, DISK, 'one exact reviewed placement qualification')
        material(binding, review); output.mkdir(mode=0o700); owner = {}; h.capture_destination(owner, output)
        p.save_json(output / 'binding.json', binding); binding_sha = p.sha(output / 'binding.json')
        process = run(worker_argv(binding, output, binding_sha), cwd=output, env=gui.child_environment(), log=output / 'command.log',
                      timeout=max(.001, min(INNER, TOTAL - 5 - (time.monotonic() - ENTRY))),
                      max_log_bytes=512*1024, max_group_rss_bytes=RSS, max_workdir_bytes=DISK)
        h.owned_destination(owner); p.save_json(output / 'process.json', process)
        result = output / 'work/result.json'
        data = f.read_json(result) if result.is_file() else None
        work_hashes = pc.inventory(output / 'work', max_bytes=DISK) if (output / 'work').is_dir() else {}
        outer = dict(schema=1, kind=KIND, status='failed', placement_qualified=False, **{key: False for key in AUTHORITY},
            process=process, binding_sha256=binding_sha, child_receipt_sha256=p.sha(result) if data else None,
            worker_artifact_hashes=work_hashes, total_limit_seconds=TOTAL, publication_allowance_seconds=1,
            controller_exit_not_measured=True, space_plan=space, whole_project_drc_clean=False)
        def remaining(): return min(TOTAL - (time.monotonic()-ENTRY), TOTAL - (cpu()-PARENT_CPU-CHILD_CPU))
        def account():
            outer.update(complete_worker_exit_wall_seconds=time.monotonic()-ENTRY,
                         parent_plus_waited_child_cpu_seconds=cpu()-PARENT_CPU-CHILD_CPU)
            if outer['status'] != 'pending_candidate' or remaining() < 1:
                outer['placement_qualified'] = False
                if remaining() < 1: outer['status'] = 'budget_exhausted'
        def stable():
            h.owned_destination(owner)
            need(p.sha(output / 'binding.json') == binding_sha, 'binding changed')
            material(binding, review)
            if data:
                stable_work(output, work_hashes, pc)
                need(p.sha(result) == outer['child_receipt_sha256'] and equal(f.read_json(result), data), 'worker receipt changed')
                if data['placement_qualified']: work_prl(output, binding)
        def final():
            stable()
            if outer['placement_qualified']: outer_proof(process, outer, data)
        try:
            need(data is not None, 'worker produced no receipt')
            proof(output, binding, review, choice, data); stable()
            outer.update(status='pending_candidate', placement_qualified=True)
            account(); outer_proof(process, outer, data)
        except (Exception, KeyboardInterrupt) as exc:
            outer.update(status='cancelled' if isinstance(exc,KeyboardInterrupt) or process['status']=='cancelled' else 'failed',
                         placement_qualified=False, reason=type(exc).__name__+': '+str(exc))
        # The shared publisher invalidates a canonical result on cancellation,
        # stale files or interrupted writes; account clears our pending flag too.
        outer = f.publish(output, outer, stable, account, remaining,
                          owned=lambda: h.owned_destination(owner), final_check=final)
        print(canonical({key:value for key,value in outer.items() if key not in ('process','space_plan','worker_artifact_hashes')}))
        return 0 if outer['placement_qualified'] and outer['status'] == 'pending_candidate' else 2



if __name__ == '__main__':
    def interrupted(*_): raise KeyboardInterrupt
    for sig in (signal.SIGINT,signal.SIGTERM): signal.signal(sig,interrupted)
    raise SystemExit(main())
