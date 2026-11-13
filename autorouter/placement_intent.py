"""Saved-project placement input and review intent, without editing authority.

Reuse the qualified narrow geometry contract and MIT search. No fixture names,
historical run directories, model calls, Native processes or PCB writes belong
here. Proposals are geometry drafts until a separate Native qualification.
"""
from __future__ import annotations

import copy
from decimal import Context, Decimal, InvalidOperation, localcontext
import hashlib
from pathlib import Path
import threading

from . import design_intent, gui, local_settings, placement_clearance as pc
from . import preferences, placement_copper as copper, routing_scope
from experiments.placement_native_proposal_v1 import contract
from experiments.constrained_placement_v1 import constraints, prototype

KIND = 'autorouter.selected-placement-intent.v1'
SETTINGS_KIND = 'autorouter.selected-placement-settings.v1'
ORDINARY_SETTINGS_KIND = 'autorouter.selected-placement-settings.v2'
COPPER_SETTINGS_KIND = 'autorouter.selected-placement-settings.v3'
GROUP_SETTINGS_KIND = 'autorouter.selected-placement-settings.v4'
GROUP_POLICY = constraints.RIGID_TRANSLATION_POLICY
COPPER_POLICY = 'rebuild-affected-unlocked-v1'
LIMITS = (
    'Experimental translation only: unrotated front footprints, circular through-hole pads, rectangular courtyards and board.',
    'Unselected, locked and existing-routed-net components stay fixed. Every existing copper item is preserved.',
    'The movement rectangle must avoid preserved copper and zone envelopes. Groups, flips, rotation, cutouts and keepouts are not supported yet.',
    'Geometry proposals do not establish Native, electrical or manufacturing suitability. Qualification and separate routing review are required.',
)
ORDINARY_LIMITS = (
    'Experimental front-side translation at fixed cardinal orientations; only eligible two-pad SMD parts may move.',
    'Unselected, locked, ineligible and existing-routed-net components stay fixed. Every existing copper item is preserved.',
    'Courtyard envelopes are conservative search obstacles. Groups, flips, rotation changes, cutouts and keepouts are not supported yet.',
    'The movement rectangle must avoid preserved copper and zone envelopes. Native validation and separate routing review remain required.',
    'No electrical, thermal, timing or manufacturing suitability is inferred from connectivity or shorter connections.',
)
COPPER_LIMITS = (
    'Explicit opt-in: rebuild all unlocked routing on every named net incident to the selected eligible parts.',
    'Any incident locked or user-protected net/route refuses this scope. Unrelated copper, fixed parts, zones and original requirements remain unchanged.',
    'The exact affected-copper plan requires review; a placement draft grants no execution, routing or warning-approval authority.',
    'Mandatory original-project Native inspection, validated placement, protected selected-net routing and fresh original-to-final delivery checks remain required.',
    'Existing geometry limits and preserved copper/zone movement boundaries still apply. No electrical suitability is inferred from names, DRC or shorter routing.',
)
CONTEXT_LIMITS = (
    'Experimental fixed-context translation: eligible front two-pad SMD parts only; other parts and passive artwork remain immutable.',
    'The exact unchanged fixed baseline is retained, including inherited courtyard-proxy conflicts; every moving-part boundary, region and obstacle check stays mandatory.',
    'Ordinary copper-zone definitions are preserved and refilled by KiCad; derived fill may change. Copper pours are not placement keepouts; actual rule areas remain unsupported.',
    'Explicitly named protected nets with copper pours are refused: exact protected fill is not guaranteed. Route-UUID protection applies to those routes only.',
    'Retained segments are conservative courtyard obstacles. No grouping, side/orientation changes, physical or electrical suitability is implied.',
    'Source-bound Native silkscreen/mask boxes prefilter new annotation conflicts; these conservative proxies do not replace final Native checks.',
    'Native checks, original design, protected copper and exact finding continuity remain required before delivery.',
)


