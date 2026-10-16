"""Owned two-/three-pad net-tie locality fixture; Native qualification pending.

SPDX-License-Identifier: GPL-3.0-or-later
Copyright (C) 2026 KiCad-Autorouter contributors.
This grant covers this factory and all generated design files. No external
CAD, symbol library, Native API or inherited rule file is used. The schematic
property grammar reuses the owned full-schematic fixture helper.
"""
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import uuid

from experiments.native_schematic_toolchain_v1 import fixture as base

STEM = 'owned-net-tie-contact'
CASES = ('positive', 'outside_short')
NS = uuid.UUID('e576902c-5c8f-4b73-8d86-3f03a40363ba')
NETS = ('N2_A', 'N2_B', 'N3_A', 'N3_B', 'N3_C')
FPIDS = {1: 'OwnedNetTieAnchor', 2: 'OwnedNetTie2', 3: 'OwnedNetTie3'}
LIB_IDS = {count: 'OwnedNetTie:Passive' + str(count) for count in (1, 2, 3)}
# Reference, PCB x/y, pin count, ordered pin nets, schematic x/y.
COMPONENTS = (
    ('JP1', '15', '10', 2, NETS[:2], '60.96', '40.64'),
    ('JP2', '15', '22', 3, NETS[2:], '60.96', '81.28'),
    ('J1', '7', '10', 1, ('N2_A',), '116.84', '30.48'),
    ('J2', '7', '14', 1, ('N2_B',), '116.84', '50.8'),
    ('J3', '7', '22', 1, ('N3_A',), '116.84', '71.12'),
    ('J4', '15', '29', 1, ('N3_B',), '116.84', '91.44'),
    ('J5', '23', '22', 1, ('N3_C',), '116.84', '111.76'),
)
LOCAL_PAD_X = {1: ('0',), 2: ('-0.5207', '0.5207'),
               3: ('-1.0414', '0', '1.0414')}
LIB_PIN_Y = {1: ('0',), 2: ('1.27', '-1.27'),
             3: ('2.54', '0', '-2.54')}


def uid(label):
    return str(uuid.uuid5(NS, label))


def q(value):
    return json.dumps(value, ensure_ascii=True)


def number(value):
    text = format(Decimal(value), 'f')
    return text.rstrip('0').rstrip('.') if '.' in text else text


FOOTPRINT_UUIDS = {ref: uid(ref + '-footprint') for ref, *_ in COMPONENTS}
PAD_UUIDS = {ref: {str(pin): uid(ref + '-pad-' + str(pin))
                   for pin in range(1, count + 1)}
             for ref, _, _, count, *_ in COMPONENTS}
BRIDGE_UUIDS = {'JP1': (uid('JP1-bridge-1'),),
               'JP2': (uid('JP2-bridge-1'), uid('JP2-bridge-2'))}
# KiCad's net_tie_pad_groups node has no UUID: bind it to its owning footprint.
GROUP_BINDINGS = {
    'JP1': {'footprint_uuid': FOOTPRINT_UUIDS['JP1'], 'pad_groups': ('1,2',)},
    'JP2': {'footprint_uuid': FOOTPRINT_UUIDS['JP2'], 'pad_groups': ('1,2,3',)},
}
# Label, start, end, original net. Every positive track is source-protected.
TRACKS = (
    ('N2_A-anchor', ('14.4793', '10'), ('7', '10'), 'N2_A'),
    ('N2_B-outbound', ('15.5207', '10'), ('23', '14'), 'N2_B'),
    ('N2_B-final', ('23', '14'), ('7', '14'), 'N2_B'),
    ('N3_A-anchor', ('13.9586', '22'), ('7', '22'), 'N3_A'),
    ('N3_B-anchor', ('15', '22'), ('15', '29'), 'N3_B'),
    ('N3_C-anchor', ('16.0414', '22'), ('23', '22'), 'N3_C'),
)
TRACK_UUIDS = {label: uid('track-' + label) for label, *_ in TRACKS}
PROTECTED_TRACK_UUIDS = tuple(TRACK_UUIDS.values())
OUTSIDE_SHORT_UUID = uid('outside-short-track')
NEGATIVE_ALLOWED_ITEM_UUID_PAIRS = (
    (OUTSIDE_SHORT_UUID, PAD_UUIDS['J2']['1']),
    (OUTSIDE_SHORT_UUID, TRACK_UUIDS['N2_B-final']),
)


