"""Pure source mutation and control-decision threats; no native execution."""
import copy,importlib.util,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('placement_pruning_control_driver',HERE/'driver.py');d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)

class Controls(unittest.TestCase):
    def setUp(self):self.board=(d.BASE/'smoke.kicad_pcb').read_bytes();self.original=d.sx.parse(self.board.decode())
    def test_sources_add_only_area_and_declared_negative_zone_extent(self):
        before=self.board;positive=d.sx.parse(d.derive(self.board,'redundant').decode());negative=d.sx.parse(d.derive(self.board,'necessary').decode())
        self.assertEqual(self.board,before);self.assertEqual(positive[:-1],self.original)
        self.assertEqual(negative[-1],positive[-1]);zone=d.sx.children(negative,'zone')[0]
        points=d.sx.one(d.sx.one(zone,'polygon'),'pts');self.assertEqual(points[2][1],'24');self.assertEqual(points[3][1],'24')
        points[2][1]=points[3][1]='44';self.assertEqual(negative,positive)
    def test_unknown_case_or_changed_source_rejected(self):
        with self.assertRaisesRegex(d.p.Rejected,'unknown'):d.derive(self.board,'unknown')
        changed=copy.deepcopy(self.original);d.sx.one(d.sx.children(changed,'zone')[0],'net')[1]='"WRONG"'
        with self.assertRaisesRegex(d.p.Rejected,'scene differs'):d.derive((d.sx.dump(changed)+'\n').encode(),'redundant')
    def test_bridge_replaces_all_generated_ground_only_without_mutating(self):
        tree=d.sx.parse(d.derive(self.board,'redundant').decode())
        a=d.sx.parse('(segment (start 10 10) (end 40 10) (width 0.3) (layer "F.Cu") (net "SIGNAL_A") (uuid "900d7b68-bad0-4e14-b5d6-0dfe6594ebf3"))')
        g=d.sx.parse('(segment (start 10 30) (end 20 30) (width 0.3) (layer "B.Cu") (net "GND") (uuid "1f39ee56-17a6-47db-a0fb-edc16b60dbdd"))')
        tree.extend([a,g]);before=copy.deepcopy(tree);result,recipe=d.bridge_parent(tree,{'"GND"'})
        self.assertEqual(tree,before);self.assertEqual(d.p.immutable(result),d.p.immutable(tree));self.assertIn(a,d.p.routes(result));self.assertNotIn(g,d.p.routes(result))
        self.assertEqual(recipe['removed_generated_zone_route_ids'],[d.s.route_id(g)]);self.assertFalse(recipe['reference_route_used_for_optimizer'])
        proposal=d.s.proposals(result,{'"GND"'},[],True);self.assertEqual(len(proposal),1);self.assertEqual(len(proposal[0]['route_ids']),1)
    def test_locked_or_wrong_net_parent_rejected(self):
        tree=d.sx.parse(d.derive(self.board,'redundant').decode());route=d.sx.parse('(segment (start 10 30) (end 40 30) (width 0.3) (layer "B.Cu") (net "GND") (uuid "1f39ee56-17a6-47db-a0fb-edc16b60dbdd") (locked yes))');tree.append(route)
        with self.assertRaisesRegex(d.p.Rejected,'protected'):d.bridge_parent(tree,{'"GND"'})
        with self.assertRaisesRegex(d.p.Rejected,'one GND'):d.bridge_parent(tree,{'"SIGNAL_A"'})
    def test_authored_bridge_deletion_preserves_geometry(self):
        tree=d.sx.parse(d.derive(self.board,'necessary').decode());parent,_=d.bridge_parent(tree,{'"GND"'});proposal=d.s.proposals(parent,{'"GND"'},[],True)[0]
        result=d.s.delete_routes(parent,proposal['route_ids'],{'"GND"'},[])
        self.assertEqual(d.p.routes(result),[]);self.assertEqual(d.p.immutable(result),d.p.immutable(parent))
    def native(self,opens=0,findings=None):return {'opens':opens,'blocking':0,'warnings':0,'exclusions':0,'findings':findings or [],'ignored_checks':[]}
    def test_redundant_requires_actual_native_validity_and_strict_quality_gain(self):
        good=self.native();metrics={'track_length_mm':30.,'vias':0};short={'track_length_mm':0.,'vias':0}
        self.assertTrue(d.control_observation('redundant',good,good,metrics,short)[0]);self.assertFalse(d.control_observation('redundant',good,good,metrics,metrics)[0])
        self.assertFalse(d.control_observation('redundant',self.native(1),good,metrics,short)[0]);self.assertFalse(d.control_observation('redundant',good,self.native(1),metrics,short)[0])
    def test_negative_requires_exact_native_disconnected_pad_pair_and_no_exclusions(self):
        row={'type':'unconnected_items','severity':'error','excluded':False,'items':[{'uuid':d.OUTSIDE_PAD},{'uuid':d.ZONE_UUID}]}
        bad=self.native(1,[row]);self.assertTrue(d.control_observation('necessary',self.native(),bad,{}, {})[0])
        altered=copy.deepcopy(bad);altered['findings'][0]['items'][0]['uuid']='unrelated';self.assertFalse(d.control_observation('necessary',self.native(),altered,{}, {})[0])
        altered=copy.deepcopy(bad);altered['exclusions']=1;self.assertFalse(d.control_observation('necessary',self.native(),altered,{}, {})[0])
    def test_fresh_monitored_output_is_narrow_and_cannot_reuse_attempt(self):
        with tempfile.TemporaryDirectory(dir=d.ROOT/'.runs',prefix='placement-pruning-controls-owned-') as tmp:
            outer=Path(tmp);target=outer/'run'
            self.assertEqual(d.control_output(target),target)
            for wrong in (outer/'other',outer/'nested/run'):
                with self.assertRaises(d.p.Rejected):d.control_output(wrong)
            target.mkdir()
            with self.assertRaises(d.p.Rejected):d.control_output(target)
    def test_no_explicit_native_flag_or_unpromoted_draft_can_create_output(self):
        with patch.object(d,'HERE',d.ROOT/'.runs/placement-pruning-controls-draft-001'),patch.object(d,'shared') as shared:
            with self.assertRaisesRegex(d.p.Rejected,'promote'):d.experiment(d.ROOT/'.runs/must-not-exist',run_native=True)
            with self.assertRaisesRegex(d.p.Rejected,'promote'):d.experiment(d.ROOT/'.runs/must-not-exist',run_native=False)
            shared.owned.assert_not_called()
if __name__=='__main__':unittest.main()