def settings(selected, region_nm, *, scope=contract.MULTIPAD_SCOPE, copper_policy=None,
             protected_names=None, protected_route_ids=None, group_policy=None):
    options = contract.scope_options(scope=scope, selected=selected, region_nm=region_nm)
    if scope not in (contract.MULTIPAD_SCOPE, contract.ORDINARY_SCOPE, contract.CONTEXT_SCOPE):
        raise ValueError('Unsupported product placement scope.')
    value = dict(schema=1, kind=SETTINGS_KIND, selected=options['selected'], region_nm=options['region_nm'],
                preserve_existing=True, orientation='preserve', side='preserve',
                search=dict(seed=7, steps=160, alternatives=2, seconds=2))
    if contract.ordinary_scope(scope):
        value.update(schema=2, kind=ORDINARY_SETTINGS_KIND, scope=scope)
    if scope == contract.CONTEXT_SCOPE:
        value.update(fixed_context_policy=constraints.FIXED_CONTEXT_POLICY,
                     zone_policy='preserve-intent-native-refill-v1',
                     metadata_finding_policy='exact-footprint-anchor-translation-v1',
                     annotation_policy='native-silk-mask-proxy-v1')
    if copper_policy is None:
        if protected_names is not None or protected_route_ids is not None:
            raise ValueError('Explicit copper policy required for protected-net/route settings.')
    else:
        if type(copper_policy) is not str or copper_policy != COPPER_POLICY:
            raise ValueError('Unsupported placement copper policy.')
        names = [] if protected_names is None else protected_names
        if type(names) is not list:
            raise ValueError('Explicit protected native net-name list required.')
        names = routing_scope.validate_names(names) if names else []
        ids = copper._uuids([] if protected_route_ids is None else protected_route_ids,
                            maximum=64, empty=True)
        value.update(schema=3, kind=COPPER_SETTINGS_KIND, scope=scope, preserve_existing=False,
                     copper_policy=copper_policy, protected_names=names, protected_route_ids=ids)
    if group_policy is not None:
        if type(group_policy) is not str or group_policy != GROUP_POLICY or len(options['selected']) < 2:
            raise ValueError('A rigid group requires two or more explicitly selected eligible components.')
        if copper_policy != COPPER_POLICY:
            raise ValueError('Rigid-group delivery currently requires the explicit affected-net rebuild workflow; protected copper remains fixed.')
        value.update(schema=4, kind=GROUP_SETTINGS_KIND, scope=scope, group_policy=group_policy)
    return value


def settings_scope(value):
    return value.get('scope') if value.get('schema') in (2, 3, 4) else contract.MULTIPAD_SCOPE


def rebuilds_copper(value):
    """Semantic dispatch for already validated settings; schema is not policy."""
    return value.get('copper_policy') == COPPER_POLICY and value.get('preserve_existing') is False


def grouped(value):
    return value.get('group_policy') == GROUP_POLICY


def validate_settings(value):
    if type(value) is not dict or type(value.get('schema')) is not int:
        raise ValueError('Explicit selected-placement settings are required.')
    kwargs = {}
    if value['schema'] == 3 or value['schema'] == 4 and any(
            key in value for key in ('copper_policy', 'protected_names', 'protected_route_ids')):
        kwargs = {key: value.get(key) for key in ('copper_policy', 'protected_names', 'protected_route_ids')}
    if value['schema'] == 4:
        kwargs['group_policy'] = value.get('group_policy')
    expected = settings(value.get('selected'), value.get('region_nm'), scope=settings_scope(value), **kwargs)
    # Canonical comparison refuses Boolean/integer substitutions and extra tools.
    if constraints.encoded(value) != constraints.encoded(expected):
        raise ValueError('Unsupported placement settings; constraints were not changed.')
    return expected


def load_settings(path):
    return validate_settings(preferences._parse(pc.read_bytes(path, 64 * 1024), 64 * 1024))


