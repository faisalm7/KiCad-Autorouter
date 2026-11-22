"""Actual whole handlers and passive geometry; no Native or UI qualification."""
import copy
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase, main
from unittest.mock import Mock
from autorouter import placement_view as view, placement_gui as gui
from tests.test_placement_copper_gui import parts_control, text_control
from tests import test_placement_source_baseline as baseline
from tests.test_placement_view import observation

Window = gui.window_type(SimpleNamespace(Frame=object))

class GeometryTests(TestCase):
    def setUp(self):
        self.obs = observation()
        self.scene = view.scene(self.obs, {}, [], self.obs['outline']['bounds_nm'])

    def screen(self, nm, size):
        sw, sh = self.scene['size']; w,h=size
        fit=min(w/sw,h/sh); l,t,s,ox,oy=self.scene['transform']
        return (round((nm[0]-l)*s*fit+ox*fit+(w-sw*fit)/2),
                round((nm[1]-t)*s*fit+oy*fit+(h-sh*fit)/2))

    def test_source_detached_and_empty_overview(self):
        original=copy.deepcopy(self.obs)
        scene=view.scene(self.obs,{},[],self.obs['outline']['bounds_nm'])
        self.assertEqual(self.obs,original)
        bounds = self.obs['outline']['bounds_nm']
        self.assertEqual(scene['size'], (800, round(800 * (bounds[3] - bounds[1]) / (bounds[2] - bounds[0]))))
        self.assertEqual(len(scene['components']),3)
        with self.assertRaises(ValueError):view.render(self.obs,{},[],self.obs['outline']['bounds_nm'])

    def test_resize_and_retina_pick_same_identity(self):
        for size in ((640,350),(900,500),(1800,1000),(1000,900)):
            with self.subTest(size=size):
                self.assertEqual(view.pick_component(self.scene,self.screen((10_000_000,10_000_000),size),size),'J1')
                self.assertEqual(view.pick_component(self.scene,self.screen((20_000_000,20_000_000),size),size),'J3')
                self.assertIsNone(view.pick_component(self.scene,(-1,-1),size))
                self.assertIsNone(view.screen_point(self.scene,(0,size[1]-1),size))

    def test_overlap_does_not_guess(self):
        duplicate=dict(self.scene['components'][0],uuid='another')
        self.scene['components']+= (duplicate,)
        self.assertIsNone(view.pick_component(self.scene,self.screen((10_000_000,10_000_000),(900,500)),(900,500)))

    def test_draw_both_directions_snap_and_no_mutation(self):
        before=copy.deepcopy(self.scene);size=(1000,540)
        a,b=self.screen((5_000_000,5_000_000),size),self.screen((30_000_000,22_000_000),size)
        value=view.drawn_region(self.scene,a,b,size)
        self.assertEqual(value,view.drawn_region(self.scene,b,a,size))
        self.assertEqual(value,[5_000_000,5_000_000,30_000_000,22_000_000])
        self.assertEqual(before,self.scene)
        with self.assertRaises(ValueError):view.drawn_region(self.scene,a,a,size)
        with self.assertRaises(ValueError):view.drawn_region(self.scene,(-100,-100),b,size)

    def test_bad_coordinates_refuse(self):
        for value in ((float('nan'),0),(True,1),('1',2),(10**10,0)):
            with self.subTest(value=value),self.assertRaises(ValueError):view.screen_point(self.scene,value,(800,600))
        for size in ((0,600),(800,-1)):
            with self.subTest(size=size),self.assertRaises(ValueError):view.screen_point(self.scene,(10,10),size)

