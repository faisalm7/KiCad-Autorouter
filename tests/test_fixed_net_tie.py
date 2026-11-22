import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from autorouter import design_intent, fixed_net_tie, pipeline, sexpr
from autorouter.__main__ import preview
from experiments.net_tie_contact_v1 import fixture


class FixedNetTieTest(unittest.TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.folder = Path(directory.name).resolve()
        for name, content in fixture.single_fixed_routing_files().items():
            (self.folder / name).write_bytes(content)
        self.source = self.folder / (fixture.STEM + '.kicad_pcb')
        self.original = sexpr.read(self.source)
        self.settings = dict(scope='selected_nets', profile='completion-only', nets=['N3_A'])

    def test_ordinary_preview_admits_only_the_unrelated_net(self):
        with patch.object(pipeline.c, 'NATIVE_VERSION', '10.0.7'):
            shown = preview(self.source, overrides=self.settings)
            self.assertEqual(shown['fixed_net_tie']['nets'], ['N2_A', 'N2_B'])
            self.assertEqual(shown['protected_route_items'], 3)
            self.assertIs(shown['native_validation_performed'], False)
            with self.assertRaisesRegex(pipeline.Rejected, 'remove tied nets.*N2_A'):
                preview(self.source, overrides={**self.settings, 'nets': ['N2_A', 'N3_A']})
            with self.assertRaisesRegex(pipeline.Rejected, 'net ties not qualified'):
                preview(self.source, overrides=dict(scope='partial_completion'))

    def test_unsupported_or_detached_bridge_is_visible_and_refused(self):
        footprint, = [fp for fp in sexpr.children(self.original, 'footprint') if sexpr.children(fp, 'net_tie_pad_groups')]
        bridge, = sexpr.children(footprint, 'fp_poly')
        for point in sexpr.one(bridge, 'pts')[1:]:
            point[1] = str(float(point[1]) + 2)
        sexpr.write(self.source, self.original)
        report = design_intent.inspect_project(self.source)
        self.assertIn('JP1: the bridge must overlap both', report['fixed_net_tie_refusal'])
        with patch.object(pipeline.c, 'NATIVE_VERSION', '10.0.7'):
            with self.assertRaisesRegex(pipeline.Rejected, 'JP1: the bridge must overlap both'):
                preview(self.source, overrides=self.settings)

    def test_transport_requires_same_layer_bridge_and_exact_pin_partition(self):
        tie = fixed_net_tie.describe(self.original)
        dsn = b'''(pcb owned (parser (string_quote ")) (structure (rule (width 200)))
          (network (net N2_A (pins J1-1 JP1-1)) (net N2_B (pins J2-1 JP1-2)) (net N3_A (pins J3-1 J5-1))
          (class kicad_default N2_A N2_B N3_A (circuit (use_via V)) (rule (width 200) (clearance 150)))))'''
        exported = self.folder / 'native.dsn'
        obstacles = self.folder / 'obstacles.json'
        exported.write_bytes(dsn)
        box = {'kind': 'PCB_SHAPE', 'layer': 'F.Cu', 'bbox_mm': [14.75, 9.85, 15.25, 10.15]}
        obstacles.write_text(json.dumps([box]))
        self.assertEqual(fixed_net_tie.transport(self.folder, self.original, tie)['native_terminal_count'], 6)
        obstacles.write_text(json.dumps([{**box, 'dsn_layer': 'B.Cu'}]))
        with self.assertRaisesRegex(ValueError, 'bridge keepout is missing or differs'):
            fixed_net_tie.transport(self.folder, self.original, tie)
        obstacles.write_text(json.dumps([box]))
        exported.write_bytes(dsn.replace(b'J1-1 JP1-1', b'J1-1 JP1-2').replace(b'J2-1 JP1-2', b'J2-1 JP1-1'))
        with self.assertRaisesRegex(pipeline.Rejected, 'terminal identity or net differs'):
            fixed_net_tie.transport(self.folder, self.original, tie)


if __name__ == '__main__':
    unittest.main()
