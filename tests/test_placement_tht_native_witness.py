"""Small pure witness-seam controls; these do not qualify actual Native APIs."""
import copy
import json
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from experiments.placement_native_proposal_v1 import contract as c, ordinary_native as witness
from tests import test_placement_context_geometry as f


def pair(x, y):
    return SimpleNamespace(x=x, y=y)


class Pad:
    """One hand-entered world-space PTH, independent of parser observations."""
    def __init__(self, pcb):
        self.m_Uuid = SimpleNamespace(AsString=lambda: f.uid('tht-pad'))
        self.pcb = pcb; self.drill = 1; self.shape = pcb.PAD_SHAPE_ROUNDRECT
    def GetAttribute(self): return self.pcb.PAD_ATTRIB_PTH
    def IsFlipped(self): return False
    def GetLayerSet(self): return SimpleNamespace(Seq=lambda: [0, 2, 1, 3])
    def GetShape(self, layer): return self.shape
    def GetSize(self, layer): return pair(1000000, 1000000)
    def GetOffset(self, layer): return pair(0, 0)
    def GetRoundRectRadiusRatio(self, layer): return .25
    def GetRoundRectCornerRadius(self, layer): return 250000
    def GetPosition(self): return pair(10000000, 20000000)
    def GetFPRelativePosition(self): return pair(0, 0)
    def GetOrientationDegrees(self): return 90
    def GetDrillSize(self): return pair(500000, 500000)
    def GetDrillShape(self): return self.drill
    def GetNumber(self): return '1'
    def GetNetname(self): return 'ROUTE_A'
    def GetRemoveUnconnected(self): return False
    def GetKeepTopBottom(self): return False
    def GetNetCode(self): return 1


def seam(*, point=False, circle_court=False):
    tree = f.context_board()
    board, pcb, fc, fps = f.independent_native()
    pcb.F_Mask = 1; pcb.B_Mask = 3; pcb.F_Paste = 4
    pcb.PAD_ATTRIB_PTH = 0; pcb.PAD_ATTRIB_SMD = 1
    pcb.PAD_SHAPE_CIRCLE = 0; pcb.PAD_SHAPE_RECT = 1; pcb.PAD_SHAPE_ROUNDRECT = 2
    pcb.PAD_DRILL_SHAPE_CIRCLE = 1
    pcb.LSET = SimpleNamespace(AllCuMask=lambda: SimpleNamespace(Seq=lambda: [0, 2]))
    pad = Pad(pcb); fps[0].pads = [pad]; board.GetPads = lambda: [pad]
    by_id = {str(fp.m_Uuid.AsString()): fp for fp in fps}
    old_formatter = pcb.PCB_IO_KICAD_SEXPR
    class Formatter:
        def Format(self, item):
            self.item = item
        def GetStringOutput(self, clear):
            if hasattr(self.item, 'formatted'):
                return c.sx.dump(self.item.formatted)
            other = old_formatter(); other.Format(self.item)
            return other.GetStringOutput(clear)
    pcb.PCB_IO_KICAD_SEXPR = Formatter
    for fp in c.sx.children(tree, 'footprint'):
        fp.append(['duplicate_pad_numbers_are_jumpers', 'no'])
        native = by_id[c.uid(fp)]; native.formatted = fp
        native.GetDuplicatePadNumbersAreJumpers = lambda: False
        native.Points = lambda: []
        native.GetUnitInfo = lambda: (_ for _ in ()).throw(AssertionError('opaque unit getter must not run'))
    front = c.sx.children(tree, 'footprint')[0]
    front.append(['pad', '"1"', 'thru_hole', 'roundrect', ['at', '0', '0', '90'],
        ['size', '1', '1'], ['drill', '0.5'], ['layers', '"*.Cu"', '"*.Mask"'],
        ['net', '"ROUTE_A"'], ['roundrect_rratio', '0.25'], ['uuid', json.dumps(f.uid('tht-pad'))]])
    front.append(['units', ['unit', ['name', '"A"'], ['pins', '"1"']]])
    if point:
        front.append(['point', ['at', '10.25', '20'], ['size', '1'],
            ['layer', '"F.Fab"'], ['uuid', json.dumps(f.uid('fixed-point'))]])
        fps[0].Points = lambda: [object()]
    if circle_court:
        rectangle = c.sx.children(front, 'fp_rect')[0]; front.remove(rectangle)
        front.append(f.graphic('fp_circle', 'court-circle', ['center', '0', '0'],
            ['end', '1', '0'], layer='F.CrtYd', width='0.05'))
        fps[0].graphics[0] = f.NativeShape('court-circle', pcb.SHAPE_T_CIRCLE, pcb.F_CrtYd,
            start=[10000000,20000000], end=[10000000,19000000], width=50000)
    return tree, board, pcb, fc, fps, pad


