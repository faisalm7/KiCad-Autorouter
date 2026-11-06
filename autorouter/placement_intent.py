"""Saved-project placement input and review intent, without editing authority.

Reuse the qualified narrow geometry contract and MIT search. No fixture names,
historical run directories, model calls, Native processes or PCB writes belong
here. Proposals are geometry drafts until a separate Native qualification.
"""
from __future__ import annotations

import copy
from decimal import Decimal, InvalidOperation
from pathlib import Path
import threading

from . import design_intent, gui, local_settings, placement_clearance as pc
from . import preferences
from experiments.placement_native_proposal_v1 import contract
from experiments.constrained_placement_v1 import constraints, prototype

KIND = 'autorouter.selected-placement-intent.v1'
SETTINGS_KIND = 'autorouter.selected-placement-settings.v1'
ORDINARY_SETTINGS_KIND = 'autorouter.selected-placement-settings.v2'
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


def settings(selected, region_nm, *, scope=contract.MULTIPAD_SCOPE):
    options = contract.scope_options(scope=scope, selected=selected, region_nm=region_nm)
    if scope not in (contract.MULTIPAD_SCOPE, contract.ORDINARY_SCOPE):
        raise ValueError('Unsupported product placement scope.')
    value = dict(schema=1, kind=SETTINGS_KIND, selected=options['selected'], region_nm=options['region_nm'],
                preserve_existing=True, orientation='preserve', side='preserve',
                search=dict(seed=7, steps=160, alternatives=2, seconds=2))
    if scope == contract.ORDINARY_SCOPE:
        value.update(schema=2, kind=ORDINARY_SETTINGS_KIND, scope=scope)
    return value


def settings_scope(value):
    return value.get('scope') if value.get('schema') == 2 else contract.MULTIPAD_SCOPE


def validate_settings(value):
    if type(value) is not dict or type(value.get('schema')) is not int:
        raise ValueError('Explicit selected-placement settings are required.')
    expected = settings(value.get('selected'), value.get('region_nm'), scope=settings_scope(value))
    # Canonical comparison refuses Boolean/integer substitutions and extra tools.
    if constraints.encoded(value) != constraints.encoded(expected):
        raise ValueError('Unsupported placement settings; constraints were not changed.')
    return expected


def load_settings(path):
    return validate_settings(preferences._parse(pc.read_bytes(path, 64 * 1024), 64 * 1024))


def inspect_saved(board):
    """Return bounded actual saved-file facts, never inferred electrical intent."""
    static = design_intent.inspect_project(board)
    source = Path(static['source'])
    raw = pc.read_bytes(source, contract.MAX_BYTES)
    try:
        observation = contract.inspect_board(raw, scope=contract.MULTIPAD_SCOPE)
    except ValueError:
        observation = contract.inspect_board(raw, scope=contract.ORDINARY_SCOPE)
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
    return dict(schema=1, kind='autorouter.saved-placement-inspection.v1', source=str(source),
        source_hashes=static['source_hashes'], observation=observation, components=components,
        native_validation_performed=False, execution_authorized=False, approval_granted=False,
        limitations=list(ORDINARY_LIMITS if observation['scope'] == contract.ORDINARY_SCOPE else LIMITS))


def current(inspection):
    """Compare actual current source, including local-settings metadata."""
    fresh = inspect_saved(inspection['source'])
    if constraints.encoded(fresh) != constraints.encoded(inspection):
        raise ValueError('Placement source changed; inspect the saved project again.')
    return fresh


def facts(inspection, value):
    value = validate_settings(value)
    if settings_scope(value) != inspection['observation']['scope']:
        raise ValueError('Placement settings geometry scope differs; inspect and choose settings for this project.')
    # Give the actionable protection reason before geometric search can fail.
    fixed = {row['uuid'] for row in inspection['components'] if row['fixed_reasons']}
    if set(value['selected']) & fixed:
        raise ValueError('Selected components include fixed, locked or routed-net components; deselect those components.')
    result = contract.facts_from_observation(inspection['observation'], scope=settings_scope(value),
        selected=value['selected'], region_nm=value['region_nm'])
    if set(value['selected']) & constraints.immovable(result):
        raise ValueError('Selected components include locked or routed-net components; deselect those components.')
    if len(value['selected']) < 2:
        raise ValueError('This search requires at least two movable components; nothing was moved.')
    return result