def source_factory_hashes():
    return {
        'experiments/net_tie_contact_v1/fixture.py':
            hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'experiments/native_schematic_toolchain_v1/fixture.py':
            hashlib.sha256(Path(base.__file__).read_bytes()).hexdigest(),
    }


def _pcb_property(ref, name, value, layer):
    return ('(property ' + q(name) + ' ' + q(value) +
            ' (at 0 0 0) (layer ' + q(layer) + ') (hide yes) (uuid ' +
            q(uid(ref + '-property-' + name)) +
            ') (effects (font (size 0.7 0.7) (thickness 0.1))))')


def _bridge(ref, index, center_x):
    xmin = number(Decimal(center_x) - Decimal('0.25'))
    xmax = number(Decimal(center_x) + Decimal('0.25'))
    return ('(fp_poly (pts (xy ' + xmin + ' -0.15) (xy ' + xmax +
            ' -0.15) (xy ' + xmax + ' 0.15) (xy ' + xmin + ' 0.15))'
            ' (stroke (width 0) (type solid)) (fill yes) (layer "F.Cu")'
            ' (uuid ' + q(BRIDGE_UUIDS[ref][index]) + '))')


def _footprint(component):
    ref, x, y, count, nets, _, _ = component
    rows = ['(footprint ' + q(FPIDS[count]) + ' (layer "F.Cu")'
            ' (uuid ' + q(FOOTPRINT_UUIDS[ref]) + ') (at ' + x + ' ' + y + ')']
    for name, value, layer in (('Reference', ref, 'F.SilkS'),
                               ('Value', FPIDS[count], 'F.Fab'),
                               ('Datasheet', '', 'F.Fab'),
                               ('Description', '', 'F.Fab')):
        rows.append(_pcb_property(ref, name, value, layer))
    rows.append('(path ' + q('/' + uid(ref + '-symbol')) + ')')
    rows.append('(attr through_hole)' if count == 1 else '(attr smd)')
    if count > 1:
        rows.append('(net_tie_pad_groups ' + q(','.join(str(i) for i in range(1, count + 1))) + ')')
        for index, center in enumerate(('0',) if count == 2 else ('-0.5207', '0.5207')):
            rows.append(_bridge(ref, index, center))
    half_x = '1.25' if count == 1 else '1.1' if count == 2 else '1.65'
    half_y = '1.25' if count == 1 else '1'
    rows.append('(fp_rect (start -' + half_x + ' -' + half_y + ')'
                ' (end ' + half_x + ' ' + half_y + ')'
                ' (stroke (width 0.05) (type default)) (fill none)'
                ' (layer "F.CrtYd") (uuid ' + q(uid(ref + '-courtyard')) + '))')
    for pin, (local_x, net) in enumerate(zip(LOCAL_PAD_X[count], nets), 1):
        number_text = str(pin)
        shape = 'thru_hole circle' if count == 1 else 'smd rect'
        geometry = ('(size 2 2) (drill 0.8) (layers "*.Cu" "*.Mask")'
                    if count == 1 else '(size 0.6604 1.27) (layers "F.Cu" "F.Mask")')
        rows.append('(pad ' + q(number_text) + ' ' + shape + ' (at ' + local_x + ' 0) '
                    + geometry + ' (net ' + q(net) + ') (pinfunction ' + q(number_text) + ')'
                    ' (pintype "passive") (uuid ' + q(PAD_UUIDS[ref][number_text]) + '))')
    rows.append('(embedded_fonts no))')
    return '\n'.join(rows)


def _segment(start, end, net, ident):
    return ('(segment (start ' + ' '.join(start) + ') (end ' + ' '.join(end) + ')'
            ' (width 0.3) (layer "F.Cu") (net ' + q(net) + ')'
            ' (locked yes) (uuid ' + q(ident) + '))')


