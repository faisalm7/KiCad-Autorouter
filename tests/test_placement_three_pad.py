"""Guard the explicit three-pad placement slice without running Native."""
import unittest

from autorouter import placement_intent, sexpr as sx
from experiments.constrained_placement_v1 import prototype
from experiments.placement_native_proposal_v1 import contract, three_pad_fixture


class ThreePadPlacementTests(unittest.TestCase):
    def setUp(self):
        self.raw = three_pad_fixture.files()[three_pad_fixture.STEM + '.kicad_pcb']
        self.observation = contract.inspect_board(self.raw, scope=contract.THREE_PAD_SCOPE)
        self.parts = {part['reference']: part for part in self.observation['footprints']}
        self.selected = self.parts['J1']['uuid']
        self.options = dict(scope=contract.THREE_PAD_SCOPE, selected=[self.selected],
                            region_nm=[14_000_000, 8_000_000, 22_000_000, 13_000_000],
                            region_initialization=prototype.EXACT_TRACK_REGION_POLICY)

    def test_three_named_terminals_are_available_only_in_the_new_scope(self):
        legacy = contract.inspect_fixed_context(self.raw)
        self.assertEqual(legacy['scope'], contract.THT_BASELINE_SCOPE)
        self.assertFalse(next(row for row in legacy['footprints'] if row['reference'] == 'J1')['placement_eligible'])
        self.assertTrue(self.parts['J1']['placement_eligible'])
        checks = contract.facts_from_observation(self.observation, **self.options)
        component = next(row for row in checks['components'] if row['id'] == self.selected)
        self.assertEqual({pad['net'] for pad in component['pads']}, {'ROUTE_A', 'ROUTE_B', 'ROUTE_C'})
        with self.assertRaisesRegex(ValueError, 'Choose one'):
            contract.facts_from_observation(self.observation,
                                           **(self.options | {'selected': [self.selected, self.parts['J2']['uuid']]}))
        with self.assertRaisesRegex(ValueError, 'all existing copper'):
            placement_intent.settings(**self.options, copper_policy=placement_intent.COPPER_POLICY)

    def test_translation_refuses_a_changed_third_pad_or_outside_courtyard(self):
        good = {self.selected: [19_500_000, 10_000_000]}
        tree = contract.translated_tree(self.raw, good, **self.options)
        raw = (sx.dump(tree) + '\n').encode()
        self.assertTrue(contract.check_translation(self.raw, raw, good, **self.options)['exact_immutable_AST'])
        part = next(row for row in sx.children(tree, 'footprint') if contract.uid(row) == self.selected)
        third = next(pad for pad in sx.children(part, 'pad') if pad[1] == '"3"')
        sx.one(third, 'net')[1] = '"ROUTE_B"'
        with self.assertRaisesRegex(ValueError, 'changed fields'):
            contract.check_translation(self.raw, (sx.dump(tree) + '\n').encode(), good, **self.options)
        with self.assertRaises(ValueError):
            contract.validate_moves(self.observation, {self.selected: [22_000_000, 10_000_000]}, **self.options)
