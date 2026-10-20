"""Constructed parent dispatch/import boundaries; no Native execution claim."""
import unittest
from unittest.mock import patch
from autorouter import pipeline as p, strategy as s, floor_route as f
from tests import test_normal_selected_import as import_fixture, test_result as result_fixture


class ParentDirectImportTests(unittest.TestCase):
    def test_direct_and_mixed_import_population_cannot_impersonate_pruning(self):
        for mixed in (False, True):
            with self.subTest(mixed=mixed):
                root, data, original, _, check = import_fixture.NormalSelectedImportControls.make(self, selected=False)
                self.assertIsInstance(check(), dict)  # Real constructed direct proof first.
                data['strategy'] = 'native_validated_zone_net_pruning'
                imports = [dict(cwd=str(root))]
                if mixed:imports.append(dict(cwd=str(root / 'incumbent')))
                with self.assertRaisesRegex(p.Rejected, 'checked incumbent, not a direct import'):
                    p.normal_import_contract(root, data, imports, input_policy='native', original=original)

    def test_absent_or_empty_import_census_cannot_pass_parent(self):
        root, data, original, _, _ = import_fixture.NormalSelectedImportControls.make(self, selected=False)
        data.update(strategy='native_validated_zone_net_pruning', baseline='C-prototype')
        for imports in (None, []):
            with self.subTest(imports=imports), self.assertRaises((p.Rejected, FileNotFoundError)):
                p.normal_import_contract(root, data, imports, input_policy='native', original=original)


class ParentScoringDispatchTests(unittest.TestCase):
    setUp = result_fixture.ResultFreshnessTests.setUp
    save_receipt = result_fixture.ResultFreshnessTests.save_receipt

    def test_admitted_parent_reaches_mandatory_import_boundary_without_early_child_replay(self):
        self.data['strategy'] = 'native_validated_zone_net_pruning'; self.save_receipt()
        # Source-derived admission is an explicit seam here. The existing real
        # source/candidate/process census runs up to the import boundary, where
        # the sentinel refuses; this does not fabricate an accepted parent.
        with patch.object(s, 'native7_parent', return_value={'constructed-admission-only': True}), \
                patch.object(s, 'check_incumbent_scoring', side_effect=AssertionError('early replay')), \
                patch.object(p, 'normal_import_contract', side_effect=p.Rejected('mandatory import boundary')) as imported:
            with self.assertRaisesRegex(p.Rejected, 'mandatory import boundary'):
                p._check_result_uncached(self.receipt)
        imported.assert_called_once()

    def test_legacy_or_unadmitted_parent_still_checks_scoring_at_entry(self):
        self.data['strategy'] = 'native_validated_zone_net_pruning'; self.save_receipt()
        with patch.object(s, 'native7_parent', return_value=None), \
                patch.object(s, 'check_incumbent_scoring', side_effect=p.Rejected('legacy scoring boundary')) as scoring, \
                patch.object(p, 'normal_import_contract') as imported:
            with self.assertRaisesRegex(p.Rejected, 'legacy scoring boundary'):
                p._check_result_uncached(self.receipt)
        scoring.assert_called_once(); imported.assert_not_called()

    def test_parent_cannot_use_another_derived_policy_to_skip_incumbent_import(self):
        self.data['strategy'] = 'native_validated_zone_net_pruning'; self.save_receipt()
        with patch.object(s, 'native7_parent', return_value={'constructed-admission-only': True}), \
                patch.object(f, 'receipt_policy', return_value='board-floors-v1'), \
                patch.object(p, 'normal_import_contract') as imported:
            with self.assertRaisesRegex(p.Rejected, 'derived native import policy'):
                p._check_result_uncached(self.receipt)
        imported.assert_not_called()