def positive_board():
    rows = ['''(kicad_pcb (version 20260206) (generator "pcbnew")
  (generator_version "10.0") (general (thickness 1.6)) (paper "A4")
  (layers (0 "F.Cu" signal) (2 "B.Cu" signal)
    (13 "F.Paste" user) (15 "B.Paste" user)
    (5 "F.SilkS" user) (7 "B.SilkS" user)
    (1 "F.Mask" user) (3 "B.Mask" user) (25 "Edge.Cuts" user)
    (31 "F.CrtYd" user) (29 "B.CrtYd" user)
    (35 "F.Fab" user) (33 "B.Fab" user))
  (setup (pad_to_mask_clearance 0) (allow_soldermask_bridges_in_footprints no))''']
    rows.extend(_footprint(component) for component in COMPONENTS)
    rows.extend(_segment(start, end, net, TRACK_UUIDS[label])
                for label, start, end, net in TRACKS)
    rows.append('(gr_rect (start 3 3) (end 27 32)'
                ' (stroke (width 0.05) (type default)) (fill none)'
                ' (layer "Edge.Cuts") (uuid ' + q(uid('edge')) + '))')
    rows.append('(embedded_fonts no))')
    return ('\n'.join(rows) + '\n').encode('ascii')


def board(case):
    if case not in CASES:
        raise ValueError('unknown owned net-tie case')
    positive = positive_board()
    if case == 'positive':
        return positive
    addition = ('\n' + _segment(('7', '10'), ('7', '14'), 'N2_A',
                               OUTSIDE_SHORT_UUID) + '\n').encode('ascii')
    if not positive.endswith(b')\n') or OUTSIDE_SHORT_UUID.encode() in positive:
        raise ValueError('fresh outside-short identity/root required')
    negative = positive[:-2] + addition + b')\n'
    if negative.count(addition) != 1 or negative.replace(addition, b'', 1) != positive:
        raise ValueError('negative must add exactly the one outside segment')
    return negative


def _library_symbol(count):
    name = 'Passive' + str(count)
    rows = ['(symbol ' + q(LIB_IDS[count]) +
            ' (pin_names (offset 0) hide) (exclude_from_sim no) (in_bom yes) (on_board yes)']
    for key, value in (('Reference', 'J' if count == 1 else 'JP'),
                       ('Value', FPIDS[count]), ('Footprint', FPIDS[count]),
                       ('Datasheet', ''), ('Description', '')):
        rows.append(base.sch_property(key, value))
    rows.append('(symbol ' + q(name + '_0_1') +
                ' (rectangle (start -1.27 3.81) (end 1.27 -3.81)'
                ' (stroke (width 0.254) (type default)) (fill (type background))))')
    rows.append('(symbol ' + q(name + '_1_1'))
    for pin, local_y in enumerate(LIB_PIN_Y[count], 1):
        text = q(str(pin))
        rows.append('(pin passive line (at -2.54 ' + local_y + ' 0) (length 1.27)'
                    ' (name ' + text + ' (effects (font (size 1.27 1.27))))'
                    ' (number ' + text + ' (effects (font (size 1.27 1.27)))))')
    rows.append('))')
    return '\n'.join(rows)