def inspect_saved(board, *, native_context=None):
    """Return bounded actual saved-file facts, never inferred electrical intent."""
    static = design_intent.inspect_project(board)
    source = Path(static['source'])
    raw = pc.read_bytes(source, contract.MAX_BYTES)
    if native_context is not None:
        observation = contract.inspect_board(raw, scope=contract.CONTEXT_SCOPE)
    else:
        try:
            observation = contract.inspect_board(raw, scope=contract.MULTIPAD_SCOPE)
        except ValueError:
            try:
                observation = contract.inspect_board(raw, scope=contract.ORDINARY_SCOPE)
            except ValueError:
                observation = contract.inspect_board(raw, scope=contract.CONTEXT_SCOPE)
    local_settings.check_current_metadata(source.with_suffix('.kicad_prl'))
    if gui.source_inventory(source) != static['source_hashes']:
        raise ValueError('Saved project changed during placement inspection.')
    routed_nets = {row['net'] for row in observation['routes']}
    components = []
    for fp in observation['footprints']:
        reasons = list(fp.get('fixed_reasons', []))
        if fp['locked']: reasons.append('Locked in KiCad')
        if any(pad['net'] in routed_nets for pad in fp['pads']):
            reasons.append('Shares a net with existing copper')
        components.append(dict(uuid=fp['uuid'], reference=fp['reference'],
            position_nm=fp['position_nm'], pad_count=len(fp['pads']), fixed_reasons=reasons))
    result = dict(schema=1, kind='autorouter.saved-placement-inspection.v1', source=str(source),
        source_hashes=static['source_hashes'], observation=observation, components=components,
        native_validation_performed=False, execution_authorized=False, approval_granted=False,
        limitations=list(CONTEXT_LIMITS if observation['scope'] == contract.CONTEXT_SCOPE else
                          ORDINARY_LIMITS if observation['scope'] == contract.ORDINARY_SCOPE else LIMITS))
    if native_context is not None:
        descriptor, annotations = _native_context(source, static['source_hashes'], native_context)
        result.update(native_context=descriptor, annotation_context=annotations)
    return result


def _native_context(source, hashes, reference):
    """Read only a source-bound, completed shared inspection; no Native launch."""
    from . import project_inspection as inspection, handoff
    supplied = reference if type(reference) is dict else None
    if supplied is not None:
        if set(supplied) != {'receipt', 'receipt_sha256', 'context_sha256'}:
            raise ValueError('Exact Native placement context reference required.')
        reference = supplied['receipt']
    if type(reference) not in (str, Path) and not isinstance(reference, Path):
        raise ValueError('Native placement inspection receipt path required.')
    path = handoff.real_path(reference)
    receipt_raw = pc.read_bytes(path, 512 * 1024)
    record = inspection.check(path)
    if constraints.encoded(record) != constraints.encoded(preferences._parse(receipt_raw, 512 * 1024)):
        raise ValueError('Native placement receipt changed during readback.')
    if record.get('policy') != inspection.PLACEMENT_POLICY or record['source'] != str(source) or record['source_hashes'] != hashes:
        raise ValueError('Native placement inspection belongs to another source.')
    raw = pc.read_bytes(path.parent / 'placement-context.json', 512 * 1024)
    digest = hashlib.sha256(raw).hexdigest()
    if digest != record['placement_context']['sha256']:
        raise ValueError('Native placement context changed during inspection.')
    data = preferences._parse(raw, 512 * 1024)
    descriptor = dict(receipt=str(path), receipt_sha256=hashlib.sha256(receipt_raw).hexdigest(), context_sha256=digest)
    if supplied is not None and constraints.encoded(supplied) != constraints.encoded(descriptor):
        raise ValueError('Native placement evidence changed; inspect again.')
    from . import placement_annotations
    context = placement_annotations.validate(data['context'])
    if (context['source_board_sha256'] != hashes[source.name] or gui.source_inventory(source) != hashes
            or pc.read_bytes(path, 512 * 1024) != receipt_raw):
        raise ValueError('Native annotation source changed.')
    return descriptor, context


def current(inspection):
    """Compare actual current source, including local-settings metadata."""
    fresh = (inspect_saved(inspection['source'], native_context=inspection['native_context'])
             if 'native_context' in inspection else inspect_saved(inspection['source']))
    if constraints.encoded(fresh) != constraints.encoded(inspection):
        raise ValueError('Placement source changed; inspect the saved project again.')
    return fresh


def _effective_context(inspection, value):
    if type(value) is dict and grouped(value):
        with localcontext(Context(prec=50)):
            return _effective_context_context(inspection, value)
    return _effective_context_context(inspection, value)


