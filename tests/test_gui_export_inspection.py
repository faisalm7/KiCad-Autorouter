"""Pre-open reader/liveness controls; actual Native proofs qualified separately."""
import json
from pathlib import Path
from unittest.mock import Mock
import unittest
from autorouter import gui
from tests import test_gui as gt


class ExportInspectionTests(unittest.TestCase):
    setUp=gt.GuiWorkflowTests.setUp
    request=gt.GuiWorkflowTests.request
    flow=gt.GuiWorkflowTests.flow

    def prepared(self):
        flow=self.flow();candidate=flow.workspace/'export/validation/candidate'/self.board.name
        candidate.parent.mkdir(parents=True);candidate.write_bytes(b'owned candidate')
        project=candidate.with_suffix('.kicad_pro');project.write_bytes(b'{}')
        flow.ready={'review','choice','export','verify_export'}
        flow.records['export']={'candidate':str(candidate),'project_file':str(project),'candidate_sha256':'a'*64}
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


if __name__=='__main__':unittest.main()
