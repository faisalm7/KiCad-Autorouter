"""Constructed via-high preference/admission seams; no Native qualification."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from autorouter import config as c, pipeline as p, preferences as pref
from tests import test_rejected_attempt as negatives


class ViaHighPreferenceTests(unittest.TestCase):
    def test_persistent_bytes_and_standard_engine_change_only_two_cost_flags(self):
        original_defaults=dict(pref.DEFAULTS)
        parent=c.ROOT/'.cache';parent.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='via-high-preset-',dir=parent) as tmp:
            path=Path(tmp)/'settings.json'
            path.write_text(json.dumps(dict(pref.DEFAULTS,seconds=90,scoring_preference='via_high')))
            captured=pref.load(path);before=path.read_bytes()
            effective=pref.resolve(captured);record=pref.snapshot(captured)
            self.assertEqual(pref.readback(record,effective),effective)
            self.assertEqual(pref.route_arguments(effective)['scoring_variant'],'via_high')
            self.assertEqual(effective['profile'],'standard')
            with patch.object(c,'NATIVE_VERSION','10.0.7'):
                p.require_native_scope(scoring=effective['scoring_preference'])
                p.require_native_scope(scope='partial_completion',scoring=effective['scoring_preference'])
            for strict in (False,True):
                plain=p.engine_profile_settings('standard',90.,strict_class_targets=strict)
                high=p.engine_profile_settings('standard',90.,strict_class_targets=strict,scoring_variant='via_high')
                self.assertEqual(high['argv'],plain['argv']+[
                    '--router.scoring.via_costs=100','--router.scoring.plane_via_costs=10'])
                for name in ('profile','strict_class_targets','assigned_job_timeout_seconds',
                             'assigned_optimizer_timeout_seconds','native_finalization_reserve_seconds',
                             'engine_grace_reserve_seconds'):
                    self.assertEqual(high[name],plain[name])
            self.assertEqual(path.read_bytes(),before)
            path.write_bytes(before+b' ')
            with self.assertRaises(pref.PreferenceError):pref.check_fresh(captured)
        self.assertEqual(dict(pref.DEFAULTS),original_defaults)
        self.assertIsNone(pref.DEFAULTS['scoring_preference'])

    def test_only_high_is_new_and_other_scope_profile_layer_guards_remain(self):
        class Name(str):pass
        with patch.object(c,'NATIVE_VERSION','10.0.7'):
            for scoring in ('via_default','via_low','unknown',True,0,[],{},Name('via_high')):
                with self.subTest(scoring=scoring),self.assertRaises(p.Rejected):p.require_native_scope(scoring=scoring)
            for extra in ({'scope':'selected_nets'},{'layers':['F.Cu']},{'profile':'tuned'},
                          {'profile':'completion-only'},{'adapter':'none'},{'guidance':'board-floors-v1'},
                          {'purpose':'thermal-recovery'},{'purpose':'improve','profile':'tuned'}):
                with self.subTest(extra=extra),self.assertRaises(p.Rejected):
                    p.require_native_scope(scoring='via_high',**extra)
        # The old selected0 admission remains unchanged; no new branch there.
        with patch.object(c,'NATIVE_VERSION','10.0.0'):p.require_native_scope(profile='tuned',scoring='via_low')


class ViaHighNegativeSelectorTests(unittest.TestCase):
    def setUp(self):
        # Existing fully synthetic0 fixture. We stop selected7 at the mandatory
        # engine reader; these bytes are never relabelled as Native7 evidence.
        self.case=negatives.CompletedNegativeTests('test_zero_warning_blocking_negative_is_disjoint_immutable_diagnostic')
        self.case.PROFILE='standard';self.case.SCORING='via_high'
        self.addCleanup(self.case.doCleanups);self.case.setUp()

    def selected(self):
        return patch.multiple(c,NATIVE_VERSION='10.0.7',current_native_selection=lambda:{'version':'10.0.7'})

    def test_explicit_score_expectation_reaches_mandatory_engine_reader(self):
        with self.selected(),patch.object(p,'require_native_scope',wraps=p.require_native_scope) as scope, \
                patch.object(p,'check_normal_engine_provenance',side_effect=RuntimeError('mandatory-engine-reader')) as engine:
            with self.assertRaisesRegex(RuntimeError,'mandatory-engine-reader'):
                p.check_rejected_routing_attempt(self.case.receipt,ordinary_profile='standard',ordinary_scoring='via_high')
            scope.assert_called_once_with(purpose='route',scope='whole_board_unlocked_routing',guidance='native',
                layers='source_all',profile='standard',adapter='both',scoring='via_high')
            engine.assert_called_once_with(self.case.run,self.case.data)

    def test_score_is_not_inferred_and_partial_negative_scope_stays_closed(self):
        with self.selected(),patch.object(p,'check_normal_engine_provenance') as engine:
            with self.assertRaises(p.Rejected):
                p.check_rejected_routing_attempt(self.case.receipt,ordinary_profile='standard')
            original=copy.deepcopy(self.case.data)
            for change in ({'scoring_variant':None},{'scoring_variant':'via_low'},{'scope':'partial_completion'}):
                self.case.data=dict(original,**change);self.case.save_receipt()
                with self.subTest(change=change),self.assertRaises(p.Rejected):
                    p.check_rejected_routing_attempt(self.case.receipt,ordinary_profile='standard',ordinary_scoring='via_high')
            engine.assert_not_called()

    def test_explicit_selector_cannot_mix_authority_or_enter_positive_private_mode(self):
        with self.selected():
            for kwargs in ({'ordinary_profile':'tuned','ordinary_scoring':'via_high'},
                           {'ordinary_profile':'standard','ordinary_scoring':'via_low'},
                           {'ordinary_profile':'standard','ordinary_scoring':True},
                           {'ordinary_profile':'standard','ordinary_scoring':'via_high','comparison_context':object()}):
                with self.subTest(kwargs=kwargs),self.assertRaises(p.Rejected):
                    p.check_rejected_routing_attempt('/not-read/result.json',**kwargs)
            for kwargs in ({'_rejected_profile':'standard'},
                           {'_rejected_attempt':True,'_rejected_profile':'tuned'},
                           {'_rejected_attempt':True,'_rejected_profile':'standard','comparison_context':object()},
                           {'_rejected_attempt':True,'_rejected_profile':'standard','_improve_context':object()}):
                with self.subTest(kwargs=kwargs),self.assertRaises(p.Rejected):
                    p._check_result_uncached('/not-read/result.json',_rejected_scoring='via_high',**kwargs)
        with patch.object(c,'NATIVE_VERSION','10.0.0'),self.assertRaises(p.Rejected):
            p.check_rejected_routing_attempt('/not-read/result.json',ordinary_profile='standard',ordinary_scoring='via_high')

    def test_existing_default_selector_dispatch_is_unchanged(self):
        marker=object()
        with patch.object(p,'_check_result_uncached',return_value=marker) as body:
            self.assertIs(p.check_rejected_routing_attempt(self.case.receipt),marker)
            body.assert_called_once_with(self.case.receipt,_rejected_attempt=True)
            body.reset_mock()
            self.assertIs(p.check_rejected_routing_attempt(self.case.receipt,ordinary_profile='standard'),marker)
            body.assert_called_once_with(self.case.receipt,_rejected_attempt=True,_rejected_profile='standard')


if __name__=='__main__':unittest.main()
