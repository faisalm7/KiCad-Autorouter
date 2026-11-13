"""Owned source-contract regressions; no Native or routing qualification claim."""
import copy
import json
import unittest
import xml.etree.ElementTree as ET
from decimal import Decimal

from autorouter import placement, placement_copper as copper, placement_intent as intent
from autorouter import placement_view as view
from experiments.constrained_placement_v1 import constraints
from experiments.placement_native_proposal_v1 import contract as c, ordinary_fixture as fixture
from experiments.placement_native_proposal_v1 import engineering_metadata as metadata


def raw(tree):
    return (c.sx.dump(tree) + '\n').encode()


def fp(tree, reference):
    return next(row for row in c.sx.children(tree, 'footprint')
                if fixture.base.reference(row) == reference)


def board():
    """Extend our owned fixture, never a stripped version of a licensed board."""
    tree = fixture.board()
    for owner in c.sx.children(tree, 'footprint'):
        owner.append(['duplicate_pad_numbers_are_jumpers', 'no'])
        numbers = sorted({pad[1] for pad in c.sx.children(owner, 'pad')})
        owner.append(['units', ['unit', ['name', '"A"'], ['pins', *numbers]]])
    for reference in ('J1', 'J2'):
        owner = fp(tree, reference)
        c.sx.one(owner, 'attr')[1:] = ['through_hole']
        for pad in c.sx.children(owner, 'pad'):
            pad[2] = 'thru_hole'
            pad.append(['drill', '0.3'])
            c.sx.one(pad, 'layers')[1:] = ['"*.Cu"', '"*.Mask"']
        # Real THT libraries often anchor pad1, away from the courtyard centre.
        # Use an exact off-centre proxy without changing pad offsets.
        for line in c.sx.children(owner, 'fp_line'):
            if c.atom(line, 'layer') != 'F.CrtYd': continue
            for key in ('start', 'end'):
                row = c.sx.one(line, key)
                row[1] = str(Decimal(row[1]) + Decimal('0.1'))
        owner.append(['fp_circle', ['center', '0', '0'], ['end', '0.2', '0'],
            ['stroke', ['width', '0.05'], ['type', 'solid']], ['fill', 'none'],
            ['layer', '"F.Fab"'], ['uuid', json.dumps(fixture.uid(reference+'-tht-circle'))]])
        owner.append(['fp_arc', ['start', '-0.2', '0'], ['mid', '0', '0.2'], ['end', '0.2', '0'],
            ['stroke', ['width', '0.05'], ['type', 'solid']],
            ['layer', '"F.Fab"'], ['uuid', json.dumps(fixture.uid(reference+'-tht-arc'))]])
    return tree


