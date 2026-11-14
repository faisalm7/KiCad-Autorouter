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
import stat
import sys
import time

if __package__ in (None, ''):
    # Fixed owned entry permits the resource controller's cwd to be one job,
    # rather than scanning the installation's historical .runs.
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    __package__ = 'autorouter'

from . import config as c, floor_route as f, gui, handoff as h, pipeline as p
from . import local_settings, placement_clearance as pc, placement_intent as intent, provenance
from . import placement_copper as copper
from .runner import elapsed_time
from experiments.placement_native_proposal_v1 import contract
from experiments import placement_native_evidence as retained

KIND = 'autorouter.reviewed-placement-qualification.v1'
TOTAL_SECONDS, WORKER_SECONDS = 120, 105
DISK_BYTES, RSS_BYTES = 512 * 1024**2, 2 * 1024**3
AUTHORITY = ('accepted', 'routing_accepted', 'execution_authorized', 'approval_granted',
             'warning_acknowledged', 'human_PCB_approval', 'original_mutated')
ORIGIN_FILE = 'placement-origin.json'
ORIGIN_KIND = 'autorouter.reviewed-placement-origin.v1'


def need(value, reason):
    if not value: raise ValueError('Placement qualification: ' + reason)


def code_pins():
    return {name: provenance.file_digest(c.ROOT / name)[0]
        for name in sorted(provenance.PLACEMENT_FILES)
        if name.startswith(('experiments/placement_native_proposal_v1/', 'experiments/constrained_placement_v1/'))}


def native_worker():
    return c.ROOT / 'experiments/placement_native_proposal_v1/worker.py'


@contract.sx.parsing_session()
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
    inspection = (intent.inspect_saved(draft.get('source'), native_context=draft['native_context'])
                  if 'native_context' in draft else intent.inspect_saved(draft.get('source')))
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
    roles = ['snapshot', 'candidate', 'refill-preimage', 'refill-native']
    if intent.rebuilds_copper(binding.get('intent', {}).get('settings', {})):
        roles.append('prepared')
    return work, {role: work / role / name for role in roles}


def _options(binding):
    value = intent.validate_settings(binding['intent']['settings'])
    return intent.contract_options(value)


def _prepared_source(binding, raw):
    """Recompute the reviewed partition; never trust a removal list alone."""
    settings = intent.validate_settings(binding['intent']['settings'])
    if not intent.rebuilds_copper(settings):
        need('copper_plan' not in binding['intent'], 'unexpected copper-removal authority')
        return None, raw
    plan = intent.copper_plan(binding['inspection'], settings)
    need(f.canonical(binding['intent'].get('copper_plan')) == f.canonical(plan), 'reviewed copper plan differs')
    return plan, copper.prepare(raw, plan)


def _retained_native_details(details, plan, *, scope=None, observation=None):
    """Only approved route UUIDs disappear; pad/net/zone witnesses stay exact."""
    keys = {'native_pad_netcodes', 'native_route_netcodes', 'actual_native_areas'}
    if contract.tht_scope(scope): keys.add('engineering_metadata')
    need(type(details) is dict and set(details) == keys, 'complete Native identity witnesses required')
    need(type(details['actual_native_areas']) is dict, 'Native area witness differs')
    for key in ('native_pad_netcodes', 'native_route_netcodes'):
        need(type(details[key]) is dict and all(type(identity) is str and type(code) is int and code > 0
             for identity, code in details[key].items()), 'Native net-code witness differs')
    need(bool(details['native_pad_netcodes']), 'Native pad identity witness absent')
    if contract.tht_scope(scope):
        from experiments.placement_native_proposal_v1 import engineering_metadata as metadata
        need(type(observation) is dict and observation.get('scope') == scope
             and type(observation.get('footprints')) is list, 'exact THT metadata source observation required')
        sources = {row['uuid']: metadata.validate(row['engineering_metadata'])
                   for row in observation['footprints']}
        witnesses = details['engineering_metadata']
        need(len(sources) == len(observation['footprints']) and type(witnesses) is dict
             and set(witnesses) == set(sources), 'Native engineering metadata owner census differs')
        for identity, source in sources.items():
            need(source['owner_uuid'] == identity, 'Native metadata source owner differs')
            row = witnesses[identity]
            expected = dict(policy=metadata.POLICY, owner_uuid=identity,
                immutable_metadata_equal=True, metadata_sha256=metadata.digest(source),
                supplied_jumper_getter=False, points_fixed=True, native_execution_proven=False)
            need(type(row) is dict and set(row) == set(expected) | {
                'point_census_method','direct_point_count_unavailable','point_count'},
                'complete Native engineering metadata witness required')
            need(all(type(row[key]) is type(value) and row[key] == value for key,value in expected.items()),
                 'Native immutable engineering metadata differs from exact source')
            need(type(row['point_count']) is int and row['point_count'] == len(source['points']),
                 'Native engineering point census differs')
            need(type(row['point_census_method']) is str
                 and (row['direct_point_count_unavailable'] is None
                      or type(row['direct_point_count_unavailable']) is str)
                 and ((row['point_census_method'] == 'Points-length-and-exact-footprint-formatter'
                  and row['direct_point_count_unavailable'] is None)
                 or (row['point_census_method'] == 'exact-footprint-formatter'
                     and row['direct_point_count_unavailable'] in ('AttributeError','TypeError'))),
                 'Native point census evidence method differs')
    expected = copy.deepcopy(details)
    if plan is not None:
        routes = expected.get('native_route_netcodes')
        removed = [row['uuid'] for row in plan['removed_routes']]
        need(type(routes) is dict and len(routes) == plan['original_route_count']
             and len(set(removed)) == len(removed) and set(removed) <= set(routes),
             'Native original/removed route census differs')
        for identity in removed: del routes[identity]
        need(set(routes) == {row['uuid'] for row in plan['protected_routes']}, 'Native retained route census differs')
    return expected


