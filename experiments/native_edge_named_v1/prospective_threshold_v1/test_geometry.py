"""One pure preparation regression, never Native threshold qualification."""
from decimal import Decimal
import unittest
from autorouter import pipeline as p,sexpr as sx
from experiments.native_edge_named_v1.prospective_threshold_v1 import controller as t

class FrozenGeometry(unittest.TestCase):
    def test_four_authored_controls_preserve_source_and_original_class_dimensions(self):
        original=sx.read(t.SOURCE);protected=p.routes(original)
        native=t.f.read_json(t.importer.BASE/'native-preparation/literal300/native-netclasses.json')
        left=Decimal(sx.one(sx.one(original,'gr_rect'),'start')[1])
        project=t.f.read_json(t.SOURCE.with_suffix('.kicad_pro'))
        self.assertEqual(Decimal(str(project['board']['design_settings']['rules']['min_copper_edge_clearance'])),Decimal('.3'))
        for name,kind,x,positive in t.CASES:
            with self.subTest(case=name):
                tree=t.candidate_tree(original,name,kind,x)
                self.assertEqual(p.immutable(tree),p.immutable(original))
                self.assertEqual(p.routes(tree)[:len(protected)],protected)
                self.assertEqual(p.audit_route_dimensions(tree,protected,native)['checked'],
                                 dict(segments=5,arcs=0,vias=int(kind=='via'),protected=1))
                new=[row for row in p.routes(tree) if row not in protected]
                if kind=='track':
                    gap=min(min(Decimal(sx.one(row,'start')[1]),Decimal(sx.one(row,'end')[1]))-
                            Decimal(sx.one(row,'width')[1])/2-left for row in new)
                else:
                    via=next(row for row in new if row[0]=='via')
                    gap=Decimal(sx.one(via,'at')[1])-Decimal(sx.one(via,'size')[1])/2-left
                    self.assertTrue(all(min(Decimal(sx.one(row,'start')[1]),Decimal(sx.one(row,'end')[1]))-
                                        Decimal(sx.one(row,'width')[1])/2-left>Decimal('.3')
                                        for row in new if row[0]=='segment'))
                self.assertEqual(gap,Decimal('.35') if positive else Decimal('.25'))
        self.assertEqual(sx.read(t.SOURCE),original)

if __name__=='__main__':unittest.main()
