"""Deferred warning-sheet lifecycle; actual Cocoa interaction remains separate."""
import json
from pathlib import Path
import sys
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import Mock
from autorouter import gui
from tests import test_gui as gt
from tests.test_gui import window_method


class WarningDialogControls(unittest.TestCase):
    def prepared(self, *, flow=None, request=None, warning_read=None):
        read = warning_read if warning_read is not None else Mock(return_value='bound findings')
        callback = window_method('queue_warning_dialog', warning_review_text=read)
        wx = callback.__globals__['wx']; wx.ID_OK = 5100
        queued = []; wx.CallAfter.side_effect = queued.append
        if flow is None:
            temporary = tempfile.TemporaryDirectory(prefix='warning-sheet-')
            self.addCleanup(temporary.cleanup)
            flow = SimpleNamespace(workspace=Path(temporary.name).resolve(), fresh=Mock(),
                check_request=Mock(spec=gui.Workflow.__new__(gui.Workflow).check_request))
        if request is None:
            request=gui.Request('/owned/source/board.kicad_pcb','/owned',json.dumps(dict(gui.pref.DEFAULTS)),True)
        job = gui.CliJob()
        challenge = gt.warning_challenge(flow.workspace)
        ready = threading.Event(); failures = []
        program = ('import json,sys; event=json.loads(sys.argv[1]); print(json.dumps(event),flush=True); '
            'reply=json.loads(sys.stdin.readline()); assert reply["nonce"]==event["nonce"]; '
            'sys.exit(0 if reply["decision"]=="accept_updated_findings" else 2)')
        def observed(value):
            self.assertEqual(value, challenge)
            ready.set()
        def run():
            try:
                job.run([sys.executable, '-B', '-c', program, json.dumps(challenge), '--warning-review-stdio'],
                        flow.workspace/'export.command.log', timeout=35, on_warning_review=observed)
            except Exception as exc: failures.append(exc)
            finally: ready.set()
        worker = threading.Thread(target=run, daemon=False)
        def cleanup():
            if worker.is_alive(): job.cancel()
            worker.join(5)
            self.assertFalse(worker.is_alive(), 'Owned warning fixture did not finish cleanup')
            self.assertIsNotNone(job.process.poll())
            self.assertTrue(job.process.stdout.closed); self.assertTrue(job.process.stdin.closed)
        self.addCleanup(cleanup); worker.start()
        self.assertTrue(ready.wait(5), 'Owned live warning fixture did not become ready')
        self.assertFalse(failures)
        job.check_warning_review(challenge)  # Prove the valid live baseline before each mutation.
        job.check_warning_review = Mock(wraps=job.check_warning_review)
        job.reply_warning_review = Mock(wraps=job.reply_warning_review)
        job.cancel = Mock(wraps=job.cancel)
        window = SimpleNamespace(**gt.displayed_inputs(request),job=job, flow=flow, busy=True, closing=False, warning_dialog=None,
            input_generation=0, status=Mock(), log=Mock(), timer=Mock(), Destroy=Mock(),
            inspected=Mock(), refresh=Mock(), refused=Mock())
        dialog=Mock()
        callback(window, dialog, job, flow, challenge)
        closed=dialog.Bind.call_args.args[1]
        event=Mock(); event.GetDialog.return_value=dialog; event.GetReturnCode.return_value=5100
        return window, dialog, job, flow, challenge, queued, closed, event

    def test_deferred_sheet_adopts_once_only_after_matching_completion(self):
        w,d,j,f,c,q,closed,event=self.prepared()
        d.ShowModal.assert_not_called(); d.ShowWindowModal.assert_not_called(); j.reply_warning_review.assert_not_called()
        q.pop()(); d.ShowWindowModal.assert_called_once(); d.Destroy.assert_not_called()
        event.GetDialog.return_value=Mock(); closed(event); j.reply_warning_review.assert_not_called()
        event.GetDialog.return_value=d; closed(event); closed(event)
        j.reply_warning_review.assert_called_once_with(c,'accept_updated_findings'); d.Destroy.assert_called_once()
        self.assertIsNone(w.warning_dialog)

    def test_expired_queued_challenge_never_opens(self):
        w,d,j,f,c,q,closed,event=self.prepared()
        j.check_warning_review.side_effect=ValueError('expired')
        q.pop()(); d.ShowWindowModal.assert_not_called(); d.Destroy.assert_called_once()
        j.reply_warning_review.assert_not_called(); j.cancel.assert_called_once(); self.assertIsNone(w.warning_dialog)

    def test_inputs_changed_or_explicit_reject_never_send_accept(self):
        for stale in (False,True):
            with self.subTest(stale=stale):
                w,d,j,f,c,q,closed,event=self.prepared(); q.pop()()
                event.GetReturnCode.return_value=5101
                if stale: w.input_generation+=1
                closed(event)
                if stale: j.reply_warning_review.assert_not_called(); j.cancel.assert_called_once()
                else: j.reply_warning_review.assert_called_once_with(c,'reject')
                d.Destroy.assert_called_once()

    def test_finished_before_show_retires_sheet_before_closing_parent(self):
        w,d,j,f,c,q,closed,event=self.prepared(); w.closing=True
        window_method('finished')(w,j,None,'export',None,'expired')
        w.Destroy.assert_not_called(); d.ShowWindowModal.assert_not_called()
        q.pop()(); d.Destroy.assert_called_once(); w.Destroy.assert_called_once()
        j.reply_warning_review.assert_not_called()

    def test_live_expiry_closes_sheet_without_acknowledging(self):
        w,d,j,f,c,q,closed,event=self.prepared(); q.pop()()
        j.check_warning_review.side_effect=ValueError('child expired')
        d.EndModal.side_effect=lambda _:closed(event)
        window_method('finished')(w,j,None,'export',None,'expired')
        d.EndModal.assert_called_once(); d.Destroy.assert_called_once(); j.reply_warning_review.assert_not_called()
        self.assertIsNone(w.job); self.assertFalse(w.busy); self.assertIsNone(w.warning_dialog)


