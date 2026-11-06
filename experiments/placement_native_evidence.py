"""Read retained placement-v1 evidence; never execute Native or grant approval.

The caller freezes the returned witness and compares a fresh check before use.
Current source/runtime/code pins are required: historical results remain evidence
but do not become current merely because a prior audit called them valid.
"""
import hashlib
import json
import math
from pathlib import Path


def _need(condition, reason):
    if not condition:
        raise ValueError('Placement evidence: ' + reason)


def _number(value):
    _need(type(value) in (int, float) and 0 <= value <= 900 and math.isfinite(value),
          'invalid bounded resource measurement')
    return value


def _false(record, *fields):
    _need(all(record.get(key) is False for key in fields), 'approval/execution authority or missing refusal flags')


def _scope(spec, expected_scope, contract):
    _need(type(expected_scope) is str and expected_scope in (contract.DEFAULT_SCOPE, contract.MULTIPAD_SCOPE),
          'explicit supported expected scope required')
    _need(spec.get('placement_scope', contract.DEFAULT_SCOPE) == expected_scope, 'placement scope differs')
    _need(type(spec.get('selected_footprints')) is list and type(spec.get('allowed_region_nm')) is list,
          'complete prospective selected UUIDs and region required')
    return contract.scope_options(scope=expected_scope, selected=spec['selected_footprints'],
                                  region_nm=spec['allowed_region_nm'])


def _scoped(record, options, *, legacy=False):
    keys = {'placement_scope', 'selected_footprints', 'allowed_region_nm'}
    if legacy and not keys.intersection(record):
        return
    _need(record.get('placement_scope') == options['scope']
          and record.get('selected_footprints') == options['selected']
          and record.get('allowed_region_nm') == options['region_nm'], 'retained selected UUIDs/region differ')


def _success(process):
    _need(process.get('status') == 'success' and type(process.get('exit_code')) is int
          and process['exit_code'] == 0 and process.get('cleanup_complete') is True
          and process.get('log_truncated') is False, 'incomplete or failed retained process')


def _relative(root, name, h):
    _need(type(name) is str and not Path(name).is_absolute() and '..' not in Path(name).parts,
          'relative project evidence path required')
    value = h.real_path(root / name)
    _need(root in value.parents, 'evidence path escaped project')
    return value


