"""Small fake-Native capture fences; actual API concordance is separate evidence."""
import copy
from types import SimpleNamespace
import unittest

from experiments.native_annotation_geometry_v1 import native as n


def xy(x, y): return SimpleNamespace(x=x, y=y)


class Line:
    def __init__(self, points): self.points = points
    def PointCount(self): return len(self.points)
    def CPoint(self, index): return xy(*self.points[index])


class Poly:
    def __init__(self):
        self.rows = [dict(outer=[[100, 200], [200, 200], [200, 300], [100, 300]],
                         holes=[[[120, 220], [140, 220], [140, 240], [120, 240]]])]
        self.arcs = 0
    def OutlineCount(self): return len(self.rows)
    def ArcCount(self): return self.arcs
    def HoleCount(self, index): return len(self.rows[index]['holes'])
    def COutline(self, index): return Line(self.rows[index]['outer'])
    def CHole(self, index, hole): return Line(self.rows[index]['holes'][hole])


class Text:
    def __init__(self):
        self.visible = True; self.knockout = False; self.font = ''; self.bold = self.italic = self.mirror = False
        self.raw = self.shown = 'R2'; self.angle = 90.; self.pen = 150000; self.calls = []
        self.mutate = None
    def IsVisible(self): return self.visible
    def IsKnockout(self): return self.knockout
    def GetFontName(self): return self.font
    def IsBold(self): return self.bold
    def IsItalic(self): return self.italic
    def IsMirrored(self): return self.mirror
    def GetText(self): return self.raw
    def GetShownText(self, allow):
        assert allow is True
        return self.shown
    def GetTextAngleDegrees(self): return self.angle
    def GetEffectiveTextPenWidth(self): return self.pen
    def TransformTextToPolySet(self, poly, clearance, error, location):
        self.calls.append((clearance, error, location))
        if self.mutate: self.mutate(poly)


class Circle:
    def __init__(self):
        self.m_Uuid = SimpleNamespace(AsString=lambda:'fixed-circle')
        self.start = [1000,2000]; self.end = [1100,2000]; self.radius = 100; self.width = 11
        self.shape = 2; self.fill = 0; self.layer = 37; self.locked = False
    def GetShape(self): return self.shape
    def GetFillMode(self): return self.fill
    def GetLayer(self): return self.layer
    def IsLocked(self): return self.locked
    def GetStart(self): return xy(*self.start)
    def GetEnd(self): return xy(*self.end)
    def GetRadius(self): return self.radius
    def GetWidth(self): return self.width


PCB = SimpleNamespace(PCB_TEXT=Text, PCB_SHAPE=Circle, SHAPE_POLY_SET=Poly,
    SHAPE_T_CIRCLE=2, FILL_T_NO_FILL=0, FILL_T_FILLED_SHAPE=1, F_SilkS=37, ERROR_OUTSIDE=1)


def source():
    return dict(kind='fp_circle',uuid='fixed-circle',fill='none',stroke_type='solid',
        layer='F.SilkS',locked=False,center_nm=[1000,2000],end_nm=[1100,2000],radius_nm=100,stroke_nm=11)