class WarningDialogCurrentRequestTests(unittest.TestCase):
    """Real ordinary Workflow input fences; the challenge/dialog remain UI stubs."""
    setUp = gt.GuiWorkflowTests.setUp
    request = gt.GuiWorkflowTests.request
    flow = gt.GuiWorkflowTests.flow
    prepared = WarningDialogControls.prepared

    def test_changed_popup_without_event_never_shows_old_warning_sheet(self):
        flow=self.flow();w,d,j,f,c,q,closed,event=self.prepared(flow=flow,request=self.request())
        w.config.return_value['scope']='partial_completion'
        q.pop()()
        self.assertEqual(w.input_generation,0)
        d.ShowWindowModal.assert_not_called();d.Destroy.assert_called_once()
        j.reply_warning_review.assert_not_called();j.cancel.assert_called_once()
        self.assertIsNone(w.warning_dialog)
        self.assertIn('Displayed source or settings differ',w.log.SetValue.call_args.args[0])

    def test_changed_popup_without_event_never_acknowledges_old_warning_sheet(self):
        flow=self.flow();w,d,j,f,c,q,closed,event=self.prepared(flow=flow,request=self.request())
        q.pop()();d.ShowWindowModal.assert_called_once()
        w.config.return_value['scope']='partial_completion'
        closed(event)
        self.assertEqual(w.input_generation,0)
        j.reply_warning_review.assert_not_called();j.cancel.assert_called_once()
        d.Destroy.assert_called_once();self.assertIsNone(w.warning_dialog)

    def test_late_warning_record_read_cannot_acknowledge_changed_displayed_request(self):
        flow=self.flow();read=Mock(return_value='bound findings')
        w,d,j,f,c,q,closed,event=self.prepared(flow=flow,request=self.request(),warning_read=read)
        q.pop()();d.ShowWindowModal.assert_called_once()
        def last_read(*args):
            w.config.return_value['scope']='partial_completion'
            return 'bound findings'
        read.side_effect=last_read
        closed(event)
        read.assert_called_once_with(c,flow.workspace/'export/warning-review.json')
        self.assertEqual(w.input_generation,0)
        j.reply_warning_review.assert_not_called();j.cancel.assert_called_once();d.Destroy.assert_called_once()

    def test_matching_ordinary_request_checks_current_flow_before_show_and_reply(self):
        flow=self.flow();w,d,j,f,c,q,closed,event=self.prepared(flow=flow,request=self.request())
        from unittest.mock import patch
        with patch.object(flow,'check_request',wraps=flow.check_request) as check:
            q.pop()();closed(event)
        self.assertEqual(check.call_count,2)
        for call in check.call_args_list:self.assertEqual(call.args,(self.request(),))
        d.ShowWindowModal.assert_called_once();d.Destroy.assert_called_once()
        j.reply_warning_review.assert_called_once_with(c,'accept_updated_findings')
        j.cancel.assert_not_called()
