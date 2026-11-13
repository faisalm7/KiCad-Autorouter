"""Synthetic controller/clock proofs; no wx, Native PCB or human approval."""
import copy
import io
import json
from pathlib import Path
import tempfile
import sys
import threading
import time
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from autorouter import gui, pipeline as p, review_export as ex
from autorouter.runner import ELAPSED_CLOCK_POLICY


class Clock:
    def __init__(self, value=1000.0): self.value = value
    def __call__(self): return self.value


class Pipe(io.BytesIO):
    def __init__(self, value=b''):
        super().__init__(value); self.writes = []
    def write(self, value):
        self.writes.append(value); return super().write(value)


class Child:
    """Subprocess double admitted only through the actual run/Popen seam."""
    def __init__(self, output=b'', *, finish=None, code=0):
        self.stdout = Pipe(output); self.stdin = Pipe(); self.returncode = None
        self.code = code; self.finish = finish; self.signals = []
    def poll(self): return self.returncode
    def wait(self):
        if self.finish: self.finish(); self.finish = None
        self.returncode = self.code; return self.code
    def send_signal(self, value): self.signals.append(value)


class GuiElapsedDeadline(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='gui-elapsed-')
        self.addCleanup(temporary.cleanup); self.root = Path(temporary.name).resolve()
        self.clock = Clock(); self.timer = Mock()  # start deliberately never fires.
        self.addCleanup(patch.stopall)
        patch.object(gui, 'elapsed_time', self.clock).start()
        patch.object(ex, 'elapsed_time', self.clock).start()
        patch.object(gui.threading, 'Timer', return_value=self.timer).start()

    def run_child(self, child, *, warning=None, seconds=30):
        job = gui.CliJob(); log = self.root/'export.command.log'
        argv = ['owned-software-test', '--warning-review-stdio'] if warning else ['owned-software-test']
        with patch.object(gui.subprocess, 'Popen', return_value=child):
            result = job.run(argv, log, timeout=seconds,
                             on_warning_review=(lambda event: warning(job, event)) if warning else None)
        return job, result, log

    def packet(self, *, sent=1000.0, expires=1005.0):
        finding = dict(type='connection_width', severity='warning', description='owned warning', items=[])
        review = dict(policy=ex.WARNING_REVIEW_POLICY, delta=dict(previous=finding, fresh=finding),
            findings_equivalent=False, review_text='Synthetic warning protocol fixture only.', copper_witness={},
            previous_findings=[finding], fresh_findings=[finding])
        pending = dict(schema=1, kind='live-warning-review-pending-v1', policy=ex.WARNING_REVIEW_POLICY,
            export_accepted=False, resumable_after_exit=False, nonce='c'*32,
            candidate_sha256='a'*64, native_report_sha256='b'*64,
            clock_policy=ELAPSED_CLOCK_POLICY, sent_elapsed_time=sent, expires_elapsed_time=expires,
            budget_seconds=30, sent_wall_seconds=0.0, warning_review=review)
        path = self.root/'export/warning-review.json'; path.parent.mkdir(exist_ok=True)
        path.write_text(json.dumps(pending))
        event = dict(kind='autorouter.warning-review-required.v1', pending=str(path),
            pending_sha256=p.sha(path), delta_sha256=ex._warning_digest(review), nonce=pending['nonce'],
            remaining_seconds=expires-sent, clock_policy=ELAPSED_CLOCK_POLICY,
            sent_elapsed_time=sent, expires_elapsed_time=expires,
            candidate_sha256=pending['candidate_sha256'], native_report_sha256=pending['native_report_sha256'],
            warning_review={key:review[key] for key in ('policy','delta','findings_equivalent','review_text','copper_witness')})
        return event, path

    def test_pre_run_liveness_and_cancellation_are_preserved(self):
        job = gui.CliJob(); job.check_live()
        job.cancel()
        with self.assertRaises(ValueError): job.check_live()
        with patch.object(gui.subprocess, 'Popen') as launch, self.assertRaises(ValueError):
            job.run(['owned'], self.root/'cancel.log', timeout=10)
        launch.assert_not_called()

    def test_unarmed_job_and_injected_process_cannot_adopt_or_acknowledge(self):
        for injected in (False, True):
            with self.subTest(injected=injected):
                job = gui.CliJob(); flow = Mock()
                if injected: job.process = Child()
                with self.assertRaises(ValueError): job.adopt(flow, 'route', {}, self.root/'absent')
                flow.adopt.assert_not_called()
                with self.assertRaises(ValueError): job.reply_warning_review({}, 'accept_updated_findings')

    def test_delayed_timer_cannot_promote_zero_exit_after_suspend(self):
        child = Child(finish=lambda:setattr(self.clock, 'value', 1031.0))
        job, result, _ = self.run_child(child)
        self.assertEqual(result['exit_code'], 0)
        self.assertTrue(result['cancel_requested']); self.assertIsNotNone(result['deadline_error'])
        self.assertEqual(result['wall_seconds'], 31.0)
        self.timer.start.assert_called_once()
        flow = Mock()
        with self.assertRaises(ValueError): job.adopt(flow, 'route', result, self.root/'absent')
        flow.adopt.assert_not_called()

    def test_automatic_deadline_stop_is_distinct_from_explicit_cancellation(self):
        child = Child(finish=lambda:setattr(self.clock, 'value', 1031.0))
        job, result, log = self.run_child(child)
        self.assertIsNotNone(result['deadline_error'])
        flow = Mock()
        with self.assertRaisesRegex(ValueError, 'timed out or its timing'):
            job.adopt(flow, 'route', result, log)
        flow.adopt.assert_not_called()
        explicit = gui.CliJob(); explicit.cancel()
        self.assertIsNone(explicit._deadline_error)
        with self.assertRaisesRegex(ValueError, 'was cancelled'):
            explicit.check_live()

    def test_expiry_before_adoption_prevents_readback(self):
        job, result, log = self.run_child(Child())
        self.clock.value = 1031
        flow = Mock()
        with self.assertRaises(ValueError): job.adopt(flow, 'route', result, log)
        flow.adopt.assert_not_called()

    def test_expiry_during_adoption_revokes_positive_state(self):
        job, result, log = self.run_child(Child())
        flow = SimpleNamespace(ready={'route'}, records={'route':{'accepted':True}}, choice='accept')
        def adopt(*args, **kwargs):
            self.clock.value = 1031; return {'accepted':True}
        flow.adopt = adopt
        with self.assertRaises(ValueError): job.adopt(flow, 'route', result, log)
        self.assertEqual(flow.ready, set()); self.assertEqual(flow.records, {}); self.assertIsNone(flow.choice)

    def test_backward_clock_cannot_become_a_positive_receipt(self):
        child = Child(finish=lambda:setattr(self.clock, 'value', 999.0))
        with self.assertRaises(ValueError): self.run_child(child)

    def test_transport_delay_does_not_renew_expired_warning(self):
        event, _ = self.packet(); self.clock.value = 1006
        child = Child((json.dumps(event)+'\n').encode()); callback = Mock()
        with self.assertRaisesRegex(ValueError, 'expired'):
            self.run_child(child, warning=callback)
        callback.assert_not_called(); self.assertEqual(child.stdin.writes, [])

    def test_live_bound_warning_reply_passes_and_stays_expired_after_exit(self):
        event, _ = self.packet(); self.clock.value = 1001
        child = Child((json.dumps(event)+'\n').encode())
        job, result, _ = self.run_child(child,
            warning=lambda job,event:job.reply_warning_review(event, 'accept_updated_findings'))
        self.assertFalse(result['cancel_requested']); self.assertEqual(result['exit_code'], 0)
        reply = json.loads(b''.join(child.stdin.writes))
        self.assertEqual(reply['nonce'], event['nonce']); self.assertEqual(reply['pending_sha256'], event['pending_sha256'])
        with self.assertRaises(ValueError): job.reply_warning_review(event, 'accept_updated_findings')

    def test_delayed_timer_does_not_allow_expired_warning_reply(self):
        event, _ = self.packet(); child = Child((json.dumps(event)+'\n').encode())
        def late(job, event):
            self.clock.value = 1005
            job.reply_warning_review(event, 'accept_updated_findings')
        with self.assertRaises(ValueError): self.run_child(child, warning=late)
        self.assertEqual(child.stdin.writes, [])

    def test_timely_warning_reply_allows_later_readback_within_action_deadline(self):
        event, _ = self.packet()
        child = Child((json.dumps(event)+'\n').encode(), finish=lambda:setattr(self.clock, 'value', 1005.0))
        job, result, _ = self.run_child(child,
            warning=lambda job,event:job.reply_warning_review(event, 'accept_updated_findings'))
        self.assertEqual(len(child.stdin.writes), 1)
        self.assertFalse(result['cancel_requested'])
        flow = Mock(); flow.adopt.return_value = {'software_test_readback':True}
        self.assertEqual(job.adopt(flow, 'export', result, self.root/'absent'), {'software_test_readback':True})
        self.clock.value = 1031
        with self.assertRaises(ValueError): job.check_live()

    def test_pending_change_after_offer_prevents_reply(self):
        event, path = self.packet(); child = Child((json.dumps(event)+'\n').encode())
        def changed(job, event):
            path.write_text('{}')
            job.reply_warning_review(event, 'accept_updated_findings')
        with self.assertRaises(ValueError): self.run_child(child, warning=changed)
        self.assertEqual(child.stdin.writes, [])

    def test_policy_candidate_report_and_clock_changes_refuse_before_display(self):
        event, path = self.packet()
        for field, value in (('clock_policy','awake-clock'), ('candidate_sha256','d'*64),
                ('native_report_sha256','e'*64), ('sent_elapsed_time', True),
                ('expires_elapsed_time',float('nan')), ('expires_elapsed_time',1006.0)):
            with self.subTest(field=field), self.assertRaises(ValueError):
                gui.warning_review_text(dict(event, **{field:value}), path)

    def test_cancellation_during_callback_cannot_send_ack(self):
        event, _ = self.packet(); child = Child((json.dumps(event)+'\n').encode())
        def cancelled(job, event):
            job.cancel(); job.reply_warning_review(event, 'accept_updated_findings')
        with self.assertRaises(ValueError): self.run_child(child, warning=cancelled)
        self.assertEqual(child.stdin.writes, [])