def check(output, runtime, protocol, expected_scope):
    """Return a fresh, detached witness for one qualified placement proposal.

    All arguments identify existing local files/directories. Raises on missing,
    stale, malformed, unsupported or failed evidence. This function only reads;
    no Native process, search, model, application or routing is performed.
    """
    from experiments.placement_native_proposal_v1 import driver
    runtime = Path(runtime)
    c, p, f, gui, h, pc = driver.context(runtime)
    from autorouter import local_settings
    from experiments.placement_native_proposal_v1 import contract
    from experiments.constrained_placement_v1 import constraints, prototype

    runtime, output, protocol = (h.real_path(path) for path in (runtime, output, protocol))
    _need(output.parent == driver.ROOT / '.runs' and protocol.parent == driver.HERE,
          'placement-v1 output/protocol location differs')
    work = h.real_path(output / 'work')
    spec = f.read_json(protocol)
    options = _scope(spec, expected_scope, contract)
    scope = options['scope']; legacy = 'placement_scope' not in spec
    policy = contract.application_policy(spec['application_policy'])
    _need(spec['schema'] == 1 and spec['kind'] == 'placement-native-proposal-feasibility-v1'
          and spec['runtime'] == str(runtime.relative_to(driver.ROOT)), 'protocol identity differs')
    _need(spec['total_wall_and_cpu_seconds'] == 120 and spec['worker_wall_and_cpu_seconds'] == 110
          and spec['output_bytes'] == spec['peak_temporary_bytes'] == 512 * 1024**2
          and spec['process_group_rss_bytes'] == 2 * 1024**3, 'prospective resource limits differ')
    _need(spec['search'] == dict(seed=7, steps=160, alternatives=1 if scope == contract.DEFAULT_SCOPE else 2, seconds=2),
          'prospective search limits differ')
    reader_hash = p.sha(Path(__file__))
    protocol_hash = p.sha(protocol)
    artifacts = pc.inventory(output, max_bytes=spec['output_bytes'])
    outer = f.read_json(output / 'execution.json')
    data = f.read_json(work / 'result.json')
    proposal = f.read_json(work / 'proposal.json')
    _need(outer.get('placement_proposal_qualified') is True and outer.get('source_unchanged') is True,
          'outer qualification failed')
    _false(outer, 'accepted', 'routing_accepted', 'actual_GUI', 'live_application')
    _need(outer['model_calls'] == 0 and outer['controller_exit_not_measured'] is True,
          'outer execution claim differs')
    _need(outer['child_receipt_sha256'] == p.sha(work / 'result.json')
          and outer['protocol_sha256'] == data['protocol_sha256'] == protocol_hash, 'receipt/protocol hash differs')
    _need(data.get('placement_proposal_validated') is True and data.get('status') == 'placement_proposal_validated',
          'worker did not validate a placement proposal')
    _false(data, 'accepted', 'routing_accepted', 'human_approval', 'production_admitted', 'original_mutated', 'routing_performed')
    for row in (outer, data):
        _need(row['application_policy'] == policy and row['native_save_board_called'] is (policy == 'native-save-v1')
              and row.get('placement_scope', contract.DEFAULT_SCOPE) == scope, 'application policy/scope differs')
    _need(data['external_exit_required'] is True and data['explicit_review_required'] is True
          and data['refill_save_board_requested'] is True and data['warning_records_unchanged'] is True,
          'required qualification flags absent')
    _need(data['budget_seconds'] == data['cpu_budget_seconds'] == spec['worker_wall_and_cpu_seconds'], 'worker budget differs')
    p.check_resource_accounting(data)
    _need(outer['total_limit_seconds'] == spec['total_wall_and_cpu_seconds'] and outer['publication_allowance_seconds'] == 1
          and max(_number(outer['complete_worker_exit_wall_seconds']), _number(outer['parent_plus_waited_child_cpu_seconds'])) + 1 <= 120,
          'complete worker exit exceeds budget')
    process = f.read_json(output / 'process.json'); _success(process)
    _need(_number(process['wall_seconds']) <= outer['complete_worker_exit_wall_seconds']
          and _number(process['cpu_seconds']) <= outer['parent_plus_waited_child_cpu_seconds'],
          'outer accounting is below completed worker cost')
    guards = process['resource_guards']
    _need(guards['max_group_rss_bytes'] == spec['process_group_rss_bytes']
          and guards['max_workdir_bytes'] == spec['output_bytes'] and guards['os_enforced'] is False,
          'recorded resource guards differ')
    argv = [str(runtime / '.venv/bin/python'), '-B', str(driver.HERE / 'driver.py'), '--runtime', str(runtime),
            '--protocol', str(protocol), '--protocol-sha256', protocol_hash, '--output', str(output), '--application-policy', policy]
    if not legacy: argv += ['--placement-scope', scope]
    argv += ['--execute-native', '--worker']
    _need(process == outer['process'] and process['argv'] == argv and process['cwd'] == str(output), 'outer process binding differs')

    source = _relative(driver.ROOT, spec['seed'], h)
    manifest = _relative(driver.ROOT, spec['seed_manifest'], h)
    task = work / 'task' / source.name; candidate = work / 'candidate' / source.name
    snapshot = work / 'snapshot' / source.name
    _need(data['source'] == str(source) and data['source_hashes'] == spec['source_hashes'], 'source binding differs')
    saved = f.read_json(manifest)
    if scope == contract.DEFAULT_SCOPE: saved = saved['roles']['ordinary']
    _need(saved['source'] == str(source) and saved['source_hashes'] == spec['source_hashes'], 'source provenance differs')

    def fresh_inputs():
        _need(p.sha(protocol) == protocol_hash and p.sha(Path(__file__)) == reader_hash, 'reader/protocol changed')
        _need(driver.code_pins() == spec['code_sha256'], 'placement code changed')
        _need(p.sha(manifest) == spec['seed_manifest_sha256'], 'source provenance manifest changed')
        _need(gui.source_inventory(source) == gui.source_inventory(snapshot) == spec['source_hashes'], 'source/snapshot changed')

    fresh_inputs()
    derived, derivation = driver.task_bytes(pc.read_bytes(source, contract.MAX_BYTES), scope)
    _need(derivation == spec['derivation'] == data['derivation'] and pc.read_bytes(task, contract.MAX_BYTES) == derived,
          'task derivation differs')
    task_hashes = dict(spec['source_hashes']); task_hashes[source.name] = hashlib.sha256(derived).hexdigest()
    _need(gui.source_inventory(task) == data['task_hashes'] == task_hashes, 'derived task sidecars differ')
    candidate_raw = pc.read_bytes(candidate, contract.MAX_BYTES)
    candidate_hashes = dict(task_hashes); candidate_hashes[source.name] = hashlib.sha256(candidate_raw).hexdigest()
    _need(data['candidate'] == str(candidate) and data['candidate_sha256'] == candidate_hashes[source.name]
          and gui.source_inventory(candidate) == data['candidate_hashes'] == candidate_hashes, 'candidate/sidecars changed')
    _false(proposal, 'accepted', 'routing_accepted', 'execution_authorized', 'human_approval')
    _scoped(proposal, options, legacy=legacy)
    _need(proposal['schema'] == 1 and proposal['source'] == str(task) and proposal['source_hashes'] == task_hashes
          and proposal['application_policy'] == policy and p.sha(work / 'proposal.json') == data['proposal_sha256']
          and proposal['quantization'] == 'nearest 1 nm; independently revalidated', 'proposal binding differs')
    observation = contract.inspect_board(derived, scope=scope)
    facts = contract.facts_from_observation(observation, **options)
    search = data['search']; bounds = spec['search']
    _need(search['status'] == 'proposals_ready' and search['source_sha256'] == constraints.digest(facts)
          and search['upstream_commit'] == prototype.UPSTREAM_COMMIT
          and search['bounds'] == dict(seed=bounds['seed'], steps_per_alternative=bounds['steps'],
                                      alternatives=bounds['alternatives'], wall_and_cpu_seconds=bounds['seconds'])
          and 0 < len(search['alternatives']) <= bounds['alternatives'], 'search provenance differs')
    _false(search, 'native_validation_performed', 'execution_authorized', 'approval_granted')
    _need(max(_number(search['sampled_wall_seconds']), _number(search['sampled_cpu_seconds'])) < bounds['seconds'],
          'search exceeded its prospective cooperative budget')
    _need(search['source_unchanged'] is True and search['supplied_connectivity_and_pad_identities_preserved'] is True
          and search['fixed_components'] == sorted(constraints.immovable(facts)), 'search preservation differs')
    for alternative in search['alternatives']:
        constraints.validate_alternative(facts, alternative['candidate'])
    selected, moves = contract.quantized_translation(facts, search['alternatives'][0]['candidate'])
    _need(selected == proposal['candidate'] and moves == proposal['moves_nm']
          and selected != constraints.original_alternative(facts), 'first quantized proposal/pose differs')
    immutable = contract.check_translation(derived, candidate_raw, moves, **options)
    _need(immutable == data['immutable_check'], 'strict immutable comparison differs')

    observations = []
    for name, board, hashes, expected in (
        ('capture', task, task_hashes, observation), ('translate', task, task_hashes, observation),
        ('final-capture', candidate, candidate_hashes, contract.inspect_board(candidate_raw, scope=scope))):
        request_path = work / (name + '-request.json'); observed_path = work / (name + '-observation.json')
        request = f.read_json(request_path); observed = f.read_json(observed_path)
        translated = name == 'translate'
        identity = work.stat()
        expected_request = dict(schema=1, mode='translate' if translated else 'capture', board=str(board), source_hashes=hashes,
            candidate=str(candidate) if translated else None, moves_nm=moves if translated else {}, job=str(work),
            job_identity=[identity.st_dev, identity.st_ino], application_policy=policy,
            runtime_manifest_sha256=spec['runtime_manifest_sha256'], wrapper_sha256=spec['wrapper_sha256'], code_sha256=spec['code_sha256'])
        if not legacy: expected_request.update(placement_scope=scope, selected_footprints=options['selected'], allowed_region_nm=options['region_nm'])
        _need(request == expected_request, 'Native request binding differs: ' + name)
        step = f.process_check(work, data, name, [*f.SANDBOX, str(c.PYTHON), str(driver.HERE / 'worker.py'),
            '--runtime', str(runtime), '--request', str(request_path), '--output', str(observed_path)])
        _success(step); _false(observed, 'accepted', 'routing_accepted'); _scoped(observed, options, legacy=legacy)
        _need(observed['schema'] == 1 and observed['status'] == ('translated_copy' if translated else 'observed')
              and observed['native_version'] == c.NATIVE_VERSION and observed['actual_native_observation'] is True
              and observed['source'] == str(board) and observed['source_hashes'] == hashes
              and observed['request_sha256'] == p.sha(request_path) and observed['observation'] == expected
              and observed['application_policy'] == policy and observed['board_saved'] is translated
              and observed['native_save_board_called'] is (translated and policy == 'native-save-v1')
              and observed['candidate'] == (str(candidate) if translated else None), 'Native observation differs: ' + name)
        observations.append(observed)
    _need(observations[0]['details'] == observations[1]['details'] == observations[2]['details'], 'Native flags/net codes changed')
    _need(p.sha(work / 'capture-observation.json') == proposal['source_observation_sha256']
          and p.sha(work / 'translate-observation.json') == data['translation_observation_sha256']
          and p.sha(work / 'final-capture-observation.json') == data['observed_candidate_sha256'], 'Native observation hash differs')
    translation = observations[1]
    translation_hashes = data['translation_candidate_hashes']
    _need(translation['candidate_hashes_before'] == task_hashes and translation['candidate_hashes_after'] == translation_hashes
          and translation['saved_candidate_sha256'] == translation_hashes[source.name], 'translation hashes differ')
    _need({k:v for k,v in translation_hashes.items() if k != source.name} == {k:v for k,v in task_hashes.items() if k != source.name},
          'translation changed sidecars')
    refill = candidate
    if policy == 'source-translation-v1':
        preimage = work / 'refill-preimage' / source.name; refill = work / 'refill-native' / source.name
        _need(data['refill_preimage'] == str(preimage) and gui.source_inventory(preimage) == data['refill_preimage_hashes'] == translation_hashes
              and gui.source_inventory(refill) == data['refill_native_hashes'], 'retained refill input/output differs')
        preimage_raw = pc.read_bytes(preimage, contract.MAX_BYTES)
        _need(preimage_raw == (contract.sx.dump(contract.translated_tree(derived, moves, **options)) + '\n').encode(),
              'source translation bytes differ')
        _need(translation['immutable_check'] == contract.check_translation(derived, preimage_raw, moves, **options),
              'pre-refill immutable comparison differs')
        _need(contract.check_refill_reconstruction(preimage_raw, pc.read_bytes(refill, contract.MAX_BYTES), candidate_raw) == data['refill_transplant'],
              'exact derived-fill reconstruction differs')
    else:
        _need(translation['immutable_check'] == dict(immutable, candidate_sha256=translation_hashes[source.name]),
              'Native-save immutable comparison differs')
    _need(data['refill_saved_copy'] == str(refill), 'saved refill path differs')

    # Read tools before the final Native/PRL replay, then recheck every retained
    # byte and source pin. A late tool read cannot escape current metadata checks.
    _need(driver.runtime_unchanged(runtime, c.PCBNEW.with_name('pcbnew.py'), spec, data['tools'], p), 'runtime/tools changed')
    natives = {}
    stage_inputs = []
    for name, board, input_path, saved, before, key in (
        ('source-drc', task, work / 'source-drc-input' / source.name, False, task_hashes, 'source_native'),
        ('refill-drc', refill, refill, True, translation_hashes, 'refill_native'),
        ('final-drc', candidate, work / 'final-drc-input' / source.name, False, candidate_hashes, 'final_native')):
        native = f.check_drc_stage(work, data, name, board, input_path, saved, before, schematic_parity=True)
        _need(native == data[key], 'retained full-SCH Native findings differ: ' + name)
        driver.placement_findings(native, p)
        natives[key] = native; stage_inputs.append(input_path)
    for native in natives.values():
        _need(driver.placement_findings(native, p) == driver.placement_findings(natives['source_native'], p)
              and native['ignored_checks'] == natives['source_native']['ignored_checks'], 'Native warnings/check policy changed')
    for board in [source, snapshot, task, candidate, *stage_inputs]:
        local_settings.check_current_metadata(board.with_suffix('.kicad_prl'))
    fresh_inputs()
    _need(gui.source_inventory(task) == task_hashes and gui.source_inventory(candidate) == candidate_hashes,
          'task/candidate changed during readback')
    _need(pc.inventory(output, max_bytes=spec['output_bytes']) == artifacts, 'retained artifacts changed during readback')
    result = dict(schema=1, current=True, placement_proposal_validated=True, accepted=False, routing_accepted=False,
        human_approval=False, execution_authorized=False, root=str(output), artifact_hashes=artifacts,
        reader_sha256=reader_hash, protocol_sha256=protocol_hash, execution_sha256=artifacts['execution.json'],
        receipt_sha256=artifacts['work/result.json'], proposal_sha256=data['proposal_sha256'],
        candidate=str(candidate), candidate_sha256=candidate_hashes[source.name], source_hashes=candidate_hashes,
        original_source=str(source), original_source_hashes=spec['source_hashes'], derivation=derivation,
        placement_scope=scope, selected_footprints=options['selected'], allowed_region_nm=options['region_nm'],
        application_policy=policy, native_save_board_called=data['native_save_board_called'],
        complete_worker_exit_wall_seconds=outer['complete_worker_exit_wall_seconds'],
        parent_plus_waited_child_cpu_seconds=outer['parent_plus_waited_child_cpu_seconds'], controller_exit_not_measured=True,
        counts=dict(footprints=len(observation['footprints']), pads=sum(len(fp['pads']) for fp in observation['footprints']),
                    preserved_routes=len(contract.p.routes(contract.read_board(derived))), zones=len(observation['zones'])),
        Native_findings=natives, immutable_check=immutable, warning_records_unchanged=True)
    return json.loads(json.dumps(result, allow_nan=False))