def _effective_context_context(inspection, value):
    """Capture one PCB image, then fence the original source before returning."""
    if settings_scope(value) != inspection['observation']['scope']:
        raise ValueError('Placement settings geometry scope differs; inspect and choose settings for this project.')
    if not rebuilds_copper(value):
        return None, copy.deepcopy(inspection['observation'])
    current(inspection)
    source = Path(inspection['source'])
    raw = pc.read_bytes(source, contract.MAX_BYTES)
    if (hashlib.sha256(raw).hexdigest() != inspection['source_hashes'].get(source.name)
            or hashlib.sha256(raw).hexdigest() != inspection['observation']['source_board_sha256']):
        raise ValueError('Placement source changed while capturing affected copper.')
    plan = copper.propose(raw, value['selected'], protected_names=value['protected_names'],
                          protected_route_ids=value['protected_route_ids'], scope=settings_scope(value))
    observation = contract.inspect_board(copper.prepare(raw, plan), scope=settings_scope(value))
    local_settings.check_current_metadata(source.with_suffix('.kicad_prl'))
    if gui.source_inventory(source) != inspection['source_hashes']:
        raise ValueError('Placement source changed during affected-copper preparation.')
    return plan, observation


def copper_plan(inspection, value):
    """Return a fresh exact source-bound plan only for explicit v3 settings."""
    return _effective_context(inspection, validate_settings(value))[0]


def effective_observation(inspection, value):
    """Observe the in-memory prepared task; never alter the original inspection."""
    return _effective_context(inspection, validate_settings(value))[1]


def _facts(inspection, value, plan, observation):
    if type(value) is dict and grouped(value):
        with localcontext(Context(prec=50)):
            return _facts_context(inspection, value, plan, observation)
    return _facts_context(inspection, value, plan, observation)


def _facts_context(inspection, value, plan, observation):
    if settings_scope(value) != inspection['observation']['scope']:
        raise ValueError('Placement settings geometry scope differs; inspect and choose settings for this project.')
    # Give the actionable protection reason before geometric search can fail.
    fixed = {row['uuid'] for row in inspection['components'] if row['fixed_reasons']} if plan is None else set()
    if set(value['selected']) & fixed:
        raise ValueError('Selected components include fixed, locked or routed-net components; deselect those components.')
    result = contract.facts_from_observation(observation, scope=settings_scope(value),
        selected=value['selected'], region_nm=value['region_nm'])
    if settings_scope(value) == contract.CONTEXT_SCOPE:
        if 'native_context' not in inspection or 'annotation_context' not in inspection:
            raise ValueError('Inspect Native placement geometry before proposing this fixed-context task.')
        result['annotation_context'] = copy.deepcopy(inspection['annotation_context'])
        result = constraints.prepare(result)
        constraints.validate_alternative(result, constraints.original_alternative(result))
    if set(value['selected']) & constraints.immovable(result):
        raise ValueError('Selected components include locked or routed-net components; deselect those components.')
    if len(value['selected']) < 2:
        raise ValueError('This search requires at least two movable components; nothing was moved.')
    if grouped(value):
        result['groups'] = [dict(policy=GROUP_POLICY, members=list(value['selected']))]
        result = constraints.prepare(result)
        constraints.validate_alternative(result, constraints.original_alternative(result))
    return result


def facts(inspection, value):
    value = validate_settings(value)
    plan, observation = _effective_context(inspection, value)
    return _facts(inspection, value, plan, observation)


def _group_nm(atom):
    """Exact bounded decimal-to-nm conversion, independent of Decimal context."""
    if type(atom) is not str or not 0 < len(atom) <= 128:
        raise ValueError('Bounded rigid-group coordinate required.')
    try:
        value = Decimal(atom)
    except InvalidOperation as exc:
        raise ValueError('Finite rigid-group coordinate required.') from exc
    if not value.is_finite():
        raise ValueError('Finite rigid-group coordinate required.')
    sign, digits, exponent = value.as_tuple()
    if not any(digits):
        return 0
    exponent += 6
    if exponent < 0:
        tail = -exponent
        if tail >= len(digits) or any(digits[-tail:]):
            raise ValueError('Exact integer-nm rigid-group coordinate required.')
        digits = digits[:-tail]; exponent = 0
    if len(digits) + exponent > 10:
        raise ValueError('Rigid-group coordinate exceeds supported bounds.')
    result = int(''.join(map(str, digits))) * 10**exponent
    if result > 2_000_000_000:
        raise ValueError('Rigid-group coordinate exceeds supported bounds.')
    return -result if sign else result