def _request(binding, work, name, board, candidate, hashes):
    st = work.stat(); options = _options(binding)
    translating = name == 'translate'
    return dict(schema=1, mode='translate' if translating else 'capture', board=str(board), source_hashes=hashes,
        candidate=str(candidate) if translating else None, moves_nm=binding['intent']['moves_nm'] if translating else {},
        job=str(work), job_identity=[st.st_dev, st.st_ino], application_policy='source-translation-v1',
        runtime_manifest_sha256=binding['runtime_manifest_sha256'], wrapper_sha256=binding['wrapper_sha256'],
        code_sha256=binding['code_sha256'], placement_scope=options['scope'], selected_footprints=options['selected'],
        allowed_region_nm=options['region_nm'], **intent.region_options(options))


def _argv(work, name):
    return [str(c.PYTHON), str(native_worker()), '--runtime', str(c.ROOT),
            '--request', str(work / (name + '-request.json')), '--output', str(work / (name + '-observation.json'))]


def _findings(native, *, qualified_fields=False):
    need(native['blocking'] == native['exclusions'] == 0, 'blocking/excluded Native findings remain')
    for row in native['findings']:
        need(not row.get('excluded', False) and row['type'] in p.KNOWN_CHECKS | {'padstack_invalid'},
             'unknown or excluded Native finding')
        if row['type'] != 'unconnected_items':
            from . import schematic_field_evidence as fields
            field_proved = qualified_fields and row['type'] == fields.TYPE and fields.qualified(native)
            if qualified_fields and row['type'] == fields.TYPE and not field_proved:
                reason = native.get('field_parity', {}).get('qualification', {}).get('reason', 'missing or invalid complete field proof')
                need(False, 'Complete schematic-field evidence refused: ' + str(reason)[:1000])
            need(row['severity'] != 'error' and (row['type'] not in p.CRITICAL_FINDINGS or field_proved),
                 'critical Native finding remains')
    return sorted(f.canonical(row) for row in native['findings'] if row['type'] != 'unconnected_items')


def finding_continuity(native, original, observation, moves, scope):
    """Only two metadata finding anchors may follow an exact selected translation.

    Raw reports stay intact. This grants neither warning acknowledgement nor
    candidate acceptance; physical warnings and every other finding field must
    remain exact. The source/candidate Native and immutable checks are separate.
    """
    context = contract.fixed_context_scope(scope)
    before = _findings(original, qualified_fields=context)
    if not contract.fixed_context_scope(scope):
        need(_findings(native) == before, 'warning/check policy changed')
        return None
    need(observation.get('scope') == scope, 'finding continuity scope differs')
    need(type(moves) is dict and moves, 'explicit translated footprint targets required')
    contract.scope_options(scope=scope, selected=list(moves),
                           region_nm=observation['outline']['bounds_nm'])
    # The caller's immutable/region checks establish movement authority. The
    # continuity comparison below binds anchors to the exact captured footprint
    # and exact target, never to arbitrary deltas supplied in a Native report.
    footprints = {row['uuid']: row for row in observation['footprints']}
    need(set(moves) <= set(footprints), 'unknown finding translation identity')
    for identity, target in moves.items():
        need(footprints[identity]['placement_eligible'] is True and not footprints[identity]['locked']
             and type(target) is list and len(target) == 2
             and all(type(n) is int and abs(n) <= 2_000_000_000 for n in target),
             'exact eligible footprint translation required')
    expected = copy.deepcopy(original)
    changes = []
    for finding in expected['findings']:
        if (finding['type'] not in ('lib_footprint_issues', 'footprint_symbol_field_mismatch')
                or finding['severity'] != 'warning' or len(finding['items']) != 1):
            continue
        item = finding['items'][0]; identity = item.get('uuid')
        if identity not in moves:
            continue
        need(set(item) == {'uuid', 'description', 'pos'} and set(item['pos']) == {'x', 'y'},
             'metadata finding anchor shape differs')
        position = footprints[identity]['position_nm']
        need([contract.pt.nm(str(item['pos'][k]), 1000000) for k in ('x', 'y')] == position,
             'metadata finding anchor is not the captured footprint position')
        target = moves[identity]
        if target != position:
            changes.append(dict(type=finding['type'], uuid=identity,
                                original_position_nm=position, candidate_position_nm=target))
        item['pos'] = dict(zip(('x', 'y'), (n / 1e6 for n in target)))
    # The expected projection is a comparison only. Its old field proof must
    # never be relabelled as a proof for the translated warning hashes. The
    # actual candidate separately needs its own freshly derived field proof.
    expected_findings = sorted(f.canonical(row) for row in expected['findings'] if row['type'] != 'unconnected_items')
    actual_findings = _findings(native, qualified_fields=True)
    if actual_findings != expected_findings:
        from collections import Counter
        added = Counter(actual_findings) - Counter(expected_findings)
        details = '; '.join(str(count) + '× ' + json.loads(row)['type'] + ': '
                            + json.loads(row).get('description', '') for row, count in sorted(added.items()))
        need(False, 'Finding changed beyond exact metadata anchor translation. '
             + ('New/changed findings: ' + details[:2000] if details else 'Source findings disappeared or changed.'))
    need(native['ignored_checks'] == original['ignored_checks'], 'ignored check policy changed')
    return dict(policy='exact-footprint-anchor-translation-v1',
                translated_metadata_anchors=changes, warning_acknowledged=False,
                other_findings_unchanged=True, raw_reports_preserved=True)


