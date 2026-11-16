"""Whole placement-window methods and real shared tools; offline, no model/CAD/GUI claim."""
import copy
from pathlib import Path
from types import MethodType
import tempfile
import unittest
from unittest.mock import Mock, patch
from autorouter import placement_gui as pg, placement_intent as placement, design_intent as design, gui
from experiments.placement_native_proposal_v1 import multipad_fixture
from tests import test_placement_gui as ui, test_placement_copper_gui as controls

class PlacementCopilot(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory(prefix='placement-copilot-');self.addCleanup(temp.cleanup)
        self.root=Path(temp.name).resolve();self.board=multipad_fixture.write_project(self.root/'source')
        self.inspection=placement.inspect_saved(self.board)
        self.selected=[multipad_fixture.uid(ref+'-footprint')for ref in('J1','J2')]
        self.settings=placement.settings(self.selected,[7_000_000,7_000_000,31_000_000,13_000_000],
            copper_policy=placement.COPPER_POLICY,protected_names=['KEEP'])
        self.context=pg.copilot_context(self.inspection,self.settings,'90')
        self.proposal=design.validate_placement_route_proposal(self.inspection,self.context,design.placement_request(self.context))
        self.original=gui.source_inventory(self.board)
    def window(self):
        w=ui.PlacementGuiTests().window();w.gate.review=None;w.gate.acknowledged=False
        w.inspection=self.inspection;w.board=controls.text_control(str(self.board));w.route_budget=controls.text_control('90')
        w.assistant_request=controls.text_control('Keep fixed parts and KEEP, place selected parts in this region, then route approved connections.')
        w.assistant_ack=controls.text_control(False);w.assistant_result=controls.text_control();w.assistant_use=Mock()
        w.pages=Mock();w.find_alternatives=Mock();w.options=Mock(return_value=self.settings)
        work=self.root/'jobs';work.mkdir(exist_ok=True);w.owned_workspace=Mock(return_value=work)
        for name in('current_copilot_context','check_copilot_plan','receive_copilot','use_copilot_plan','invalidate_copilot','assistant_changed'):
            setattr(w,name,MethodType(ui.window_method(name),w))
        return w
    def result(self):return dict(proposal=copy.deepcopy(self.proposal),clarification=None,metrics=dict(request_count=1,cost_usd=None,endpoint_scope='offline_control'))
    def receive(self,w,result=None):
        w.receive_copilot(self.result()if result is None else result,self.context,w.copilot_generation,w.assistant_request.GetValue())
    def test_generic_identifiers_have_no_route_uuid_prerequisite(self):
        self.assertNotIn('UUID',design.MODEL_DATA_INSTRUCTIONS)
        self.assertIn('exact observed net names',design.MODEL_DATA_INSTRUCTIONS)
        self.assertIn('component UUID map',design.placement_model_contract()['instructions'])
        self.assertEqual(design.tool_schema()['function']['parameters']['properties']['nets']['items'],{'type':'string'})
    def test_visible_context_has_every_unselected_part_fixed_and_explicit_permission(self):
        fixed={row['uuid']for row in self.inspection['components']}-set(self.selected)
        self.assertEqual(set(self.context['fixed_components']),fixed)
        self.assertEqual(self.context['approved_route_nets'],['ROUTE_A','ROUTE_B'])
        self.assertIs(self.context['rebuild_permission'],True)
        with self.assertRaisesRegex(ValueError,'explicit'):
            pg.copilot_context(self.inspection,placement.settings(self.selected,self.settings['region_nm']),'90')
        for text in('bad','90.0','-1','901'):
            with self.subTest(text=text),self.assertRaises(ValueError):pg.copilot_context(self.inspection,self.settings,text)
    def test_plan_is_visible_but_cannot_search_or_approve_itself(self):
        w=self.window();self.receive(w)
        self.assertIn('waiting for your approval',w.assistant_result.GetValue())
        self.assertIn('User-protected nets: KEEP',w.assistant_result.GetValue())
        self.assertIn('90 seconds',w.assistant_result.GetValue())
        self.assertIsNone(w.approved_copilot);self.assertFalse(w.gate.acknowledged)
        self.assertIsNone(w.qualified);w.find_alternatives.assert_not_called()
        for ack in(False,1,'yes',None):
            w.assistant_ack.SetValue(ack);w.use_copilot_plan(None);w.find_alternatives.assert_not_called()
            self.assertIsNone(w.approved_copilot)
        self.assertEqual(gui.source_inventory(self.board),self.original)
    def test_explicit_plan_choice_calls_the_existing_search_only(self):
        w=self.window();self.receive(w);w.assistant_ack.SetValue(True);w.use_copilot_plan(None)
        w.find_alternatives.assert_called_once_with(None)
        self.assertIsNotNone(w.approved_copilot);self.assertIsNone(w.pending_copilot)
        self.assertIsNone(w.qualified);self.assertFalse(w.gate.acknowledged)
        self.assertIn('reviewed for placement alternatives only',w.assistant_result.GetValue())
        receipt=next((self.root/'jobs').glob('assistant-plan-choice-*.json'))
        self.assertIn('"human_PCB_approval": false',receipt.read_text())
    def test_stale_context_is_refused_before_untrusted_reply(self):
        w=self.window();w.route_budget.SetValue('120')
        with self.assertRaises(design.PendingContextChanged):self.receive(w,{'bad':'response'})
        self.assertIsNone(w.pending_copilot);w.find_alternatives.assert_not_called()
    def test_changed_request_generation_and_source_cannot_adopt_reply(self):
        for mode in('generation','request','source'):
            w=self.window();generation=w.copilot_generation;text=w.assistant_request.GetValue()
            if mode=='generation':w.copilot_generation+=1
            elif mode=='request':w.assistant_request.SetValue('Different intent')
            else:self.board.with_suffix('.kicad_pro').write_bytes(self.board.with_suffix('.kicad_pro').read_bytes()+b'\n')
            with self.subTest(mode=mode),self.assertRaises(ValueError):
                w.receive_copilot(self.result(),self.context,generation,text)
            self.assertIsNone(w.pending_copilot)
    def test_unsupported_clarification_is_a_question_not_completion(self):
        w=self.window();value=dict(proposal=None,clarification=dict(reason='unsupported_requirement',questions=['Which supported requirement should be used without waiving KEEP?']),metrics=dict(request_count=1))
        self.receive(w,value);self.assertIsNone(w.pending_copilot);self.assertIsNone(w.approved_copilot)
        self.assertIn('Clarification needed',w.assistant_result.GetValue());w.find_alternatives.assert_not_called()
    def test_returned_authority_and_receipt_failure_cannot_adopt(self):
        w=self.window();value=self.result();value['proposal']['approval_granted']=True
        with self.assertRaisesRegex(ValueError,'differs'):self.receive(w,value)
        self.assertIsNone(w.pending_copilot)
        with patch.object(pg,'write_new_json',side_effect=OSError('receipt unavailable')):
            with self.assertRaises(OSError):self.receive(w)
        self.assertIsNone(w.pending_copilot);self.assertIsNone(w.approved_copilot)
    def test_late_visible_budget_or_request_changes_revoke_plan_choice(self):
        for target in('budget','request'):
            w=self.window();self.receive(w);w.assistant_ack.SetValue(True)
            if target=='budget':w.route_budget.SetValue('120')
            else:w.assistant_request.SetValue('Different intent')
            w.use_copilot_plan(None);w.find_alternatives.assert_not_called();self.assertIsNone(w.approved_copilot)
    def test_visual_area_change_clears_plan_even_if_old_values_are_restored(self):
        w=self.window();self.receive(w);w.assistant_ack.SetValue(True);w.use_copilot_plan(None)
        generation=w.copilot_generation
        w.region=[controls.text_control(pg.mm(n))for n in self.settings['region_nm']]
        w.draw_area=Mock();w.updating=False;w.layout_panel=Mock();w.overview=Mock()
        w.revoke=Mock();w.approved_copilot={'context':copy.deepcopy(self.context)}
        ui.window_method('area_on_board')(w,[8_000_000,7_000_000,30_000_000,13_000_000])
        self.assertGreater(w.copilot_generation,generation);self.assertIsNone(w.approved_copilot)
        self.assertIsNone(w.pending_copilot);self.assertFalse(w.assistant_ack.GetValue())
        ui.window_method('area_on_board')(w,self.settings['region_nm'])
        self.assertIsNone(w.approved_copilot)
    def test_visual_component_toggle_clears_pending_plan(self):
        w=self.window();self.receive(w);generation=w.copilot_generation
        w.rebuild_copper=Mock(return_value=True);w.parts=Mock();w.parts.IsChecked.return_value=True
        w.revoke=Mock();ui.window_method('pick_on_board')(w,self.selected[0])
        self.assertGreater(w.copilot_generation,generation);self.assertIsNone(w.pending_copilot)
        w.parts.Check.assert_called_once()
    def test_routing_setting_guard_refuses_budget_net_and_revoked_parent(self):
        w=self.window();self.receive(w);w.assistant_ack.SetValue(True);w.use_copilot_plan(None)
        frame=controls.routing_frame();pg.prefill_copper_routing(frame,self.proposal['copper_plan'])
        expected=copy.deepcopy(self.proposal['routing_preferences'])
        self.assertEqual(frame.config(),expected)
        def guard(settings):
            w.check_copilot_plan(full=False)
            if settings!=expected:raise ValueError('reviewed routing settings changed')
        frame._settings_guard=guard
        self.assertEqual(frame.config(),expected)
        frame.seconds.SetValue('120')
        with self.assertRaisesRegex(ValueError,'changed'):frame.config()
        frame.seconds.SetValue('90');frame.nets.SetValue('ROUTE_A')
        with self.assertRaisesRegex(ValueError,'changed'):frame.config()
        frame.nets.SetValue('ROUTE_A\nROUTE_B');w.invalidate_copilot()
        with self.assertRaisesRegex(ValueError,'approve'):frame.config()
    def test_ordinary_routing_handoff_keeps_the_visible_budget(self):
        frame=controls.routing_frame()
        pg.prefill_copper_routing(frame,self.proposal['copper_plan'],seconds=pg.routing_seconds('120'))
        self.assertEqual(frame.config()['seconds'],120)
        self.assertIn('120-second',frame.status.SetLabel.call_args.args[0])
        self.assertEqual(pg.routing_seconds('090'),90)
    def test_ready_callback_refreshes_current_gates_without_granting_authority(self):
        w=self.window();w.gate.acknowledged=False
        ui.window_method('preview_ready')(w)
        w.refresh.assert_called_once();self.assertFalse(w.gate.acknowledged);self.assertIsNone(w.qualified)
        w.refresh.reset_mock();w.gate.closed=True;ui.window_method('preview_ready')(w);w.refresh.assert_not_called()

if __name__=='__main__':unittest.main()
