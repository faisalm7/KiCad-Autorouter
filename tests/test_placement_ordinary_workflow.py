"""Owned ordinary-footprint workflow controls; no Native or GUI qualification."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

from autorouter import gui, placement_intent as intent, placement_view, sexpr as sx
from experiments.constrained_placement_v1 import constraints
from experiments.placement_native_proposal_v1 import contract, ordinary_fixture as fixture


class OrdinaryPlacementWorkflowTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='ordinary-placement-workflow-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.board = fixture.write_project(self.root / 'saved project')
        self.pristine = self.board.read_bytes()
        self.selected = fixture.selected()
        self.region = [7_000_000, 7_000_000, 31_000_000, 13_000_000]
        self.scope = contract.ORDINARY_SCOPE
        self.options = intent.settings(self.selected, self.region, scope=self.scope)
        self.inspection = intent.inspect_saved(self.board)
        self.original = gui.source_inventory(self.board)

    def footprint(self, tree, ref):
        return next(fp for fp in sx.children(tree, 'footprint') if fixture.base.reference(fp) == ref)

    def rewrite(self, change):
        tree = sx.parse(self.pristine.decode()); change(tree)
        self.board.write_text(sx.dump(tree) + '\n')

    def moves(self):
        return {self.selected[0]: [13_000_000, 10_000_000], self.selected[1]: [25_000_000, 10_000_000]}

    def rows(self, svg, role):
        return [node for node in ET.fromstring(svg).iter() if node.get('data-role') == role]

    def test_saved_source_has_two_eligible_smd_parts_and_preserved_fixed_copper(self):
        with patch('subprocess.Popen', side_effect=AssertionError('inspection must remain pure')):
            observed = intent.inspect_saved(self.board)
        self.assertEqual(observed, self.inspection)
        self.assertEqual(observed['observation']['scope'], self.scope)
        rows = {row['reference']: row for row in observed['components']}
        self.assertFalse(rows['J1']['fixed_reasons']); self.assertFalse(rows['J2']['fixed_reasons'])
        for reference in ('J3', 'J4'):
            self.assertIn('Shares a net with existing copper', rows[reference]['fixed_reasons'])
        self.assertTrue(rows['J5']['fixed_reasons']); self.assertTrue(rows['J6']['fixed_reasons'])
        self.assertEqual(observed['observation']['route_count'], 1)
        self.assertTrue(observed['observation']['routes'][0]['locked'])
        self.assertEqual(len(observed['observation']['zones']), 1)
        for key in ('native_validation_performed', 'execution_authorized', 'approval_granted'):
            self.assertIs(observed[key], False)
        self.assertEqual(gui.source_inventory(self.board), self.original)

    def test_explicit_v2_settings_persist_and_cannot_fall_back_to_pth_scope(self):
        self.assertEqual(self.options['schema'], 2)
        self.assertEqual(self.options['kind'], intent.ORDINARY_SETTINGS_KIND)
        self.assertEqual(self.options['scope'], self.scope)
        path = self.root / 'ordinary-settings.json'; path.write_text(json.dumps(self.options))
        self.assertEqual(intent.load_settings(path), self.options)
        old = intent.settings(self.selected, self.region)
        self.assertEqual(old['schema'], 1)
        self.assertNotIn('scope', old)
        with self.assertRaisesRegex(ValueError, 'scope differs'):
            intent.facts(self.inspection, old)
        for key, value in (('scope', contract.MULTIPAD_SCOPE), ('preserve_existing', False),
                           ('orientation', 'any'), ('side', 'back'), ('approval_granted', True)):
            bad = copy.deepcopy(self.options); bad[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError): intent.validate_settings(bad)

    def test_locked_routed_and_ineligible_components_are_not_movable_choices(self):
        by_ref = {row['reference']: row['uuid'] for row in self.inspection['components']}
        for fixed in ('J3', 'J4', 'J5', 'J6'):
            value = intent.settings([self.selected[0], by_ref[fixed]], self.region, scope=self.scope)
            with self.subTest(reference=fixed), self.assertRaisesRegex(ValueError, 'fixed|locked|routed'):
                intent.facts(self.inspection, value)
        self.rewrite(lambda tree: self.footprint(tree, 'J1').append(['locked', 'yes']))
        inspection = intent.inspect_saved(self.board)
        row = next(row for row in inspection['components'] if row['reference'] == 'J1')
        self.assertIn('Locked in KiCad', row['fixed_reasons'])
        before = gui.source_inventory(self.board)
        with self.assertRaisesRegex(ValueError, 'fixed|locked|routed'):
            intent.facts(inspection, self.options)
        self.assertEqual(gui.source_inventory(self.board), before)

    def test_bounded_actual_search_and_review_are_detached_non_authoritative_proposals(self):
        before = copy.deepcopy(self.inspection)
        with patch('subprocess.Popen', side_effect=AssertionError('search must remain pure')):
            proposal = intent.propose(self.inspection, self.options)
        self.assertEqual(proposal['search']['status'], 'proposals_ready')
        self.assertTrue(1 <= len(proposal['search']['alternatives']) <= 2)
        facts = intent.facts(self.inspection, self.options)
        for row in proposal['search']['alternatives']:
            constraints.validate_alternative(facts, row['candidate'])
            self.assertEqual(set(row['moves_nm']), set(self.selected))
            self.assertTrue(all(type(n) is int for xy in row['moves_nm'].values() for n in xy))
        review = intent.Review(proposal)
        draft = review.decision(acknowledged=True, accepted=True)
        self.assertEqual(intent.validate_draft(self.inspection, draft), draft)
        for field in ('native_validation_performed', 'execution_authorized', 'approval_granted',
                      'routing_accepted', 'warning_acknowledged', 'human_PCB_approval'):
            self.assertIs(draft[field], False)
        self.assertEqual(self.inspection, before)
        self.assertEqual(gui.source_inventory(self.board), self.original)

    def test_translation_changes_only_selected_anchor_xy_not_angles_pads_or_other_ast(self):
        options = dict(scope=self.scope, selected=self.selected, region_nm=self.region)
        moved = contract.translated_tree(self.pristine, self.moves(), **options)
        expected = sx.parse(self.pristine.decode())
        for ref, x in (('J1', '13'), ('J2', '25')):
            sx.one(self.footprint(expected, ref), 'at')[1:3] = [x, '10']
        self.assertEqual(moved, expected)
        candidate = (sx.dump(moved) + '\n').encode()
        proof = contract.check_translation(self.pristine, candidate, self.moves(), **options)
        self.assertTrue(proof['exact_immutable_AST'])
        self.assertEqual(sx.one(self.footprint(moved, 'J1'), 'at')[3], '90')
        self.assertEqual(sx.one(self.footprint(moved, 'J2'), 'at')[3], '270')
        altered = copy.deepcopy(moved)
        sx.one(sx.children(self.footprint(altered, 'J1'), 'pad')[0], 'roundrect_rratio')[1] = '0.2'
        with self.assertRaises(ValueError):
            contract.check_translation(self.pristine, (sx.dump(altered) + '\n').encode(), self.moves(), **options)
        self.assertEqual(gui.source_inventory(self.board), self.original)

    def test_fixed_noncentered_courtyard_proxy_covers_original_geometry_without_moving_anchor(self):
        facts = intent.facts(self.inspection, self.options)
        uid = next(row['uuid'] for row in self.inspection['components'] if row['reference'] == 'J5')
        component = next(row for row in facts['components'] if row['id'] == uid)
        proxy = constraints.bounds(component, constraints.pose(component))
        # Source anchor is (12, 24); the slightly sloped courtyard spans 10.7..13.5.
        # A 0.05 mm stroke adds 0.025 mm at each side. This is an obstacle envelope,
        # never a rewritten courtyard or a new anchor in the saved PCB.
        for got, expected in zip(proxy, (10.675, 22.675, 13.525, 25.325)):
            self.assertAlmostEqual(got, expected, places=8)
        self.assertEqual(component['position_mm'], [12.1, 24.0])
        self.assertEqual(component['pads'][0]['offset_mm'], [-0.1, 0.0])
        original = constraints.original_alternative(facts)
        mapped, moves = contract.quantized_translation(facts, original, observation=self.inspection['observation'])
        self.assertEqual(mapped, original)
        self.assertEqual(moves, {self.selected[0]: [12_000_000, 10_000_000],
                                 self.selected[1]: [26_000_000, 10_000_000]})
        self.assertEqual(sx.one(self.footprint(sx.parse(self.pristine.decode()), 'J5'), 'at')[1:3], ['12', '24'])
        self.assertIn(uid, constraints.immovable(facts))
        self.assertEqual(gui.source_inventory(self.board), self.original)

    def test_roundrect_preview_has_rotated_real_pad_centres_and_no_fake_smd_holes(self):
        svg = placement_view.render(self.inspection['observation'], self.moves(), self.selected, self.region)
        originals = {node.get('data-pad'): node for node in self.rows(svg, 'original-selected-pad')}
        proposed = {node.get('data-pad'): node for node in self.rows(svg, 'proposed-selected-pad')}
        self.assertEqual(len(proposed), 4)
        for ref, x, ys, angle in (('J1', 13_000_000, (10_825_000, 9_175_000), 90),
                                  ('J2', 25_000_000, (9_175_000, 10_825_000), 270)):
            pads = sx.children(self.footprint(sx.parse(self.pristine.decode()), ref), 'pad')
            for pad, y in zip(pads, ys):
                uid = sx.unquote(sx.one(pad, 'uuid')[1]); node = proposed[uid]
                self.assertTrue(node.tag.endswith('}rect'))
                self.assertEqual(node.get('data-shape'), 'roundrect')
                self.assertEqual(node.get('data-angle'), str(angle))
                self.assertEqual(node.get('data-centre-nm'), str(x) + ',' + str(y))
                self.assertTrue(node.get('transform').startswith('rotate(' + str(-angle) + ' '))
                self.assertAlmostEqual(float(node.get('rx')) / float(node.get('width')), .25, places=8)
                self.assertEqual(originals[uid].get('width'), node.get('width'))
        self.assertEqual(self.rows(svg, 'proposed-selected-drill'), [])
        self.assertEqual(len(self.rows(svg, 'fixed-drill')), 4)
        self.assertEqual(len(self.rows(svg, 'preserved-segment')), 1)
        self.assertEqual(gui.source_inventory(self.board), self.original)

    def test_roundrect_display_refuses_missing_none_and_zero_radius_ratio(self):
        for value in ('missing', None, 0):
            observation = copy.deepcopy(self.inspection['observation'])
            fp = next(row for row in observation['footprints'] if row['uuid'] == self.selected[0])
            if value == 'missing': del fp['pads'][0]['roundrect_rratio']
            else: fp['pads'][0]['roundrect_rratio'] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                placement_view.render(observation, self.moves(), self.selected, self.region)

    def test_invalid_pad_geometry_angles_and_copper_graphics_are_refused_without_repair(self):
        def pad(tree): return sx.children(self.footprint(tree, 'J1'), 'pad')[0]
        changes = {
            'zero_size': lambda tree: sx.one(pad(tree), 'size').__setitem__(1, '0'),
            'excess_rounding': lambda tree: sx.one(pad(tree), 'roundrect_rratio').__setitem__(1, '0.6'),
            'wrong_copper_side': lambda tree: sx.one(pad(tree), 'layers').__setitem__(1, '"B.Cu"'),
            'noncardinal_footprint': lambda tree: sx.one(self.footprint(tree, 'J1'), 'at').__setitem__(3, '45'),
            'noncardinal_pad': lambda tree: sx.one(pad(tree), 'at').__setitem__(3, '45'),
            'footprint_copper_graphic': lambda tree: sx.one(sx.children(self.footprint(tree, 'J1'), 'fp_line')[-1], 'layer').__setitem__(1, '"F.Cu"'),
            'board_copper_graphic': lambda tree: sx.one(sx.children(tree, 'gr_text')[0], 'layer').__setitem__(1, '"F.Cu"'),
        }
        for name, mutate in changes.items():
            self.rewrite(mutate); before = gui.source_inventory(self.board)
            with self.subTest(name=name), self.assertRaises(ValueError): intent.inspect_saved(self.board)
            self.assertEqual(gui.source_inventory(self.board), before)

    def test_stale_saved_project_cannot_search_or_issue_review_intent(self):
        proposal = intent.propose(self.inspection, self.options); review = intent.Review(proposal)
        project = self.board.with_suffix('.kicad_pro'); project.write_bytes(project.read_bytes() + b'\n')
        before = gui.source_inventory(self.board)
        with self.assertRaisesRegex(ValueError, 'source changed'): intent.propose(self.inspection, self.options)
        with self.assertRaisesRegex(ValueError, 'source changed'):
            review.decision(acknowledged=True, accepted=True)
        self.assertIsNone(review.intent)
        self.assertEqual(gui.source_inventory(self.board), before)


if __name__ == '__main__': unittest.main()