class HandlerTests(TestCase):
    def window(self):
        obs=observation();gate=gui.ReviewGate()
        obs['scope'] = gui.intent.contract.ORDINARY_SCOPE
        gate.review=SimpleNamespace(intent={'approved':True});gate.acknowledged=True
        rows=[dict(uuid=x['uuid'],reference=x['reference'],fixed_reasons=['Locked in KiCad'] if x['locked'] else []) for x in obs['footprints']]
        # Use the real window class so handlers call its real shared methods.
        # Only external controls/lifecycle effects are controlled dependencies.
        w=Window.__new__(Window)
        vars(w).update(busy=False,gate=gate,inspection=dict(observation=obs,components=rows),qualified={'old':True},
            validation_revoked=False,ack=Mock(),picture=Mock(),routing=Mock(),findings=Mock(),refresh=Mock(),message=Mock(),
            parts=Mock(),rebuild_copper=Mock(return_value=False),revoke=Mock(),region=[Mock() for _ in range(4)],
            draw_area=Mock(),updating=False,overview=Mock(),layout_panel=Mock(),part=Mock(),coordinates=Mock(),
            copilot_generation=1,pending_copilot={'old':True},approved_copilot=None,
            assistant_ack=Mock(),assistant_result=Mock(),constraint_offer=None,constraint_review=None,pages=Mock(),
            target_region=text_control(False), rigid_group=text_control(False))
        w.parts.IsChecked.return_value=False
        return w

    def test_fixed_visual_pick_cannot_change_selection_or_approval(self):
        w=self.window();w.gate.review=None
        Window.pick_on_board(w,'J3')
        w.parts.Check.assert_not_called();w.revoke.assert_not_called()
        self.assertEqual(w.copilot_generation,1);self.assertIsNotNone(w.pending_copilot)
        self.assertIn('Locked in KiCad',w.message.call_args.args[0])

    def test_pick_uses_exact_identity_and_existing_revocation(self):
        w=self.window();w.gate.review=None
        Window.pick_on_board(w,'J1')
        w.parts.Check.assert_called_once_with(0,True);w.revoke.assert_called_once_with(discard=True)
        self.assertEqual(w.copilot_generation,2);self.assertIsNone(w.pending_copilot)
        w.assistant_ack.SetValue.assert_called_once_with(False)
        Window.pick_on_board(w,'unknown');self.assertEqual(w.parts.Check.call_count,1)

    def test_click_current_draft_focuses_without_silently_changing_it(self):
        w=self.window();w.gate.review.settings={'selected':['J1','J2']}
        Window.pick_on_board(w,'J2')
        w.part.SetSelection.assert_called_once_with(1);w.coordinates.assert_called_once()
        w.parts.Check.assert_not_called();w.revoke.assert_not_called()

    def test_draw_on_other_scopes_keeps_the_existing_region_policy(self):
        w=self.window()
        Window.area_on_board(w,[5_000_000,5_000_000,30_000_000,22_000_000])
        w.revoke.assert_called_once_with(discard=True)
        self.assertEqual([f.ChangeValue.call_args.args[0] for f in w.region],['5','5','30','22'])
        w.target_region.SetValue.assert_not_called()
        self.assertEqual(w.copilot_generation,2);self.assertIsNone(w.pending_copilot)
        w.assistant_ack.SetValue.assert_called_once_with(False)
        self.assertFalse(w.updating);self.assertFalse(w.picture.draw_area)

    def target_window(self):
        w = self.window()
        source = baseline.SourceCopperBaseline()
        source.setUp()  # Deliberately synthetic Native context over owned geometry.
        w.inspection = source.inspection()
        w.inspection['components'] = [dict(uuid=part['uuid'], reference=part['reference'], fixed_reasons=[])
                                      for part in source.observation['footprints']]
        w.region = [text_control(gui.mm(value)) for value in source.region]
        w.parts = parts_control(w.inspection['components'], [i for i, part in enumerate(w.inspection['components'])
                                                            if part['uuid'] in source.selected])
        return w, source

    def test_target_draw_derives_start_policy_only_when_an_eligible_pair_needs_it(self):
        w, source = self.target_window()
        area = [14_000_000, 8_000_000, 22_000_000, 13_000_000]
        Window.area_on_board(w, area)
        value = Window.options(w, validate_geometry=False)
        self.assertTrue(w.target_region.GetValue())
        self.assertEqual(value['region_initialization'], gui.intent.prototype.EXACT_TRACK_REGION_POLICY)
        self.assertEqual(value['region_nm'], area)
        self.assertTrue(value['preserve_existing'])
        Window.area_on_board(w, source.region)
        self.assertFalse(w.target_region.GetValue())
        w.inspection.pop('annotation_context')
        Window.area_on_board(w, area)
        self.assertFalse(w.target_region.GetValue())

    def test_target_numeric_edit_derives_mode_and_advanced_choice_can_override(self):
        w, _ = self.target_window()
        w.region[0].ChangeValue('14')
        event = Mock(); event.GetEventObject.return_value = w.region[0]
        Window.settings_changed(w, event)
        self.assertTrue(w.target_region.GetValue())
        w.target_region.SetValue(False)
        event.GetEventObject.return_value = w.target_region
        Window.settings_changed(w, event)
        self.assertFalse(w.automatic_target_area)
        self.assertNotIn('region_initialization', Window.options(w, validate_geometry=False))

    def test_invalid_or_cancelled_drag_has_no_input_or_authority_change(self):
        for region,error in (([1,1,1,2],None),([-1,0,10,10],None),(None,'outside outline')):
            w=self.window();Window.area_on_board(w,region,error)
            w.revoke.assert_not_called()
            self.assertEqual(w.copilot_generation,1);self.assertIsNotNone(w.pending_copilot)
            for field in w.region:field.ChangeValue.assert_not_called()

    def test_busy_and_closed_ignore_visual_actions(self):
        for attr in ('busy','closed'):
            w=self.window()
            if attr=='busy':w.busy=True
            else:w.gate.closed=True
            Window.pick_on_board(w,'J1');Window.area_on_board(w,[1,1,2,2])
            w.revoke.assert_not_called();w.parts.Check.assert_not_called()

    def test_late_paint_failure_revokes_handoff_without_render_retry(self):
        w=self.window();review=w.gate.review
        Window.preview_failed(w,'deliberate raster failure')
        self.assertIsNone(w.qualified);self.assertFalse(w.gate.acknowledged);self.assertIsNone(review.intent)
        w.routing.Close.assert_called_once();w.picture.SetScene.assert_called_once_with(None)
        w.overview.assert_not_called()
        self.assertIn('No current placement validation',w.findings.SetValue.call_args.args[0])

if __name__=='__main__':main(verbosity=2)
