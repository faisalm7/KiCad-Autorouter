import copy
import unittest
from .ring import MAX_NM, separate


class RingMath(unittest.TestCase):
    def result(self, polygons, **kwargs):
        return separate(polygons, kwargs.get('center',[0,0]), kwargs.get('r2',100),
                        kwargs.get('stroke',1), kwargs.get('clearance',0))

    def test_filled_polygon_strictly_inside_hole(self):
        value=self.result([[[-1,-1],[1,-1],[0,1]]])
        self.assertTrue(value['clear']);self.assertEqual(value['inner_hole_nm'],8)
        self.assertEqual(value['contour_classification'],['inside-inner-hole'])
        self.assertTrue(value['holes_filled_conservatively']);self.assertFalse(value['Native_concordance_proven'])

    def test_strictly_outside_disk(self):
        value=self.result([[[13,-1],[15,-1],[15,1],[13,1]]])
        self.assertTrue(value['clear']);self.assertEqual(value['outer_disk_nm'],12)

    def test_tangent_inner_or_outer_is_never_clear(self):
        for p in ([[[8,0],[7,1],[7,-1]]], [[[12,-1],[13,-1],[13,1],[12,1]]]):
            with self.subTest(p=p):self.assertFalse(self.result(p)['clear'])

    def test_circle_inside_filled_polygon_is_not_clear(self):
        self.assertFalse(self.result([[[-20,-20],[20,-20],[20,20],[-20,20]]])['clear'])

    def test_all_vertices_outside_but_edges_cross_disk_is_not_clear(self):
        p=[[-20,-1],[20,-1],[20,1],[-20,1]]
        self.assertTrue(all(x*x+y*y>144 for x,y in p))
        self.assertFalse(self.result([p])['clear'])

    def test_polygon_within_ring_is_not_clear(self):
        self.assertFalse(self.result([[[9,0],[10,0],[9,1]]])['clear'])

    def test_each_disconnected_contour_has_its_own_proof(self):
        p=[[[-1,-1],[1,-1],[0,1]],[[13,-1],[15,-1],[15,1],[13,1]]]
        value=self.result(p);self.assertTrue(value['clear'])
        self.assertEqual(value['contour_classification'],['inside-inner-hole','outside-outer-disk'])
        p.append([[9,0],[10,0],[9,1]])
        self.assertFalse(self.result(p)['clear'])

    def test_odd_width_clearance_and_irrational_radius_expand_outward(self):
        value=self.result([[[15,-1],[16,-1],[16,1],[15,1]]],stroke=3,clearance=1)
        self.assertEqual((value['radius_interval_nm'],value['half_stroke_ceil_nm'],value['inner_hole_nm'],value['outer_disk_nm']),([9,11],2,6,14))
        self.assertTrue(value['clear'])
        value=self.result([[[14,-1],[15,-1],[15,1],[14,1]]],r2=101)
        self.assertEqual(value['radius_interval_nm'],[9,12]);self.assertEqual(value['outer_disk_nm'],13)
        self.assertTrue(value['clear'])

    def test_negative_translation_vertex_and_contour_relabel_invariance(self):
        p=[[[-1,-1],[1,-1],[0,1]],[[13,-1],[15,-1],[15,1],[13,1]]]
        before=copy.deepcopy(p);expected=self.result(p)['clear']
        for dx,dy in ((-100,-200),(1000000000,-1000000000)):
            moved=[[[x+dx,y+dy]for x,y in row]for row in p]
            self.assertEqual(self.result(moved,center=[dx,dy])['clear'],expected)
        self.assertEqual(self.result([list(reversed(row[1:]+row[:1]))for row in reversed(p)])['clear'],expected)
        self.assertEqual(p,before)

    def test_nonconvex_outer_contour_still_checks_every_edge_and_enclosure(self):
        p=[[-20,-20],[20,-20],[20,20],[15,20],[15,-15],[-15,-15],[-15,20],[-20,20]]
        self.assertTrue(self.result([p])['clear'])
        p[4:6]=[[15,-5],[-15,-5]]
        self.assertFalse(self.result([p])['clear'])

    def test_degenerate_unknown_type_and_population_refusals(self):
        invalid=[[],[[]],[[[0,0],[1,1],[2,2]]],[[[0,0],[1,0],[0,0]]],
            [[[0,0],[2,2],[0,2],[2,0]]],[[[0,0],[3,0],[2,0],[2,1],[0,1]]],
            [[[0,0],[4,4],[0,5],[5,0],[5,5]]],
            [{'kind':'arc'}],[[[False,0],[1,0],[0,1]]],[[[0.0,0],[1,0],[0,1]]],
            [[['0',0],[1,0],[0,1]]],[[[MAX_NM+1,0],[1,0],[0,1]]],
            [[[0,0],[1,0],[0,1]]]*65,[[[i,i%2]for i in range(4097)]]]
        for value in invalid:
            with self.subTest(value=repr(value)[:80]),self.assertRaises(ValueError):self.result(value)

    def test_circle_bounds_and_exact_integer_parameters(self):
        p=[[[-1,-1],[1,-1],[0,1]]]
        for kw in (dict(center=[MAX_NM,0]),dict(r2=True),dict(r2=0),dict(r2=10**100),
                   dict(stroke=0),dict(stroke=True),dict(clearance=-1),dict(clearance=float('nan'))):
            with self.subTest(kw=kw),self.assertRaises(ValueError):self.result(p,**kw)


if __name__=='__main__':unittest.main()