def group_moves(observation, value, moves):
    """Exact integer-nm rigidity from original footprint anchors, not DRC."""
    value = validate_settings(value)
    if not grouped(value):
        return None
    selected = value['selected']
    if type(moves) is not dict or set(moves) != set(selected):
        raise ValueError('Rigid group requires the exact selected member moves.')
    anchors = {row['uuid']: row['position_nm'] for row in observation['footprints']}
    deltas = set()
    for key in selected:
        target = moves[key]
        if (key not in anchors or type(target) is not list or len(target) != 2
                or any(type(n) is not int or abs(n) > 2_000_000_000 for n in target)):
            raise ValueError('Rigid group requires bounded exact integer-nm positions.')
        deltas.add(tuple(target[i] - anchors[key][i] for i in range(2)))
    if len(deltas) != 1:
        raise ValueError('Rigid group members must retain exact relative positions; shear refused.')
    return dict(policy=GROUP_POLICY, members=list(selected), delta_nm=list(next(iter(deltas))),
                moves_sha256=constraints.digest(moves))


def group_candidate(source_raw, candidate_raw, value, moves):
    if not grouped(validate_settings(value)):
        return None
    with localcontext(Context(prec=50)):
        return _group_candidate(source_raw, candidate_raw, value, moves)


def _group_candidate(source_raw, candidate_raw, value, moves):
    """Recheck actual candidate anchors and source-bound rigidity at delivery."""
    value = validate_settings(value)
    if not grouped(value):
        return None
    observation = contract.inspect_board(source_raw, scope=settings_scope(value))
    audit = group_moves(observation, value, moves)
    tree = contract.read_board(candidate_raw)
    found = {}
    for footprint in contract.sx.children(tree, 'footprint'):
        key = contract.uid(footprint)
        if key in moves:
            at = contract.sx.one(footprint, 'at')
            if key in found or at is None or len(at) not in (3, 4):
                raise ValueError('Rigid-group candidate anchor identity differs.')
            found[key] = [_group_nm(n) for n in at[1:3]]
    if found != moves:
        raise ValueError('Actual candidate anchors differ from reviewed rigid-group moves.')
    return dict(audit, actual_candidate_anchors_verified=True)


def propose(inspection, value, *, cancel_event=None):
    """Bounded deterministic search; all alternatives remain non-Native drafts."""
    if cancel_event is not None and type(cancel_event) is not threading.Event:
        raise ValueError('A threading.Event cancellation token is required.')
    value = validate_settings(value)
    if not rebuilds_copper(value):
        current(inspection)
    plan, observation = _effective_context(inspection, value)
    original = _facts(inspection, value, plan, observation)
    result = prototype.propose(original, **value['search'], cancel_event=cancel_event)
    current(inspection)
    if cancel_event is not None and cancel_event.is_set():
        result['status'] = 'cancelled'; result['alternatives'] = []
    # Quantization is part of the draft contract, not deferred to the writer.
    for row in result['alternatives']:
        row['candidate'], row['moves_nm'] = contract.quantized_translation(original, row['candidate'], observation=observation)
        group_moves(observation, value, row['moves_nm'])
    proposal = dict(schema=1, kind='autorouter.placement-proposals.v1', inspection=copy.deepcopy(inspection),
        settings=value, search=result, native_validation_performed=False,
        execution_authorized=False, approval_granted=False)
    if plan is not None:
        proposal.update(copper_plan=plan, limitations=list(COPPER_LIMITS))
    return proposal


def original_proposal(inspection, value):
    """Explicit original-group review; never describe it as a search success."""
    value = validate_settings(value)
    if not grouped(value):
        raise ValueError('Original arrangement review currently requires explicit rigid-group settings.')
    current(inspection)
    plan, observation = _effective_context(inspection, value)
    original = _facts(inspection, value, plan, observation)
    candidate, moves = contract.quantized_translation(original,
        constraints.original_alternative(original), observation=observation)
    group_moves(observation, value, moves)
    current(inspection)
    return dict(schema=1, kind='autorouter.placement-proposals.v1', inspection=copy.deepcopy(inspection),
        settings=value, copper_plan=plan, limitations=list(COPPER_LIMITS),
        search=dict(status='original_for_review', alternatives=[dict(candidate=candidate,
                    moves_nm=moves, origin='source-original')], search_performed=False),
        native_validation_performed=False, execution_authorized=False, approval_granted=False)