class QuietChildDeadline(unittest.TestCase):
    def test_elapsed_jump_interrupts_silent_child_before_awake_timeout(self):
        # Real child/stdio/watchdog, simulated elapsed jump; no actual OS sleep.
        with tempfile.TemporaryDirectory(prefix='quiet-clock-') as temporary:
            jumped = threading.Event(); real_clock = gui.elapsed_time
            job = gui.CliJob(); timer = threading.Timer(0.2, jumped.set)
            started = time.monotonic()
            try:
                timer.start()
                with patch.object(gui, 'elapsed_time', side_effect=lambda:real_clock() + (20 if jumped.is_set() else 0)):
                    result = job.run([sys.executable, '-B', '-c', 'import time; time.sleep(10)'],
                                     Path(temporary)/'quiet.log', timeout=4)
            finally:
                timer.cancel(); timer.join()
                if job.process is not None and job.process.poll() is None:
                    job.process.kill(); job.process.wait(timeout=5)
            self.assertLess(time.monotonic()-started, 2, 'Silent child waited for the old awake timeout')
            self.assertTrue(jumped.is_set()); self.assertTrue(result['cancel_requested'])
            self.assertIsNotNone(result['deadline_error']); self.assertIsNotNone(job.process.poll())
            self.assertTrue(job.process.stdout.closed)



    def test_clock_read_failure_interrupts_silent_child_and_cannot_publish(self):
        with tempfile.TemporaryDirectory(prefix='quiet-clock-failure-') as temporary:
            failed = threading.Event(); real_clock = gui.elapsed_time
            job = gui.CliJob(); timer = threading.Timer(0.2, failed.set)
            def read():
                if failed.is_set(): raise RuntimeError('owned clock-read failure')
                return real_clock()
            started = time.monotonic()
            try:
                timer.start()
                with patch.object(gui, 'elapsed_time', side_effect=read), self.assertRaises(RuntimeError):
                    job.run([sys.executable, '-B', '-c', 'import time; time.sleep(10)'],
                            Path(temporary)/'quiet.log', timeout=4)
            finally:
                timer.cancel(); timer.join()
                if job.process is not None and job.process.poll() is None:
                    job.process.kill(); job.process.wait(timeout=5)
            self.assertLess(time.monotonic()-started, 2)
            self.assertTrue(job.cancel_requested); self.assertIsNotNone(job._deadline_error)
            self.assertIsNotNone(job.process.poll()); self.assertTrue(job.process.stdout.closed)
            self.assertFalse((Path(temporary)/'quiet.process.json').exists())

    def test_completed_job_stops_owned_watchdog_before_later_clock_jump(self):
        with tempfile.TemporaryDirectory(prefix='closed-watchdog-') as temporary:
            jumped = threading.Event(); real_clock = gui.elapsed_time; real_timer = threading.Timer
            job = gui.CliJob()
            with patch.object(gui, 'elapsed_time', side_effect=lambda:real_clock() + (20 if jumped.is_set() else 0)), \
                    patch.object(gui.threading, 'Timer', wraps=real_timer) as timer:
                result = job.run([sys.executable, '-B', '-c', 'print("owned",flush=True)'],
                                 Path(temporary)/'normal.log', timeout=4)
                jumped.set(); time.sleep(0.15)
                self.assertFalse(job.cancel_requested)
            timer.assert_called_once()
            self.assertFalse(result['cancel_requested']); self.assertEqual(result['exit_code'], 0)
            self.assertTrue(job.process.stdout.closed)



    def test_watchdog_start_failure_reaps_real_owned_child_and_closes_output(self):
        with tempfile.TemporaryDirectory(prefix='watchdog-start-failure-') as temporary:
            timer = Mock(); timer.start.side_effect = RuntimeError('owned thread-start failure')
            job = gui.CliJob()
            with patch.object(gui.threading, 'Timer', return_value=timer), self.assertRaisesRegex(RuntimeError, 'thread-start'):
                job.run([sys.executable, '-B', '-c', 'import time; time.sleep(10)'],
                        Path(temporary)/'quiet.log', timeout=4)
            self.assertTrue(job.cancel_requested); self.assertIsNotNone(job.process.poll())
            self.assertTrue(job.process.stdout.closed)
            timer.cancel.assert_called_once(); timer.join.assert_not_called()
            self.assertFalse((Path(temporary)/'quiet.process.json').exists())


