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
        log = flow.workspace / 'preview.command.log'
        process = gt.run_cli_fixture(job, ['owned-preview-controller-fixture'], log, record)
        job.check_live(require_armed=True)
        job.adopt(flow, 'preview', process, log)
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

    def test_ready_preview_keeps_the_captured_board_visible(self):
        flow, job, record, window = self.completed_preview()
        window.in_workspace = True
        window.placement_scene = object()
        window.workspace_tabs = Mock()
        window.buttons = {'route': Mock()}
        gt.window_method('finished')(window, job, flow, 'preview', record, None)
        window.workspace_tabs.SetSelection.assert_called_once_with(0)
        window.buttons['route'].SetFocus.assert_called_once_with()

    def test_checked_export_keeps_the_reviewed_board_and_focuses_open(self):
        flow, job, _, window = self.export_case()
        window.in_workspace = True
        window.workspace_render = {'diagrams': {'F.Cu': object()}}
        window.workspace_tabs = Mock()
        window.review_caption = Mock()
        window.buttons = {'open_export': Mock()}
        gt.window_method('finished')(window, job, flow, 'export', flow.records['verify_export'], None)
        window.workspace_tabs.SetSelection.assert_called_once_with(0)
        window.review_caption.SetLabel.assert_called_once_with('Reviewed copper · Checked copy saved')
        window.buttons['open_export'].SetFocus.assert_called_once_with()

    def test_guided_route_review_requires_current_successful_job(self):
        for failure in (None, 'source', 'cancel', 'new job', 'reflow changed state'):
            with self.subTest(failure=failure):
                flow = self.flow()
                job = gui.CliJob()
                job.follow_up = 'review'
                record = dict(accepted=True, status='routing_accepted', source=str(self.board),
                              source_hashes=json.loads(flow.files_json))
                result = flow.workspace / 'route/result.json'
                result.parent.mkdir()
                result.write_text(json.dumps(record))
                log = flow.workspace / 'route.command.log'
                process = gt.run_cli_fixture(job, ['owned-route-fixture'], log, record)
                job.adopt(flow, 'route', process, log)
                window = self.window(flow, job)
                window.in_workspace = True
                window.act = Mock()
                window.workspace_tabs = Mock()
                window.findings_header = Mock()
                original = self.board.read_bytes()
                if failure == 'source':
                    self.board.write_bytes(original + b'changed')
                elif failure == 'cancel':
                    job.cancel()
                elif failure == 'new job':
                    window.job = gui.CliJob()
                elif failure == 'reflow changed state':
                    window.refresh.side_effect = lambda: setattr(window, 'flow', None)
                try:
                    gt.window_method('finished')(window, job, flow, 'route', record, None)
                finally:
                    if failure == 'source':
                        self.board.write_bytes(original)
                if failure is None:
                    window.act.assert_called_once_with('review')
                else:
                    window.act.assert_not_called()

    def test_guided_export_requires_the_exact_explicit_acceptance(self):
        from autorouter import handoff

        def save(stage, record):
            path = flow.workspace / stage / (stage if stage != 'route' else 'result')
            path = path.with_suffix('.json')
            path.parent.mkdir(exist_ok=True)
            path.write_text(json.dumps(record))
            return handoff.digest(path.read_bytes())

        for choice, follow_up, changed in (('accept', 'export', False), ('reject', 'export', False),
                                           ('accept', None, False), ('accept', 'export', True)):
            with self.subTest(choice=choice, follow_up=follow_up, changed=changed):
                flow = self.flow()
                route = {'candidate_sha256': 'a' * 64}
                review = {'receipt_sha256': save('route', route)}
                save('review', review)
                flow.records.update(route=route, review=review)
                flow.ready.update(('route', 'review'))
                binding = flow.check_displayed_review()
                record = dict(binding, choice=choice, choice_recorded=True,
                              review=str(flow.workspace / 'review/review.json'),
                              receipt=str(flow.workspace / 'route/result.json'),
                              handoff_stage_policy=handoff.STAGE_POLICY, within_budget=True,
                              budget_seconds=handoff.CHOICE_SECONDS, cpu_budget_seconds=handoff.CHOICE_SECONDS,
                              wall_seconds=1, total_cpu_seconds=1)
                choice_hash = save('choice', record)
                job = gui.CliJob()
                job.follow_up = follow_up
                log = flow.workspace / 'choice.command.log'
                process = gt.run_cli_fixture(job, ['owned-choice-fixture'], log, record)
                job.adopt(flow, 'choice', process, log, choice=choice, choice_binding=binding)
                if changed:
                    save('review', dict(review, modified=True))
                window = self.window(flow, job)
                window.in_workspace = True
                window.act = Mock()
                window.workspace_tabs = Mock()
                window.findings_header = Mock()
                gt.window_method('finished')(window, job, flow, 'choice', record, None)
                if choice == 'accept' and follow_up == 'export' and not changed:
                    window.act.assert_called_once_with('export')
                    command = flow.command('export')
                    self.assertEqual(command[command.index('--expected-choice-sha256') + 1], choice_hash)
                    inputs = {**binding, 'choice_sha256': choice_hash,
                              'review': record['review'], 'receipt': record['receipt']}
                    report = {'export_accepted': True, 'inputs': inputs}
                    save('export', {**report, 'inputs': {**inputs, 'choice_sha256': '0' * 64}})
                    with self.assertRaisesRegex(ValueError, 'acceptance shown'):
                        flow.adopt('export', process, log)
                    self.assertNotIn('export', flow.ready)
                    save('export', report)
                    self.assertEqual(flow.adopt('export', process, log), report)
                else:
                    window.act.assert_not_called()
                if choice == 'reject':
                    window.stage_heading, window.stage_details = Mock(), Mock()
                    gt.window_method('show_stage_summary')(window, flow.ready)
                    window.stage_heading.SetLabel.assert_called_once_with('Result rejected')

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

    def test_queued_delivery_refuses_changed_final_native_findings(self):
        from autorouter import review_export as ex
        flow, project, record = self.prepared()
        report = project.parents[1] / 'final-drc.json'
        report.write_text('{"violations": []}')
        flow.records['export']['export_evidence'] = ex.evidence(flow.workspace / 'export')
        (flow.workspace / 'export/export.json').write_text(json.dumps(flow.records['export']))
        job = self.export_job(record)
        flow.inspect_path('export', job=job)
        window = self.window(flow, job)
        report.write_text('{"violations": ["changed while delivery was queued"]}')
        gt.window_method('finished')(window, job, flow, 'export', record, None)
        self.assert_revoked(window, flow)
        self.assertIn('export changed during delivery', window.log.SetValue.call_args.args[0])

    def test_idle_cancel_preserves_current_export(self):
        flow, _project, _record = self.prepared()
        window = self.window(flow, None)
        window.busy = False
        gt.window_method('act')(window, 'cancel')
        self.assertIs(window.flow, flow)
        self.assertIn('verify_export', flow.ready)

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
