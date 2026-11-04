"""Deferred warning-sheet lifecycle; actual Cocoa interaction remains separate."""
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock
from tests.test_gui import window_method


class WarningDialogControls(unittest.TestCase):
    def prepared(self):
        callback = window_method('queue_warning_dialog', warning_review_text=Mock(return_value='bound findings'))
        wx = callback.__globals__['wx']; wx.ID_OK = 5100
        queued = []; wx.CallAfter.side_effect = queued.append
        job = Mock(); flow = SimpleNamespace(workspace=Path('/owned/job'), fresh=Mock())
        window = SimpleNamespace(job=job, flow=flow, busy=True, closing=False, warning_dialog=None,
            input_generation=0, status=Mock(), log=Mock(), timer=Mock(), Destroy=Mock(),
            inspected=Mock(), refresh=Mock(), refused=Mock())
        dialog=Mock(); challenge={'kind':'owned-challenge'}
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
