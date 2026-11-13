"""Portable UI-controller guards, not wx/Native or GUI qualification."""
import ast
import io
import json
from pathlib import Path
import signal
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from autorouter import gui, preferences as pref, pipeline as p


def run_cli_fixture(job, argv, log, record, *, timeout=90, code=0, hook=None):
    """Run the actual controller through its Popen seam; no Native proof claimed."""
    child = Mock(); child.returncode = None
    child.stdout = io.BufferedReader(io.BytesIO((json.dumps(record)+'\n').encode()))
    child.poll.side_effect = lambda: child.returncode
    def wait():
        child.returncode = code
        return code
    child.wait.side_effect = wait
    with patch.object(gui.subprocess, 'Popen', return_value=child):
        # A caller may wrap job.run for command assertions; never recurse into it.
        process = gui.CliJob.run(job, argv, log, timeout=timeout)
    if hook: hook(job)
    return process


def warning_challenge(workspace, *, seconds=30):
    """Owned wire/display packet, including clock binding; not Native validation."""
    from autorouter import review_export as ex
    previous = dict(type='connection_width', severity='warning', description='Owned software fixture warning', items=[
        dict(uuid='11111111-1111-4111-8111-111111111111', description='Via [SIG] on F.Cu - B.Cu', pos=dict(x=0., y=0.)),
        dict(uuid='22222222-2222-4222-8222-222222222222', description='Track [SIG] on B.Cu, length 0.2000 mm', pos=dict(x=1., y=0.))])
    fresh = json.loads(json.dumps(previous))
    fresh['items'][1].update(uuid='33333333-3333-4333-8333-333333333333', pos=dict(x=2., y=0.))
    native = lambda finding:dict(opens=0, blocking=0, warnings=1, exclusions=0, ignored_checks=[], findings=[finding])
    review = ex.warning_review_delta(native(previous), native(fresh))
    review['copper_witness'] = {'software_fixture_only':True}
    sent = gui.elapsed_time()
    pending = dict(schema=1, kind='live-warning-review-pending-v1', policy=ex.WARNING_REVIEW_POLICY,
        export_accepted=False, resumable_after_exit=False, nonce='c'*32,
        candidate_sha256=ex._warning_digest({'software_candidate_only':True}),
        native_report_sha256=ex._warning_digest(native(fresh)), clock_policy=ex.ELAPSED_CLOCK_POLICY,
        sent_elapsed_time=sent, expires_elapsed_time=sent+seconds,
        budget_seconds=max(seconds, ex.MIN_SECONDS), sent_wall_seconds=0., warning_review=review)
    path = Path(workspace)/'export/warning-review.json'; path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(pending))
    event = dict(kind='autorouter.warning-review-required.v1', pending=str(path), pending_sha256=p.sha(path),
        delta_sha256=ex._warning_digest(review), nonce=pending['nonce'], remaining_seconds=seconds,
        warning_review={key:review[key] for key in ('policy','delta','findings_equivalent','review_text','copper_witness')})
    event.update({key:pending[key] for key in ('clock_policy','sent_elapsed_time','expires_elapsed_time',
                                             'candidate_sha256','native_report_sha256')})
    return event


def window_method(name, **overrides):
    """Execute the actual wx callback body without importing or launching wx."""
    tree = ast.parse(Path(gui.__file__).read_text())
    main = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'create_window')
    window = next(node for node in main.body if isinstance(node, ast.ClassDef) and node.name == 'Window')
    function = next(node for node in window.body if isinstance(node, ast.FunctionDef) and node.name == name)
    namespace = dict(vars(gui), wx=Mock(OK=1,ICON_ERROR=16), **overrides)
    request_helper = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == '_window_request')
    # Keep the real shared helper in this test namespace too, so explicit
    # Request constructor traps still prevent an action from launching work.
    exec(compile(ast.fix_missing_locations(ast.Module(body=[request_helper, function], type_ignores=[])),
                 str(Path(gui.__file__)), 'exec'), namespace)
    return namespace[name]


