import copy,json,unittest
from pathlib import Path
import copper_path as c
import attempt_graph_v3 as v
ROOT=Path(__file__).resolve().parent
class GraphControls(unittest.TestCase):
    def scene(self):return json.loads((ROOT/'graph-control-scene.json').read_text())
    def test_unbound_rejected(self):
        with self.assertRaises(c.Unsupported):v.run(self.scene())
    def test_positive_candidates_clear_gap_drill(self):
        g=self.scene();r=v.run(g,True)
        self.assertTrue(r['path_certificate_candidates'])
        holes=v.d.drill_census(g)[0]
        for p in r['path_certificate_candidates']:
            self.assertTrue(v.bridge_clear(p['start_nm'],p['end_nm'],holes,10000,c.Guard()))
            self.assertNotEqual(p['target_logical_terminal'],p['other_logical_terminal'])
    def test_known_bridge_crossing_rejected(self):
        holes=v.d.drill_census(self.scene())[0]
        self.assertFalse(v.bridge_clear([375000,-250000],[1000000,-250000],holes,10000,c.Guard()))
    def test_target_net_mismatch_rejected(self):
        g=self.scene();g['pads'][0]['net_code']=999
        with self.assertRaises(c.Unsupported):v.run(g,True)
    def test_body_net_mismatch_rejected(self):
        g=self.scene();g['bodies'][1]['net_code']=999
        with self.assertRaises(c.Unsupported):v.run(g,True)
    def test_body_layer_mismatch_rejected(self):
        g=self.scene();g['bodies'][1]['layer_id']=0
        with self.assertRaises(c.Unsupported):v.run(g,True)
    def test_duplicate_target_uuid_rejected(self):
        g=self.scene();g['pads'].append(copy.deepcopy(g['pads'][0]))
        with self.assertRaises(c.Unsupported):v.run(g,True)
    def test_duplicate_logical_terminal_cannot_anchor(self):
        g=self.scene();g['pads'][1]['logical_terminal']=g['pads'][0]['logical_terminal']
        self.assertFalse(v.run(g,True)['path_certificate_candidates'])
    def test_renaming_invariance(self):
        g=self.scene();base=v.run(g,True);g['target_pad_uuid']='PWR_A';g['zone_uuid']='zone_renamed'
        for i,p in enumerate(g['pads']):p['uuid']='PWR_A' if i==0 else 'RETURN_B';p['logical_terminal']=['footprint_renamed',str(i)]
        for b in g['bodies']:b['zone_uuid']='zone_renamed';b['native_outline_index']+=10
        fresh=v.run(g,True)
        coords=lambda r:[(p['start_nm'],p['end_nm']) for p in r['path_certificate_candidates']]
        self.assertEqual(coords(base),coords(fresh))
    def test_polygon_winding_and_order_invariance(self):
        g=self.scene();base=v.run(g,True)
        for b in g['bodies']:b['outer_nm']=list(reversed(b['outer_nm']))
        g['bodies'].reverse();fresh=v.run(g,True)
        coords=lambda r:[(p['start_nm'],p['end_nm']) for p in r['path_certificate_candidates']]
        self.assertEqual(coords(base),coords(fresh))
    def test_closed_crossing_rejected(self):
        g=self.scene();g['bodies'][0]['outer_nm']=[[-1000000,-1000000],[600000,1000000],[-1000000,1000000],[600000,-1000000]]
        with self.assertRaises(c.Unsupported):v.run(g,True)
    def test_waypoint_guard_is_charged(self):
        with self.assertRaises(c.Unsupported):v.waypoints(self.scene()['bodies'][0]['outer_nm'],500000,c.Guard(operations=1))
if __name__=='__main__':unittest.main(verbosity=2)