class ExportWarningElapsedDeadline(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='export-elapsed-')
        self.addCleanup(temporary.cleanup); self.output = Path(temporary.name).resolve()
        self.clock = Clock(); self.start = 990.0
        self.record = dict(candidate_sha256='a'*64, native_report_sha256='b'*64,
                           runtime_source_sha256={}, metrics={}, budget_seconds=120,
                           wall_seconds=10.0, total_cpu_seconds=0.0)
        self.binding = {'owned_binding':'not a Native proof'}; self.report = {}
        self.delta = dict(policy=ex.WARNING_REVIEW_POLICY, delta={}, findings_equivalent=False,
                          review_text='Software clock test only.', copper_witness={})
        self.patches = [patch.object(ex, 'elapsed_time', self.clock), patch.object(ex.h, 'cpu_seconds', return_value=0.0),
            patch.object(ex, '_warning_eligibility', return_value=self.delta), patch.object(ex, '_check_stage_proof'),
            patch.object(ex, 'evidence', side_effect=lambda *_:dict(files={}))]
        for item in self.patches: item.start(); self.addCleanup(item.stop)

    def account(self):
        self.record.update(wall_seconds=self.clock.value-self.start, total_cpu_seconds=0.0)

    def invoke(self, callback):
        ex._live_warning_review(self.output, self.record, self.binding, self.report,
            None, None, None, {}, callback, lambda:90.0, lambda:None, self.account, self.start, 0.0)

    def response(self, event):
        return dict(kind='autorouter.warning-review-response.v1', decision='accept_updated_findings',
                    nonce=event['nonce'], pending_sha256=event['pending_sha256'], delta_sha256=event['delta_sha256'])

    def test_absolute_clock_is_sealed_before_callback_and_completed_ack_remains_readable(self):
        def timely(event, remaining, guard):
            pending = ex.f.read_json(self.output/'warning-review.json')
            self.assertEqual(p.sha(self.output/'warning-review.json'), event['pending_sha256'])
            for field in ('clock_policy','sent_elapsed_time','expires_elapsed_time','candidate_sha256','native_report_sha256'):
                self.assertEqual(pending[field], event[field])
            self.assertEqual(event['expires_elapsed_time'], 1090.0)
            self.clock.value = 1001.0; guard(); return self.response(event)
        self.invoke(timely)
        ack = ex.f.read_json(self.output/'warning-acknowledgement.json')
        self.assertEqual(ack['acknowledged_elapsed_time'], 1001.0)
        self.clock.value = 5000.0
        ex._check_warning_acknowledgement(self.output, self.record, self.binding, self.report,
                                          None, None, None, {})

    def test_absolute_expiry_refuses_even_if_callback_remaining_clock_stalls(self):
        def late(event, *_):
            self.clock.value = 1200.0; return self.response(event)
        with self.assertRaisesRegex(p.Rejected, 'expired'): self.invoke(late)
        self.assertFalse((self.output/'warning-acknowledgement.json').exists())
        self.assertNotIn('warning_review_acknowledgement', self.record)

    def test_expiry_cannot_be_relabelled_as_extra_review_budget(self):
        packet = dict(clock_policy=ELAPSED_CLOCK_POLICY, sent_elapsed_time=1000., expires_elapsed_time=1090.,
                      budget_seconds=90., sent_wall_seconds=10.)
        with self.assertRaisesRegex(p.Rejected, 'original export budget'): ex._warning_clock(packet)


if __name__ == '__main__': unittest.main()
