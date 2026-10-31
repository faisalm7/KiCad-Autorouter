"""Fixed stage-budget/receipt controls; not Native or GUI qualification."""
import copy
import json
import signal
from contextlib import contextmanager
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from autorouter import handoff as h, gui, review_export as ex
from tests import test_handoff as fixture, test_gui as gui_fixture
from tests import test_review_export as export_fixture


def budget(stage):
    seconds = 60 if stage == 'review' else 30
    return dict(handoff_stage_policy='bounded-review60-choice30-v2', budget_seconds=seconds,
        cpu_budget_seconds=seconds, within_budget=True, wall_seconds=0., total_cpu_seconds=0.)


class FixedStageReceiptControls(unittest.TestCase):
    def test_independent_exact_constants_and_stage_policy(self):
        self.assertEqual((h.REVIEW_SECONDS,h.CHOICE_SECONDS,h.SECONDS),(60,30,30))
        self.assertEqual(h.STAGE_POLICY,'bounded-review60-choice30-v2')
        for stage in ('review','choice'):
            self.assertIsNone(h.check_stage_budget(budget(stage),stage))
        for stage in ('export',None,True):
            with self.subTest(stage=stage),self.assertRaises(h.Rejected):h.check_stage_budget(budget('review'),stage)

    def test_old_policy_receipt_caps_and_nonfinite_samples_never_authorize_new_stage(self):
        for stage in ('review','choice'):
            original=budget(stage)
            changes=[dict(handoff_stage_policy=None),dict(handoff_stage_policy='old-review30-v1'),
                dict(budget_seconds=999),dict(cpu_budget_seconds=999),dict(budget_seconds=True),
                dict(cpu_budget_seconds=float(original['cpu_budget_seconds'])),dict(within_budget=1)]
            if stage=='review':changes.append(dict(budget_seconds=30,cpu_budget_seconds=30))
            for field in ('wall_seconds','total_cpu_seconds'):
                changes += [{field:value} for value in (-1.,True,float('inf'),float('nan'),original['budget_seconds']+.001)]
            for change in changes:
                with self.subTest(stage=stage,change=change),self.assertRaises(h.Rejected):
                    h.check_stage_budget(dict(original,**change),stage)
            self.assertEqual(original,budget(stage))

    def test_cleanup_uses_stage_identity_and_counts_its_own_work_not_forged_receipt_cap(self):
        for stage,elapsed,accepted in (('review',45,True),('choice',45,False),('review',61,False)):
            with self.subTest(stage=stage,elapsed=elapsed),tempfile.TemporaryDirectory() as folder:
                out=Path(folder).resolve();name=stage+'.json'
                record=dict(status='ready_for_manual_review' if stage=='review' else 'disposition_recorded',
                    budget_seconds=10000,cpu_budget_seconds=10000,within_budget=True)
                h.save_json(out/name,record)
                if stage=='review':(out/'preview.html').write_text('owned preview')
                with patch.object(h.time,'monotonic',return_value=elapsed),patch.object(h,'cpu_seconds',return_value=elapsed):
                    if accepted:self.assertIs(h.finish_session(record,out,0,0,name),record)
                    else:
                        with self.assertRaisesRegex(h.Rejected,'cleanup exceeded'):h.finish_session(record,out,0,0,name)
                        self.assertEqual(h.f.read_json(out/name)['status'],'rejected')
                        self.assertTrue(list(out.glob('invalidated-session-*-'+name)))
                        if stage=='review':self.assertFalse((out/'preview.html').exists())


