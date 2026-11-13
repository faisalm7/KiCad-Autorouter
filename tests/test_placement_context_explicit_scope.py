"""Explicit placement-plan scope controls, never Native qualification."""
import copy
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from autorouter import gui, placement_copper as copper, placement_intent as intent
from experiments.placement_native_proposal_v1 import contract, ordinary_fixture
from experiments.placement_native_proposal_v1.test_contract import raw


class ExplicitPlanScopeTests(unittest.TestCase):
    def setUp(self):
        self.source = raw(ordinary_fixture.board())
        self.selected = ordinary_fixture.selected()
        self.region = [7000000, 7000000, 31000000, 13000000]
        self.moves = {self.selected[0]: [14000000, 10000000],
                      self.selected[1]: [24000000, 10000000]}

    def test_legacy_default_none_and_explicit_ordinary_keep_exact_plan_bytes(self):
        # Captured from audited d7454427213b4debaa7ee096bbecad208c9ac283.
        expected = 'aac161649422506920a02d54b8450fa21cebcf5cb3b70cc2b36e93c860d2bdd6'
        default = copper.propose(self.source, self.selected, protected_names=['GND'])
        self.assertEqual(hashlib.sha256(copper._encoded(default)).hexdigest(), expected)
        for scope in (None, contract.ORDINARY_SCOPE):
            with self.subTest(scope=scope):
                current = copper.propose(self.source, self.selected,
                    protected_names=['GND'], scope=scope)
                self.assertEqual(copper._encoded(current), copper._encoded(default))
                self.assertEqual(copper.prepare(self.source, current), self.source)

    def test_explicit_context_overrides_legacy_readability_and_replays_same_policy(self):
        self.assertEqual(copper.propose(self.source, self.selected)['source_scope'],
                         contract.ORDINARY_SCOPE)
        plan = copper.propose(self.source, self.selected, scope=contract.CONTEXT_SCOPE)
        self.assertEqual(plan['source_scope'], contract.CONTEXT_SCOPE)
        self.assertFalse(plan['execution_authorized'])
        self.assertEqual(copper.prepare(self.source, plan), self.source)
        candidate = raw(contract.translated_tree(self.source, self.moves,
            scope=contract.CONTEXT_SCOPE, selected=self.selected, region_nm=self.region))
        for audit in (copper.audit_translation, copper.audit_routed):
            with self.subTest(audit=audit.__name__):
                result = audit(self.source, candidate, plan, self.moves,
                    scope=contract.CONTEXT_SCOPE, region_nm=self.region)
                self.assertTrue(result['audit_passed'])
                self.assertFalse(result['native_validation_performed'])
                self.assertFalse(result['routing_accepted'])
                self.assertFalse(result['approval_granted'])

    def test_explicit_context_refuses_unrelated_protected_pour_before_partition(self):
        baseline = copper.propose(self.source, self.selected, scope=contract.CONTEXT_SCOPE)
        self.assertNotIn('GND', baseline['incident_names'])
        with patch.object(copper.rs, 'bind') as partition:
            with self.assertRaisesRegex(ValueError, 'Protected net copper-zone fill'):
                copper.propose(self.source, self.selected, scope=contract.CONTEXT_SCOPE,
                               protected_names=['GND'])
            partition.assert_not_called()

    def test_changed_scope_or_source_cannot_reconstruct_the_same_reviewed_plan(self):
        plan = copper.propose(self.source, self.selected, scope=contract.CONTEXT_SCOPE)
        for scope in (contract.ORDINARY_SCOPE, 'unknown', True):
            changed = copy.deepcopy(plan); changed['source_scope'] = scope
            with self.subTest(scope=scope), self.assertRaises(ValueError):
                copper.prepare(self.source, changed)
        changed = copy.deepcopy(plan); changed['protected_names'] = ['GND']
        with self.assertRaisesRegex(ValueError, 'Protected net copper-zone fill'):
            copper.prepare(self.source, changed)
        with self.assertRaisesRegex(ValueError, 'plan/source changed'):
            copper.prepare(self.source + b'\n', plan)

    def test_unknown_explicit_scope_cannot_silently_use_legacy_fallback(self):
        for scope in (True, False, 1, '', 'unknown', {}, []):
            with self.subTest(scope=scope), self.assertRaisesRegex(ValueError, 'scope'):
                copper.propose(self.source, self.selected, scope=scope)

    def test_product_context_passes_explicit_scope_after_inspection_guard(self):
        # Only the previously completed Native-inspection replay is stubbed.
        # Actual source capture, constructor, partition and scope checks execute.
        with tempfile.TemporaryDirectory() as temporary:
            board = Path(temporary).resolve() / 'owned.kicad_pcb'
            board.write_bytes(self.source)
            board.with_suffix('.kicad_pro').write_text('{}')
            board.with_suffix('.kicad_sch').write_text('(kicad_sch)')
            inspection = dict(source=str(board), source_hashes=gui.source_inventory(board),
                observation=contract.inspect_board(self.source, scope=contract.CONTEXT_SCOPE))
            settings = intent.settings(self.selected, self.region,
                scope=contract.CONTEXT_SCOPE, copper_policy=intent.COPPER_POLICY)
            with patch.object(intent, 'current', return_value=inspection) as replay, \
                    patch.object(copper, 'propose', wraps=copper.propose) as constructor:
                plan, observation = intent._effective_context(inspection, settings)
            replay.assert_called_once_with(inspection)
            self.assertEqual(constructor.call_args.kwargs['scope'], contract.CONTEXT_SCOPE)
            self.assertEqual(plan['source_scope'], contract.CONTEXT_SCOPE)
            self.assertEqual(observation['scope'], contract.CONTEXT_SCOPE)
            self.assertEqual(board.read_bytes(), self.source)


if __name__ == '__main__':
    unittest.main()
