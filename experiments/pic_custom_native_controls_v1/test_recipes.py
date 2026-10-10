import copy,unittest
from fractions import Fraction
import recipes as g

class Controls(unittest.TestCase):
    def test_source_shapes_are_single_five_vertex_polygons(self):
        self.assertEqual((len(g.CONVEX),len(g.CONCAVE)),(5,5));self.assertEqual(len(g.hull(g.CONVEX)),5);self.assertEqual(len(g.hull(g.CONCAVE)),4)
    def test_anchor_non_strict_containment_and_real_boundary_touch(self):
        for poly in (g.CONVEX,g.CONCAVE):
            self.assertTrue(all(g.inside(poly,p) for p in (*g.ANCHOR,(-150000,0),(150000,0),(0,150000),(0,-150000))))
        self.assertTrue(g.inside(g.CONCAVE,(-150000,0)));self.assertFalse(g.inside(g.CONCAVE,(-150000,0),boundary=False))
    def test_positive_real_contact_on_both_polygons(self):
        for variant in ('front0','back90'):
            s=g.scene('positive',variant);t=s['tracks'][0]
            self.assertTrue(g.inside(s['pads'][0]['polygon'],t['start'],boundary=False));self.assertTrue(g.inside(s['pads'][1]['polygon'],t['end'],boundary=False))
    def test_false_endpoint_inside_hull_but_entire_capsule_outside_pad(self):
        for variant in ('front0','back90'):
            s=g.scene('false_hull',variant);t=s['tracks'][0];poly=s['pads'][1]['polygon']
            self.assertTrue(g.inside(g.hull(poly),t['end'],boundary=False));self.assertFalse(g.inside(poly,t['end']))
            self.assertGreater(g.segment_gap2(t['start'],t['end'],poly),Fraction(350000**2))
            self.assertAlmostEqual(g.analytic('false_hull',variant)['capsule_to_pad_gap_nm'],124422.632452029,places=5)
    def test_bad_false_control_that_really_touches_is_detected(self):
        s=g.scene('false_hull');p=s['pads'][1]['polygon'];start=s['tracks'][0]['start'];end=(19800000,15000000)
        self.assertLess(g.segment_gap2(start,end,p),Fraction((g.WIDTH//2)**2))
    def test_false_case_changes_only_contact_track_endpoint(self):
        for variant in ('front0','back90'):
            a=g.scene('positive',variant);b=g.scene('false_hull',variant);a['case']=b['case'];a['tracks'][0]['end']=b['tracks'][0]['end'];self.assertEqual(a,b)
    def test_foreign_intrusion_keeps_both_original_foreign_contacts(self):
        for variant in ('front0','back90'):
            s=g.scene('foreign_intrusion',variant);t=s['tracks'][1]
            self.assertTrue(g.on(t['start'],t['end'],s['pads'][3]['at']))
            self.assertTrue(g.inside(s['pads'][1]['polygon'],t['end'],boundary=False));self.assertNotEqual(t['net'],s['pads'][1]['net'])
    def test_foreign_case_changes_only_foreign_track_endpoint(self):
        for variant in ('front0','back90'):
            a=g.scene('positive',variant);b=g.scene('foreign_intrusion',variant);a['case']=b['case'];a['tracks'][1]['end']=b['tracks'][1]['end'];self.assertEqual(a,b)
    def test_orthogonal_back_transform_preserves_exact_distances(self):
        a,b,c=(1,2),(333,779),(-454,588)
        self.assertEqual(g.distance2(a,b,c),g.distance2(g.transform(a,'back90'),g.transform(b,'back90'),g.transform(c,'back90')))
        self.assertEqual(g.transform(g.transform(a,'back90'),'back90'),a)
    def test_no_rule_or_width_relaxation_in_any_case(self):
        for variant in ('front0','back90'):
            for case in ('positive','false_hull','foreign_intrusion'):
                s=g.scene(case,variant);self.assertEqual({t['width_nm'] for t in s['tracks']},{500000});self.assertFalse(s['native_executed']);self.assertFalse(s['custom_pad_support_qualified'])
    def test_unknown_variants_reject(self):
        with self.assertRaises(ValueError):g.scene('whatever')
        with self.assertRaises(ValueError):g.scene('positive','whatever')
    def test_positive_contacts_require_primitive_not_only_anchor(self):
        for variant in ('front0','back90'):
            s=g.scene('positive',variant);track=s['tracks'][0]
            for center in ((10000000,15000000),(20000000,15000000)):
                anchor=tuple(g.transform(p,variant) for p in g.move(g.ANCHOR,center))
                self.assertGreater(g.segment_gap2(track['start'],track['end'],anchor),Fraction((g.WIDTH//2)**2))
    def test_foreign_negative_hits_custom_body_without_touching_anchor_or_contact_route(self):
        for variant in ('front0','back90'):
            s=g.scene('foreign_intrusion',variant);t=s['tracks'][1];main=s['tracks'][0]
            anchor=tuple(g.transform(p,variant) for p in g.move(g.ANCHOR,(20000000,15000000)))
            self.assertGreater(g.segment_gap2(t['start'],t['end'],anchor),Fraction((g.WIDTH//2)**2))
            self.assertFalse(g.intersects(t['start'],t['end'],main['start'],main['end']))
            dist=min(g.distance2(t['start'],main['start'],main['end']),g.distance2(t['end'],main['start'],main['end']),g.distance2(main['start'],t['start'],t['end']),g.distance2(main['end'],t['start'],t['end']))
            self.assertGreater(dist,Fraction(750000**2))

if __name__=='__main__':unittest.main()