def _metadata(paths, source):
    expected = source.with_suffix('.kicad_prl').exists()
    for board in (source, *paths):
        present = local_settings.check_current_metadata(board.with_suffix('.kicad_prl'))
        need(present or not expected, 'required local settings disappeared')


@contract.sx.parsing_session()
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
    plan, prepared_raw = _prepared_source(binding, before)
    prepared = paths.get('prepared', snapshot)
    prepared_hashes = dict(hashes); prepared_hashes[source.name] = hashlib.sha256(prepared_raw).hexdigest()
    need(pc.read_bytes(prepared, contract.MAX_BYTES) == prepared_raw
         and gui.source_inventory(prepared) == prepared_hashes, 'prepared source/sidecars differ')
    immutable = (contract.check_translation(before, after, moves, **options) if plan is None else
        copper.audit_translation(before, after, plan, moves, scope=options['scope'], region_nm=options['region_nm'],
                                 **intent.region_options(options)))
    need(immutable == data['immutable_check'], 'immutable design differs')
    group_check = intent.group_candidate(before, after, binding['intent']['settings'], moves)
    need((data.get('group_check') == group_check if group_check is not None else 'group_check' not in data),
         'rigid-group source/candidate proof differs')
    preimage, refill = paths['refill-preimage'], paths['refill-native']
    pre_raw = pc.read_bytes(preimage, contract.MAX_BYTES)
    expected_raw = (contract.sx.dump(contract.translated_tree(prepared_raw, moves, **options)) + '\n').encode()
    need(pre_raw == expected_raw, 'translated source bytes differ')
    expected = dict(hashes); expected[source.name] = hashlib.sha256(after).hexdigest()
    pre_hashes = dict(hashes); pre_hashes[source.name] = hashlib.sha256(pre_raw).hexdigest()
    need(gui.source_inventory(candidate) == data['candidate_hashes'] == expected
         and data['candidate'] == str(candidate) and gui.source_inventory(preimage) == pre_hashes, 'candidate/sidecars differ')
    need(contract.check_refill_reconstruction(pre_raw, pc.read_bytes(refill, contract.MAX_BYTES), after)
         == data['refill_transplant'], 'derived-fill reconstruction differs')
    history = None; details = None
    for name, board, captured, observed_raw in (('capture', snapshot, hashes, before),
            ('translate', prepared, prepared_hashes, prepared_raw), ('final-capture', candidate, expected, after)):
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
             and ('region_initialization' in observed) == ('region_initialization' in options)
             and observed.get('region_initialization') == options.get('region_initialization')
             and observed['candidate'] == (str(candidate) if translating else None)
             and observed['observation'] == contract.inspect_board(observed_raw, scope=options['scope']),
             'Native observation differs: ' + name)
        if details is None:
            details = _retained_native_details(observed['details'], plan,
                scope=options['scope'], observation=observed['observation'])
        else:
            need(f.canonical(observed['details']) == f.canonical(details),
                 'Native connectivity/area identity changed beyond reviewed route removal')
        if translating:
            need(observed['candidate_hashes_before'] == prepared_hashes and observed['candidate_hashes_after'] == pre_hashes
                 and observed['saved_candidate_sha256'] == pre_hashes[source.name]
                 and observed['immutable_check'] == contract.check_translation(prepared_raw, pre_raw, moves, **options), 'translation differs')
    natives = {}; drc_inputs = []
    for name, board, saved, captured in (('source-drc', snapshot, False, hashes),
            ('refill-drc', refill, True, pre_hashes), ('final-drc', candidate, False, expected)):
        target = board if saved else work / (name + '-input') / source.name
        native = f.check_drc_stage(work, data, name, board, target, saved, captured, schematic_parity=True)
        need(native == data[name.replace('-', '_')], 'Native DRC readback differs')
        natives[name] = native; drc_inputs.append(target)
    observation = contract.inspect_board(prepared_raw, scope=options['scope'])
    continuity = {}
    for name, native in natives.items():
        if name == 'source-drc':
            _findings(native, qualified_fields=contract.fixed_context_scope(options['scope']))
            continue
        checked = finding_continuity(native, natives['source-drc'], observation, moves, options['scope'])
        need(native['ignored_checks'] == natives['source-drc']['ignored_checks'], 'warning/check policy changed')
        if name != 'source-drc' and checked is not None:
            continuity[name] = checked
    if contract.fixed_context_scope(options['scope']):
        need(data.get('finding_continuity') == continuity, 'metadata finding continuity proof differs')
    material(binding); _metadata([*paths.values(), *drc_inputs], source)
    return dict(candidate=str(candidate), candidate_sha256=expected[source.name], source_hashes=expected,
                original_source=str(source), original_source_hashes=hashes, findings=natives['final-drc'])


