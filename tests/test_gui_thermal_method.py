"""Graphical recovery contract controls; no wx/Native or routing qualification."""
import copy
import json
import os
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from autorouter import gui, pipeline as p, preferences as pref
from tests import test_gui as gt


class ThermalMethodTests(unittest.TestCase):
    def setUp(self):
        gt.GuiWorkflowTests.setUp(self)
        self.settings = dict(pref.DEFAULTS, seconds=90)
        # Model the trusted selected7 runtime for these controller-only tests.
        # No selected tool, native source, worker or receipt is qualified here.
        self.version = patch.object(gui.c, 'NATIVE_VERSION', '10.0.7')
        self.version.start(); self.addCleanup(self.version.stop)
        self.selection = patch.object(gui.c, 'current_native_selection', return_value={'version': '10.0.7'})
        self.selection.start(); self.addCleanup(self.selection.stop)
        self.two_layers = ['kicad_pcb', ['layers', ['0', '"F.Cu"', 'signal'], ['31', '"B.Cu"', 'signal']]]

    def request(self, settings=None, method='recover'):
        return gui.Request(str(self.board), str(self.output), json.dumps(settings or self.settings), True, method)

    def flow(self, settings=None):
        with patch.object(p, 'preflight', return_value=self.two_layers) as preflight:
            flow = self.request(settings).prepare()
        preflight.assert_called_once_with(self.board)
        return flow

    def test_third_explicit_method_keeps_route_and_improve_indices(self):
        self.assertEqual([gui.method_for_index(i) for i in range(3)], ['route', 'improve', 'recover'])
        self.assertEqual(gui.Request.__dataclass_fields__['method'].default, 'route')
        for value in (-1, 3, True, '2', None):
            with self.subTest(value=value), self.assertRaises(ValueError): gui.method_for_index(value)

    def test_incompatible_settings_refuse_before_workspace_without_rewriting(self):
        cases = [dict(self.settings, scope='partial_completion'), dict(self.settings, profile='tuned'),
            dict(self.settings, adapter='none'), dict(self.settings, layers=['F.Cu','B.Cu']),
            dict(self.settings, scoring_preference='via_low'), dict(self.settings, seconds=89),
            dict(self.settings, guidance='board-floors-v1')]
        for settings in cases:
            before = copy.deepcopy(settings)
            with self.subTest(settings=settings), patch.object(p, 'preflight') as preflight:
                with self.assertRaises(ValueError): self.request(settings).prepare()
                preflight.assert_not_called()
            self.assertEqual(settings, before); self.assertEqual(list(self.output.iterdir()), [])

    def test_other_tool_profiles_refuse_without_workspace_or_native(self):
        for version in ('10.0.0', '10.0.8', None):
            with self.subTest(version=version), patch.object(gui.c, 'NATIVE_VERSION', version):
                with self.assertRaisesRegex(ValueError, 'selected KiCad 10.0.7'): self.request().prepare()
            self.assertEqual(list(self.output.iterdir()), [])

    def test_shared_source_preflight_and_four_layer_refusal_precede_workspace(self):
        with patch.object(p, 'preflight', side_effect=p.Rejected('unverified class/rule source')):
            with self.assertRaisesRegex(p.Rejected, 'unverified'): self.request().prepare()
        self.assertEqual(list(self.output.iterdir()), [])
        four = copy.deepcopy(self.two_layers); four[1].insert(2, ['2','"In1.Cu"','signal'])
        four[1].insert(3, ['4','"In2.Cu"','signal'])
        with patch.object(p, 'preflight', return_value=four):
            with self.assertRaisesRegex(ValueError, 'two source copper layers'): self.request().prepare()
        self.assertEqual(list(self.output.iterdir()), [])

    def test_source_changed_during_support_check_is_not_captured_as_eligible(self):
        def changed(board):
            board.write_bytes(b'changed after the captured source inventory')
            return self.two_layers
        with patch.object(p, 'preflight', side_effect=changed):
            with self.assertRaisesRegex(ValueError, 'changed during thermal support'): self.request().prepare()
        self.assertEqual(list(self.output.iterdir()), [])

    def test_actual_commands_preserve_method_and_export_budgets(self):
        for seconds in (90, 120, 420, 900):
            with self.subTest(seconds=seconds):
                settings = dict(self.settings, seconds=seconds); flow = self.flow(settings)
                preview = flow.command('preview')
                self.assertEqual(preview[4:], ['preview', str(self.board), '--settings', str(flow.workspace/'settings.json')])
                flow.ready.add('preview')
                self.assertEqual(flow.command('route')[4:], ['recover', str(self.board), '--seconds', str(seconds),
                                                           '--output', str(flow.workspace/'route')])
                self.assertEqual(flow.timeout('route'), seconds+45)
                self.assertEqual(json.loads(flow.settings_bytes), settings)
                flow.ready.update(('route','review','choice')); flow.choice='accept'
                exported = flow.command('export'); expected=gui.export_validation_seconds(seconds)
                self.assertEqual(float(exported[exported.index('--seconds')+1]), expected)
                self.assertEqual(flow.timeout('export'), expected+45)
                self.assertEqual(json.loads((flow.workspace/'settings.json').read_bytes()), settings)

    def test_captured_settings_and_displayed_method_changes_refuse(self):
        flow = self.flow(); flow.check_request(self.request())
        with self.assertRaisesRegex(ValueError, 'Displayed source or settings differ'):
            flow.check_request(self.request(method='route'))
        (flow.workspace/'settings.json').write_text(json.dumps(dict(self.settings, seconds=120)))
        with self.assertRaisesRegex(ValueError, 'Captured settings changed'): flow.command('preview')

    def test_recovery_outcome_must_bind_actual_method_not_plain_route(self):
        good = dict(status='routing_accepted', accepted=True, source=str(self.board),
            source_hashes=json.loads(self.flow().files_json), strategy='native_validated_thermal_bridge',
            scope='whole_board_unlocked_routing', engine_profile='standard', adapter='both',
            budget_seconds=90, cpu_budget_seconds=90, metrics={'copper_layers':2})
        process=dict(cancel_requested=False,exit_code=0,log_truncated=False)
        for change in ({'strategy':None}, {'scope':'partial_completion'}, {'engine_profile':'tuned'},
                       {'adapter':'none'}, {'budget_seconds':120}, {'cpu_budget_seconds':120},
                       {'metrics':{'copper_layers':4}}, {}):
            flow=self.flow();flow.ready.add('preview')
            with self.subTest(change=change), patch.object(gui, 'read_record', return_value=dict(good, **change)):
                if change:
                    with self.assertRaisesRegex(ValueError, 'captured whole-method contract'):
                        flow.adopt('route',process,flow.workspace/'route.command.log')
                    self.assertEqual(flow.ready, {'preview'})
                else:
                    flow.adopt('route',process,flow.workspace/'route.command.log')
                    self.assertEqual(flow.ready, {'preview','route'})

    def test_cancelled_or_rejected_method_retains_incumbent_without_positive_state(self):
        flow=self.flow();flow.ready.add('preview')
        incumbent=flow.workspace/'route/incumbent/result.json';incumbent.parent.mkdir(parents=True)
        incumbent.write_bytes(b'owned retained incumbent proof\n')
        for process in (dict(cancel_requested=True,exit_code=0,log_truncated=False),
                        dict(cancel_requested=False,exit_code=-9,log_truncated=False),
                        dict(cancel_requested=False,exit_code=2,log_truncated=False)):
            with self.subTest(process=process), patch.object(gui, 'read_record', return_value=dict(
                    accepted=False,status='rejected',reason='bounded recovery found no valid candidate')):
                with self.assertRaises(ValueError): flow.adopt('route',process,flow.workspace/'route.command.log')
            self.assertEqual(flow.ready, {'preview'});self.assertIsNone(flow.choice)
            self.assertEqual(incumbent.read_bytes(),b'owned retained incumbent proof\n')
            self.assertFalse((flow.workspace/'export').exists())

    def test_explicit_reject_still_blocks_export(self):
        flow=self.flow();flow.ready.update(('preview','route','review'))
        with patch.object(gui, 'read_record', return_value=dict(choice_recorded=True,choice='reject',
                handoff_stage_policy='bounded-review60-choice60-v3',budget_seconds=60,cpu_budget_seconds=60,
                within_budget=True,wall_seconds=0.,total_cpu_seconds=0.)):
            flow.adopt('choice',dict(cancel_requested=False,exit_code=0,log_truncated=False),
                       flow.workspace/'choice.command.log',choice='reject')
        with self.assertRaisesRegex(ValueError, 'Only explicit acceptance'): flow.command('export')

    def test_method_callback_does_not_transform_incompatible_preset(self):
        window=SimpleNamespace(busy=False,method=Mock(),flow=object(),inspected=Mock(),status=Mock(),
            config=Mock(return_value=dict(self.settings,scope='partial_completion')),choices={'scope':Mock()},
            budget_label=Mock(),method_note=Mock(),buttons={'route':Mock()},refresh=Mock(),refused=Mock())
        window.method.GetSelection.return_value=2
        gt.window_method('method_changed')(window,Mock())
        window.config.assert_not_called();window.choices['scope'].SetSelection.assert_not_called()
        window.budget_label.SetLabel.assert_called_once_with('Whole recovery-method budget (seconds)')
        window.method_note.SetLabel.assert_called_once_with(gui.THERMAL_HELP)
        window.method.SetSelection.assert_not_called();window.refused.assert_not_called()

    def test_actual_action_captures_third_method_without_starting_worker(self):
        window=SimpleNamespace(busy=False,inspected=Mock(),board=Mock(),output=Mock(),
            config=Mock(return_value=self.settings),ack=Mock(),method=Mock(),refused=Mock())
        window.method.GetSelection.return_value=2
        request=Mock(side_effect=ValueError('stop before a worker can start'))
        gt.window_method('act',Request=request)(window,'preview')
        self.assertEqual(request.call_args.args[-1],'recover')
        window.refused.assert_called_once()

    def test_load_incompatible_recovery_preset_refuses_before_widget_writes(self):
        callback=gt.window_method('load_preset');wx=callback.__globals__['wx'];wx.FD_OPEN=1;wx.FD_FILE_MUST_EXIST=2
        window=SimpleNamespace(busy=False,method=Mock(),choices={'scope':Mock()},seconds=Mock(),nets=Mock(),
            refused=Mock(),values={'scope':[('Whole','whole_board_unlocked_routing')]})
        window.method.GetSelection.return_value=2
        def choose(dialog,loaded):
            try:loaded('/owned/preset.json')
            except Exception as exc:window.refused(str(exc))
        window.choose_path=choose
        with patch.object(pref,'load',return_value=object()),patch.object(pref,'resolve',return_value=dict(self.settings,scope='partial_completion')):
            callback(window,None)
        window.choices['scope'].SetSelection.assert_not_called();window.seconds.SetValue.assert_not_called()
        window.nets.SetValue.assert_not_called();window.refused.assert_called_once()

    def test_recovery_summary_names_whole_method_and_separate_export_allocation(self):
        text=gui.human_summary('preview',dict(status='preview',effective_preferences=dict(self.settings,seconds=420)),method='recover')
        self.assertIn('whole recovery-method budget 420 s',text)
        self.assertIn('incumbent, repair attempts and final validation',text)
        self.assertIn('one exposed board family',text);self.assertIn('120 s after acceptance, separate from recovery',text)
        self.assertNotIn('; routing budget 420',text)

    def test_progress_reads_bounded_recovery_phase_logs(self):
        flow=self.flow();base=flow.workspace/'route'
        incumbent=base/'incumbent/engine.log';incumbent.parent.mkdir(parents=True);incumbent.write_text('incumbent progress')
        repair=base/'recovery/thermal-geometry.log';repair.parent.mkdir();repair.write_text('repair progress')
        os.utime(incumbent,ns=(100,100));os.utime(repair,ns=(200,200))
        window=SimpleNamespace(busy=True,flow=flow,log=Mock())
        gt.window_method('tick')(window,None)
        window.log.SetValue.assert_called_once_with('recovery/thermal-geometry.log\nrepair progress')

    def test_progress_survives_phase_log_disappearing_after_file_check(self):
        flow=self.flow();phase=flow.workspace/'route/recovery/thermal-geometry.log'
        phase.parent.mkdir(parents=True);phase.write_text('temporary progress')
        window=SimpleNamespace(busy=True,flow=flow,log=Mock())
        original_stat=type(phase).stat
        def disappearing(path,*args,**kwargs):
            result=original_stat(path,*args,**kwargs)
            if path==phase and kwargs.get('follow_symlinks',True):
                phase.unlink()
            return result
        with patch.object(type(phase),'stat',autospec=True,side_effect=disappearing):
            gt.window_method('tick')(window,None)
        window.log.SetValue.assert_not_called()
        self.assertIs(window.flow,flow);self.assertTrue(window.busy)


if __name__=='__main__':unittest.main()
