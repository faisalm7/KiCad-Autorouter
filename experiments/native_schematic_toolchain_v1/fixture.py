"""Prospective owned full-schematic field controls; not Native qualification.

GPL-3.0-or-later. Authoring only: no pcbnew/project imports or external libraries.
Lead must integrate/checkpoint and run the actual pinned experimental toolchain.
"""
from pathlib import Path
import argparse
import json
import uuid

STEM = 'owned1007-fields'
CASES = ('positive', 'hidden_later_custom_field')
NS = uuid.UUID('3663569e-02ea-41ba-81f6-45220a40b488')
FIELD = 'AutorouterDiagnosticLater'
MATCH = 'OWNED_FIELD_MATCH_J1_001'
MISMATCH = 'OWNED_FIELD_MISMATCH_J1_001'
DESCRIPTION = 'Project-owned single-pin terminal'
FOOTPRINT = 'owned1007_terminal'
# ref, PCB x/y, global net, schematic x/y, left-facing pin endpoint x.
TERMINALS = (('J1', '10', '10', 'SIGNAL', '40.64', '40.64', '38.1'),
             ('J2', '20', '10', 'SIGNAL', '81.28', '40.64', '78.74'),
             ('J3', '10', '16', 'GND', '40.64', '71.12', '38.1'),
             ('J4', '20', '16', 'GND', '81.28', '71.12', '78.74'))


def uid(label):
    return str(uuid.uuid5(NS, label))


def q(text):
    return json.dumps(text, ensure_ascii=True)


def matching_field(ref):
    return MATCH if ref == 'J1' else 'OWNED_FIELD_MATCH_' + ref + '_001'


def pcb_property(ref, name, value, layer):
    return ('(property ' + q(name) + ' ' + q(value) +
            ' (at 0 0 0) (layer ' + q(layer) + ') (hide yes) (uuid ' +
            q(uid(ref + '-property-' + name)) +
            ') (effects (font (size 1 1) (thickness 0.15))))')


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
    for ref, x, y, net, _, _, _ in TERMINALS:
        rows.append('(footprint ' + q(FOOTPRINT) + ' (layer "F.Cu") (uuid ' +
                    q(uid(ref + '-footprint')) + ') (at ' + x + ' ' + y + ')')
        # Datasheet deliberately precedes the hidden custom field in every FP.
        for name, value, layer in (('Reference', ref, 'F.SilkS'),
                                   ('Value', FOOTPRINT, 'F.Fab'),
                                   ('Datasheet', '~', 'F.Fab'),
                                   ('Description', DESCRIPTION, 'F.Fab'),
                                   (FIELD, matching_field(ref), 'F.Fab')):
            rows.append(pcb_property(ref, name, value, layer))
        # Flat symbol-only path follows the already observed PIC grammar.
        # Native1007 must establish this newly authored schematic correspondence.
        rows.append('(path ' + q('/' + uid(ref + '-symbol')) + ')')
        rows.append('(attr through_hole)')
        rows.append('(fp_rect (start -1.25 -1.25) (end 1.25 1.25) '
                    '(stroke (width 0.05) (type default)) (fill none) '
                    '(layer "F.CrtYd") (uuid ' + q(uid(ref + '-courtyard')) + '))')
        rows.append('(pad "1" thru_hole circle (at 0 0) (size 2 2) (drill 0.8) '
                    '(layers "*.Cu" "*.Mask") (net ' + q(net) +
                    ') (pinfunction "1") (pintype "passive") (uuid ' +
                    q(uid(ref + '-pad')) + ')) (embedded_fonts no))')
    rows.append('(gr_rect (start 5 5) (end 25 21) '
                '(stroke (width 0.05) (type default)) (fill none) '
                '(layer "Edge.Cuts") (uuid ' + q(uid('edge')) + '))')
    rows.append('(segment (start 10 10) (end 20 10) (width 0.3) '
                '(layer "F.Cu") (net "SIGNAL") (locked yes) (uuid ' +
                q(uid('signal-track')) + '))')
    # Same owned geometry as kicad8_native_compat_v1, in modern net-name grammar.
    # Source has an authored unfilled zone; real saved refill must connect J3/J4.
    rows.append('(zone (net "GND") (layer "B.Cu") (uuid ' + q(uid('gnd-zone')) +
                ') (hatch edge 0.5) (connect_pads yes (clearance 0.3)) '
                '(min_thickness 0.25) (filled_areas_thickness no) '
                '(fill yes (thermal_gap 0.3) (thermal_bridge_width 0.3)) '
                '(polygon (pts (xy 6 13) (xy 24 13) (xy 24 20) (xy 6 20))))')
    rows.append('(embedded_fonts no))')
    return ('\n'.join(rows) + '\n').encode()


