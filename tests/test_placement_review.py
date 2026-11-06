"""Draft interaction controls, not Native placement or GUI qualification."""
import ast
import copy
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock
from experiments import placement_review as adapter
from experiments.placement_review import Review
from experiments.placement_native_proposal_v1 import contract as c
from experiments.placement_native_proposal_v1.test_contract import fixture, moves
from experiments.constrained_placement_v1 import constraints


def review():
    observation=c.inspect_board(fixture())
    options=c.scope_options()
    facts=c.facts_from_observation(observation,**options)
    qualified=c.validate_moves(observation,moves(),**options)
    original=constraints.original_alternative(facts)
    return Review(observation,options,[qualified,original],qualified,{'hash':'fresh'})


class PlacementReview(unittest.TestCase):
    def test_edited_pose_loses_native_match_and_intent(self):
        r=review();self.assertTrue(r.matches_native_pose)
        d=r.decision(acknowledged=True,accepted=True,current_witness={'hash':'fresh'})
        self.assertFalse(d['execution_authorized']);self.assertFalse(d['routing_accepted'])
        r.edit(c.SELECTED[0],'14.5','10')
        self.assertFalse(r.matches_native_pose);self.assertIsNone(r.intent)
        d=r.decision(acknowledged=True,accepted=True,current_witness={'hash':'fresh'})
        self.assertTrue(d['native_validation_required_for_changed_pose'])
        self.assertFalse(d['new_native_validation_performed']);self.assertFalse(d['human_PCB_approval'])
        self.assertFalse(d['warning_acknowledged'])

    def test_invalid_fixed_and_outside_edits_never_adopt(self):
        r=review();before=copy.deepcopy(r.pose);generation=r.revision
        fixed=next(row['uuid'] for row in r.observation['footprints'] if row['uuid'] not in c.SELECTED)
        for component,x,y in [(fixed,'8','8'),(c.SELECTED[0],'3000','10'),
                              (c.SELECTED[0],'7','10'),(c.SELECTED[0],'24','10'),
                              (c.SELECTED[0],'nan','10'),(c.SELECTED[0],'1e99999','10'),
                              (c.SELECTED[0],'abc','10')]:
            with self.subTest(component=component,x=x),self.assertRaises(ValueError):r.edit(component,x,y)
            self.assertEqual(r.pose,before);self.assertEqual(r.revision,generation)

    def test_selection_and_nanometre_quantization_revoke_prior_choice(self):
        r=review();r.decision(acknowledged=True,accepted=False,current_witness={'hash':'fresh'})
        r.choose(1);self.assertIsNone(r.intent);self.assertFalse(r.matches_native_pose)
        r.edit(c.SELECTED[0],'14.0000006','10')
        self.assertEqual(r.moves[c.SELECTED[0]],[14000001,10000000])
        with self.assertRaises(ValueError):r.choose(True)
        with self.assertRaises(ValueError):r.choose(9)

    def test_changed_source_or_evidence_and_missing_ack_refuse(self):
        r=review()
        for ack in (False,1,None):
            with self.assertRaises(ValueError):r.decision(acknowledged=ack,accepted=True,current_witness={'hash':'fresh'})
        with self.assertRaisesRegex(ValueError,'changed'):
            r.decision(acknowledged=True,accepted=True,current_witness={'hash':'changed'})
        self.assertIsNone(r.intent)

    def test_detached_inputs_and_outputs_cannot_mutate_the_pose(self):
        r=review();d=r.decision(acknowledged=True,accepted=True,current_witness={'hash':'fresh'})
        d['moves_nm'][c.SELECTED[0]][0]=1
        self.assertNotEqual(r.moves[c.SELECTED[0]][0],1)
        self.assertNotEqual(r.intent['moves_nm'][c.SELECTED[0]][0],1)
        self.assertNotEqual(r.witness_digest,constraints.digest({'hash':'changed'}))


def window_callbacks(r, **overrides):
    """Run the actual wx callback bodies with passive controls, never a wx app."""
    tree=ast.parse(Path(adapter.__file__).read_text())
    window=next(node for node in ast.walk(tree)
                if isinstance(node,ast.ClassDef) and node.name=='Window')
    methods=[node for node in window.body if isinstance(node,ast.FunctionDef)
             and node.name in {'pending_edit','decide','finish','close'}]
    namespace=dict(review=r,json=json,uuid=SimpleNamespace(uuid4=lambda:SimpleNamespace(hex='test')),
                   late_material=Mock(),write=Mock(return_value=Path('intent-test.json')),
                   threading=SimpleNamespace(Thread=Mock(side_effect=AssertionError('Unexpected worker'))))
    namespace.update(overrides)
    exec(compile(ast.Module(body=methods,type_ignores=[]),adapter.__file__,'exec'),namespace)
    control=lambda:SimpleNamespace(Enable=Mock(),Disable=Mock(),SetValue=Mock(),GetValue=Mock(return_value=True))
    state=SimpleNamespace(busy=False,closed=False,dirty=False,controls=[control()],ack=control(),
                          message=control(),save=control(),reject=control(),Destroy=Mock())
    return state,namespace