class THTNativeWitnessTests(unittest.TestCase):
    def capture(self, state, *, scope=c.THT_SCOPE):
        tree, board, pcb, fc, *_ = state
        return witness.capture(board, pcb, f.raw(tree), c, fc, scope=scope)

    def test_new_scope_checks_hand_entered_curves_metadata_and_roundrect_PTH(self):
        state = seam(); before = copy.deepcopy(state[0]); observed, details = self.capture(state)
        self.assertEqual(state[0], before)
        self.assertEqual(observed['scope'], c.THT_SCOPE)
        meta = details['engineering_metadata'][f.uid('front')]
        self.assertTrue(meta['immutable_metadata_equal'])
        self.assertEqual(meta['point_count'], 0)
        self.assertNotIn('formatted_footprint_sha256', meta)
        self.assertFalse(meta['native_execution_proven'])
        self.assertEqual(details['native_pad_netcodes'], {f.uid('tht-pad'): 1})

    def test_equal_XY_oblong_or_boolean_drill_cannot_pass_new_scope(self):
        for drill in (2, True):
            state = seam(); state[-1].drill = drill
            with self.subTest(drill=drill), self.assertRaisesRegex(ValueError, 'circular PTH drill'):
                self.capture(state)

    def test_metadata_getter_and_exact_formatted_census_are_mandatory(self):
        for fault in ('true', 'missing', 'changed-unit', 'missing-source-census'):
            state = seam(); native = state[4][0]
            if fault == 'true': native.GetDuplicatePadNumbersAreJumpers = lambda: True
            if fault in ('missing', 'changed-unit'):
                native.formatted = copy.deepcopy(native.formatted)
                if fault == 'missing': native.formatted.remove(c.sx.one(native.formatted, 'units'))
                else: c.sx.one(native.formatted, 'units')[1][1][1] = '"B"'
            if fault == 'missing-source-census':
                observed = c.inspect_board(f.raw(state[0]), scope=c.THT_SCOPE)
                for row in observed['footprints']: row.pop('engineering_metadata')
                with patch.object(c, 'inspect_board', return_value=observed):
                    with self.assertRaisesRegex(ValueError, 'metadata record'):
                        self.capture(state)
            else:
                with self.subTest(fault=fault), self.assertRaises(ValueError): self.capture(state)

    def test_point_census_length_is_checked_without_dereferencing_point_objects(self):
        state = seam(point=True); _, details = self.capture(state)
        meta = details['engineering_metadata'][f.uid('front')]
        self.assertEqual(meta['point_count'], 1)
        self.assertEqual(meta['point_census_method'], 'Points-length-and-exact-footprint-formatter')
        state[4][0].Points = lambda: []
        with self.assertRaisesRegex(ValueError, 'point count differs'): self.capture(state)

    def test_opaque_point_count_is_explicit_formatter_fallback_not_field_omission(self):
        state = seam(point=True)
        state[4][0].Points = lambda: object()
        _, details = self.capture(state)
        meta = details['engineering_metadata'][f.uid('front')]
        self.assertEqual(meta['point_census_method'], 'exact-footprint-formatter')
        self.assertEqual(meta['direct_point_count_unavailable'], 'TypeError')
        native = state[4][0]; native.formatted = copy.deepcopy(native.formatted)
        native.formatted.remove(c.sx.one(native.formatted, 'point'))
        with self.assertRaisesRegex(ValueError, 'metadata differs'): self.capture(state)

    def test_other_point_API_failures_are_not_hidden_by_fallback(self):
        state = seam(point=True)
        def broken(): raise RuntimeError('point API failed')
        state[4][0].Points = broken
        with self.assertRaisesRegex(RuntimeError, 'point API failed'): self.capture(state)

    def test_circle_courtyard_has_same_exact_native_shape_fences(self):
        state = seam(circle_court=True); observed, _ = self.capture(state)
        source = next(row for row in observed['footprints'] if row['uuid'] == f.uid('front'))
        self.assertFalse(source['courtyard']['rectangular'])
        state[4][0].graphics[0].width += 1
        with self.assertRaisesRegex(ValueError, 'shape/stroke/lock'): self.capture(state)

    def test_old_context_does_not_call_new_metadata_or_drill_interfaces(self):
        tree = f.context_board(); board, pcb, fc, fps = f.independent_native()
        def forbidden(): raise AssertionError('new metadata getter used by old scope')
        for fp in fps:
            fp.GetDuplicatePadNumbersAreJumpers = forbidden
            fp.Points = forbidden
        observed, details = witness.capture(board, pcb, f.raw(tree), c, fc, scope=c.CONTEXT_SCOPE)
        self.assertEqual(observed, c.inspect_board(f.raw(tree), scope=c.CONTEXT_SCOPE))
        self.assertEqual(set(details), {'native_pad_netcodes', 'native_route_netcodes', 'actual_native_areas'})


if __name__ == '__main__':
    unittest.main()
