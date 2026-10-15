"""Prospective portable source controls; no Native or engine correctness claim.

SPDX-License-Identifier: GPL-3.0-or-later
Intended integration: tests/test_native_schematic_transport_fixture.py.
"""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from autorouter import pipeline as p, sexpr as sx
from experiments.native_schematic_transport_v1 import fixture


def props(node):
    return {sx.unquote(row[1]): sx.unquote(row[2])
            for row in sx.children(node, 'property')}


class NativeSchematicTransportFixture(unittest.TestCase):
    def test_complete_packet_default_rules_and_normal_preflight(self):
        material = fixture.files()
        self.assertEqual(set(material), {fixture.STEM + ext for ext in
                         ('.kicad_pcb', '.kicad_sch', '.kicad_pro', '.kicad_prl')})
        self.assertEqual(material, fixture.files())
        project = json.loads(material[fixture.STEM + '.kicad_pro'])
        settings = project['board']['design_settings']
        self.assertEqual(settings['drc_exclusions'], [])
        self.assertTrue(all(settings['rule_severities'][key] == 'error'
                            for key in p.CRITICAL_CHECKS))
        self.assertNotIn('ignore', settings['rule_severities'].values())
        self.assertEqual(project['net_settings'], {
            'classes': [{'name': 'Default', 'clearance': 0.2, 'track_width': 0.3,
                         'via_diameter': 0.8, 'via_drill': 0.4}],
            'netclass_patterns': [], 'netclass_assignments': None})
        self.assertEqual(settings['rules']['min_connection'], 0.25)
        with tempfile.TemporaryDirectory() as name:
            output = Path(name).resolve() / 'project'
            fixture.write_project(output)
            board = output / (fixture.STEM + '.kicad_pcb')
            self.assertEqual(p.preflight(board), sx.parse(fixture.board().decode()))
            self.assertIsNone(p.netclass_policy(board))
            self.assertFalse(board.with_suffix('.kicad_dru').exists())

    def test_six_pads_one_real_unrouted_pair_and_separate_protected_net(self):
        tree = sx.parse(fixture.board().decode())
        fps = sx.children(tree, 'footprint')
        self.assertEqual(len(fps), 6)
        expected = {row[0]: row for row in fixture.TERMINALS}
        nets = {}
        for fp in fps:
            ref = props(fp)['Reference']; row = expected[ref]
            self.assertEqual(sx.one(fp, 'at'), ['at', row[1], row[2]])
            pads = sx.children(fp, 'pad'); self.assertEqual(len(pads), 1)
            pad = pads[0]
            self.assertEqual(pad[1:4], ['"1"', 'thru_hole', 'circle'])
            self.assertEqual(sx.one(pad, 'size'), ['size', '2', '2'])
            self.assertEqual(sx.one(pad, 'drill'), ['drill', '0.8'])
            self.assertEqual(sx.unquote(sx.one(pad, 'net')[1]), row[3])
            nets.setdefault(row[3], []).append(ref)
        self.assertEqual(nets, {'ROUTE': ['J1', 'J2'], 'KEEP': ['J3', 'J4'],
                                'GND': ['J5', 'J6']})
        routes = p.routes(tree); self.assertEqual(len(routes), 1)
        keep = routes[0]
        self.assertEqual(keep[0], 'segment'); self.assertTrue(p.locked(keep))
        self.assertEqual(sx.one(keep, 'net'), ['net', '"KEEP"'])
        self.assertEqual(sx.one(keep, 'start'), ['start', '12', '16'])
        self.assertEqual(sx.one(keep, 'end'), ['end', '26', '16'])
        self.assertEqual(sx.one(keep, 'width'), ['width', '0.3'])
        self.assertEqual(sx.one(keep, 'layer'), ['layer', '"F.Cu"'])
        zones = sx.children(tree, 'zone'); self.assertEqual(len(zones), 1)
        self.assertEqual(sx.one(zones[0], 'net'), ['net', '"GND"'])
        self.assertEqual(sx.one(zones[0], 'layer'), ['layer', '"B.Cu"'])
        self.assertEqual(sx.one(zones[0], 'polygon'),
                         ['polygon', ['pts', ['xy', '7', '21'], ['xy', '31', '21'],
                          ['xy', '31', '29'], ['xy', '7', '29']]])
        self.assertFalse(sx.children(zones[0], 'filled_polygon'))
        self.assertFalse(sx.children(zones[0], 'fill_segments'))
        self.assertEqual(sum(sx.unquote(row[1]).endswith('.Cu')
                             for row in sx.one(tree, 'layers')[1:]), 2)
        self.assertEqual(len(sx.children(tree, 'gr_rect')), 1)

    def test_complete_flat_schematic_matches_pcb_terminal_identity(self):
        board = sx.parse(fixture.board().decode())
        schematic = sx.parse(fixture.schematic().decode())
        self.assertFalse(sx.children(schematic, 'sheet'))
        symbols = sx.children(schematic, 'symbol')
        self.assertEqual(len(symbols), 6)
        labels = sx.children(schematic, 'global_label')
        self.assertEqual(len(labels), 6)
        by_ref = {props(fp)['Reference']: fp for fp in sx.children(board, 'footprint')}
        label_by_at = {tuple(sx.one(row, 'at')[1:]): sx.unquote(row[1]) for row in labels}
        for sym in symbols:
            ref = props(sym)['Reference']; fp = by_ref[ref]
            row = next(row for row in fixture.TERMINALS if row[0] == ref)
            self.assertEqual(sx.one(sym, 'uuid')[1], '"' + fixture.uid(ref + '-symbol') + '"')
            self.assertEqual(sx.unquote(sx.one(fp, 'path')[1]), '/' + fixture.uid(ref + '-symbol'))
            self.assertEqual(label_by_at[(row[6], row[5], '0')], row[3])
            self.assertEqual(sx.one(sym, 'at'), ['at', row[4], row[5], '0'])
            for key in ('Value', 'Description', fixture.FIELD):
                self.assertEqual(props(fp)[key], props(sym)[key])
            self.assertEqual(props(fp)['Datasheet'], '~')
            self.assertEqual(props(sym)['Datasheet'], '')
            self.assertEqual([pin[1] for pin in sx.children(sym, 'pin')], ['"1"'])
        library = sx.one(sx.one(schematic, 'lib_symbols'), 'symbol')
        self.assertEqual(sx.unquote(library[1]), fixture.LIB_ID)
        self.assertEqual(props(library)['Footprint'], fixture.FOOTPRINT)

    def test_normal_transplant_preserves_locked_source_and_rejects_changed_or_missing_keep(self):
        original = sx.parse(fixture.board().decode())
        keep = p.routes(original)[0]
        imported = copy.deepcopy(original)
        imported.append(sx.parse('(segment (start 12 10) (end 26 10) (width 0.3) '
            '(layer "F.Cu") (net "ROUTE") (uuid "' + fixture.uid('test-generated-route') + '"))'))
        audit = {}; result = p.transplant_routes(original, imported, protected=[keep], audit=audit)
        self.assertEqual(p.immutable(result), p.immutable(original))
        self.assertIn(keep, p.routes(result)); self.assertEqual(len(p.routes(result)), 2)
        for changed in ('missing', 'width', 'lock', 'net'):
            with self.subTest(changed=changed):
                bad = copy.deepcopy(imported); route = p.routes(bad)[0]
                if changed == 'missing': bad.remove(route)
                elif changed == 'width': sx.one(route, 'width')[1] = '0.4'
                elif changed == 'lock': route.remove(sx.one(route, 'locked'))
                else: sx.one(route, 'net')[1] = '"ROUTE"'
                with self.assertRaises(p.Rejected):
                    p.transplant_routes(original, bad, protected=[keep])

    def test_writer_never_overwrites_or_follows_alias(self):
        with tempfile.TemporaryDirectory() as name:
            parent = Path(name).resolve(); target = parent / 'new'
            fixture.write_project(target)
            self.assertEqual({p.name: p.read_bytes() for p in target.iterdir()}, fixture.files())
            with self.assertRaises(ValueError): fixture.write_project(target)
            link = parent / 'alias'; link.symlink_to(parent, target_is_directory=True)
            with self.assertRaises(ValueError): fixture.write_project(link / 'other')
            self.assertFalse((parent / 'other').exists())
            with self.assertRaises(ValueError): fixture.write_project(Path('relative'))


if __name__ == '__main__':
    unittest.main()
