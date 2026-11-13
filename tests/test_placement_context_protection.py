"""Pure scope/protection controls; no Native validation or delivery claims."""
import unittest

from autorouter import placement_copper as copper
from experiments.placement_native_proposal_v1 import contract, ordinary_fixture
from experiments.placement_native_proposal_v1.test_contract import identity, raw


class ContextProtectionTests(unittest.TestCase):
    def setUp(self):
        self.selected = ordinary_fixture.selected()
        self.region = [7000000, 7000000, 31000000, 13000000]
        self.moves = {self.selected[0]: [14000000, 10000000],
                      self.selected[1]: [24000000, 10000000]}

    def source(self, *, full_pour=False, context_only=False):
        tree = ordinary_fixture.board()
        if full_pour:
            zone = contract.sx.children(tree, 'zone')[0]
            points = contract.sx.one(contract.sx.one(zone, 'polygon'), 'pts')
            points[1:] = [['xy', '0', '0'], ['xy', '38', '0'],
                          ['xy', '38', '30'], ['xy', '0', '30']]
        if context_only:
            fixed = next(fp for fp in contract.sx.children(tree, 'footprint')
                         if ordinary_fixture.base.reference(fp) == 'J5')
            fixed.append(['fp_circle', ['center', '0', '0'], ['end', '.2', '0'],
                          ['stroke', ['width', '.05'], ['type', 'solid']],
                          ['fill', 'none'], ['layer', '"F.Fab"'],
                          ['uuid', '"' + identity('context-protection-circle') + '"']])
        return raw(tree)

    def candidate(self, source, plan, *, changed_fill=False):
        prepared = copper.prepare(source, plan)
        tree = contract.translated_tree(prepared, self.moves,
            scope=contract.CONTEXT_SCOPE, selected=self.selected, region_nm=self.region)
        if changed_fill:
            # Deliberately authored derived data exercises a pure audit only.
            # This is not a KiCad-generated fill or a validated candidate.
            contract.sx.children(tree, 'zone')[0].append(['filled_polygon',
                ['layer', '"B.Cu"'], ['pts', ['xy', '1', '1'],
                ['xy', '2', '1'], ['xy', '1', '2']]])
        return raw(tree)

    def legacy_plan(self, source):
        plan = copper.propose(source, self.selected, protected_names=['GND'])
        self.assertEqual(plan['source_scope'], contract.ORDINARY_SCOPE)
        self.assertEqual(plan['protected_names'], ['GND'])
        self.assertNotIn('GND', plan['incident_names'])
        self.assertFalse(plan['execution_authorized'])
        return plan

    def test_exact_legacy_scope_still_reaches_a_successful_translation_audit(self):
        source = self.source()
        plan = self.legacy_plan(source)
        result = copper.audit_translation(source, self.candidate(source, plan), plan,
            self.moves, scope=contract.ORDINARY_SCOPE, region_nm=self.region)
        self.assertTrue(result['audit_passed'])
        self.assertFalse(result['native_validation_performed'])
        self.assertFalse(result['routing_accepted'])

    def test_protected_plane_legacy_plan_cannot_authorize_context_translation(self):
        source = self.source(full_pour=True)
        plan = self.legacy_plan(source)
        candidate = self.candidate(source, plan, changed_fill=True)
        with self.assertRaisesRegex(ValueError, 'scope differs'):
            copper.audit_translation(source, candidate, plan, self.moves,
                scope=contract.CONTEXT_SCOPE, region_nm=self.region)

    def test_protected_plane_legacy_plan_cannot_authorize_context_routed_audit(self):
        source = self.source(full_pour=True)
        plan = self.legacy_plan(source)
        candidate = self.candidate(source, plan, changed_fill=True)
        with self.assertRaisesRegex(ValueError, 'scope differs'):
            copper.audit_routed(source, candidate, plan, self.moves,
                scope=contract.CONTEXT_SCOPE, region_nm=self.region)

    def test_context_plan_refuses_unrelated_protected_zone_net(self):
        source = self.source(full_pour=True, context_only=True)
        baseline = copper.propose(source, self.selected)
        self.assertEqual(baseline['source_scope'], contract.CONTEXT_SCOPE)
        self.assertNotIn('GND', baseline['incident_names'])
        with self.assertRaisesRegex(ValueError, 'Protected net copper-zone fill'):
            copper.propose(source, self.selected, protected_names=['GND'])


if __name__ == '__main__':
    unittest.main()