def _worker(output, binding_sha):
    started, cpu_start, children = elapsed_time(), time.process_time(), f.child_cpu()
    output = h.real_path(output)
    need(output.parent == c.ROOT/'.runs' and not (output/'work').exists(), 'fresh owned runtime worker directory required')
    binding = f.read_json(output / 'binding.json')
    need(p.sha(output / 'binding.json') == binding_sha, 'binding changed')
    need(f.canonical(_binding(binding['draft'], binding['draft_sha256'])) == f.canonical(binding), 'binding differs')
    work, paths = _paths(output, binding); source = Path(binding['inspection']['source'])
    need(source.parent != output and source.parent not in output.parents, 'worker output overlaps original source')
    def remaining():
        return min(WORKER_SECONDS - (elapsed_time()-started), WORKER_SECONDS - (time.process_time()-cpu_start + f.child_cpu()-children))
    job = f.FloorJob(work, WORKER_SECONDS, remaining, protect_local_settings=True)
    record = dict(schema=1, kind=KIND, status='failed', placement_qualified=False,
        **{key: False for key in AUTHORITY}, binding_sha256=binding_sha, tools=binding['tools'],
        budget_seconds=WORKER_SECONDS, cpu_budget_seconds=WORKER_SECONDS, steps=job.steps, external_exit_required=True)
    def stable():
        h.owned_destination(job._local_settings_owner)
        need(p.sha(output/'binding.json') == binding_sha, 'binding changed'); material(binding)
    def account():
        record.update(wall_seconds=elapsed_time()-started,
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
        drc('source-drc', paths['snapshot'])
        _findings(record['source_drc'], qualified_fields=contract.fixed_context_scope(_options(binding)['scope']))
        native('capture', paths['snapshot'])
        original_raw = pc.read_bytes(paths['snapshot'], contract.MAX_BYTES)
        plan, prepared_raw = _prepared_source(binding, original_raw)
        prepared = paths.get('prepared', paths['snapshot'])
        if plan is not None:
            pc.copy_project(paths['snapshot'].parent, prepared.parent)
            prepared.write_bytes(prepared_raw)
        pc.copy_project(prepared.parent, paths['candidate'].parent)
        native('translate', prepared)
        pc.copy_project(paths['candidate'].parent, paths['refill-preimage'].parent)
        pc.copy_project(paths['refill-preimage'].parent, paths['refill-native'].parent)
        drc('refill-drc', paths['refill-native'], True)
        options = _options(binding); moves = binding['intent']['moves_nm']
        observation = contract.inspect_board(prepared_raw, scope=options['scope'])
        continuity = finding_continuity(record['refill_drc'], record['source_drc'], observation, moves, options['scope'])
        if continuity is not None:
            record['finding_continuity'] = {'refill-drc': continuity}
        stable()
        before = pc.read_bytes(paths['refill-preimage'], contract.MAX_BYTES)
        need(pc.read_bytes(paths['candidate'], contract.MAX_BYTES) == before, 'candidate changed before refill')
        filled = pc.read_bytes(paths['refill-native'], contract.MAX_BYTES)
        paths['candidate'].write_bytes(contract.transplant_refill(before, filled))
        after = pc.read_bytes(paths['candidate'], contract.MAX_BYTES)
        record['refill_transplant'] = contract.check_refill_reconstruction(before, filled, after)
        options = _options(binding); moves = binding['intent']['moves_nm']
        record['immutable_check'] = (contract.check_translation(original_raw, after, moves, **options) if plan is None else
            copper.audit_translation(original_raw, after, plan, moves, scope=options['scope'], region_nm=options['region_nm'],
                                     **intent.region_options(options)))
        group_check = intent.group_candidate(original_raw, after, binding['intent']['settings'], moves)
        if group_check is not None:
            record['group_check'] = group_check
        drc('final-drc', paths['candidate']); native('final-capture', paths['candidate'])
        if contract.fixed_context_scope(options['scope']):
            record['finding_continuity']['final-drc'] = finding_continuity(
                record['final_drc'], record['source_drc'], observation, moves, options['scope'])
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


def _worker_refusal(output, binding_sha256):
    """Bounded failure diagnostics only; never a replacement success proof."""
    try:
        path = output / 'work/result.json'
        raw = pc.read_bytes(path, 2 * 1024**2)
        value = intent.preferences._parse(raw, 2 * 1024**2)
        need(type(value) is dict and type(value.get('schema')) is int and value['schema'] == 1
             and value.get('kind') == KIND and value.get('status') in ('failed', 'cancelled', 'budget_exhausted', 'invalidated')
             and value.get('placement_qualified') is False and all(value.get(key) is False for key in AUTHORITY)
             and value.get('binding_sha256') == binding_sha256, 'unbound worker refusal')
        reason = value.get('reason')
        need(type(reason) is str and 0 < len(reason) <= 4096
             and all(ord(c) >= 32 or c in '\n\t' for c in reason), 'bounded worker diagnostic required')
        return dict(reason=reason, worker_record_sha256=hashlib.sha256(raw).hexdigest(),
                    diagnostic_only=True, grants_approval=False)
    except (OSError, ValueError, KeyError, TypeError, p.Rejected):
        return None


def qualify(draft, draft_sha256, output, *, confirmed=False):
    """Explicit execution only; ordinary controls and CLI share this operation."""
    from .runner import run
    import shutil
    started, cpu_start = elapsed_time(), h.cpu_seconds()
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
        timeout=max(.001, min(WORKER_SECONDS, TOTAL_SECONDS-8-(elapsed_time()-started))),
        max_log_bytes=512*1024, max_group_rss_bytes=RSS_BYTES, max_workdir_bytes=DISK_BYTES)
    h.owned_destination(owner); p.save_json(output/'process.json', process)
    record = dict(schema=1, kind=KIND, status='failed', placement_qualified=False,
        **{key: False for key in AUTHORITY}, binding_sha256=digest, process_sha256=p.sha(output/'process.json'),
        total_seconds=TOTAL_SECONDS, worker_seconds=WORKER_SECONDS, measured_free_bytes=free, required_free_bytes=required,
        controller_exit_not_measured=True, publication_allowance_seconds=1)
    def remaining(): return min(TOTAL_SECONDS-(elapsed_time()-started), TOTAL_SECONDS-(h.cpu_seconds()-cpu_start))
    def stable():
        h.owned_destination(owner); need(p.sha(output/'binding.json') == digest, 'binding changed'); material(binding)
        need(p.sha(output/'process.json') == record['process_sha256'], 'process receipt changed')
        if record['placement_qualified']:
            need(pc.inventory(output/'work', max_bytes=DISK_BYTES) == record['worker_artifact_hashes'], 'worker evidence changed')
            work, boards = _paths(output, binding)
            _metadata([*boards.values(), *(work/(name+'-input')/source.name for name in ('source-drc','final-drc'))], source)
    def account():
        record.update(wall_seconds=elapsed_time()-started, full_cpu_seconds=h.cpu_seconds()-cpu_start)
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
        refusal = _worker_refusal(output, digest)
        if refusal is not None:
            record.update(execution_error=record['reason'], worker_refusal=refusal,
                          reason='Placement worker refused: ' + refusal['reason'])
    account()
    return f.publish(output, record, stable, account, remaining, owned=lambda: h.owned_destination(owner), final_check=stable)