class THTScope(unittest.TestCase):
    def setUp(self):
        self.tree = board()
        self.selected = fixture.selected()
        self.region = [7_000_000, 7_000_000, 31_000_000, 13_000_000]

    def inspect(self, tree=None):
        return c.inspect_board(raw(self.tree if tree is None else tree), scope=c.THT_SCOPE)

    def test_new_scope_is_explicit_and_does_not_broaden_old_contracts(self):
        before = copy.deepcopy(self.tree)
        for scope in (c.MULTIPAD_SCOPE, c.ORDINARY_SCOPE, c.CONTEXT_SCOPE):
            with self.subTest(scope=scope), self.assertRaises(ValueError):
                c.inspect_board(raw(self.tree), scope=scope)
        observed = self.inspect()
        self.assertEqual(c.inspect_fixed_context(raw(self.tree)), observed)
        self.assertEqual(observed['scope'], c.THT_SCOPE)
        self.assertEqual(self.tree, before)
        for row in observed['footprints']:
            self.assertFalse(row['engineering_metadata']['duplicate_pad_numbers_are_jumpers'])
        for row in observed['footprints']:
            if row['uuid'] in self.selected:
                self.assertTrue(row['placement_eligible'])
                self.assertFalse(row['courtyard']['centered'])
                self.assertEqual({pad['kind'] for pad in row['pads']}, {'thru_hole'})

    def test_exact_off_anchor_translation_preserves_every_other_source_field(self):
        observed = self.inspect()
        options = dict(scope=c.THT_SCOPE, selected=self.selected, region_nm=self.region)
        facts = c.facts_from_observation(observed, **options)
        pose = constraints.original_alternative(facts)
        for row in pose['transforms']:
            if row['component_id'] in self.selected:
                row['x_mm'] += 1
                row['y_mm'] += .1
        _, moves = c.quantized_translation(facts, pose, observation=observed)
        anchors = {row['uuid']: row['position_nm'] for row in observed['footprints']}
        self.assertEqual(moves, {key: [anchors[key][0]+1_000_000, anchors[key][1]+100_000]
                                 for key in self.selected})
        candidate = raw(c.translated_tree(raw(self.tree), moves, **options))
        c.check_translation(raw(self.tree), candidate, moves, **options)
        after = c.read_board(candidate)
        for owner in c.sx.children(after, 'footprint'):
            if c.uid(owner) in moves:
                c.sx.one(owner, 'at')[1:3] = c.sx.one(fp(self.tree, fixture.base.reference(owner)), 'at')[1:3]
        self.assertEqual(after, self.tree)

    def test_split_collinear_courtyard_keeps_original_primitive_census(self):
        owner = fp(self.tree, 'J1')
        line = next(row for row in c.sx.children(owner, 'fp_line') if c.atom(row, 'layer') == 'F.CrtYd')
        end = list(c.sx.one(line, 'end')[1:])
        start = c.sx.one(line, 'start')[1:]
        midpoint = [str((Decimal(a)+Decimal(b))/2) for a,b in zip(start,end)]
        extra = copy.deepcopy(line)
        c.sx.one(line, 'end')[1:] = midpoint
        c.sx.one(extra, 'start')[1:] = midpoint
        c.sx.one(extra, 'end')[1:] = end
        c.sx.one(extra, 'uuid')[1] = json.dumps(fixture.uid('split-court'))
        owner.append(extra)
        observed = self.inspect()
        court = next(row['courtyard'] for row in observed['footprints'] if row['uuid'] == self.selected[0])
        self.assertTrue(court['rectangular'])
        self.assertEqual(len(court['primitives']), 5)
        c.sx.one(line, 'end')[1:3] = ['10', '-0.73']
        c.sx.one(extra, 'start')[1:3] = ['10', '-0.73']
        with self.assertRaises(ValueError): self.inspect()

    def test_circular_courtyard_is_fixed_with_outward_integer_envelope(self):
        owner = fp(self.tree, 'J3')
        owner.remove(c.sx.one(owner, 'fp_rect'))
        owner.append(['fp_circle', ['center', '0', '0'], ['end', '2', '0.000001'],
            ['stroke', ['width', '0.05'], ['type', 'solid']], ['fill', 'none'],
            ['layer', '"F.CrtYd"'], ['uuid', json.dumps(fixture.uid('fixed-circle-court'))]])
        observed = self.inspect()
        row = next(row for row in observed['footprints'] if row['uuid'] == c.uid(owner))
        self.assertFalse(row['placement_eligible'])
        self.assertFalse(row['courtyard']['rectangular'])
        self.assertEqual(row['courtyard']['local_bounds_nm'], [-2000001,-2000001,2000001,2000001])

    def test_physical_duplicate_terminals_remain_separate_and_fixed(self):
        owner = fp(self.tree, 'J3'); pad = c.sx.children(owner, 'pad')[0]
        second = copy.deepcopy(pad)
        c.sx.one(second, 'uuid')[1] = json.dumps(fixture.uid('physical-duplicate'))
        c.sx.one(second, 'at')[1:3] = ['0.2', '0']
        owner.append(second)
        row = next(row for row in self.inspect()['footprints'] if row['uuid'] == c.uid(owner))
        self.assertFalse(row['placement_eligible'])
        self.assertEqual(len(row['pads']), 2)
        self.assertEqual(len({pad['uuid'] for pad in row['pads']}), 2)
        self.assertEqual(len({pad['number'] for pad in row['pads']}), 1)
        facts = c.facts_from_observation(self.inspect(), scope=c.THT_SCOPE,
                                        selected=self.selected, region_nm=self.region)
        physical = next(part for part in facts['components'] if part['id'] == row['uuid'])
        self.assertEqual(len(physical['pads']), 2)
        self.assertEqual(len({pad['id'] for pad in physical['pads']}), 2)
        c.sx.one(second, 'net')[1:] = c.sx.one(c.sx.children(fp(self.tree,'J1'),'pad')[0], 'net')[1:]
        with self.assertRaisesRegex(ValueError, 'differing nets'): self.inspect()

    def test_point_bearing_selected_footprint_is_fixed(self):
        owner = fp(self.tree, 'J1')
        owner.append(['point', ['at','12','10'], ['size','2'], ['layer','"F.Fab"'],
                      ['uuid',json.dumps(fixture.uid('fixed-point'))]])
        observed = self.inspect()
        with self.assertRaisesRegex(ValueError, 'fixed in ordinary'):
            c.facts_from_observation(observed, scope=c.THT_SCOPE, selected=self.selected, region_nm=self.region)

    def test_copper_plan_scope_cannot_be_laundered_and_protected_pour_stays_blocked(self):
        source = raw(self.tree)
        plan = copper.propose(source, self.selected, scope=c.THT_SCOPE)
        self.assertEqual(plan['source_scope'], c.THT_SCOPE)
        with self.assertRaisesRegex(ValueError, 'Protected net copper-zone fill'):
            copper.propose(source, self.selected, scope=c.THT_SCOPE, protected_names=['GND'])
        anchors = {row['uuid']:row['position_nm'] for row in self.inspect()['footprints']}
        moves = {key:[anchors[key][0]+1_000_000,anchors[key][1]] for key in self.selected}
        for scope in (c.CONTEXT_SCOPE,c.ORDINARY_SCOPE):
            with self.subTest(scope=scope), self.assertRaisesRegex(ValueError, 'scope differs'):
                copper.audit_translation(source, source, plan, moves, scope=scope, region_nm=self.region)
        settings = intent.settings(self.selected,self.region,scope=c.THT_SCOPE,
                                   copper_policy=intent.COPPER_POLICY)
        self.assertEqual(intent.validate_settings(settings), settings)
        self.assertEqual(settings['annotation_policy'],'native-silk-mask-proxy-v1')

    def test_new_scope_still_requires_exact_source_bound_Native_annotations(self):
        observed = self.inspect()
        settings = intent.settings(self.selected, self.region, scope=c.THT_SCOPE)
        inspection = dict(observation=observed, components=[])
        with self.assertRaisesRegex(ValueError, 'Inspect Native placement geometry'):
            intent._facts(inspection, settings, None, observed)
        inspection.update(native_context={}, annotation_context={'scope':c.CONTEXT_SCOPE})
        with self.assertRaisesRegex(ValueError, 'exact reviewed geometry scope'):
            intent._facts(inspection, settings, None, observed)

    def test_roundrect_THT_preview_keeps_distinct_pad_and_drill_identities(self):
        observed = self.inspect()
        moves = {row['uuid']:row['position_nm'] for row in observed['footprints'] if row['uuid'] in self.selected}
        root = ET.fromstring(view.render(observed,moves,self.selected,self.region))
        pads = [row for row in root.iter() if row.get('data-role') == 'proposed-selected-pad']
        drills = [row for row in root.iter() if row.get('data-role') == 'proposed-selected-drill']
        self.assertEqual(len(pads),4)
        self.assertEqual({row.get('data-shape') for row in pads},{'roundrect'})
        self.assertEqual({row.get('data-pad') for row in pads},{row.get('data-pad') for row in drills})

    def test_zone_layer_enumeration_order_is_not_geometry_or_membership_change(self):
        expected = copy.deepcopy(self.inspect()['zones'][0])
        expected['layers'] = ['B.Cu','F.Cu']
        observed = copy.deepcopy(expected)
        observed.update(placement_enabled=False,placement_source_type='SHEETNAME',
                        placement_source='',disallow={flag:False for flag in c.pt.FLAGS})
        observed['layers'] = ['F.Cu','B.Cu']
        before = copy.deepcopy((expected,observed))
        self.assertEqual(c.check_ordinary_zone(expected,observed),observed)
        self.assertEqual((expected,observed),before)
        for layers in (['F.Cu'],['B.Cu'],['F.Cu','B.Cu','F.Cu'],['F.Cu','In1.Cu'],[],True):
            bad = dict(observed,layers=layers)
            with self.subTest(layers=layers),self.assertRaises(ValueError):
                c.check_ordinary_zone(expected,bad)
        bad = copy.deepcopy(observed);bad['outlines_nm'][0][0][0] += 1
        with self.assertRaises(ValueError): c.check_ordinary_zone(expected,bad)

    def test_retained_metadata_reader_requires_exact_new_scope_and_complete_source_census(self):
        observed = self.inspect()
        witnesses = {}
        for owner in observed['footprints']:
            source = owner['engineering_metadata']
            witnesses[owner['uuid']] = dict(policy=metadata.POLICY, owner_uuid=owner['uuid'],
                immutable_metadata_equal=True, metadata_sha256=metadata.digest(source),
                supplied_jumper_getter=False, points_fixed=True, native_execution_proven=False,
                point_census_method='Points-length-and-exact-footprint-formatter',
                direct_point_count_unavailable=None,point_count=len(source['points']))
        details = dict(native_pad_netcodes={pad['uuid']:1 for owner in observed['footprints'] for pad in owner['pads']},
            native_route_netcodes={},actual_native_areas={},engineering_metadata=witnesses)
        before = copy.deepcopy(details)
        self.assertEqual(placement._retained_native_details(details,None,scope=c.THT_SCOPE,observation=observed),details)
        self.assertEqual(details,before)
        with self.assertRaises(ValueError): placement._retained_native_details(details,None)
        for key,value in [('metadata_sha256','0'*64),('immutable_metadata_equal',False),
                          ('supplied_jumper_getter',True),('point_count',True),
                          ('point_count',1),('point_census_method','ignored'),
                          ('direct_point_count_unavailable','RuntimeError'),('native_execution_proven',True)]:
            bad = copy.deepcopy(details)
            bad['engineering_metadata'][self.selected[0]][key] = value
            with self.subTest(key=key,value=value),self.assertRaises(ValueError):
                placement._retained_native_details(bad,None,scope=c.THT_SCOPE,observation=observed)
        bad = copy.deepcopy(details);del bad['engineering_metadata'][self.selected[0]]
        with self.assertRaises(ValueError):
            placement._retained_native_details(bad,None,scope=c.THT_SCOPE,observation=observed)


if __name__ == '__main__': unittest.main()
