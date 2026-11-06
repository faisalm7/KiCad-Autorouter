"""Pure exact-source lineage/callback controls, not Native or wx qualification."""
import dataclasses
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from autorouter import gui
from tests import test_gui as base


class SourceGuardTests(unittest.TestCase):
    setUp = base.GuiWorkflowTests.setUp

    def guard(self):
        origin=self.root/'origin-proof.json';origin.write_bytes(b'original lineage')
        expected=hashlib.sha256(origin.read_bytes()).hexdigest()
        state=SimpleNamespace(after=None)
        def verify():
            if hashlib.sha256(origin.read_bytes()).hexdigest()!=expected:
                raise ValueError('Saved placement origin changed')
            if state.after:state.after()
        return gui.SourceGuard(self.board,verify),origin,state

    def request(self,guard=None,board=None):
        return gui.Request(str(board or self.board),str(self.output),json.dumps(self.settings),True,source_guard=guard)

    def preview(self,flow):
        record={'status':'preview','static_preflight_passed':True,'source':str(self.board),
                'source_sha256':hashlib.sha256(self.board.read_bytes()).hexdigest()}
        path=flow.workspace/'preview.command.log';path.write_text(json.dumps(record))
        process={'exit_code':0,'cancel_requested':False,'log_truncated':False}
        return record,path,process

    def window(self,flow,job,guard):
        board=Mock();board.GetValue.return_value=str(self.board)
        state=SimpleNamespace(job=job,flow=flow,source_guard=guard,board=board,busy=True,closing=False,
            inspected=Mock(),log=Mock(),status=Mock(),refresh=Mock(),timer=Mock(),Destroy=Mock())
        state.refused=lambda error:base.window_method('refused')(state,error)
        return state

    def test_stale_origin_refuses_before_creating_workspace(self):
        guard,origin,_=self.guard();origin.write_bytes(b'changed lineage')
        with self.assertRaisesRegex(ValueError,'origin changed'):self.request(guard).prepare()
        self.assertEqual(list(self.output.iterdir()),[])
        self.assertEqual(self.board.read_bytes(),b'owned synthetic source\n')

    def test_source_guard_is_frozen_exact_board_and_not_result_authority(self):
        guard,_,_=self.guard()
        with self.assertRaises(dataclasses.FrozenInstanceError):guard.board=self.root/'other.kicad_pcb'
        with self.assertRaisesRegex(ValueError,'no approval'):
            gui.SourceGuard(self.board,lambda:{'accepted':True})
        other=self.root/'other';other.mkdir();board=other/self.board.name
        for suffix in ('.kicad_pcb','.kicad_pro','.kicad_sch'):board.with_suffix(suffix).write_bytes(b'other')
        with self.assertRaisesRegex(ValueError,'bound source origin'):self.request(guard,board).prepare()
        self.assertEqual(list(self.output.iterdir()),[])
        with self.assertRaisesRegex(ValueError,'trusted SourceGuard'):
            self.request({'accepted':True}).prepare()

    def test_guard_also_refuses_candidate_changes_before_first_preview(self):
        guard,_,_=self.guard();self.board.with_suffix('.kicad_pro').write_bytes(b'changed candidate rules')
        with self.assertRaisesRegex(ValueError,'Bound source project changed'):self.request(guard).prepare()
        self.assertEqual(list(self.output.iterdir()),[])

    def test_guard_identity_carries_through_request_and_workflow(self):
        guard,_,_=self.guard();request=self.request(guard);flow=request.prepare()
        self.assertIs(flow.source_guard,guard);flow.check_request(request)
        with self.assertRaises(AttributeError):flow.source_guard=None
        replacement=gui.SourceGuard(self.board,guard.verify_origin)
        for changed in (self.request(),self.request(replacement)):
            with self.assertRaisesRegex(ValueError,'Displayed source or settings differ'):flow.check_request(changed)
        flow.fresh();self.assertEqual(flow.ready,set());self.assertIsNone(flow.choice)
        self.assertEqual(json.loads(flow.settings_bytes),self.settings)

    def test_stale_origin_refuses_action_and_adoption(self):
        guard,origin,_=self.guard();flow=self.request(guard).prepare()
        flow.command('preview');record,log,process=self.preview(flow)
        origin.write_bytes(b'changed while child ran')
        with self.assertRaisesRegex(ValueError,'origin changed'):flow.command('preview')
        with self.assertRaisesRegex(ValueError,'origin changed'):gui.CliJob().adopt(flow,'preview',process,log)
        self.assertFalse(flow.ready);self.assertFalse(flow.records);self.assertIsNone(flow.choice)

    def test_origin_mutation_during_result_read_refuses_final_adoption(self):
        guard,origin,_=self.guard();flow=self.request(guard).prepare();record,log,process=self.preview(flow)
        read=Path.read_bytes
        def read_and_change(path):
            raw=read(path)
            if path==log:origin.write_bytes(b'changed during adoption')
            return raw
        with patch.object(Path,'read_bytes',read_and_change):
            with self.assertRaisesRegex(ValueError,'origin changed'):flow.adopt('preview',process,log)
        self.assertFalse(flow.ready);self.assertFalse(flow.records)

    def test_late_runtime_read_cannot_escape_origin_guard(self):
        from autorouter import handoff
        guard,origin,_=self.guard();flow=self.request(guard).prepare()
        def runtime_read():
            origin.write_bytes(b'changed during runtime material read')
            return flow.runtime_hashes
        with patch.object(handoff,'runtime_inventory',side_effect=runtime_read):
            with self.assertRaisesRegex(ValueError,'origin changed'):flow.fresh()

    def test_queued_finished_refuses_changed_origin_and_clears_ready_state(self):
        guard,origin,_=self.guard();flow=self.request(guard).prepare();record,log,process=self.preview(flow)
        job=gui.CliJob();job.adopt(flow,'preview',process,log)
        window=self.window(flow,job,guard);origin.write_bytes(b'changed after completed child')
        base.window_method('finished')(window,job,flow,'preview',record,None)
        self.assertIsNone(window.flow);self.assertFalse(flow.ready);self.assertFalse(flow.records)
        self.assertIn('origin changed',window.log.SetValue.call_args.args[0])
        self.assertIs(window.source_guard,guard)

    def test_queued_finished_never_detaches_guard_on_displayed_path_or_guard_change(self):
        for mode in ('path','guard'):
            with self.subTest(mode=mode):
                guard,_,_=self.guard();flow=self.request(guard).prepare();record,log,process=self.preview(flow)
                job=gui.CliJob();job.adopt(flow,'preview',process,log);window=self.window(flow,job,guard)
                if mode=='guard':window.source_guard=None
                else:
                    other=self.root/'different.kicad_pcb';other.write_bytes(b'other')
                    window.board.GetValue.return_value=str(other)
                base.window_method('finished')(window,job,flow,'preview',record,None)
                self.assertIsNone(window.flow);self.assertFalse(flow.ready)
                self.assertIn('guard differs',window.log.SetValue.call_args.args[0])

    def test_finished_unchanged_works_and_late_cancel_or_close_never_adopts(self):
        for mode in ('unchanged','cancel','close','already_closed'):
            with self.subTest(mode=mode):
                guard,_,verifier=self.guard();flow=self.request(guard).prepare();record,log,process=self.preview(flow)
                job=gui.CliJob();job.adopt(flow,'preview',process,log);window=self.window(flow,job,guard)
                if mode=='cancel':verifier.after=job.cancel
                if mode=='close':verifier.after=lambda:setattr(window,'closing',True)
                if mode=='already_closed':window.closing=True
                base.window_method('finished')(window,job,flow,'preview',record,None)
                if mode=='unchanged':
                    self.assertIs(window.flow,flow);self.assertIn('preview',flow.ready)
                else:
                    self.assertIsNone(window.flow);self.assertFalse(flow.ready);self.assertFalse(flow.records)
                if mode in ('close','already_closed'):window.Destroy.assert_called_once_with()

    def test_queued_open_checks_origin_after_export_material_and_cancel(self):
        for mode in ('unchanged','origin','late_origin','cancel','close'):
            with self.subTest(mode=mode):
                guard,origin,verifier=self.guard();flow=self.request(guard).prepare();job=gui.CliJob()
                project=flow.workspace/'owned-export.kicad_pro';project.write_bytes(b'{}')
                flow.ready={'review','choice','export','verify_export'};flow.choice='accept'
                flow.records={'export':{'status':'exported','project_file':str(project)}}
                flow.check_open_export_material=Mock()
                window=self.window(flow,job,guard)
                if mode=='origin':origin.write_bytes(b'changed after readback')
                if mode=='late_origin':flow.check_open_export_material.side_effect=lambda:origin.write_bytes(b'changed during export material')
                if mode=='cancel':verifier.after=job.cancel
                if mode=='close':window.closing=True
                with patch.object(gui.subprocess,'Popen') as opener:
                    base.window_method('opened')(window,'export',project,None)
                if mode=='unchanged':
                    opener.assert_called_once();self.assertIs(window.flow,flow)
                else:
                    opener.assert_not_called();self.assertIsNone(window.flow);self.assertFalse(flow.ready)
                if mode=='close':window.Destroy.assert_called_once_with()

    def test_path_changed_keeps_injected_guard_for_next_request(self):
        guard,_,_=self.guard();flow=self.request(guard).prepare();window=self.window(flow,gui.CliJob(),guard)
        window.busy=False;window.ack=Mock();window.chooser=None;window.input_generation=0
        window.pending_proposal=None;window.inspection_path=None
        window.changed=lambda event:base.window_method('changed')(window,event)
        base.window_method('path_changed')(window,Mock())
        self.assertIs(window.source_guard,guard);self.assertIsNone(window.flow)
        window.ack.SetValue.assert_called_with(False)

    def test_actual_action_and_assistant_requests_keep_the_injected_guard(self):
        guard,_,_=self.guard()
        for action in ('preview','suggest'):
            with self.subTest(action=action):
                window=self.window(None,None,guard);window.busy=False;window.chooser=None
                window.output=Mock();window.output.GetValue.return_value=str(self.output)
                window.config=lambda:self.settings;window.ack=Mock();window.ack.GetValue.return_value=True
                window.method=Mock();window.method.GetSelection.return_value=0;window.refused=Mock()
                window.inspection_path=self.root/'inspection.json';window.model_config=Mock()
                window.model_config.GetValue.return_value='explicit-local-settings.json'
                window.intent_text=Mock();window.intent_text.GetValue.return_value='Keep existing copper'
                constructor=Mock(side_effect=ValueError('stop before worker'))
                if action=='preview':base.window_method('act',Request=constructor)(window,action)
                else:base.window_method('suggest_settings',Request=constructor)(window,None)
                constructor.assert_called_once()
                self.assertIs(constructor.call_args.kwargs['source_guard'],guard)
                self.assertEqual(constructor.call_args.args[0],str(self.board))
                window.refused.assert_called_once_with('stop before worker')

    def test_ordinary_request_remains_unguarded(self):
        request=self.request();flow=request.prepare()
        self.assertIsNone(request.source_guard);self.assertIsNone(flow.source_guard)
        record,log,process=self.preview(flow);flow.adopt('preview',process,log)
        self.assertEqual(flow.ready,{'preview'});self.assertEqual(flow.records['preview'],record)
        self.assertIsNone(flow.choice)


if __name__=='__main__':unittest.main()