@contract.sx.parsing_session()
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


def routing_settings(witness, seconds=90):
    """Visible constrained starter, not execution or acceptance authority."""
    plan = witness['binding']['intent'].get('copper_plan')
    need(plan is not None, 'affected-copper routing requires its reviewed plan')
    return intent.preferences.validate(dict(intent.preferences.DEFAULTS, scope='selected_nets',
        profile='completion-only', adapter='both', guidance='native', layers='source_all',
        scoring_preference=None, seconds=seconds, nets=copy.deepcopy(plan['incident_names'])))


def _routing_task(witness, settings, method, candidate=None):
    """One original-to-final checker shared by controls and ordinary readers."""
    binding = witness['binding']; value = intent.preferences.validate(settings)
    need(intent.rebuilds_copper(binding['intent']['settings']), 'explicit affected-copper placement required')
    need(method == 'route', 'affected-copper placement supports ordinary Route only')
    expected = routing_settings(witness, value['seconds'])
    need(f.canonical(value) == f.canonical(expected),
         'route every reviewed affected net with both corrections, native completion-only, source layers and engine-default via cost')
    source = Path(binding['inspection']['source'])
    raw = pc.read_bytes(source, contract.MAX_BYTES)
    plan, _ = _prepared_source(binding, raw)
    if candidate is not None:
        candidate = h.real_path(candidate)
        need(candidate.name == source.name, 'composed candidate PCB identity differs')
        before = gui.source_inventory(candidate)
        expected_files = dict(binding['inspection']['source_hashes'])
        expected_files[source.name] = p.sha(candidate)
        need(before == expected_files, 'composed candidate sidecars or file set differ from original')
        local_settings.check_current_metadata(candidate.with_suffix('.kicad_prl'))
        intent.group_candidate(raw, pc.read_bytes(candidate, contract.MAX_BYTES),
            binding['intent']['settings'], binding['intent']['moves_nm'])
        audit = copper.audit_routed(raw, pc.read_bytes(candidate, contract.MAX_BYTES), plan,
            binding['intent']['moves_nm'], scope=intent.settings_scope(binding['intent']['settings']),
            region_nm=binding['intent']['settings']['region_nm'], **intent.region_options(binding['intent']['settings']))
        need(gui.source_inventory(candidate) == before, 'composed candidate changed during audit')
        local_settings.check_current_metadata(candidate.with_suffix('.kicad_prl'))
        return audit
    return None