def board(case):
    if case not in CASES:
        raise ValueError('unknown owned field-control case')
    positive = positive_board()
    if positive.count(MATCH.encode()) != 1:
        raise ValueError('J1 field replacement must be unique')
    if case == 'positive':
        return positive
    negative = positive.replace(MATCH.encode(), MISMATCH.encode(), 1)
    if negative.replace(MISMATCH.encode(), MATCH.encode(), 1) != positive:
        raise ValueError('negative must change only J1 hidden custom field value')
    return negative


def sch_property(name, value, x='0', y='0', *, hidden=True):
    return ('(property ' + q(name) + ' ' + q(value) + ' (at ' + x + ' ' + y +
            ' 0) (effects (font (size 1.27 1.27))' +
            (' (hide yes)' if hidden else '') + '))')


def schematic():
    # Embedded original passive one-pin symbol: no installed symbol library.
    rows = ['(kicad_sch (version 20250114) (generator "eeschema") '
            '(generator_version "10.0") (uuid ' + q(uid('schematic-root')) +
            ') (paper "A4") (lib_symbols (symbol "Owned1007:Terminal" '
            '(pin_names (offset 0) hide) (exclude_from_sim no) '
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
        rows.append('(symbol (lib_id "Owned1007:Terminal") (at ' + x + ' ' + y +
                    ' 0) (unit 1) (exclude_from_sim no) (in_bom yes) '
                    '(on_board yes) (dnp no) (uuid ' + q(uid(ref + '-symbol')) + ')')
        for name, value in (('Reference', ref), ('Value', FOOTPRINT),
                            ('Footprint', FOOTPRINT), ('Datasheet', ''),
                            ('Description', DESCRIPTION),
                            (FIELD, matching_field(ref))):
            rows.append(sch_property(name, value, x, y,
                                     hidden=name not in ('Reference', 'Value')))
        rows.append('(pin "1" (uuid ' + q(uid(ref + '-schematic-pin')) + ')) '
                    '(instances (project ' + q(STEM) + ' (path ' +
                    q('/' + uid('schematic-root')) + ' (reference ' + q(ref) +
                    ') (unit 1)))))')
    rows.append('(embedded_fonts no))')
    return ('\n'.join(rows) + '\n').encode()


def project():
    # No inherited preset, DRC exclusions, ignored severities or global libs.
    errors = ('clearance', 'shorting_items', 'unconnected_items', 'track_width',
              'via_diameter', 'annular_width', 'drill_out_of_range',
              'hole_clearance', 'hole_near_hole', 'copper_edge_clearance',
              'items_not_allowed', 'net_conflict', 'missing_footprint',
              'extra_footprint', 'footprint_symbol_mismatch')
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
                                 'min_connection': 0,
                                 'min_resolved_spokes': 2,
                                 'allow_blind_buried_vias': False,
                                 'allow_microvias': False}}},
             'net_settings': {'classes': [{'name': 'Default', 'clearance': 0.2,
                               'track_width': 0.3, 'via_diameter': 0.8,
                               'via_drill': 0.4}],
                              'netclass_patterns': [],
                              'netclass_assignments': None},
             'schematic': {'drawing': {}, 'legacy_lib_dir': '',
                           'legacy_lib_list': []}}
    return (json.dumps(value, indent=2, sort_keys=True) + '\n').encode()


def files(case):
    # Both cases share byte-identical SCH/PRO/DRU/PRL; only one PCB value differs.
    return {STEM + '.kicad_pcb': board(case), STEM + '.kicad_sch': schematic(),
            STEM + '.kicad_pro': project(),
            STEM + '.kicad_dru': b'''(version 1)
(rule "Owned fixed signal minimum"
  (condition "A.NetName == 'SIGNAL'")
  (constraint track_width (min 0.25mm)))
''',
            STEM + '.kicad_prl': (json.dumps({'meta': {'filename': STEM +
                '.kicad_prl', 'version': 5}, 'board': {'active_layer': 0,
                'hidden_nets': [], 'hidden_netclasses': []}},
                indent=2, sort_keys=True) + '\n').encode()}


def fresh_output(output):
    output = Path(output)
    if (not output.is_absolute() or output.exists() or output.is_symlink()
            or output.parent.resolve() != output.parent
            or not output.parent.is_dir() or '..' in output.parts):
        raise ValueError('fresh canonical absolute output with existing parent required')
    return output


def write_project(output, case):
    """Write one exact five-file case; never overwrite an existing directory."""
    material = files(case)  # Reject an unknown case before creating output.
    output = fresh_output(output)
    output.mkdir()
    for name, raw in material.items():
        with (output / name).open('xb') as stream:
            stream.write(raw)


def write(output):
    output = fresh_output(output)
    output.mkdir()
    for case in CASES:
        write_project(output / case, case)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    write(args.output)
