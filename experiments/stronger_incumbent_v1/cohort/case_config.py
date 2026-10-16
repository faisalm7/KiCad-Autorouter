"""Prospective case selectors for the ONE existing matched driver; not a launcher.
SPDX-License-Identifier: GPL-3.0-or-later
The unchanged case-table is static evidence, not resolved source qualification.
"""
from decimal import Decimal
from pathlib import Path
from autorouter import pipeline as p, strategy as s, engine_angle, schematic_field_evidence as fields
from scripts import experiment_quality as q

PROJECTS = ('sonde', 'nus-usb-led', 'push-button-led', 'ds18b20', 'arcdice')
METHODS = ('B2_stronger', 'C_stronger')


def population():
    return [(project, name) for project in PROJECTS for name in METHODS]


def execution_order(cases):
    # Source gates do not silently delete a role; prepare must resolve them all.
    return [(project, name) for project in PROJECTS
            if cases[project]['scope']['private_policy'] is not None for name in METHODS]


def arm_spec(case, name):
    if name not in METHODS or case['scope']['private_policy'] is None:
        raise p.Rejected('declared supported case and method required')
    arm = dict(id=name, adapter='both', operation='route', engine_profile='tuned-free-angle')
    if name == 'C_stronger':
        arm.update(operation='prune', engine_profile='tuned', proposal_policy='chains',
                   incumbent_policy=case['scope']['private_policy'])
    return arm


def source(case):
    # Registry already uses the correct distinct capture machinery for all five.
    # Never call capture_native_source on a registry id it does not implement.
    board, family = q.selected_source(case['selected_source_id'])
    files = p.tree_hash(board.parent)
    if (str(board) != case['source'] or family != case['family']
            or files != case['source_sha256']):
        raise p.Rejected('complete pinned original/notice packet differs')
    return board, family, dict(packet=str(board.parent), files=files)


def eligibility(board, case):
    policy = p.netclass_policy(board)
    width = p.minimum_width_guard(board, 'both')
    expected = case['scope']['private_policy']
    if expected is None:
        if policy is None:
            raise p.Rejected('frozen unsupported named-class disposition changed')
        return dict(execution_eligible=False, derived_strict_class_targets=True,
                    netclass_policy=policy, minimum_width_guard=width,
                    refusal='unsupported: named-class policy remains outside this private cohort')
    strict = policy is not None or width is not None
    if policy is not None or expected not in s.STRONG_INCUMBENT_POLICIES:
        raise p.Rejected('single Default private policy required')
    v2 = expected == s.STRONG_WIDTH_INCUMBENT_POLICY
    if (v2 is not (width is not None) or
            (v2 and Decimal(str(width['min_track_width_mm'])) !=
             Decimal(str(case['Default']['min_track_width_mm'])))):
        raise p.Rejected('literal original minimum/private policy differs')
    return dict(execution_eligible=True, derived_strict_class_targets=strict,
                netclass_policy=policy, minimum_width_guard=width, refusal=None)


def invoke(board, folder, case, name):
    # Exact current method allowances/reserve and current acceptance are inherited.
    if name == 'C_stronger':
        return s.prune(board, folder, 120, proposal_policy='chains',
                       incumbent_scoring='via_default',
                       _incumbent_policy=case['scope']['private_policy'])
    if name != 'B2_stronger':
        raise p.Rejected('declared method required')
    extra = {}
    if case['scope']['engine_global_width_policy'] is not None:
        extra['_engine_global_width_policy'] = case['scope']['engine_global_width_policy']
    return p.route(board, folder, 120, False, 'both', 'tuned-free-angle',
                   scoring_variant='via_default', _fanout_enabled=False,
                   _optimizer_enabled=False, _engine_clearance_margin_nm=20000, **extra)


def check_planning(folder, data, case):
    p.check_engine_profile_record(data, folder)
    engine_angle.check_scope(data, 'native')
    proof = engine_angle.check(folder, data)
    changes = proof.get('planning_clearance', {}).get('changes', [])
    expected_width_policy = case['scope']['engine_global_width_policy']
    if (data.get('engine_profile') != 'tuned-free-angle'
            or data.get('scoring_variant') != 'via_default'
            or data.get('engine_fanout_override') is not False
            or data.get('engine_optimizer_override') is not False
            or type(data.get('engine_planning_clearance_margin_nm')) is not int
            or data['engine_planning_clearance_margin_nm'] != 20000
            or p.check_engine_global_width_policy(data) != expected_width_policy
            or len(changes) != 2
            or any(Decimal(row['before']) != Decimal(case['Default']['planning_clearance_before_um'])
                   or Decimal(row['after']) != Decimal(case['Default']['planning_clearance_after_um'])
                   for row in changes)):
        raise p.Rejected('case-specific exact strong stock planning differs')
    return proof


def check_field_census(native, case):
    # obs.candidate/check_result still perform complete shared proof replay first.
    has_fields = fields.has_fields(native['findings'])
    contract = case['conditional_effective_fields']
    if not has_fields:
        if native.get('field_parity'):
            raise p.Rejected('stray field bridge without actual field finding')
        return
    expected = contract['expected_census']
    if contract['bridge_absence_expected'] or expected is None:
        raise p.Rejected('unexpected field bridge; resolve before freezing cohort')
    actual = native.get('field_parity', {}).get('qualification', {})
    if (actual.get('qualified') is not True
            or actual.get('component_count') != expected['components']
            or actual.get('compared_field_count') != expected['compared_fields']):
        raise p.Rejected('case-specific complete effective field census differs')


def stage_id(project, name):
    if project not in PROJECTS or name not in METHODS:
        raise p.Rejected('declared stage identity required')
    return project + '--' + name
