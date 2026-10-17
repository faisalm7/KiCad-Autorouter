"""Pre-open reader/liveness controls; actual Native proofs qualified separately."""
import json
from pathlib import Path
from unittest.mock import Mock
from unittest.mock import patch
from types import SimpleNamespace
import unittest
from autorouter import gui
from tests import test_gui as gt


class ExportInspectionTests(unittest.TestCase):
    setUp=gt.GuiWorkflowTests.setUp
    request=gt.GuiWorkflowTests.request
    flow=gt.GuiWorkflowTests.flow

    def prepared(self):
        from autorouter import review_export as ex
        flow=self.flow();candidate=flow.workspace/'export/validation/candidate'/self.board.name
        candidate.parent.mkdir(parents=True);candidate.write_bytes(b'owned candidate')
        project=candidate.with_suffix('.kicad_pro');project.write_bytes(b'{}')
        flow.ready={'review','choice','export','verify_export'}
        flow.records['export']={'schema':1,'export_accepted':True,'applied':False,
            'candidate':str(candidate),'project_file':str(project),'candidate_sha256':'a'*64}
        flow.records['export']['export_evidence']=ex.evidence(flow.workspace/'export')
        (flow.workspace/'export/export.json').write_text(json.dumps(flow.records['export']))
        record={'current':True,'export_accepted':True,'applied':False,'candidate':str(candidate),'candidate_sha256':'a'*64}
        return flow,project,record

    def job(self,record,*,code=0,hook=None):
        job=gui.CliJob()
        def run(argv,log,*,timeout):
            self.assertEqual(argv[4],'review-export-check');self.assertEqual(timeout,90)
            self.assertEqual(Path(argv[5]).name,'export.json')
            log.write_text(json.dumps(record))
            if hook:hook(job)
            return dict(exit_code=code,cancel_requested=job.cancel_requested,log_truncated=False)
        job.run=Mock(side_effect=run)
        return job

    def test_checked_path_requires_new_cli_result_and_retains_unique_checks(self):
        flow,project,record=self.prepared()
        with self.assertRaisesRegex(ValueError,'fresh cancellable'):flow.inspect_path('export')
        job=self.job(record)
        self.assertEqual(flow.inspect_path('export',job=job),project)
        self.assertEqual(flow.inspect_path('export',job=job),project)
        logs=[call.args[1] for call in job.run.call_args_list]
        self.assertEqual(len(set(logs)),2);self.assertTrue(all(p.is_file() for p in logs))

    def test_old_ready_state_cannot_override_failed_or_mismatched_fresh_reader(self):
        for changed in ({'current':False},{'export_accepted':False},{'applied':True},
                        {'candidate':'/different/board.kicad_pcb'},{'candidate_sha256':'b'*64},
                        {'current':1},{'applied':0}):
            with self.subTest(changed=changed):
                flow,project,record=self.prepared();job=self.job({**record,**changed})
                with self.assertRaises(ValueError):flow.inspect_path('export',job=job)
        flow,project,record=self.prepared()
        with self.assertRaises(ValueError):flow.inspect_path('export',job=self.job(record,code=2))

    def test_cached_project_or_candidate_identity_cannot_redirect_current_reader(self):
        for key in ('candidate','project_file'):
            with self.subTest(key=key):
                flow,project,record=self.prepared();flow.records['export'][key]=str(self.board)
                with self.assertRaises(ValueError):flow.inspect_path('export',job=self.job(record))

    def test_cancellation_and_source_changes_during_reader_prevent_path_delivery(self):
        for mode in ('cancel','source'):
            with self.subTest(mode=mode):
                flow,project,record=self.prepared();before=self.board.read_bytes()
                hook=(lambda job:job.cancel()) if mode=='cancel' else (lambda job:self.board.write_bytes(b'changed source'))
                with self.assertRaises(ValueError):flow.inspect_path('export',job=self.job(record,hook=hook))
                self.board.write_bytes(before)

    def window(self, flow, job):
        window=SimpleNamespace(job=job, flow=flow, busy=True, inspected=Mock(),
            status=Mock(), log=Mock(), refresh=Mock(), closing=False)
        window.refused=lambda error:gt.window_method('refused')(window,error)
        return window

    def test_source_or_settings_change_after_worker_before_queued_open_refuses(self):
        for mode in ('source', 'settings'):
            with self.subTest(mode=mode):
                flow,project,record=self.prepared();job=self.job(record)
                target=flow.inspect_path('export',job=job)
                changed=self.board if mode=='source' else flow.workspace/'settings.json'
                before=changed.read_bytes();changed.write_bytes(b'changed after inspection worker')
                window=self.window(flow,job)
                with patch.object(gui.subprocess,'Popen') as opener:
                    gt.window_method('opened')(window,'export',target,None)
                opener.assert_not_called();self.assertIsNone(window.flow)
                self.assertFalse(flow.ready);self.assertFalse(flow.records)
                self.assertIsNone(flow.choice);self.assertIn('changed',window.log.SetValue.call_args.args[0])
                changed.write_bytes(before)

    def test_unchanged_queued_open_succeeds_and_cancel_skips_freshness(self):
        for cancelled in (False,True):
            with self.subTest(cancelled=cancelled):
                flow,project,record=self.prepared();job=self.job(record)
                target=flow.inspect_path('export',job=job)
                if cancelled:job.cancel()
                window=self.window(flow,job)
                with patch.object(flow,'fresh',wraps=flow.fresh) as fresh, \
                        patch.object(gui.subprocess,'Popen') as opener:
                    gt.window_method('opened')(window,'export',target,None)
                if cancelled:
                    opener.assert_not_called();fresh.assert_not_called();self.assertIsNone(window.flow)
                else:
                    fresh.assert_called_once_with();opener.assert_called_once()
                    self.assertEqual(opener.call_args.args[0][-1],str(project))
                    self.assertIs(window.flow,flow)

    def test_queued_candidate_rule_or_receipt_change_refuses_open(self):
        for mode in ('candidate','new-rule','receipt'):
            with self.subTest(mode=mode):
                flow,project,record=self.prepared();job=self.job(record)
                target=flow.inspect_path('export',job=job)
                changed={'candidate':project.with_suffix('.kicad_pcb'),
                    'new-rule':project.with_suffix('.kicad_dru'),
                    'receipt':flow.workspace/'export/export.json'}[mode]
                changed.write_bytes(b'changed after inspection worker')
                window=self.window(flow,job)
                with patch.object(gui.subprocess,'Popen') as opener:
                    gt.window_method('opened')(window,'export',target,None)
                opener.assert_not_called();self.assertIsNone(window.flow)
                self.assertFalse(flow.ready);self.assertFalse(flow.records)
                self.assertIsNone(flow.choice)

    def test_queued_receipt_boolean_numeric_type_changes_refuse_open(self):
        for changed in ({'export_accepted':1},{'schema':True},{'applied':0}):
            with self.subTest(changed=changed):
                flow,project,record=self.prepared();job=self.job(record)
                target=flow.inspect_path('export',job=job)
                altered={**flow.records['export'],**changed}
                self.assertEqual(altered,flow.records['export'])  # Python equality is insufficient.
                (flow.workspace/'export/export.json').write_text(json.dumps(altered))
                window=self.window(flow,job)
                with patch.object(gui.subprocess,'Popen') as opener:
                    gt.window_method('opened')(window,'export',target,None)
                opener.assert_not_called();self.assertIsNone(window.flow)
                self.assertFalse(flow.ready)


if __name__=='__main__':unittest.main()
