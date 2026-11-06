"""Queued displayed-request guards using actual shared workflows, without Native."""
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from autorouter import gui
from tests import test_gui as gt
from tests import test_gui_export_inspection as export_fixture


class DisplayedRequestAdoptionTests(unittest.TestCase):
    setUp = gt.GuiWorkflowTests.setUp
    request = gt.GuiWorkflowTests.request
    flow = gt.GuiWorkflowTests.flow
    prepared = export_fixture.ExportInspectionTests.prepared
    export_job = export_fixture.ExportInspectionTests.job

    def window(self, flow, job, *, source_guard=None):
        window = SimpleNamespace(**gt.displayed_inputs(self.request(source_guard=source_guard)),
            flow=flow, job=job, busy=True, closing=False, input_generation=7,
            inspected=Mock(), log=Mock(), status=Mock(), refresh=Mock(), timer=Mock(), Destroy=Mock())
        window.refused = lambda error: gt.window_method('refused')(window, error)
        return window

    def completed_preview(self):
        flow = self.flow(); job = gui.CliJob()
        record = dict(status='preview', static_preflight_passed=True, source=str(self.board),
            source_sha256=json.loads(flow.files_json)[self.board.name], effective_preferences=self.settings)
        log = flow.workspace / 'preview.command.log'; log.write_text(json.dumps(record))
        job.adopt(flow, 'preview', dict(exit_code=0, cancel_requested=False, log_truncated=False), log)
        return flow, job, record, self.window(flow, job)

    def export_case(self, *, source_guard=None):
        flow, project, record = self.prepared(source_guard=source_guard)
        job = self.export_job(record)
        target = flow.inspect_path('export', job=job)
        return flow, job, target, self.window(flow, job, source_guard=source_guard)

    def assert_revoked(self, window, flow):
        self.assertIsNone(window.flow); self.assertIsNone(window.job)
        self.assertFalse(window.busy); self.assertFalse(flow.ready); self.assertFalse(flow.records)
        self.assertIsNone(flow.choice)
        self.assertIn('No positive state adopted', window.log.SetValue.call_args.args[0])
        self.assertNotIn(' completed.', window.status.SetLabel.call_args.args[0])

    def alter(self, window, field):
        if field == 'board':
            other = self.root / 'other.kicad_pcb'; other.write_bytes(b'owned alternate path')
            window.board.SetValue(str(other))
        elif field == 'output':
            other = self.root / 'other-output'; other.mkdir(exist_ok=True)
            window.output.SetValue(str(other))
        elif field == 'ack': window.ack.SetValue(False)
        elif field == 'method': window.method.SetSelection(1)
        else:
            values = dict(scope='partial_completion', seconds=121, profile='tuned', adapter='graphics',
                          layers=['F.Cu'], scoring_preference='via_low')
            window.config.return_value[field] = values[field]

    def test_actual_popup_commits_without_event_and_cannot_publish_old_preview(self):
        flow, job, record, window = self.completed_preview()
        # Exercise the actual config callback reading a choice, not merely a
        # synthetic config result. No changed()/generation event is delivered.
        choice = Mock(); choice.GetSelection.return_value = 0
        choice.SetSelection.side_effect = lambda value: setattr(choice.GetSelection, 'return_value', value)
        window.choices = {'scope': choice}
        window.values = {'scope': [('Reroute', 'whole_board_unlocked_routing'), ('Keep copper', 'partial_completion')]}
        window.seconds = Mock(); window.seconds.GetValue.return_value = str(self.settings['seconds'])
        window.nets = Mock(); window.nets.GetValue.return_value = ''
        window.config = lambda: gt.window_method('config')(window)
        self.assertEqual(window.config()['scope'], json.loads(flow.settings_bytes)['scope'])
        choice.SetSelection(1)
        gt.window_method('finished')(window, job, flow, 'preview', record, None)
        self.assertEqual(window.input_generation, 7)
        self.assert_revoked(window, flow)
        self.assertIn('Displayed source or settings differ', window.log.SetValue.call_args.args[0])

    def test_all_displayed_request_fields_are_checked_before_completed_adoption(self):
        for field in ('board', 'output', 'ack', 'method', 'scope', 'seconds', 'profile', 'adapter', 'layers', 'scoring_preference'):
            with self.subTest(field=field):
                flow, job, record, window = self.completed_preview(); self.alter(window, field)
                gt.window_method('finished')(window, job, flow, 'preview', record, None)
                self.assert_revoked(window, flow)
                self.assertEqual(window.input_generation, 7)

    def test_matching_displayed_request_retains_completed_preview(self):
        flow, job, record, window = self.completed_preview()
        with patch.object(flow, 'check_request', wraps=flow.check_request) as checker:
            gt.window_method('finished')(window, job, flow, 'preview', record, None)
        checker.assert_called_once_with(self.request())
        self.assertIs(window.flow, flow); self.assertIn('preview', flow.ready)
        self.assertIn('preview completed.', window.status.SetLabel.call_args.args[0])
        self.assertIn('Reroute unlocked copper', window.log.SetValue.call_args.args[0])

    def test_queued_open_checks_displayed_values_even_without_change_event(self):
        for field in ('board', 'output', 'ack', 'method', 'scope', 'seconds'):
            with self.subTest(field=field):
                flow, job, target, window = self.export_case(); self.alter(window, field)
                with patch.object(gui.subprocess, 'Popen') as opener:
                    gt.window_method('opened')(window, 'export', target, None)
                opener.assert_not_called(); self.assert_revoked(window, flow)
                self.assertEqual(window.input_generation, 7)

    def test_displayed_request_is_checked_after_final_export_material_and_origin_reads(self):
        for phase in ('material', 'origin'):
            with self.subTest(phase=phase):
                state = SimpleNamespace(armed=False, window=None, calls=0)
                def verify_origin():
                    if state.armed:
                        state.calls += 1
                        state.window.config.return_value['scope'] = 'partial_completion'
                guard = gui.SourceGuard(self.board, verify_origin) if phase == 'origin' else None
                flow, job, target, window = self.export_case(source_guard=guard); state.window = window
                read_material = flow.check_open_export_material
                def final_material():
                    read_material()
                    if phase == 'material': window.config.return_value['scope'] = 'partial_completion'
                    else: state.armed = True
                with patch.object(flow, 'check_open_export_material', side_effect=final_material), \
                        patch.object(gui.subprocess, 'Popen') as opener:
                    gt.window_method('opened')(window, 'export', target, None)
                opener.assert_not_called(); self.assert_revoked(window, flow)
                if phase == 'origin': self.assertEqual(state.calls, 1)

    def test_ordinary_open_final_cancel_and_close_win_after_material_read(self):
        for phase in ('cancel', 'close'):
            with self.subTest(phase=phase):
                flow, job, target, window = self.export_case()
                material = flow.check_open_export_material
                def last_read():
                    material()
                    if phase == 'cancel': job.cancel()
                    else: window.closing = True
                with patch.object(flow, 'check_open_export_material', side_effect=last_read), \
                        patch.object(gui.subprocess, 'Popen') as opener:
                    gt.window_method('opened')(window, 'export', target, None)
                opener.assert_not_called(); self.assert_revoked(window, flow)
                if phase == 'close': window.Destroy.assert_called_once_with()

    def test_finished_prior_error_cancel_or_close_does_not_read_current_controls(self):
        for phase in ('error', 'cancel', 'close'):
            with self.subTest(phase=phase):
                flow, job, record, window = self.completed_preview()
                window.config.side_effect = AssertionError('Current config must not hide an existing failure')
                if phase == 'cancel': job.cancel()
                if phase == 'close': window.closing = True
                gt.window_method('finished')(window, job, flow, 'preview', record,
                    'retained original failure' if phase == 'error' else None)
                window.config.assert_not_called(); self.assert_revoked(window, flow)
                if phase == 'error': self.assertIn('retained original failure', window.log.SetValue.call_args.args[0])

    def assert_finished_material_refused(self, field):
        flow, job, record, window = self.completed_preview()
        self.assertIsNone(flow.source_guard)  # Ordinary routing needs this fence too.
        target = self.board if field == 'source' else flow.workspace / 'settings.json'
        old = target.read_bytes()
        try:
            if field == 'source': target.write_bytes(b'owned changed source after completed child')
            else: target.write_text(json.dumps(dict(self.settings, seconds=121)))
            gt.window_method('finished')(window, job, flow, 'preview', record, None)
            self.assert_revoked(window, flow)
            self.assertIn('changed', window.log.SetValue.call_args.args[0])
            self.assertEqual(window.input_generation, 7)
        finally: target.write_bytes(old)

    def test_ordinary_queued_finish_refuses_changed_source_material(self):
        self.assert_finished_material_refused('source')

    def test_ordinary_queued_finish_refuses_changed_captured_settings_material(self):
        self.assert_finished_material_refused('settings')

    def test_missing_invalid_or_detached_inputs_refuse_without_production_fallback(self):
        for phase in ('missing_config', 'invalid_config', 'invalid_method', 'guard'):
            with self.subTest(phase=phase):
                flow, job, record, window = self.completed_preview()
                if phase == 'missing_config': del window.config
                if phase == 'invalid_config': window.config.side_effect = ValueError('invalid displayed settings')
                if phase == 'invalid_method': window.method.SetSelection(-1)
                if phase == 'guard': window.source_guard = gui.SourceGuard(self.board, lambda: None)
                gt.window_method('finished')(window, job, flow, 'preview', record, None)
                self.assert_revoked(window, flow)


if __name__ == '__main__': unittest.main()