def displayed_inputs(request):
    """Explicit current controls for callbacks; never bypass their real guard.

    Tests can change a value without emitting EVT_TEXT/EVT_CHOICE, reproducing
    native widgets whose visible value changed before a queued callback.
    """
    if type(request) is not gui.Request:
        raise TypeError('An explicit GUI Request is required by the test fixture.')

    def value_control(value):
        control = Mock(spec=['GetValue', 'SetValue', 'Enable'])
        control.GetValue.return_value = value
        control.SetValue.side_effect = lambda new: setattr(control.GetValue, 'return_value', new)
        return control

    method = Mock(spec=['GetSelection', 'SetSelection', 'Enable'])
    method.GetSelection.return_value = gui.METHODS.index(request.method)
    method.SetSelection.side_effect = lambda new: setattr(method.GetSelection, 'return_value', new)
    return dict(board=value_control(request.board), output=value_control(request.output_parent),
                ack=value_control(request.saved_closed), method=method,
                config=Mock(return_value=json.loads(request.settings_json)), source_guard=request.source_guard)


class GuiWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.source = self.root / 'source'; self.source.mkdir()
        self.output = self.root / 'output'; self.output.mkdir()
        self.board = self.source / 'owned.kicad_pcb'
        for suffix in ('.kicad_pcb', '.kicad_pro', '.kicad_sch'):
            self.board.with_suffix(suffix).write_bytes(b'owned synthetic source\n')
        self.settings = dict(pref.DEFAULTS)

    def request(self, **kw):
        return gui.Request(**dict(board=str(self.board), output_parent=str(self.output),
            settings_json=json.dumps(self.settings), saved_closed=True, **kw))

    def flow(self):
        return self.request().prepare()

    def test_literal_closed_ack_and_complete_project(self):
        for ack in (False, 1, 'yes'):
            with self.subTest(ack=ack), self.assertRaises(ValueError):
                gui.Request(str(self.board), str(self.output), json.dumps(self.settings), ack).prepare()
        self.board.with_suffix('.kicad_sch').unlink()
        with self.assertRaises((ValueError, FileNotFoundError)):
            self.flow()

    def test_output_must_be_outside_source_and_source_unchanged(self):
        with self.assertRaises(ValueError):
            gui.Request(str(self.board), str(self.source), json.dumps(self.settings), True).prepare()
        flow = self.flow()
        self.assertNotIn(self.source, flow.workspace.parents)
        self.assertEqual(self.board.read_bytes(), b'owned synthetic source\n')
        flow.fresh()

    def test_source_settings_and_output_identity_staleness(self):
        for mutation in ('source', 'settings', 'identity'):
            with self.subTest(mutation=mutation):
                flow = self.flow()
                if mutation == 'source':
                    target = self.board.with_suffix('.kicad_pro'); old = target.read_bytes()
                    target.write_bytes(b'changed')
                elif mutation == 'settings':
                    (flow.workspace / 'settings.json').write_bytes(b'{}')
                else:
                    moved = flow.workspace.with_name(flow.workspace.name + '-old')
                    flow.workspace.rename(moved); flow.workspace.mkdir()
                with self.assertRaises((ValueError, RuntimeError, p.Rejected)):
                    flow.fresh()
                if mutation == 'source': target.write_bytes(old)

    def test_runtime_witness_change_refuses_before_queued_open(self):
        from autorouter import handoff
        flow=self.flow()
        changed={**flow.runtime_hashes,'owned-selected-manifest':'changed'}
        with patch.object(handoff,'runtime_inventory',return_value=changed):
            with self.assertRaisesRegex(ValueError,'Routing runtime changed'):
                flow.fresh()

    def test_exact_cli_stages_and_reject_blocks_export(self):
        flow = self.flow()
        argv = flow.command('preview')
        self.assertEqual(argv[1:5], ['-B', '-m', 'autorouter', 'preview'])
        self.assertEqual(argv[5], str(self.board))
        with self.assertRaises(ValueError): flow.command('route')
        flow.ready.add('preview')
        self.assertIn('route', flow.command('route'))
        flow.ready.update(('route', 'review', 'choice')); flow.choice = 'reject'
        with self.assertRaises(ValueError): flow.command('export')

    def test_changed_displayed_request_refused(self):
        flow = self.flow(); flow.check_request(self.request())
        settings = dict(self.settings, seconds=121)
        changed = gui.Request(str(self.board), str(self.output), json.dumps(settings), True)
        with self.assertRaises(ValueError): flow.check_request(changed)

    def test_cancelled_exit_zero_cannot_adopt(self):
        flow = self.flow(); log = flow.workspace / 'preview.command.log'
        log.write_text('{}')
        for process in ({'cancel_requested': True, 'exit_code': 0, 'log_truncated': False},
                        {'cancel_requested': False, 'exit_code': 0, 'log_truncated': True},
                        {'cancel_requested': False, 'exit_code': 2, 'log_truncated': False}):
            with self.subTest(process=process), self.assertRaises(ValueError):
                flow.adopt('preview', process, log)
        self.assertFalse(flow.ready)

    def test_preview_identity_and_route_refusal(self):
        flow = self.flow(); log = flow.workspace / 'preview.command.log'
        good = dict(status='preview', static_preflight_passed=True, source=str(self.board),
                    source_sha256=json.loads(flow.files_json)[self.board.name])
        process = dict(cancel_requested=False, exit_code=0, log_truncated=False)
        log.write_text(json.dumps(dict(good, source_sha256='0'*64)))
        with self.assertRaises(ValueError): flow.adopt('preview', process, log)
        log.write_text(json.dumps(good)); flow.adopt('preview', process, log)
        with patch.object(gui, 'read_record', return_value=dict(accepted=False, status='rejected')):
            with self.assertRaises(ValueError): flow.adopt('route', process, log)
        self.assertEqual(flow.ready, {'preview'})

    def test_external_review_path_and_unchecked_export_refused(self):
        flow = self.flow(); flow.ready.add('review')
        flow.records['review'] = {'project_file': str(self.board.with_suffix('.kicad_pro'))}
        with self.assertRaises(ValueError): flow.inspect_path('review')
        with self.assertRaises(ValueError): flow.inspect_path('export')

    def test_improve_uses_shared_scope_and_minimum_budget(self):
        with patch('autorouter.strategy.pruning_scope') as scope:
            request = gui.Request(str(self.board), str(self.output), json.dumps(self.settings), True, 'improve')
            flow = request.prepare(); scope.assert_called_once_with(self.settings)
            flow.ready.add('preview')
            self.assertEqual(flow.command('route')[4], 'improve')