class ReviewStageBudgetControls(unittest.TestCase):
    def setUp(self):
        fixture.ReviewCopyTests.setUp(self)
        self.data.update(native=dict(opens=0,blocking=0,warnings=0,exclusions=0,ignored_checks=[],findings=[]),metrics={})
        self.receipt.write_text(json.dumps(self.data))

    def not_ready(self,target):fixture.ReviewCopyTests.not_ready(self,target)

    def test_complete_review_can_cross_old30_with_current_policy_and_no_guard_removed(self):
        now=[0.];save=h.save_json;target=self.root/'review'
        def writer(path,record):
            save(path,record)
            if record.get('status')=='ready_for_manual_review':now[0]=45.
        with patch.object(h,'cpu_seconds',side_effect=lambda:now[0]),patch.object(h,'save_json',writer):
            result=h.review_copy(self.receipt,target)
        self.assertEqual(result['status'],'ready_for_manual_review');h.check_stage_budget(result,'review')
        self.assertEqual(self.check.call_count,3)
        self.assertEqual((target/'project/board.kicad_pcb').read_bytes(),(self.candidate/'board.kicad_pcb').read_bytes())

    def test_after_old30_source_mutation_still_invalidates_review(self):
        now=[0.];save=h.save_json;target=self.root/'review'
        def writer(path,record):
            save(path,record)
            if record.get('status')=='ready_for_manual_review':
                now[0]=45.;(self.source/'board.kicad_pro').write_text('changed source')
        with patch.object(h,'cpu_seconds',side_effect=lambda:now[0]),patch.object(h,'save_json',writer):
            with self.assertRaisesRegex(h.Rejected,'source project changed'):h.review_copy(self.receipt,target)
        self.not_ready(target)

    def test_cancellation_after_old30_still_invalidates_and_restores_handlers(self):
        now=[0.];save=h.save_json;target=self.root/'review'
        handlers={sig:signal.getsignal(sig) for sig in (signal.SIGINT,signal.SIGTERM)}
        def writer(path,record):
            save(path,record)
            if record.get('status')=='ready_for_manual_review':now[0]=45.;raise KeyboardInterrupt
        with patch.object(h,'cpu_seconds',side_effect=lambda:now[0]),patch.object(h,'save_json',writer):
            with self.assertRaisesRegex(h.Rejected,'cancelled'):h.review_copy(self.receipt,target)
        self.not_ready(target)
        self.assertEqual({sig:signal.getsignal(sig) for sig in handlers},handlers)

    def test_session_exit_at61_invalidates_ready_review_and_plot_html(self):
        target=self.root/'review';real=h.validation_readback_session;now=[0.]
        @contextmanager
        def session():
            with real():yield
            (target/'preview.html').write_text('owned completed preview at session exit')
            now[0]=61.
        with patch.object(h,'validation_readback_session',session),patch.object(h,'cpu_seconds',side_effect=lambda:now[0]):
            with self.assertRaisesRegex(h.Rejected,'cleanup exceeded'):h.review_copy(self.receipt,target)
        self.not_ready(target);self.assertTrue(list(target.glob('invalidated-session-*-review.json')))
        self.assertFalse((target/'preview.html').exists())
        self.assertTrue(list(target.glob('invalidated-session-*-preview.html')))

    def test_choice_refuses_legacy_review_before_output_or_central_read(self):
        target=self.root/'review';h.review_copy(self.receipt,target)
        path=target/'review.json';current=h.f.read_json(path);self.check.reset_mock()
        for change in (dict(handoff_stage_policy=None),dict(budget_seconds=30,cpu_budget_seconds=30),
                       dict(handoff_stage_policy=h.STAGE_POLICY,budget_seconds=999,cpu_budget_seconds=999)):
            with self.subTest(change=change):
                h.save_json(path,dict(current,**change))
                with self.assertRaisesRegex(h.Rejected,'fixed stage budget/policy'):
                    h.review_choice(path,self.root/'choice','accept')
                self.assertFalse((self.root/'choice').exists());self.check.assert_not_called()


class ExportStageBudgetControls(unittest.TestCase):
    setUp=export_fixture.ExportControls.setUp
    native_run=export_fixture.ExportControls.native_run

    def test_rebound_old_review_or_forged_choice_refuses_before_native_or_output(self):
        review=self.root/'review/review.json';before=h.f.read_json(review);choice=h.f.read_json(self.choice)
        for changed_stage,change in (('review',dict(handoff_stage_policy=None)),
                ('review',dict(budget_seconds=30,cpu_budget_seconds=30)),
                ('choice',dict(handoff_stage_policy=None)),('choice',dict(budget_seconds=60,cpu_budget_seconds=60))):
            with self.subTest(stage=changed_stage,change=change):
                h.save_json(review,dict(before,**change) if changed_stage=='review' else before)
                updated=dict(choice,review_sha256=h.digest(review.read_bytes()))
                if changed_stage=='choice':updated.update(change)
                h.save_json(self.choice,updated)
                with self.assertRaisesRegex(h.Rejected,'fixed stage budget/policy'):ex.export(self.choice,self.output)
                self.assertEqual(self.calls,[]);self.assertFalse(self.output.exists())


class GuiStagePolicyControls(unittest.TestCase):
    setUp=gui_fixture.GuiWorkflowTests.setUp
    request=gui_fixture.GuiWorkflowTests.request
    flow=gui_fixture.GuiWorkflowTests.flow

    def test_gui_never_adopts_old_or_forged_stage_success_even_with_exit_zero(self):
        flow=self.flow();process=dict(cancel_requested=False,exit_code=0,log_truncated=False)
        for stage in ('review','choice'):
            record=dict(budget(stage),status='ready_for_manual_review' if stage=='review' else 'disposition_recorded',
                        choice_recorded=True,choice='accept')
            for change in (dict(handoff_stage_policy=None),dict(budget_seconds=999,cpu_budget_seconds=999)):
                with self.subTest(stage=stage,change=change),patch.object(gui,'read_record',return_value=dict(record,**change)):
                    with self.assertRaises(h.Rejected):flow.adopt(stage,process,flow.workspace/'unused.log',choice='accept')
                    self.assertNotIn(stage,flow.ready);self.assertIsNone(flow.choice)