class NativeAnnotationGeometryTests(unittest.TestCase):
    def test_text_exact_outward_contours_are_detached_relative_and_holes_filled(self):
        text = Text(); result = n.capture_text(text, PCB, [50,100])
        self.assertEqual(result, dict(kind='default-text-outer-polygons-v1', error_nm=1000,
            outer_contours_nm=[[[50,100],[150,100],[150,200],[50,200]]],holes_filled=True,
            holes_count=1,font_name='',text='R2',effective_pen_width_nm=150000))
        self.assertEqual(text.calls, [(0,1000,PCB.ERROR_OUTSIDE)])
        result['outer_contours_nm'][0][0][0] += 1
        self.assertEqual(n.capture_text(text,PCB,[50,100])['outer_contours_nm'][0][0],[50,100])

    def test_known_unsupported_text_features_use_only_the_typed_exception(self):
        for field, value in (('visible',False),('knockout',True),('font','Arial'),('bold',True),
                ('italic',True),('mirror',True),('raw',''),('raw','x'*257),('shown','other'),
                ('raw','line\ntext'),('angle',45.),('pen',10000001)):
            text=Text();setattr(text,field,value)
            with self.subTest(field=field),self.assertRaises(n.UnsupportedGeometry):
                n.capture_text(text,PCB,[0,0])
            self.assertFalse(text.calls)

    def test_malformed_getters_do_not_become_supported_fallback(self):
        for field,value in (('visible',1),('font',None),('angle',True),('angle',float('nan')),('pen',False),('pen',0)):
            text=Text();setattr(text,field,value)
            with self.subTest(field=field):
                try:n.capture_text(text,PCB,[0,0])
                except ValueError as exc:self.assertNotIsInstance(exc,n.UnsupportedGeometry)
                else:self.fail('malformed getter accepted')

    def test_unexpected_Native_errors_propagate(self):
        text=Text()
        def explode(poly):raise RuntimeError('actual Native failure')
        text.mutate=explode
        with self.assertRaisesRegex(RuntimeError,'actual Native failure'):n.capture_text(text,PCB,[0,0])

    def test_conversion_bounds_include_hole_vertices_and_empty_or_arc_is_unsupported(self):
        for fault in ('empty','outlines','arcs','hole-total','outer-total'):
            text=Text()
            def mutate(poly,fault=fault):
                if fault=='empty':poly.rows=[]
                if fault=='outlines':poly.rows*=65
                if fault=='arcs':poly.arcs=1
                if fault=='hole-total':poly.rows[0]['holes']=[[[0,0],[1,0],[1,1]]]*1365
                if fault=='outer-total':poly.rows[0]['outer']=[[i,0]for i in range(4097)]
            text.mutate=mutate
            with self.subTest(fault=fault),self.assertRaises(n.UnsupportedGeometry):n.capture_text(text,PCB,[0,0])

    def test_noninteger_native_points_and_mutation_during_detachment_fail_closed(self):
        text=Text();text.mutate=lambda poly:poly.rows[0]['outer'][0].__setitem__(0,.5)
        with self.assertRaises(ValueError)as caught:n.capture_text(text,PCB,[0,0])
        self.assertNotIsInstance(caught.exception,n.UnsupportedGeometry)
        class ChangingPoly(Poly):
            def __init__(self):super().__init__();self.reads=0
            def COutline(self,index):
                self.reads+=1
                if self.reads>1:self.rows[0]['outer'][0][0]+=1
                return super().COutline(index)
        pcb=copy.copy(PCB);pcb.SHAPE_POLY_SET=ChangingPoly
        with self.assertRaisesRegex(ValueError,'changed during detachment'):n.capture_text(Text(),pcb,[0,0])

    def test_second_read_cannot_coerce_fractional_or_boolean_coordinates(self):
        for original,changed in ((100,100.5),(1,True)):
            class CoercingPoly(Poly):
                def __init__(self):
                    super().__init__();self.reads=0;self.rows[0]['outer'][0][0]=original
                def COutline(self,index):
                    self.reads+=1
                    if self.reads>1:self.rows[0]['outer'][0][0]=changed
                    return super().COutline(index)
            pcb=copy.copy(PCB);pcb.SHAPE_POLY_SET=CoercingPoly
            with self.subTest(changed=changed),self.assertRaisesRegex(ValueError,'exact integer Native polygon'):
                n.capture_text(Text(),pcb,[0,0])

    def test_second_read_census_types_are_exact(self):
        for field in ('OutlineCount','HoleCount'):
            class ChangingCount(Poly):
                def __init__(self):super().__init__();self.count_reads=0
            original=getattr(Poly,field)
            def count(poly,*args):
                poly.count_reads+=1
                return True if poly.count_reads>1 else original(poly,*args)
            setattr(ChangingCount,field,count)
            pcb=copy.copy(PCB);pcb.SHAPE_POLY_SET=ChangingCount
            with self.subTest(field=field),self.assertRaisesRegex(ValueError,'exact nonnegative Native polygon count'):
                n.capture_text(Text(),pcb,[0,0])

    def test_circle_exact_source_witness_and_owner_relative_integer_ring(self):
        row=source();before=copy.deepcopy(row)
        self.assertEqual(n.capture_circle(Circle(),PCB,[900,1900],row),
            dict(kind='unfilled-circle-v1',center_nm=[100,100],end_nm=[200,100],stroke_nm=11))
        self.assertEqual(row,before)

    def test_non_axis_circle_keeps_exact_source_radius_with_bounded_Native_rounding(self):
        circle=Circle();circle.end=[1100,2001]
        row=source();row.update(end_nm=[1100,2001],radius_nm=101)
        self.assertEqual(n.capture_circle(circle,PCB,[0,0],row)['end_nm'],[1100,2001])
        row['radius_nm']=100
        with self.assertRaisesRegex(ValueError,'radius/stroke'):
            n.capture_circle(circle,PCB,[0,0],row)

    def test_circle_tampered_witness_or_Native_metadata_is_fatal(self):
        for field,value in (('uuid','wrong'),('layer','B.SilkS'),('locked',True),
                ('center_nm',[1001,2000]),('end_nm',[1101,2000]),('radius_nm',101),('stroke_nm',12)):
            row=source();row[field]=value
            with self.subTest(field=field):
                try:n.capture_circle(Circle(),PCB,[0,0],row)
                except ValueError as exc:self.assertNotIsInstance(exc,n.UnsupportedGeometry)
                else:self.fail('changed circle metadata accepted')
        for field,value in (('shape',3),('fill',1),('radius',True),('width',False)):
            circle=Circle();setattr(circle,field,value)
            with self.subTest(field=field):
                try:n.capture_circle(circle,PCB,[0,0],source())
                except ValueError as exc:self.assertNotIsInstance(exc,n.UnsupportedGeometry)
                else:self.fail('changed Native getter accepted')

    def test_known_unsupported_circle_and_input_anchor_fences(self):
        for change in ({'kind':'fp_arc'},{'fill':'solid'},{'stroke_type':'dash'}):
            row=dict(source(),**change)
            circle=Circle()
            if change.get('fill')=='solid':circle.fill=1
            with self.subTest(change=change),self.assertRaises(n.UnsupportedGeometry):
                n.capture_circle(circle,PCB,[0,0],row)
        circle=Circle();circle.width=0;row=source();row['stroke_nm']=0
        with self.assertRaises(n.UnsupportedGeometry):n.capture_circle(circle,PCB,[0,0],row)
        for anchor in ([True,0],[0.5,0],[0],(0,0),[2000000001,0]):
            with self.subTest(anchor=anchor),self.assertRaises(ValueError):n.capture_text(Text(),PCB,anchor)

    def test_missing_witness_fields_or_fill_mismatch_are_not_typed_fallback(self):
        for missing in ('kind','stroke_type','radius_nm','uuid','locked'):
            row=source();row.pop(missing)
            with self.subTest(missing=missing):
                try:n.capture_circle(Circle(),PCB,[0,0],row)
                except ValueError as exc:self.assertNotIsInstance(exc,n.UnsupportedGeometry)
                else:self.fail('missing evidence accepted')
        row=source();row['fill']='solid'
        with self.assertRaises(ValueError)as caught:n.capture_circle(Circle(),PCB,[0,0],row)
        self.assertNotIsInstance(caught.exception,n.UnsupportedGeometry)


if __name__=='__main__':unittest.main()
