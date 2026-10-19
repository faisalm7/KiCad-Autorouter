"""Prospective project-owned full-SCH transport fixture; not Native evidence.

SPDX-License-Identifier: GPL-3.0-or-later
Copyright (C) 2026 KiCad-Autorouter contributors.
The grant covers this factory and all generated design files. See COPYING.
Adapted generator grammar from native_schematic_toolchain_v1/fixture.py;
new source identity, nets, placements, geometry, rules and UUID namespace.
"""
from pathlib import Path
import argparse
import json
import uuid

SOURCE_ID = 'owned1007-protected-transport-v1'
STEM = 'owned1007-transport'
NS = uuid.UUID('d9e13c70-52e6-4d5f-9a5d-3e890449ef54')
FOOTPRINT = 'owned1007_transport_terminal'
LIB_ID = 'OwnedTransport:Terminal'
DESCRIPTION = 'Project-owned transport diagnostic one-pin terminal'
FIELD = 'OwnedTransportIdentity'
# reference, board x/y, net, flat schematic x/y, left pin endpoint x.
TERMINALS = (('J1', '12', '10', 'ROUTE', '40.64', '40.64', '38.1'),
             ('J2', '26', '10', 'ROUTE', '81.28', '40.64', '78.74'),
             ('J3', '12', '16', 'KEEP', '40.64', '71.12', '38.1'),
             ('J4', '26', '16', 'KEEP', '81.28', '71.12', '78.74'),
             ('J5', '12', '24', 'GND', '40.64', '101.6', '38.1'),
             ('J6', '26', '24', 'GND', '81.28', '101.6', '78.74'))


def uid(label):
    return str(uuid.uuid5(NS, label))


def q(text):
    return json.dumps(text, ensure_ascii=True)


def identity(ref):
    return SOURCE_ID + ':' + ref


def pcb_property(ref, name, value, layer):
    return ('(property ' + q(name) + ' ' + q(value) +
            ' (at 0 0 0) (layer ' + q(layer) + ') (hide yes) (uuid ' +
            q(uid(ref + '-property-' + name)) +
            ') (effects (font (size 1 1) (thickness 0.15))))')


def board():
    rows = ['''(kicad_pcb (version 20260206) (generator "pcbnew")
  (generator_version "10.0") (general (thickness 1.6)) (paper "A4")
  (layers (0 "F.Cu" signal) (2 "B.Cu" signal)
    (13 "F.Paste" user) (15 "B.Paste" user)
    (5 "F.SilkS" user) (7 "B.SilkS" user)
    (1 "F.Mask" user) (3 "B.Mask" user) (25 "Edge.Cuts" user)
    (31 "F.CrtYd" user) (29 "B.CrtYd" user)
    (35 "F.Fab" user) (33 "B.Fab" user))
  (setup (pad_to_mask_clearance 0) (allow_soldermask_bridges_in_footprints no))''']
    for ref, x, y, net, _, _, _ in TERMINALS:
        rows.append('(footprint ' + q(FOOTPRINT) + ' (layer "F.Cu") (uuid ' +
                    q(uid(ref + '-footprint')) + ') (at ' + x + ' ' + y + ')')
        for name, value, layer in (('Reference', ref, 'F.SilkS'),
                                   ('Value', FOOTPRINT, 'F.Fab'),
                                   ('Datasheet', '~', 'F.Fab'),
                                   ('Description', DESCRIPTION, 'F.Fab'),
                                   (FIELD, identity(ref), 'F.Fab')):
            rows.append(pcb_property(ref, name, value, layer))
        rows.append('(path ' + q('/' + uid(ref + '-symbol')) + ') (attr through_hole)')
        rows.append('(fp_rect (start -1.25 -1.25) (end 1.25 1.25) '
                    '(stroke (width 0.05) (type default)) (fill none) '
                    '(layer "F.CrtYd") (uuid ' + q(uid(ref + '-courtyard')) + '))')
        rows.append('(pad "1" thru_hole circle (at 0 0) (size 2 2) (drill 0.8) '
                    '(layers "*.Cu" "*.Mask") (net ' + q(net) +
                    ') (pinfunction "1") (pintype "passive") (uuid ' +
                    q(uid(ref + '-pad')) + ')) (embedded_fonts no))')
    rows.append('(gr_rect (start 6 6) (end 32 30) '
                '(stroke (width 0.05) (type default)) (fill none) '
                '(layer "Edge.Cuts") (uuid ' + q(uid('edge')) + '))')
    # Authored locked copper is on KEEP. ROUTE has no copper at creation.
    rows.append('(segment (start 12 16) (end 26 16) (width 0.3) '
                '(layer "F.Cu") (net "KEEP") (locked yes) (uuid ' +
                q(uid('protected-keep-track')) + '))')
    # Authored unfilled ordinary zone; only real saved refill proves J5/J6.
    rows.append('(zone (net "GND") (layer "B.Cu") (uuid ' + q(uid('gnd-zone')) +
                ') (hatch edge 0.5) (connect_pads yes (clearance 0.3)) '
                '(min_thickness 0.25) (filled_areas_thickness no) '
                '(fill yes (thermal_gap 0.3) (thermal_bridge_width 0.3)) '
                '(polygon (pts (xy 7 21) (xy 31 21) (xy 31 29) (xy 7 29))))')
    rows.append('(embedded_fonts no))')
    return ('\n'.join(rows) + '\n').encode()


def sch_property(name, value, x='0', y='0', *, hidden=True):
    return ('(property ' + q(name) + ' ' + q(value) + ' (at ' + x + ' ' + y +
            ' 0) (effects (font (size 1.27 1.27))' +
            (' (hide yes)' if hidden else '') + '))')