def propose(inspection, value, *, cancel_event=None):
    """Bounded deterministic search; all alternatives remain non-Native drafts."""
    if cancel_event is not None and type(cancel_event) is not threading.Event:
        raise ValueError('A threading.Event cancellation token is required.')
    value = validate_settings(value); current(inspection)
    original = facts(inspection, value)
    result = prototype.propose(original, **value['search'], cancel_event=cancel_event)
    current(inspection)
    if cancel_event is not None and cancel_event.is_set():
        result['status'] = 'cancelled'; result['alternatives'] = []
    # Quantization is part of the draft contract, not deferred to the writer.
    for row in result['alternatives']:
        row['candidate'], row['moves_nm'] = contract.quantized_translation(original, row['candidate'], observation=inspection['observation'])
    return dict(schema=1, kind='autorouter.placement-proposals.v1', inspection=copy.deepcopy(inspection),
        settings=value, search=result, native_validation_performed=False,
        execution_authorized=False, approval_granted=False)


class Review:
    """Detached pose state; edits/rejection revoke any earlier review intent."""
    def __init__(self, proposal):
        self.proposal = copy.deepcopy(proposal)
        if (proposal.get('kind') != 'autorouter.placement-proposals.v1'
                or proposal['search']['status'] != 'proposals_ready'):
            raise ValueError('Current placement alternatives are required.')
        self.inspection = self.proposal['inspection']
        self.settings = validate_settings(self.proposal['settings'])
        self.facts = facts(self.inspection, self.settings)
        rows = self.proposal['search']['alternatives']
        if type(rows) is not list or not 1 <= len(rows) <= 2:
            raise ValueError('One or two bounded alternatives are required.')
        self.alternatives = [contract.quantized_translation(self.facts, r['candidate'], observation=self.inspection['observation'])[0] for r in rows]
        self.revision = 0; self.intent = None
        self.choose(0)

    def _adopt(self, candidate):
        if self.revision >= 256:
            raise ValueError('Review edit limit reached; start a new review.')
        pose, moves = contract.quantized_translation(self.facts, candidate, observation=self.inspection['observation'])
        self.pose, self.moves = pose, moves
        self.revision += 1; self.intent = None

    def choose(self, index):
        self.intent = None
        if type(index) is not int or not 0 <= index < len(self.alternatives):
            raise ValueError('Choose an available alternative.')
        self._adopt(self.alternatives[index])

    def edit(self, component, x, y):
        self.intent = None
        if component not in self.settings['selected']:
            raise ValueError('Only selected movable components can be edited.')
        target = []
        for text in (x, y):
            if type(text) is not str or not 0 < len(text) <= 32:
                raise ValueError('Enter bounded decimal coordinates in millimetres.')
            try:
                value = Decimal(text)
                if not value.is_finite() or abs(value) > 2000:
                    raise ValueError('Coordinates must be finite and within ±2000 mm.')
                target.append(int((value * 1000000).to_integral_value()))
            except InvalidOperation as exc:
                raise ValueError('Enter decimal coordinates in millimetres.') from exc
        moves = copy.deepcopy(self.moves); moves[component] = target
        pose = contract.validate_moves(self.inspection['observation'], moves,
            scope=settings_scope(self.settings), selected=self.settings['selected'], region_nm=self.settings['region_nm'])
        self._adopt(pose)

    def decision(self, *, acknowledged, accepted):
        self.intent = None
        if type(acknowledged) is not bool or not acknowledged or type(accepted) is not bool:
            raise ValueError('Explicit review of this exact draft is required.')
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
        self.intent = value
        return copy.deepcopy(value)


def validate_draft(inspection, value):
    """Untrusted JSON may describe a draft, never grant execution/approval."""
    if type(value) is not dict or type(value.get('revision')) is not int or not 1 <= value['revision'] <= 256:
        raise ValueError('A bounded explicit draft revision is required.')
    selected = validate_settings(value.get('settings')); original = facts(inspection, selected)
    pose = contract.validate_moves(inspection['observation'], value.get('moves_nm'),
        scope=settings_scope(selected), selected=selected['selected'], region_nm=selected['region_nm'])
    expected = dict(schema=1, kind=KIND, choice='reviewed_draft', revision=value['revision'],
        source=inspection['source'], source_hashes=inspection['source_hashes'],
        inspection_sha256=constraints.digest(inspection), settings=selected,
        facts_sha256=constraints.digest(original), moves_nm=value['moves_nm'],
        pose_sha256=constraints.digest(pose), native_validation_performed=False,
        execution_authorized=False, approval_granted=False, routing_accepted=False,
        warning_acknowledged=False, human_PCB_approval=False)
    if constraints.encoded(value) != constraints.encoded(expected):
        raise ValueError('Draft authority, source, settings, geometry or review choice differs.')
    current(inspection)
    return copy.deepcopy(expected)