class PlacementReviewCallbacks(unittest.TestCase):
    """Pure callback checks; these do not establish actual wx GUI support."""

    def test_queued_material_change_refuses_write_after_worker_succeeds(self):
        r=review()
        result=r.decision(acknowledged=True,accepted=True,current_witness={'hash':'fresh'})
        state,callbacks=window_callbacks(r,late_material=Mock(side_effect=ValueError('Evidence changed')))
        state.busy=True
        callbacks['finish'](state,result,None)
        callbacks['late_material'].assert_called_once_with()
        callbacks['write'].assert_not_called()
        self.assertFalse(state.busy)
        state.ack.SetValue.assert_called_once_with(False)
        self.assertIn('Intent not saved: Evidence changed',state.message.SetValue.call_args.args[0])

    def test_unchanged_queued_intent_saves_only_after_material_check(self):
        r=review()
        result=r.decision(acknowledged=True,accepted=True,current_witness={'hash':'fresh'})
        order=[]
        def material():order.append('material')
        def write(name,raw):
            order.append('write')
            data=json.loads(raw)
            self.assertEqual(data,result)
            for flag in ('execution_authorized','routing_accepted','human_PCB_approval','warning_acknowledged'):
                self.assertIs(data[flag],False)
            return Path(name)
        state,callbacks=window_callbacks(r,late_material=material,write=write)
        callbacks['finish'](state,result,None)
        self.assertEqual(order,['material','write'])

    def test_pending_coordinates_revoke_intent_and_gate_both_decisions(self):
        r=review();r.decision(acknowledged=True,accepted=True,current_witness={'hash':'fresh'})
        state,callbacks=window_callbacks(r)
        event=SimpleNamespace(Skip=Mock())
        callbacks['pending_edit'](state,event)
        self.assertTrue(state.dirty);self.assertIsNone(r.intent)
        state.ack.SetValue.assert_called_once_with(False)
        state.save.Disable.assert_called_once_with();state.reject.Disable.assert_called_once_with()
        event.Skip.assert_called_once_with()
        for accepted in (True,False):callbacks['decide'](state,accepted)
        callbacks['threading'].Thread.assert_not_called();callbacks['write'].assert_not_called()
        self.assertFalse(state.busy)

    def test_dirty_or_revised_pose_refuses_already_queued_result(self):
        for change in ('dirty','revision'):
            with self.subTest(change=change):
                r=review();result=r.decision(acknowledged=True,accepted=True,current_witness={'hash':'fresh'})
                state,callbacks=window_callbacks(r)
                if change=='dirty':state.dirty=True
                else:r.choose(1)
                callbacks['finish'](state,result,None)
                callbacks['late_material'].assert_not_called();callbacks['write'].assert_not_called()
                self.assertIn('Draft changed before saving',state.message.SetValue.call_args.args[0])

    def test_close_during_worker_rejects_queued_intent(self):
        r=review();result=r.decision(acknowledged=True,accepted=True,current_witness={'hash':'fresh'})
        state,callbacks=window_callbacks(r);state.busy=True
        event=SimpleNamespace(Veto=Mock())
        callbacks['close'](state,event)
        self.assertTrue(state.closed);self.assertIsNone(r.intent)
        event.Veto.assert_called_once_with();state.Destroy.assert_not_called()
        callbacks['finish'](state,result,None)
        callbacks['late_material'].assert_not_called();callbacks['write'].assert_not_called()
        state.Destroy.assert_called_once_with()

    def test_failed_worker_does_not_publish_or_run_material_check(self):
        state,callbacks=window_callbacks(review())
        callbacks['finish'](state,None,'Retained proof refused')
        callbacks['late_material'].assert_not_called();callbacks['write'].assert_not_called()
        self.assertIn('Intent refused: Retained proof refused',state.message.SetValue.call_args.args[0])

    def test_text_overlay_keeps_labels_literal_and_does_not_mutate_svg(self):
        svg=('<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">'
             '<text x="10" y="20" font-size="12" font-weight="bold" fill="#111111">'
             'J1 &amp; J2 — draft only</text></svg>')
        bitmap=object();image=SimpleNamespace(width=100,height=100,ConvertToBitmap=Mock(return_value=bitmap))
        font=Mock();font.Bold.return_value=font
        info=Mock();info.Family.return_value=info;info.PixelSize.return_value=info
        dc=Mock();dc.GetFullTextExtent.return_value=(40,12,2,0)
        wx=SimpleNamespace(svg=SimpleNamespace(SVGimage=SimpleNamespace(CreateFromBytes=Mock(return_value=image))),
                           MemoryDC=Mock(return_value=dc),Font=Mock(return_value=font),FontInfo=Mock(return_value=info),
                           FONTFAMILY_SWISS=1,Size=lambda x,y:(x,y),Colour=lambda value:value,NullBitmap=object())
        original=svg
        self.assertIs(adapter.bitmap_with_labels(wx,svg,size=(100,100)),bitmap)
        wx.svg.SVGimage.CreateFromBytes.assert_called_once_with(svg.encode())
        dc.DrawText.assert_called_once_with('J1 & J2 — draft only',10,10)
        dc.SelectObject.assert_called_once_with(wx.NullBitmap)
        self.assertEqual(svg,original)

if __name__=='__main__':unittest.main()
