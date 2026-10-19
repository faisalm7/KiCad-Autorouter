"""Runtime flat-map compatibility controls; no Native execution or admission.

SPDX-License-Identifier: GPL-3.0-or-later
The existing owned class fixture supplies constructed Native-shaped rows.
"""
import copy
import unittest

from autorouter import schematic_classes as q
from tests import test_flat_class_parity as fixture


class RuntimeFlatFloorControls(unittest.TestCase):
    def setUp(self):
        self.case = fixture.FlatClassParityControls()
        self.case.setUp()
        self.floors = {'min_track_width': 250000, 'min_clearance': 200000,
                       'min_via_diameter': 600000, 'min_through_hole_diameter': 300000,
                       'min_via_annular_width': 100000}

    def derive(self, native):
        case = self.case
        return q.derive(fixture.encoded(case.netlist), case.board_raw, case.project_raw,
            fixture.json_bytes(native), source=case.source, schematic_source=case.sch_source,
            schematic_raw=fixture.encoded(case.sch))

    def test_historical_and_emitted_floor_headers_preserve_complete_class_proof(self):
        before = copy.deepcopy(self.case.native)
        for extended in (False, True):
            native = copy.deepcopy(before)
            if extended: native['effective_floors_nm'] = self.floors.copy()
            snapshot = copy.deepcopy(native)
            result = self.derive(native)
            self.assertIs(result['class_parity_qualified'], True)
            self.assertIs(result['accepted'], False)
            self.assertEqual((result['components'], result['terminals'], result['nets']), (6, 6, 3))
            self.assertEqual(native, snapshot)
        self.assertEqual(self.case.native, before)

    def test_floor_extension_keeps_source_and_schema_checks_mandatory(self):
        for fault in ('source_disagrees', 'missing_floor', 'unknown_floor', 'bool',
                      'negative', 'overflow', 'not_object', 'unknown_header', 'missing_layers'):
            with self.subTest(fault=fault):
                native = copy.deepcopy(self.case.native)
                observed = native['effective_floors_nm'] = self.floors.copy()
                if fault == 'source_disagrees': observed['min_track_width'] += 1
                elif fault == 'missing_floor': del observed['min_clearance']
                elif fault == 'unknown_floor': observed['unknown_floor'] = 0
                elif fault == 'bool': observed['min_clearance'] = True
                elif fault == 'negative': observed['min_clearance'] = -1
                elif fault == 'overflow': observed['min_clearance'] = 2147483648
                elif fault == 'not_object': native['effective_floors_nm'] = None
                elif fault == 'missing_layers': del native['copper_layers']
                else: native['unknown_header'] = []
                with self.assertRaises(ValueError): self.derive(native)