class Review:
    """Detached pose state; edits/rejection revoke any earlier review intent."""
    def __init__(self, proposal):
        self.proposal = copy.deepcopy(proposal)
        if (proposal.get('kind') != 'autorouter.placement-proposals.v1'
                or proposal['search']['status'] not in ('proposals_ready', 'original_for_review')):
            raise ValueError('Current placement alternatives are required.')
        self.inspection = self.proposal['inspection']
        self.settings = validate_settings(self.proposal['settings'])
        self.copper_plan, self.observation = _effective_context(self.inspection, self.settings)
        if self.copper_plan is not None:
            if copper._encoded(self.proposal.get('copper_plan')) != copper._encoded(self.copper_plan):
                raise ValueError('Placement proposal affected-copper plan differs from the current source and settings.')
        elif 'copper_plan' in self.proposal:
            raise ValueError('Preserve-existing placement cannot include an affected-copper plan.')
        self.facts = _facts(self.inspection, self.settings, self.copper_plan, self.observation)
        rows = self.proposal['search']['alternatives']
        if type(rows) is not list or not 1 <= len(rows) <= 2:
            raise ValueError('One or two bounded alternatives are required.')
        if self.proposal['search']['status'] == 'original_for_review':
            if (not grouped(self.settings) or len(rows) != 1
                    or self.proposal['search'].get('search_performed') is not False
                    or rows[0].get('origin') != 'source-original'
                    or constraints.encoded(rows[0]['candidate']) != constraints.encoded(constraints.original_alternative(self.facts))):
                raise ValueError('Original arrangement must match the exact current source; no search success is implied.')
        self.alternatives = [contract.quantized_translation(self.facts, r['candidate'], observation=self.observation)[0] for r in rows]
        self.revision = 0; self.intent = None
        self.choose(0)

    def _adopt(self, candidate):
        if self.revision >= 256:
            raise ValueError('Review edit limit reached; start a new review.')
        pose, moves = contract.quantized_translation(self.facts, candidate, observation=self.observation)
        group_moves(self.observation, self.settings, moves)
        self.pose, self.moves = pose, moves
        self.revision += 1; self.intent = None

    def choose(self, index):
        self.intent = None
        if type(index) is not int or not 0 <= index < len(self.alternatives):
            raise ValueError('Choose an available alternative.')
        self._adopt(self.alternatives[index])

    def edit(self, component, x, y):
        self.intent = None
        if type(component) is not str or component not in self.settings['selected']:
            raise ValueError('Only selected movable components can be edited.')
        self.edit_many({component: [x, y]})

    def edit_many(self, edits):
        if grouped(self.settings):
            with localcontext(Context(prec=50)):
                return self._edit_many(edits)
        return self._edit_many(edits)

    def _edit_many(self, edits):
        """Adopt one combined final pose; never expose intermediate moves."""
        self.intent = None
        if type(edits) is not dict or not 1 <= len(edits) <= len(self.settings['selected']):
            raise ValueError('Provide a bounded set of selected component edits.')
        if any(type(component) is not str or component not in self.settings['selected'] for component in edits):
            raise ValueError('Only selected movable components can be edited.')
        moves = copy.deepcopy(self.moves)
        for component, coordinates in edits.items():
            if type(coordinates) is not list or len(coordinates) != 2:
                raise ValueError('Enter bounded decimal coordinates in millimetres.')
            target = []
            for text in coordinates:
                if type(text) is not str or not 0 < len(text) <= 32:
                    raise ValueError('Enter bounded decimal coordinates in millimetres.')
                try:
                    value = Decimal(text)
                    if not value.is_finite() or abs(value) > 2000:
                        raise ValueError('Coordinates must be finite and within ±2000 mm.')
                    target.append(_group_nm(text) if grouped(self.settings) else int((value * 1000000).to_integral_value()))
                except InvalidOperation as exc:
                    raise ValueError('Enter decimal coordinates in millimetres.') from exc
            moves[component] = target
        if grouped(self.settings):
            anchors = {row['uuid']: row['position_nm'] for row in self.observation['footprints']}
            deltas = {tuple(moves[key][i] - anchors[key][i] for i in range(2)) for key in edits}
            if len(deltas) != 1:
                raise ValueError('Rigid-group edits must give every edited member the same displacement.')
            delta = next(iter(deltas))
            moves = {key: [anchors[key][i] + delta[i] for i in range(2)] for key in self.settings['selected']}
            group_moves(self.observation, self.settings, moves)
        pose = contract.validate_moves(self.observation, moves,
            scope=settings_scope(self.settings), selected=self.settings['selected'], region_nm=self.settings['region_nm'])
        pose['source_sha256'] = constraints.digest(self.facts)
        self._adopt(pose)

    def decision(self, *, acknowledged, accepted):
        self.intent = None
        if type(acknowledged) is not bool or not acknowledged or type(accepted) is not bool:
            raise ValueError('Explicit review of this exact draft is required.')
        if self.copper_plan is not None or rebuilds_copper(self.settings):
            selected = validate_settings(self.settings)
            plan, observation = _effective_context(self.inspection, selected)
            original = _facts(self.inspection, selected, plan, observation)
            if (copper._encoded(plan) != copper._encoded(self.copper_plan)
                    or constraints.encoded(observation) != constraints.encoded(self.observation)
                    or constraints.encoded(original) != constraints.encoded(self.facts)
                    or constraints.encoded(selected) != constraints.encoded(self.proposal['settings'])):
                raise ValueError('Placement source, settings or affected-copper review changed; review a new proposal.')
        else:
            current(self.inspection)
        constraints.validate_alternative(self.facts, self.pose)
        value = dict(schema=1, kind=KIND, choice='reviewed_draft' if accepted else 'reject',
            revision=self.revision, source=self.inspection['source'],
            source_hashes=copy.deepcopy(self.inspection['source_hashes']),
            inspection_sha256=constraints.digest(self.inspection), settings=copy.deepcopy(self.settings),
            facts_sha256=constraints.digest(self.facts), moves_nm=copy.deepcopy(self.moves),
            pose_sha256=constraints.digest(self.pose), native_validation_performed=False,
            execution_authorized=False, approval_granted=False, routing_accepted=False,
            warning_acknowledged=False, human_PCB_approval=False)
        if self.copper_plan is not None:
            value['copper_plan'] = copy.deepcopy(self.copper_plan)
        if 'native_context' in self.inspection:
            value['native_context'] = copy.deepcopy(self.inspection['native_context'])
        self.intent = value
        return copy.deepcopy(value)