def schematic():
    rows = ['(kicad_sch (version 20250114) (generator "eeschema") '
            '(generator_version "10.0") (uuid ' + q(uid('schematic-root')) +
            ') (paper "A4") (lib_symbols (symbol ' + q(LIB_ID) +
            ' (pin_names (offset 0) hide) (exclude_from_sim no) '
            '(in_bom yes) (on_board yes)']
    for name, value in (('Reference', 'J'), ('Value', FOOTPRINT),
                        ('Footprint', FOOTPRINT), ('Datasheet', ''),
                        ('Description', DESCRIPTION), (FIELD, '')):
        rows.append(sch_property(name, value))
    rows.append('''(symbol "Terminal_0_1"
      (rectangle (start -1.27 1.27) (end 1.27 -1.27)
        (stroke (width 0.254) (type default)) (fill (type background))))
      (symbol "Terminal_1_1"
        (pin passive line (at -2.54 0 0) (length 1.27)
          (name "1" (effects (font (size 1.27 1.27))))
          (number "1" (effects (font (size 1.27 1.27))))))))''')
    for ref, _, _, net, x, y, pin_x in TERMINALS:
        rows.append('(global_label ' + q(net) + ' (shape input) (at ' + pin_x +
                    ' ' + y + ' 0) (effects (font (size 1.27 1.27)) '
                    '(justify left)) (uuid ' + q(uid(ref + '-label')) + '))')
        rows.append('(symbol (lib_id ' + q(LIB_ID) + ') (at ' + x + ' ' + y +
                    ' 0) (unit 1) (exclude_from_sim no) (in_bom yes) '
                    '(on_board yes) (dnp no) (uuid ' + q(uid(ref + '-symbol')) + ')')
        for name, value in (('Reference', ref), ('Value', FOOTPRINT),
                            ('Footprint', FOOTPRINT), ('Datasheet', ''),
                            ('Description', DESCRIPTION), (FIELD, identity(ref))):
            rows.append(sch_property(name, value, x, y,
                                     hidden=name not in ('Reference', 'Value')))
        rows.append('(pin "1" (uuid ' + q(uid(ref + '-schematic-pin')) + ')) '
                    '(instances (project ' + q(STEM) + ' (path ' +
                    q('/' + uid('schematic-root')) + ' (reference ' + q(ref) +
                    ') (unit 1)))))')
    rows.append('(embedded_fonts no))')
    return ('\n'.join(rows) + '\n').encode()


def project():
    # Rules are authored here at creation; no inherited DRU is removed.
    errors = ('hole_clearance', 'hole_to_hole', 'hole_near_hole', 'starved_thermal',
              'zones_intersect', 'padstack', 'items_not_allowed',
              'through_hole_pad_without_hole', 'unconnected_items', 'shorting_items',
              'clearance', 'track_width', 'via_diameter', 'annular_width',
              'drill_out_of_range', 'copper_edge_clearance', 'invalid_outline',
              'tracks_crossing', 'track_on_post_machined_layer', 'net_conflict',
              'missing_footprint', 'extra_footprint', 'footprint_symbol_mismatch')
    severities = {name: 'error' for name in errors}
    severities.update(footprint_symbol_field_mismatch='warning',
                      missing_courtyard='warning', lib_footprint_issues='warning',
                      footprint_filters_mismatch='warning',
                      footprint_type_mismatch='warning')
    value = {'meta': {'filename': STEM + '.kicad_pro', 'version': 1},
             'board': {'design_settings': {'drc_exclusions': [],
                       'rule_severities': severities,
                       'rules': {'min_clearance': 0.2, 'min_track_width': 0.25,
                                 'min_via_diameter': 0.6,
                                 'min_through_hole_diameter': 0.3,
                                 'min_via_annular_width': 0.1,
                                 'min_hole_clearance': 0.25,
                                 'min_hole_to_hole': 0.25,
                                 'min_copper_edge_clearance': 0.3,
                                 'min_connection': 0.25,
                                 'min_resolved_spokes': 2,
                                 'allow_blind_buried_vias': False,
                                 'allow_microvias': False}}},
             'net_settings': {'classes': [{'name': 'Default', 'clearance': 0.2,
                               'track_width': 0.3, 'via_diameter': 0.8,
                               'via_drill': 0.4}],
                              'netclass_patterns': [], 'netclass_assignments': None},
             'schematic': {'drawing': {}, 'legacy_lib_dir': '', 'legacy_lib_list': []}}
    return (json.dumps(value, indent=2, sort_keys=True) + '\n').encode()


def files():
    """The entire four-file source packet. DRU is absent from first creation."""
    return {STEM + '.kicad_pcb': board(), STEM + '.kicad_sch': schematic(),
            STEM + '.kicad_pro': project(),
            STEM + '.kicad_prl': (json.dumps({'meta': {'filename': STEM +
                '.kicad_prl', 'version': 5}, 'board': {'active_layer': 0,
                'hidden_nets': [], 'hidden_netclasses': []}},
                indent=2, sort_keys=True) + '\n').encode()}


def write_project(output):
    """Create one exact fresh packet without loading KiCad or changing source."""
    output = Path(output)
    if (not output.is_absolute() or output.exists() or output.is_symlink()
            or output.parent.resolve() != output.parent
            or not output.parent.is_dir() or '..' in output.parts):
        raise ValueError('fresh canonical absolute output with existing parent required')
    material = files()
    output.mkdir()
    for name, raw in material.items():
        with (output / name).open('xb') as stream:
            stream.write(raw)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    write_project(args.output)
