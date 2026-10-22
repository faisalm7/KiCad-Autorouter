"""Constructed Improve GUI parity controls; no wx/Native/GUI qualification."""
import copy
import json
from pathlib import Path
import tempfile
from unittest.mock import Mock, patch
import unittest
from autorouter import gui, preferences as pref, strategy
from tests import test_gui as gui_fixture
from tests.test_gui import window_method
from tests import test_gui_improve_preset as preset_fixture
from tests import test_gui_thermal_budget_display as budget_fixture


class ImproveSettingsParityTests(unittest.TestCase):
    setUp = gui_fixture.GuiWorkflowTests.setUp

    def test_selected7_score_refusal_is_before_workspace_and_keeps_input(self):
        for score in ('via_default','via_low','via_high'):
            config=dict(pref.DEFAULTS,profile='tuned',scoring_preference=score)
            before=copy.deepcopy(config)
            with self.subTest(score=score),patch.object(gui.c,'NATIVE_VERSION','10.0.7'):
                with self.assertRaisesRegex(ValueError,'engine-default via cost'):
                    gui.Request(str(self.board),str(self.output),json.dumps(config),True,'improve').prepare()
            self.assertEqual(config,before)
            self.assertEqual(list(self.output.iterdir()),[])

    def test_legacy0_scoring_and_selected7_default_are_preserved(self):
        for version,scores in (('10.0.0',(None,'via_default','via_low','via_high')),('10.0.7',(None,))):
            for score in scores:
                config=dict(pref.DEFAULTS,profile='tuned',scoring_preference=score)
                before=copy.deepcopy(config)
                with self.subTest(version=version,score=score),patch.object(gui.c,'NATIVE_VERSION',version):
                    self.assertEqual(gui.check_improve_settings(config),before)
                    self.assertEqual(gui.improve_preset(config),before)
                self.assertEqual(config,before)

    def test_actual_selector_shows_whole_method_budget_and_preserves_constraints(self):
        config=dict(pref.DEFAULTS,seconds=420)
        window=preset_fixture.ImprovePresetTests.window(self,config)
        window.budget_label=Mock();window.method_note=Mock();window.buttons={'route':Mock()}
        before=copy.deepcopy(config)
        with patch.object(gui.c,'NATIVE_VERSION','10.0.7'):
            window_method('method_changed')(window,Mock())
        window.budget_label.SetLabel.assert_called_once_with('Whole Improve-method budget (seconds)')
        window.method_note.SetLabel.assert_called_once_with(gui.IMPROVE_HELP)
        self.assertIn('tuned incumbent',gui.IMPROVE_HELP)
        self.assertEqual(gui.IMPROVE_RETURN_RESERVE_SECONDS,strategy.NATIVE_FINAL_RESERVE_SECONDS)
        self.assertIn(f'{strategy.NATIVE_FINAL_RESERVE_SECONDS:g}-second internal return reserve',gui.IMPROVE_HELP)
        window.refused.assert_not_called();self.assertEqual(config,before)

    def test_actual_selector_does_not_hide_selected7_score_refusal(self):
        config=dict(pref.DEFAULTS,scoring_preference='via_low')
        window=preset_fixture.ImprovePresetTests.window(self,config);before=copy.deepcopy(config)
        with patch.object(gui.c,'NATIVE_VERSION','10.0.7'):
            window_method('method_changed')(window,Mock())
        for control in window.choices.values():control.SetSelection.assert_not_called()
        window.refused.assert_called_once()
        self.assertIn('engine-default via cost',str(window.refused.call_args.args[0]))
        self.assertEqual(config,before)


class ImproveSummaryParityTests(unittest.TestCase):
    findings = budget_fixture.RecoveryBudgetDisplayTests.findings

    def setUp(self):
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
        self.workspace=Path(temporary.name).resolve()
        settings=dict(pref.DEFAULTS,profile='tuned',seconds=420)
        self.settings_bytes=json.dumps(settings).encode()
        self.route=dict(status='routing_accepted',strategy='native_validated_zone_net_pruning',
            scope='whole_board_unlocked_routing',budget_seconds=420,cpu_budget_seconds=420,
            engine_profile='tuned',adapter='both',pruning_preferences=dict(effective=settings),
            native=dict(opens=0,blocking=0,warnings=6,exclusions=0))
        self.review=dict(status='ready_for_manual_review',budget_seconds=30,cpu_budget_seconds=30)
        self.choice=dict(choice_recorded=True,choice='accept',budget_seconds=30)
        self.export=dict(status='export_validated',export_accepted=True,budget_seconds=120,cpu_budget_seconds=120)
        self.records=dict(route=self.route,review=self.review,choice=self.choice,export=self.export)
        self.receipt_bytes={}
        for stage,record in self.records.items():
            path=self.workspace/stage/('result.json' if stage=='route' else stage+'.json');path.parent.mkdir()
            raw=(json.dumps(record,sort_keys=True)+'\n').encode();path.write_bytes(raw);self.receipt_bytes[path]=raw

    def test_exact_pruning_capture_wins_over_merged_stage_or_other_preferences(self):
        record=dict(self.route,budget_seconds=30,effective_preferences=dict(pref.DEFAULTS,seconds=30,scope='partial_completion'))
        before=copy.deepcopy(record)
        text=gui.human_summary('review',record,method='improve')
        self.assertIn(f'{strategy.NATIVE_FINAL_RESERVE_SECONDS:g}-second internal return reserve',text)
        self.assertIn('whole Improve-method budget 420 s',text)
        self.assertIn('Reroute unlocked copper; preserve locked routing',text)
        self.assertNotIn('preserve all existing routing',text)
        self.assertIn('Additional Native export-validation budget: 120 s',text)
        self.assertEqual(record,before)

    def test_actual_finished_route_review_accept_export_keep_method_and_receipt_budgets(self):
        for stage,record in (('route',self.route),('review',self.review),('choice',self.choice),
                ('export',dict(current=True,export_accepted=True))):
            with self.subTest(stage=stage):
                text=self.findings(stage,record,method='improve')
                self.assertIn('whole Improve-method budget 420 s',text)
                self.assertNotIn('whole Improve-method budget 30 s',text)
                self.assertNotIn('whole Improve-method budget 120 s',text)
                self.assertIn('Additional Native export-validation budget: 120 s',text)
                self.assertIn('preserve locked routing',text)
                self.assertIn('6 warnings',text)
        self.assertEqual(self.review['budget_seconds'],30)
        self.assertEqual(self.export['budget_seconds'],120)

    def test_route_and_recovery_summary_meanings_stay_separate(self):
        settings=dict(pref.DEFAULTS,seconds=420)
        route=dict(status='routing_accepted',routing_preferences=dict(effective=settings))
        ordinary=gui.human_summary('route',route,method='route')
        recovery=gui.human_summary('route',dict(route,strategy='native_validated_thermal_bridge'),method='recover')
        self.assertIn('; routing budget 420 s',ordinary)
        self.assertNotIn('whole Improve-method budget',ordinary)
        self.assertIn('whole recovery-method budget 420 s',recovery)
        self.assertNotIn('whole Improve-method budget',recovery)


if __name__=='__main__':unittest.main()