def schematic():
    rows = ['(kicad_sch (version 20250114) (generator "eeschema")'
            ' (generator_version "10.0") (uuid ' + q(uid('schematic-root')) + ')'
            ' (paper "A4") (lib_symbols']
    rows.extend(_library_symbol(count) for count in (1, 2, 3))
    rows.append(')')
    for ref, _, _, count, nets, x, y in COMPONENTS:
        # Library y points upward; placed schematic page y points downward.
        for pin, (local_y, net) in enumerate(zip(LIB_PIN_Y[count], nets), 1):
            pin_x = number(Decimal(x) - Decimal('2.54'))
            pin_y = number(Decimal(y) - Decimal(local_y))
            rows.append('(global_label ' + q(net) + ' (shape input)'
                        ' (at ' + pin_x + ' ' + pin_y + ' 0)'
                        ' (effects (font (size 1.27 1.27)) (justify left))'
                        ' (uuid ' + q(uid(ref + '-label-' + str(pin))) + '))')
        rows.append('(symbol (lib_id ' + q(LIB_IDS[count]) + ')'
                    ' (at ' + x + ' ' + y + ' 0) (unit 1) (exclude_from_sim no)'
                    ' (in_bom yes) (on_board yes) (dnp no) (uuid ' + q(uid(ref + '-symbol')) + ')')
        for key, value in (('Reference', ref), ('Value', FPIDS[count]),
                           ('Footprint', FPIDS[count]), ('Datasheet', ''), ('Description', '')):
            rows.append(base.sch_property(key, value, x, y,
                                          hidden=key not in ('Reference', 'Value')))
        for pin in range(1, count + 1):
            rows.append('(pin ' + q(str(pin)) + ' (uuid ' + q(uid(ref + '-schematic-pin-' + str(pin))) + '))')
        rows.append('(instances (project ' + q(STEM) + ' (path ' + q('/' + uid('schematic-root')) +
                    ' (reference ' + q(ref) + ') (unit 1)))))')
    rows.append('(embedded_fonts no))')
    return ('\n'.join(rows) + '\n').encode('ascii')


def project():
    # This is a newly authored complete rule object; no inherited DRU is removed.
    errors = ('hole_clearance', 'hole_to_hole', 'hole_near_hole', 'starved_thermal',
              'zones_intersect', 'padstack', 'items_not_allowed',
              'through_hole_pad_without_hole', 'unconnected_items', 'shorting_items',
              'clearance', 'track_width', 'via_diameter', 'annular_width',
              'drill_out_of_range', 'copper_edge_clearance', 'invalid_outline',
              'tracks_crossing', 'track_on_post_machined_layer', 'net_conflict',
              'missing_footprint', 'extra_footprint', 'footprint_symbol_mismatch')
    severities = {key: 'error' for key in errors}
    severities.update(footprint_symbol_field_mismatch='warning',
                      missing_courtyard='warning', lib_footprint_issues='warning',
                      lib_footprint_mismatch='warning', footprint_filters_mismatch='warning',
                      footprint_type_mismatch='warning')
    value = {
        'meta': {'filename': STEM + '.kicad_pro', 'version': 1},
        'board': {'design_settings': {'drc_exclusions': [], 'rule_severities': severities,
                  'rules': {'min_clearance': 0.2, 'min_track_width': 0.25,
                            'min_via_diameter': 0.6, 'min_through_hole_diameter': 0.3,
                            'min_via_annular_width': 0.1, 'min_hole_clearance': 0.25,
                            'min_hole_to_hole': 0.25, 'min_copper_edge_clearance': 0.3,
                            'min_connection': 0.25, 'min_resolved_spokes': 2,
                            'allow_blind_buried_vias': False, 'allow_microvias': False}}},
        'net_settings': {'classes': [{'name': 'Default', 'priority': 2147483647,
                                     'clearance': 0.2, 'track_width': 0.3,
                                     'via_diameter': 0.8, 'via_drill': 0.4}],
                         'netclass_patterns': [], 'netclass_assignments': None},
        'schematic': {'drawing': {}, 'legacy_lib_dir': '', 'legacy_lib_list': []},
        'text_variables': {},
    }
    return (json.dumps(value, sort_keys=True, indent=2) + '\n').encode('ascii')


def files(case):
    """Four-file packet; outside_short adds only one prospective PCB segment."""
    if case not in CASES:
        raise ValueError('unknown owned net-tie case')
    return {
        STEM + '.kicad_pcb': board(case),
        STEM + '.kicad_sch': schematic(),
        STEM + '.kicad_pro': project(),
        STEM + '.kicad_prl': (json.dumps({'meta': {'filename': STEM + '.kicad_prl', 'version': 5},
                                        'board': {'active_layer': 0, 'hidden_nets': [],
                                                  'hidden_netclasses': []}},
                                       sort_keys=True, indent=2) + '\n').encode('ascii'),
    }