def validate_draft(inspection, value):
    if type(value) is dict and type(value.get('settings', {})) is dict and grouped(value.get('settings', {})):
        with localcontext(Context(prec=50)):
            return validate_draft_context(inspection, value)
    return validate_draft_context(inspection, value)


def validate_draft_context(inspection, value):
    """Untrusted JSON may describe a draft, never grant execution/approval."""
    if type(value) is not dict or type(value.get('revision')) is not int or not 1 <= value['revision'] <= 256:
        raise ValueError('A bounded explicit draft revision is required.')
    selected = validate_settings(value.get('settings'))
    plan, observation = _effective_context(inspection, selected)
    original = _facts(inspection, selected, plan, observation)
    pose = contract.validate_moves(observation, value.get('moves_nm'),
        scope=settings_scope(selected), selected=selected['selected'], region_nm=selected['region_nm'])
    group_moves(observation, selected, value.get('moves_nm'))
    pose['source_sha256'] = constraints.digest(original)
    constraints.validate_alternative(original, pose)
    expected = dict(schema=1, kind=KIND, choice='reviewed_draft', revision=value['revision'],
        source=inspection['source'], source_hashes=inspection['source_hashes'],
        inspection_sha256=constraints.digest(inspection), settings=selected,
        facts_sha256=constraints.digest(original), moves_nm=value['moves_nm'],
        pose_sha256=constraints.digest(pose), native_validation_performed=False,
        execution_authorized=False, approval_granted=False, routing_accepted=False,
        warning_acknowledged=False, human_PCB_approval=False)
    if plan is not None:
        if copper._encoded(value.get('copper_plan')) != copper._encoded(plan):
            raise ValueError('Draft affected-copper plan differs from the current source and settings.')
        expected['copper_plan'] = plan
    if 'native_context' in inspection:
        expected['native_context'] = inspection['native_context']
    if constraints.encoded(value) != constraints.encoded(expected):
        raise ValueError('Draft authority, source, settings, geometry or review choice differs.')
    current(inspection)
    return copy.deepcopy(expected)