def _origin(output, witness):
    return dict(schema=1, kind=ORIGIN_KIND, qualification=str(output),
        result_sha256=p.sha(output/'result.json'), binding_sha256=p.sha(output/'binding.json'),
        evidence_sha256=hashlib.sha256(f.canonical(witness['evidence_hashes']).encode()).hexdigest())


def bind_routing(qualification, source, effective, method='route'):
    """Explicit initial CLI/structured binding to a freshly checked qualification."""
    output = h.real_path(qualification); witness = check(output)
    need(h.real_path(source) == h.real_path(witness['candidate']), 'routing source differs from qualified placement')
    _routing_task(witness, effective, method)
    descriptor = _origin(output, witness)
    # Finish after all captured bytes with the same origin metadata/lifecycle fence.
    source_guard(output, witness).check(source)
    return descriptor


def _routing_origin_descriptor(folder, report):
    """Recognize the exact paired native-origin record; grant no result authority."""
    folder = h.real_path(folder); marker = folder/ORIGIN_FILE
    present = marker.exists() or marker.is_symlink()
    if not present and 'placement_origin' not in report:
        return None
    need(present and 'placement_origin' in report, 'placement origin field/marker is missing')
    need(marker.is_file() and not marker.is_symlink(), 'regular placement origin marker required')
    need(type(report.get('schema')) is int and report['schema'] == 1
         and report.get('input_policy', 'native') == 'native' and report.get('strategy') is None
         and not any(key in report for key in ('experimental_route_policy', 'experimental_native_toolchain',
             'production_admitted', 'comparison_route', 'native_improve_child', 'native7_improve_parent',
             'single_selection_policy', 'native7_default_target_basis', 'engine_fanout_override',
             'engine_optimizer_override', 'engine_angle_binding')),
         'placement origin cannot mix experimental, comparison, Improve or transformed routing')
    descriptor = report['placement_origin']
    need(type(descriptor) is dict and set(descriptor) == {
        'schema', 'kind', 'qualification', 'result_sha256', 'binding_sha256', 'evidence_sha256'},
        'exact placement origin descriptor required')
    need(type(descriptor['schema']) is int and descriptor['schema'] == 1 and descriptor['kind'] == ORIGIN_KIND,
         'placement origin schema differs')
    qualification = descriptor['qualification']
    need(type(qualification) is str and Path(qualification).is_absolute()
         and str(h.real_path(qualification)) == qualification and Path(qualification).is_dir(),
         'canonical absolute placement qualification path required')
    need(all(type(descriptor[key]) is str and provenance._DIGEST.fullmatch(descriptor[key]) is not None
             for key in ('result_sha256', 'binding_sha256', 'evidence_sha256')),
         'placement origin digest types differ')
    need(f.canonical(f.read_json(marker)) == f.canonical(descriptor), 'placement origin marker differs')
    return descriptor


def check_routing_record(folder, report, candidate=None):
    """Inherited mandatory lineage. No marker/field means ordinary routing only.

    This consumes retained actual Native proofs; it never launches Native work.
    Mutable local evidence is consistency checked, not authenticated.
    """
    folder = h.real_path(folder); marker = folder/ORIGIN_FILE
    descriptor = _routing_origin_descriptor(folder, report)
    if descriptor is None:
        return None
    output = h.real_path(descriptor['qualification']); witness = check(output)
    need(f.canonical(_origin(output, witness)) == f.canonical(descriptor), 'placement qualification origin changed')
    need(h.real_path(report['source']) == h.real_path(witness['candidate']), 'routing source differs from placement origin')
    effective = report['routing_preferences']['effective']
    audit = _routing_task(witness, effective, 'route', candidate)
    source_guard(output, witness).check(report['source'])
    need(f.canonical(f.read_json(marker)) == f.canonical(descriptor), 'placement marker changed during origin audit')
    return audit