class CliJobTests(unittest.TestCase):
    def test_real_success_closes_captured_output_after_reaping(self):
        with tempfile.TemporaryDirectory() as tmp:
            job = gui.CliJob()
            result = job.run([sys.executable, '-B', '-c', 'print("owned output")'],
                             Path(tmp) / 'run.log', timeout=5)
            self.assertEqual(result['exit_code'], 0)
            self.assertIsNotNone(job.process.poll())
            self.assertTrue(job.process.stdout.closed)

    def test_late_cancel_before_and_during_adoption_rejects_old_snapshot(self):
        temporary = tempfile.TemporaryDirectory(); self.addCleanup(temporary.cleanup)
        for when in ('before', 'during'):
            with self.subTest(when=when):
                job = gui.CliJob()
                process = run_cli_fixture(job, ['owned-controller-fixture'], Path(temporary.name)/(when+'.log'), {'status':'preview'})
                job.check_live(require_armed=True)
                flow = SimpleNamespace(ready=set(), records={}, choice=None)
                def adopt(*args, **kw):
                    flow.ready.add('preview'); flow.records['preview'] = {'status': 'preview'}
                    job.cancel()
                    return flow.records['preview']
                flow.adopt = Mock(side_effect=adopt)
                if when == 'before': job.cancel()
                with self.assertRaises(ValueError):
                    job.adopt(flow, 'preview', process, Path('not-read'))
                self.assertFalse(flow.ready); self.assertFalse(flow.records)
                if when == 'before': flow.adopt.assert_not_called()
                else: flow.adopt.assert_called_once()

    def test_queued_finish_checks_live_cancel_and_discards_ready_state(self):
        temporary = tempfile.TemporaryDirectory(); self.addCleanup(temporary.cleanup)
        job = gui.CliJob()
        run_cli_fixture(job, ['owned-controller-fixture'], Path(temporary.name)/'finished.log', {'status':'preview'})
        job.check_live(require_armed=True); job.cancel()
        flow = SimpleNamespace(ready={'preview'}, records={'preview': {}}, choice='accept')
        window = SimpleNamespace(job=job, busy=True, flow=flow, inspected=Mock(),
            status=Mock(), log=Mock(), refresh=Mock(), closing=False)
        window.refused = lambda error: window_method('refused')(window, error)
        window_method('finished')(window, job, flow, 'preview', {'status': 'preview'}, None)
        self.assertIsNone(window.flow); self.assertIsNone(window.job)
        self.assertFalse(flow.ready); self.assertFalse(flow.records); self.assertIsNone(flow.choice)
        window.inspected.SetValue.assert_called_with(False)
        shown = window.log.SetValue.call_args.args[0]
        self.assertIn('No positive state adopted', shown)
        self.assertNotIn('Status: preview', shown)

    def test_new_preview_and_review_reset_prior_inspection_acknowledgement(self):
        for action in ('preview', 'review'):
            with self.subTest(action=action):
                inspected = Mock(); inspected.GetValue.return_value = True
                window = SimpleNamespace(busy=False, inspected=inspected, board=Mock(),
                    output=Mock(), config=Mock(return_value=dict(pref.DEFAULTS)), ack=Mock(), method=Mock(), refused=Mock())
                window.method.GetSelection.return_value = 0
                # Stop after the real callback reset, before creating or launching work.
                callback = window_method('act', Request=Mock(side_effect=ValueError('stop before worker')))
                callback(window, action)
                inspected.SetValue.assert_called_once_with(False)

    def test_path_edits_clear_source_ack_and_gate_preview_inspect_until_rechecked(self):
        tree = ast.parse(Path(gui.__file__).read_text())
        main = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'create_window')
        window_class = next(node for node in main.body if isinstance(node, ast.ClassDef) and node.name == 'Window')
        init = next(node for node in window_class.body if isinstance(node, ast.FunctionDef) and node.name == '__init__')
        # Exercise the actual constructor binding, not just an unbound callback.
        binding = next(node for node in init.body if isinstance(node, ast.For)
                       and isinstance(node.iter, ast.Tuple)
                       and [getattr(item, 'attr', None) for item in node.iter.elts] == ['board', 'output'])
        for edited in ('board', 'output'):
            for action in ('preview', 'inspect'):
                with self.subTest(edited=edited, action=action):
                    ack = Mock(); ack.GetValue.return_value = True
                    ack.SetValue.side_effect = lambda value: setattr(ack.GetValue, 'return_value', value)
                    window = SimpleNamespace(busy=False, chooser=None, input_generation=0, pending_proposal=object(),
                        flow=SimpleNamespace(workspace=Path('/owned/previous')), ack=ack, inspected=Mock(),
                        board=Mock(), output=Mock(), method=Mock(), status=Mock(), log=Mock(),
                        refresh=Mock(), refused=Mock(), config=lambda: dict(pref.DEFAULTS))
                    window.board.GetValue.return_value = '/owned/new-source/board.kicad_pcb'
                    window.output.GetValue.return_value = '/owned/new-output'
                    window.method.GetSelection.return_value = 0
                    window.changed = lambda event: window_method('changed')(window, event)
                    window.path_changed = lambda event: window_method('path_changed')(window, event)
                    wx = Mock()
                    exec(compile(ast.Module(body=[binding], type_ignores=[]), gui.__file__, 'exec'),
                         {'self': window, 'wx': wx})
                    callback = getattr(window, edited).Bind.call_args.args[1]
                    callback(Mock())
                    self.assertFalse(ack.GetValue()); self.assertIsNone(window.flow)
                    self.assertIsNone(window.pending_proposal)
                    window.inspected.SetValue.assert_called_once_with(False)
                    job = Mock(); threads = Mock()
                    act = window_method('act', CliJob=job, threading=threads)
                    act(window, action)
                    self.assertIn('acknowledge the exact paths', window.refused.call_args.args[0])
                    job.assert_not_called(); threads.Thread.assert_not_called()
                    self.assertFalse(window.busy)
                    ack.SetValue(True); window.refused.reset_mock()
                    act(window, action)
                    window.refused.assert_not_called(); job.assert_called_once_with()
                    threads.Thread.return_value.start.assert_called_once_with()

    def test_routing_only_settings_keep_source_acknowledgement(self):
        ack = Mock(); ack.GetValue.return_value = True
        window = SimpleNamespace(busy=False, input_generation=0, flow=None, ack=ack,
            inspected=Mock(), status=Mock(), log=Mock(), refresh=Mock())
        window_method('changed')(window, Mock())
        ack.SetValue.assert_not_called(); self.assertTrue(ack.GetValue())
        window.inspected.SetValue.assert_called_once_with(False)

    def test_cancel_once_and_before_start_never_launches(self):
        job = gui.CliJob(); job.process = Mock(); job.process.poll.return_value = None
        job.cancel(); job.cancel()
        job.process.send_signal.assert_called_once_with(signal.SIGINT)
        with tempfile.TemporaryDirectory() as tmp, patch.object(gui.subprocess, 'Popen') as popen:
            with self.assertRaises(ValueError): job.run(['never'], Path(tmp) / 'cancel.log')
            popen.assert_not_called()

    def test_watchdog_log_overflow_and_cancelled_exit_zero(self):
        process = Mock(); process.returncode = None
        process.poll.side_effect = lambda: process.returncode
        def wait(): process.returncode = 0; return 0
        process.wait.side_effect = wait
        process.stdout = io.BufferedReader(io.BytesIO(b'abcdefghi'))
        timer = Mock()
        with tempfile.TemporaryDirectory() as tmp, patch.object(gui.subprocess, 'Popen', return_value=process), \
                patch.object(gui.threading, 'Timer', return_value=timer), patch.object(gui, 'LOG_LIMIT', 3):
            job = gui.CliJob(); result = job.run(['owned', 'literal'], Path(tmp) / 'run.log', timeout=10)
            self.assertTrue(result['cancel_requested']); self.assertTrue(result['log_truncated'])
            self.assertEqual(result['exit_code'], 0)
            self.assertEqual((Path(tmp) / 'run.log').read_bytes(), b'abc')
            process.send_signal.assert_called_once_with(signal.SIGINT)
            timer.cancel.assert_called_once(); timer.join.assert_called_once()

    def test_environment_removes_interpreter_and_editor_ipc_secrets(self):
        with patch.dict(gui.os.environ, dict(PYTHONPATH='bad', PYTHONHOME='bad',
                KICAD_API_SOCKET='private', KICAD_API_TOKEN='private')):
            env = gui.child_environment()
        for name in ('PYTHONPATH', 'PYTHONHOME', 'KICAD_API_SOCKET', 'KICAD_API_TOKEN'):
            self.assertNotIn(name, env)
        self.assertEqual(env['PYTHONNOUSERSITE'], '1')


if __name__ == '__main__':
    unittest.main()
