import unittest,math
import copper_path as c
M=1000000
BOX=[[0,0],[10*M,0],[10*M,10*M],[0,10*M]]
def guard():return c.Guard(seconds=2,operations=100000)
class PathTests(unittest.TestCase):
    def test_exact_subnanometre_gap_is_preserved(self):
        self.assertEqual(c.point_segment_sq([2,0],[0,0],[4,1]),(4,17))
    def test_inside_leg_positive(self):
        self.assertTrue(c.certified_leg([M,M],[9*M,9*M],BOX,[],10000,guard()))
    def test_crossing_hole_rejected_even_endpoints_safe(self):
        self.assertFalse(c.certified_leg([M,5*M],[9*M,5*M],BOX,[{'center':[5*M,5*M],'radius':M}],10000,guard()))
    def test_margin_tangent_rejected(self):
        self.assertFalse(c.certified_leg([M,10000],[9*M,10000],BOX,[],10000,guard()))
    def test_polygon_concavity_leg_rejected(self):
        poly=[[0,0],[10*M,0],[10*M,10*M],[6*M,10*M],[6*M,2*M],[4*M,2*M],[4*M,10*M],[0,10*M]]
        self.assertFalse(c.certified_leg([2*M,5*M],[8*M,5*M],poly,[],10000,guard()))
    def test_narrow_neck_rejected(self):
        poly=[[0,0],[4*M,0],[4*M,4999999],[6*M,4999999],[6*M,0],[10*M,0],[10*M,10*M],[6*M,10*M],[6*M,5000001],[4*M,5000001],[4*M,10*M],[0,10*M]]
        self.assertFalse(c.certified_leg([2*M,5*M],[8*M,5*M],poly,[],10000,guard()))
    def test_all_holes_included(self):
        holes=[{'center':[0,0],'radius':1000},{'center':[5*M,5*M],'radius':1000}]
        self.assertFalse(c.certified_leg([M,M],[9*M,9*M],BOX,holes,10000,guard()))
    def test_one_bend_around_hole(self):
        pad={'center':[8*M,5*M],'outer_radius':M,'drill_radius':M//2}
        holes=[{'center':[5*M,5*M],'radius':M},{'center':pad['center'],'radius':pad['drill_radius']}]
        result=c.path_to_annulus([2*M,5*M],pad,BOX,holes,10000,[[5*M,8*M]],0,guard())
        self.assertIsNotNone(result);self.assertEqual(len(result),3)
        for a,b in zip(result,result[1:]):self.assertTrue(c.certified_leg(a,b,BOX,holes,10000,guard()))
        self.assertTrue(c.annular(result[-1],pad,10000))
    def test_no_bend_means_safe_rejection(self):
        pad={'center':[8*M,5*M],'outer_radius':M,'drill_radius':M//2}
        self.assertIsNone(c.path_to_annulus([2*M,5*M],pad,BOX,[{'center':[5*M,5*M],'radius':2*M},{'center':pad['center'],'radius':pad['drill_radius']}],10000,[],0,guard()))
    def test_rotation_translation_preserves_positive(self):
        angle=math.radians(37)
        def tr(p):return [round(math.cos(angle)*p[0]-math.sin(angle)*p[1]+31*M),round(math.sin(angle)*p[0]+math.cos(angle)*p[1]-17*M)]
        self.assertTrue(c.certified_leg(tr([M,M]),tr([9*M,9*M]),[tr(p) for p in BOX],[],10000,guard()))
    def test_reversal_preserves_membership(self):
        self.assertTrue(c.certified_leg([M,M],[9*M,9*M],list(reversed(BOX)),[],10000,guard()))
    def test_caps_fail_closed(self):
        with self.assertRaises(c.Unsupported):c.certified_leg([M,M],[9*M,9*M],BOX,[],10000,c.Guard(operations=1))
if __name__=='__main__':unittest.main(verbosity=2)