def readback_origin_witness(folder, report):
    """Fresh bounded origin closure for a caller's invocation-local reuse key.

    No origin returns None. Missing, malformed or unfamiliar closure refuses;
    callers may then use the unchanged full reader. This immutable byte/identity
    witness never validates placement, runs Native, or grants result authority.
    Runtime/tool/live-checker identity and full initial validation remain the
    caller's responsibility, with this closure sampled before and after reuse.
    """
    need(type(report) is dict, 'origin routing report must be an object')
    folder = h.real_path(folder)
    descriptor = _routing_origin_descriptor(folder, report)
    if descriptor is None:
        return None
    def file(value,limit):
        before = value.lstat(); parent = value.parent.lstat()
        raw = pc.read_bytes(value,limit); after = value.lstat()
        identity = lambda row:(row.st_dev,row.st_ino,row.st_mode,row.st_uid,row.st_gid,
                              getattr(row,'st_flags',0),row.st_nlink,row.st_size,row.st_mtime_ns)
        need(identity(before) == identity(after) and stat.S_ISREG(after.st_mode)
             and (parent.st_dev,parent.st_ino) == (value.parent.lstat().st_dev,value.parent.lstat().st_ino),
             'origin dependency changed during readback')
        return (str(value),hashlib.sha256(raw).hexdigest(),identity(after),(parent.st_dev,parent.st_ino))

    # External tool reads may yield to callbacks. Sample every dependent byte
    # and metadata witness only after that fence, including the exact draft.
    wrapper_file = file(h.real_path(c.PCBNEW.with_name('pcbnew.py')),h.PROJECT_BYTES)
    descriptor = _routing_origin_descriptor(folder, report)
    need(descriptor is not None, 'placement origin disappeared during external tool read')
    descriptor = copy.deepcopy(descriptor); canonical = f.canonical(descriptor)
    output = h.real_path(descriptor['qualification']); marker = folder/ORIGIN_FILE
    need(output.parent == c.ROOT/'.runs', 'readback origin requires an exact runtime qualification job')
    marker_raw = pc.read_bytes(marker, 64*1024)
    binding_raw = pc.read_bytes(output/'binding.json', 512*1024)
    binding = intent.preferences._parse(binding_raw, 512*1024)
    need(type(binding) is dict and set(binding) == set(
        'schema kind draft draft_sha256 intent inspection runtime runtime_manifest_sha256 wrapper_sha256 code_sha256 tools'.split())
        and type(binding['schema']) is int and binding['schema'] == 1
        and binding['kind'] == KIND and binding['runtime'] == str(c.ROOT)
        and type(binding['tools']) is dict, 'unfamiliar readback origin binding')
    outer = intent.preferences._parse(pc.read_bytes(output/'result.json',512*1024),512*1024)
    need(type(outer) is dict and type(outer.get('schema')) is int and outer['schema'] == 1
         and outer.get('kind') == KIND and outer.get('status') == 'pending_candidate'
         and outer.get('placement_qualified') is True and all(outer.get(key) is False for key in AUTHORITY)
         and (output/'work/result.json').is_file(), 'unfamiliar pending Native qualification closure')
    inspection = binding['inspection']; draft = binding['intent']
    base = set('schema kind source source_hashes observation components native_validation_performed execution_authorized approval_granted limitations'.split())
    need(type(inspection) is dict and base <= set(inspection)
        and set(inspection) <= base | {'native_context','annotation_context','native_source_baseline'}
        and type(inspection['schema']) is int and inspection['schema'] == 1
        and inspection['kind'] == 'autorouter.saved-placement-inspection.v1'
        and type(inspection['source_hashes']) is dict and type(draft) is dict
        and type(draft.get('settings')) is dict, 'unfamiliar placement inspection closure')

    def path(value):
        need(type(value) is str and Path(value).is_absolute(), 'canonical absolute origin dependency required')
        result = h.real_path(value)
        need(str(result) == value, 'noncanonical origin dependency')
        return result

    source = path(inspection['source']); reviewed = path(binding['draft'])
    need(draft.get('source') == str(source) and draft.get('source_hashes') == inspection['source_hashes']
        and draft.get('native_context') == inspection.get('native_context'), 'origin source/context references differ')
    need(path(report['source']) == _paths(output,binding)[1]['candidate'], 'origin candidate path differs')
    roots = [('qualification',output),('source',source.parent)]
    reference = inspection.get('native_context')
    if reference is not None:
        need(type(reference) is dict and set(reference) == {'receipt','receipt_sha256','context_sha256'},
             'unfamiliar Native inspection reference')
        receipt = path(reference['receipt'])
        need(receipt.name == 'inspection.json', 'unfamiliar Native inspection receipt')
        roots.append(('native-inspection',receipt.parent))
        raw = pc.read_bytes(receipt,512*1024); record = intent.preferences._parse(raw,512*1024)
        fields = set('schema policy source source_hashes static tools accepted status native_validation_performed budget_seconds cpu_budget_seconds native steps wall_seconds parent_cpu_seconds child_cpu_seconds control_child_cpu_seconds monitor_cpu_seconds total_cpu_seconds native_report_sha256 note placement_context'.split())
        need(type(record) is dict and set(record) == fields and record['source'] == str(source)
            and record['source_hashes'] == inspection['source_hashes'] and record['tools'] == binding['tools'],
            'unfamiliar Native inspection dependency graph')
        # Shared inspection readers consume only this evidence tree, source
        # project and caller-witnessed runtime/tools. An external proof path
        # cannot silently become a hash-only dependency of a cached result.
        tools = binding['tools'].get('files',{})
        need(type(tools) is dict, 'unfamiliar origin tool map')
        allowed = set(tools) | {str(c.ROOT/'autorouter/native.py')}
        def references(value, depth=0):
            need(depth <= 32, 'Native inspection reference depth ceiling')
            if type(value) is dict:
                for key,item in value.items():
                    references(key,depth+1); references(item,depth+1)
            elif type(value) is list:
                for item in value: references(item,depth+1)
            elif type(value) is str and value.startswith('/'):
                item = path(value)
                need(item.is_relative_to(receipt.parent) or item.is_relative_to(source.parent)
                     or str(item) in allowed, 'unfamiliar external Native proof dependency')
        references({'source':record['source'],'steps':record['steps'],
                    'placement_context':record['placement_context']})
    else:
        need('annotation_context' not in inspection and 'native_source_baseline' not in inspection,
             'Native placement context closure is missing')
    for index,(_,root) in enumerate(roots):
        need(root.is_dir() and not folder.is_relative_to(root) and not root.is_relative_to(folder)
             and root != c.ROOT and not c.ROOT.is_relative_to(root), 'overlapping origin evidence closure')
        need(all(not root.is_relative_to(other) and not other.is_relative_to(root)
                 for _,other in roots[:index]), 'overlapping origin dependency trees')
    need(not reviewed.is_relative_to(folder), 'reviewed draft overlaps routing evidence')

    draft_file = file(reviewed,64*1024)
    need(draft_file[1] == binding['draft_sha256'] and wrapper_file[1] == binding['wrapper_sha256']
         and f.canonical(intent.preferences._parse(pc.read_bytes(reviewed,64*1024),64*1024)) == f.canonical(draft),
         'exact reviewed draft/wrapper closure differs')
    trees = []
    for role,root in roots:
        identity = retained.retained_tree_identity(root,root.parent)
        if role == 'source':
            files,directories = pc.inventory(root,with_directories=True)
            inventory = dict(files=files,directories=list(directories))
        else:
            inventory = h.evidence_witness(root)
        metadata = []
        for name in inventory['files']:
            if Path(name).suffix == '.kicad_prl':
                info = (root/name).lstat()
                metadata.append((name,info.st_dev,info.st_ino,getattr(info,'st_flags',0),
                                 info.st_nlink,stat.S_IFMT(info.st_mode)))
        need(identity == retained.retained_tree_identity(root,root.parent), 'origin evidence identity changed')
        trees.append((role,str(root),f.canonical(inventory),tuple(sorted(identity.items())),tuple(sorted(metadata))))
    need(pc.read_bytes(output/'binding.json',512*1024) == binding_raw
         and pc.read_bytes(marker,64*1024) == marker_raw
         and f.canonical(report.get('placement_origin')) == canonical, 'origin binding/marker changed during readback')
    return ('placement-origin-readback-v1',canonical,hashlib.sha256(marker_raw).hexdigest(),
            tuple(trees),draft_file,wrapper_file)


