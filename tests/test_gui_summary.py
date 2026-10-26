"""Portable presentation controls; not GUI or Native qualification."""
import unittest
import tempfile
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch
from autorouter import gui
from tests.test_gui import window_method


class GuiSummaryTests(unittest.TestCase):
    def record(self):
        return dict(status='routing_accepted', accepted=True, source='/source/owned.kicad_pcb',
            candidate='/separate/candidate.kicad_pcb', invariants_unchanged=True,
            whole_project_drc_clean=False, protected_route_import={'matches': [{}]},
            tools={'implementation_sha256': {'private-internals.py': 'hidden-hash'}},
            metrics=dict(track_length_mm=43.242640687119284, vias=0, footprints=6, pads=6, zones=1, copper_layers=2),
            native=dict(opens=0, blocking=0, warnings=2, exclusions=1,
                ignored_checks=[dict(description='Ignored check description', key='ignored_key')],
                findings=[dict(severity='warning', type='field', description='First warning', items=[dict(description='Footprint J1', pos=dict(x=12.,y=10.))]),
                          dict(severity='warning', type='field', description='Last warning', items=[])]))

    def test_route_metrics_all_findings_and_ignored_without_internal_dump(self):
        text = gui.human_summary('route', self.record(), receipt_path='/separate/result.json')
        for expected in ('43.242641 mm', '0 vias', '0 opens; 0 blocking; 2 warnings; 1 exclusions',
                         'Protected route items retained: 1', 'First warning', 'Last warning',
                         'Footprint J1', 'Ignored check description', '/separate/result.json', 'not DRC-clean'):
            self.assertIn(expected, text)
        self.assertNotIn('hidden-hash', text); self.assertNotIn('private-internals.py', text)

    def test_preview_scope_protection_settings_and_no_native_claim(self):
        text = gui.human_summary('preview', dict(status='preview', source='/source/a.kicad_pcb',
            existing_route_items=10, protected_route_items=3, rerouted_route_items=7,
            effective_preferences=dict(scope='partial_completion', profile='standard', adapter='both',
                seconds=120, layers=['F.Cu','B.Cu'], scoring_preference=None)))
        for expected in ('preserve all existing routing', 'profile standard', 'budget 120 s',
                         'protected: 3', 'to reroute: 7', 'Native routing validation has not run'):
            self.assertIn(expected, text)

    def test_improve_displays_its_checked_protection_count(self):
        for count in (0, 1, 4):
            record = self.record(); record.pop('protected_route_import')
            record.update(strategy='native_validated_zone_net_pruning', protected_routes=count)
            self.assertIn('Protected route items retained: ' + str(count),
                          gui.human_summary('route', record, method='improve'))
        for count in (True, -1, 1.0, None):
            record['protected_routes'] = count
            self.assertNotIn('Protected route items retained:',
                             gui.human_summary('route', record, method='improve'))
        record.update(protected_routes=1, invariants_unchanged=False)
        self.assertNotIn('Protected route items retained:',
                         gui.human_summary('route', record, method='improve'))

    def test_large_findings_explicitly_report_omissions_and_full_path(self):
        record = self.record(); record['native']['findings'] *= 100
        with patch.object(gui, 'SUMMARY_LIMIT', 1000):
            text = gui.human_summary('route', record, receipt_path='/full/result.json')
        self.assertIn('200 retained', text)
        self.assertIn('not displayed because of the UI text bound', text)
        self.assertIn('ALL entries remain', text); self.assertIn('/full/result.json', text)

    def test_review_choice_export_separate_project_and_intent(self):
        for stage in ('review','choice','export'):
            with self.subTest(stage=stage):
                record = dict(status='disposition_recorded', choice='accept', project_file='/separate/owned.kicad_pro')
                text = gui.human_summary(stage, record)
                self.assertIn('/separate/owned.kicad_pro', text)
                self.assertIn('no live-board application or physical/electrical approval', text)
                if stage == 'choice': self.assertIn('accept. This is not PCB certification', text)


    def test_actual_review_callback_points_omitted_findings_to_route_receipt(self):
        route = self.record(); route['native']['findings'] *= 100
        review = dict(status='ready_for_manual_review', project_file='/separate/review/project/owned.kicad_pro',
                      receipt='/separate/route/result.json')
        # Actual review records have no Native body; the callback inherits route findings.
        flow = SimpleNamespace(workspace=Path('/separate'), records={'route': route, 'review': review})
        job = gui.CliJob()
        window = SimpleNamespace(job=job, busy=True, flow=flow, inspected=Mock(),
            status=Mock(), log=Mock(), refresh=Mock(), closing=False)
        with patch.object(gui, 'SUMMARY_LIMIT', 1000):
            window_method('finished')(window, job, flow, 'review', review, None)
        text = window.log.SetValue.call_args.args[0]
        self.assertIn('Full workflow receipt: /separate/review/review.json', text)
        self.assertIn('Full findings receipt: /separate/route/result.json', text)
        self.assertIn('200 retained', text)
        self.assertTrue(text.endswith('Open it before completing review: /separate/route/result.json'))

    def test_choice_discloses_unchanged_board_and_review_metadata_changes(self):
        record = dict(status='disposition_recorded', choice='accept',
            candidate_board_unchanged=True, review_project_matches_recorded_candidate=False,
            review_project_changes={'added': ['history'], 'removed': [], 'changed': ['project', 'local']})
        text = gui.human_summary('choice', record)
        self.assertIn('Reviewed PCB: unchanged from the validated candidate', text)
        self.assertIn('1 added; 0 removed; 2 changed files', text)
        self.assertIn('original source rules and settings; review-only changes are not adopted', text)
        self.assertNotIn("['history']", text)

    def test_idle_budget_or_source_edit_replaces_completed_export_summary(self):
        for edited in ('budget', 'source'):
            with self.subTest(edited=edited):
                workspace = Path('/separate/previous90')
                exported = dict(self.record(), status='export_validated')
                flow = SimpleNamespace(workspace=workspace, method='improve',
                    settings_bytes=json.dumps(dict(gui.pref.DEFAULTS, profile='tuned', seconds=90)),
                    records={'route': self.record(), 'export': exported},
                    ready={'preview', 'route', 'review', 'choice', 'export', 'verify_export'}, choice='accept')
                names = ('preview','route','review','cancel','open_preview','open_review',
                         'accept','reject','export','open_export')
                job = gui.CliJob()
                window = SimpleNamespace(flow=flow, job=job, busy=True, input_generation=7,
                    status=Mock(), log=Mock(), inspected=Mock(), closing=False,
                    board=Mock(), seconds=Mock(), output=Mock(), ack=Mock(), edit_controls=[],
                    buttons={name: Mock() for name in names})
                window.refresh = lambda: window_method('refresh')(window)
                window_method('finished')(window, job, flow, 'export', exported, None)
                self.assertIn('export completed', window.status.SetLabel.call_args.args[0])
                self.assertIn('budget 90 s', window.log.SetValue.call_args.args[0])
                for name in ('open_preview', 'open_review', 'open_export'):
                    window.buttons[name].Enable.assert_called_with(True)
                if edited == 'budget': window.seconds.GetValue.return_value = '91'
                else: window.board.GetValue.return_value = '/different/board.kicad_pcb'
                event = Mock()
                window_method('changed')(window, event)
                self.assertIsNone(window.flow); self.assertIsNone(window.job)
                self.assertEqual(window.input_generation, 8)
                window.inspected.SetValue.assert_called_with(False)
                self.assertEqual(window.status.SetLabel.call_args.args[0],
                    'Inputs changed. Preview the saved project to start a new job.')
                shown = window.log.SetValue.call_args.args[0]
                self.assertIn('Previous findings are no longer current', shown)
                self.assertIn('Retained workspaces were not deleted', shown)
                self.assertIn('Previous workspace: ' + str(workspace), shown)
                self.assertNotIn('budget 90 s', shown); self.assertNotIn('First warning', shown)
                for name in ('open_preview', 'open_review', 'open_export'):
                    window.buttons[name].Enable.assert_called_with(False)
                window.buttons['preview'].Enable.assert_called_with(True)
                self.assertIs(flow.records['export'], exported)
                self.assertEqual(flow.choice, 'accept'); self.assertIn('verify_export', flow.ready)
                event.Skip.assert_called_once_with()

    def test_input_event_while_busy_keeps_active_flow_and_output(self):
        flow = object(); job = object()
        window = SimpleNamespace(flow=flow, job=job, busy=True, input_generation=11,
            status=Mock(), log=Mock(), inspected=Mock(), refresh=Mock())
        event = Mock()
        window_method('changed')(window, event)
        self.assertIs(window.flow, flow); self.assertIs(window.job, job)
        self.assertTrue(window.busy); self.assertEqual(window.input_generation, 12)
        window.status.SetLabel.assert_not_called(); window.log.SetValue.assert_not_called()
        window.inspected.SetValue.assert_not_called()
        window.refresh.assert_called_once_with(); event.Skip.assert_called_once_with()

    def test_open_dispatch_displays_checking_before_the_worker_starts(self):
        for kind, label in (('preview', 'preview'), ('review', 'review project'), ('export', 'export')):
            with self.subTest(kind=kind):
                flow = SimpleNamespace(inspect_path=Mock())
                window = SimpleNamespace(flow=flow, job=None, busy=False, status=Mock(),
                    refresh=Mock(), refused=Mock())
                def starting():
                    self.assertTrue(window.busy)
                    self.assertIsInstance(window.job, gui.CliJob)
                    self.assertEqual(window.status.SetLabel.call_args.args[0],
                        'Checking retained ' + label + ' before opening. Cancel remains available.')
                with patch.object(gui.threading, 'Thread') as worker:
                    worker.return_value.start.side_effect = starting
                    window_method('act')(window, 'open_' + kind)
                worker.return_value.start.assert_called_once_with()
                flow.inspect_path.assert_not_called()
                window.refused.assert_not_called()

    def test_successful_open_restores_findings_after_inspection_progress_tick(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp).resolve()
            route_dir = workspace / 'route'; route_dir.mkdir()
            (route_dir / 'final-drc.log').write_text('Found 2 schematic parity issues\n')
            review = dict(status='ready_for_manual_review', project_file=str(workspace / 'review/project/owned.kicad_pro'))
            exported = dict(self.record(), status='export_validated', project_file=str(workspace / 'export/candidate/owned.kicad_pro'))
            flow = SimpleNamespace(workspace=workspace, records={'route': self.record(), 'review': review, 'export': exported},
                fresh=Mock(), check_open_export_material=Mock())
            for kind in ('preview', 'review', 'export'):
                with self.subTest(kind=kind):
                    stage = 'export' if kind == 'export' else 'review'
                    job = gui.CliJob()
                    window = SimpleNamespace(job=job, busy=True, flow=flow, inspected=Mock(),
                        status=Mock(), log=Mock(), refresh=Mock(), closing=False, refused=Mock())
                    window_method('finished')(window, job, flow, stage, flow.records[stage], None)
                    completed = window.log.SetValue.call_args.args[0]
                    self.assertIn('First warning', completed)
                    window.busy = True; window.job = gui.CliJob()
                    window_method('tick')(window, None)
                    self.assertIn('final-drc.log\nFound 2 schematic parity issues', window.log.SetValue.call_args.args[0])
                    target = workspace / 'review/preview.html' if kind == 'preview' else Path(flow.records[stage]['project_file'])
                    with patch('webbrowser.open'), patch.object(gui.subprocess, 'Popen'):
                        window_method('opened')(window, kind, target, None)
                    self.assertEqual(window.log.SetValue.call_args.args[0], completed)
                    self.assertIn('Last warning', completed); self.assertIn('Ignored check description', completed)
                    self.assertFalse(window.busy); self.assertIsNone(window.job)
                    label = {'preview': 'Preview', 'review': 'Review project', 'export': 'Checked export'}[kind]
                    self.assertEqual(window.status.SetLabel.call_args.args[0],
                        label + ' open requested. Separate workspace: ' + str(workspace))
                    window.refused.assert_not_called()
                    count = window.log.SetValue.call_count
                    window_method('tick')(window, None)
                    self.assertEqual(window.log.SetValue.call_count, count)

    def test_completed_stages_disabled_but_retained_review_and_export_openers_work(self):
        names = ('preview','route','review','cancel','open_preview','open_review','accept','reject','export','open_export')
        ready = {'preview','route','review','choice','export','verify_export'}
        window = SimpleNamespace(flow=SimpleNamespace(ready=ready,choice='accept'),busy=False,
            buttons={name:Mock() for name in names},board=Mock(),output=Mock(),ack=Mock(),inspected=Mock(),edit_controls=[])
        window_method('refresh')(window)
        for name in ('route','review','cancel','accept','reject','export'):
            window.buttons[name].Enable.assert_called_once_with(False)
        for name in ('preview','open_preview','open_review','open_export'):
            window.buttons[name].Enable.assert_called_once_with(True)


if __name__ == '__main__': unittest.main()