def routing_origin_material(folder, report):
    """Final original-source/evidence fence after an operation's full readback.

    Recheck the pinned descriptor and exact retained bytes, without replaying
    Native proof readers. This alone never establishes a valid placement.
    """
    folder = Path(folder); marker = folder/ORIGIN_FILE
    if not marker.exists() and not marker.is_symlink() and 'placement_origin' not in report:
        return None
    descriptor = copy.deepcopy(report.get('placement_origin'))
    need(type(descriptor) is dict and set(descriptor) == {
        'schema', 'kind', 'qualification', 'result_sha256', 'binding_sha256', 'evidence_sha256'}
        and type(descriptor['schema']) is int and descriptor['schema'] == 1 and descriptor['kind'] == ORIGIN_KIND,
        'exact placement origin material required')
    need(f.canonical(f.read_json(marker)) == f.canonical(descriptor), 'placement origin marker changed')
    output = h.real_path(descriptor['qualification'])
    need(output.parent == c.ROOT/'.runs', 'placement origin outside this runtime')
    binding = f.read_json(output/'binding.json')
    def bytes_current():
        witness = dict(evidence_hashes=h.evidence_witness(output))
        need(f.canonical(_origin(output,witness)) == f.canonical(descriptor), 'placement origin material changed')
        need(f.canonical(report.get('placement_origin')) == f.canonical(descriptor)
             and f.canonical(f.read_json(marker)) == f.canonical(descriptor), 'placement origin descriptor changed')
    bytes_current()
    material(binding)
    need(h.real_path(report['source']) == _paths(output,binding)[1]['candidate'], 'placement source path changed')
    bytes_current()
    source = Path(binding['inspection']['source']); work, boards = _paths(output,binding)
    _metadata([*boards.values(), *(work/(name+'-input')/source.name for name in ('source-drc','final-drc'))],source)
    intent.current(binding['inspection'])


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
    if intent.rebuilds_copper(expected['binding']['intent']['settings']):
        def task(settings, method, candidate):
            _routing_task(expected, settings, method, candidate)
        return gui.SourceGuard(Path(expected['candidate']), fresh, task, placement_origin=output)
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
