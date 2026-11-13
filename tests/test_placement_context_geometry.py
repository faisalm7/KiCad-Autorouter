"""Pure source and independent witness-seam controls, never Native proof."""
import copy
import hashlib
import json
from math import isqrt
from types import SimpleNamespace
import unittest

from experiments.placement_native_proposal_v1 import contract as c, ordinary as o
from experiments.placement_native_proposal_v1 import ordinary_native as native, ordinary_fixture as fixture


def uid(name): return fixture.uid('context-control:' + name)
def raw(tree): return (c.sx.dump(tree) + '\n').encode()
def stroke(width='0.1', style='default'): return ['stroke', ['width', width], ['type', style]]
def graphic(kind, name, *geometry, layer='F.Fab', fill='none', width='0.1', style='default'):
    return [kind, *geometry, stroke(width, style), ['fill', fill], ['layer', json.dumps(layer)], ['uuid', json.dumps(uid(name))]]
def shapes(prefix='front', layer='F.Fab'):
    return [graphic('fp_circle', prefix+'-circle', ['center','1','2'], ['end','3','2'], layer=layer),
            graphic('fp_arc', prefix+'-arc', ['start','1','0'], ['mid','0','1'], ['end','-1','0'], layer=layer),
            graphic('fp_poly', prefix+'-poly', ['pts',['xy','0','0'],['xy','2','0'],['xy','1','1']],
                    layer=layer, fill='solid', width='0', style='solid')]
def field(name, reference, *, back=False):
    return ['property','"Reference"',json.dumps(reference),['at',*(['1','2','90'] if back else ['0','0','0'])],
            ['layer',json.dumps('B.SilkS' if back else 'F.SilkS')],['uuid',json.dumps(uid(name))],
            ['effects',['font',['size','1','1'],['thickness','0.15']],*([['justify','mirror']] if back else [])]]
def context_board():
    tree=fixture.board()
    tree[:]=[row for row in tree if not (type(row) is list and row and row[0] in ('footprint','segment','zone','gr_text'))]
    tree.append(['footprint','"Owned:physical"',['layer','"F.Cu"'],['uuid',json.dumps(uid('front'))],
                 ['at','10','20','90'],field('front-ref','F1'),
                 graphic('fp_rect','court',['start','-1','-1'],['end','1','1'],layer='F.CrtYd',width='0.05'),
                 *shapes()])
    tree.append(['footprint','"Owned:artwork"',['layer','"B.Cu"'],['uuid',json.dumps(uid('back'))],
                 ['at','20','20','90'],['attr','board_only','exclude_from_pos_files','exclude_from_bom'],
                 field('back-ref','LOGO',back=True),
                 graphic('fp_poly','back-poly',['pts',['xy','0','0'],['xy','2','0'],['xy','1','1']],
                         layer='B.SilkS',fill='solid',width='0',style='solid'),
                 ['fp_line',['start','-1','0.5'],['end','0.5','2'],stroke(),['layer','"B.SilkS"'],
                  ['uuid',json.dumps(uid('back-line'))]]])
    return tree


class NativeText:
    def __init__(self, name, text, pos, layer, angle=0, mirrored=False):
        self.m_Uuid=SimpleNamespace(AsString=lambda:uid(name));self.text=text;self.pos=pos
        self.layer=layer;self.angle=angle;self.mirrored=mirrored
    def GetText(self):return self.text
    def GetPosition(self):return SimpleNamespace(x=self.pos[0],y=self.pos[1])
    def GetLayer(self):return self.layer
    def GetTextAngleDegrees(self):return self.angle
    def IsMirrored(self):return self.mirrored


class NativeShape:
    def __init__(self,name,kind,layer,*,start=None,end=None,mid=None,points=None,width=100000,fill=0,style=-1):
        self.m_Uuid=SimpleNamespace(AsString=lambda:uid(name));self.kind=kind;self.layer=layer
        self.start=start;self.end=end;self.mid=mid;self.points=points;self.width=width;self.fill=fill
        self.style=style;self.locked=False;self.swapped=False;self.holes=0;self.arcs=0;self.outlines=1;self.radius_delta=0
    def GetLayer(self):return self.layer
    def GetShape(self):return self.kind
    def GetStart(self):return SimpleNamespace(x=self.start[0],y=self.start[1])
    def GetEnd(self):return SimpleNamespace(x=self.end[0],y=self.end[1])
    def GetArcMid(self):return SimpleNamespace(x=self.mid[0],y=self.mid[1])
    def GetWidth(self):return self.width
    def GetRadius(self):
        squared=sum((self.end[i]-self.start[i])**2 for i in range(2));root=isqrt(squared)
        return root+int(squared-root**2>root)+self.radius_delta
    def GetLineStyle(self):return self.style
    def GetFillMode(self):return self.fill
    def IsLocked(self):return self.locked
    def EndsSwapped(self):return self.swapped
    def GetPolyShape(self):return self
    def OutlineCount(self):return self.outlines
    def HoleCount(self,index):return self.holes
    def ArcCount(self):return self.arcs
    def COutline(self,index):return self
    def PointCount(self):return len(self.points)
    def CPoint(self,index):return SimpleNamespace(x=self.points[index][0],y=self.points[index][1])
    def GetPolyPoints(self):return [self.CPoint(index) for index in range(len(self.points))]


class NativeFootprint:
    def __init__(self,name,reference,pos,layer,graphics,field,*,back=False):
        self.m_Uuid=SimpleNamespace(AsString=lambda:uid(name));self.reference=reference;self.pos=pos
        self.layer=layer;self.graphics=graphics;self.field=field;self.back=back
        self.attributes=7 if back else 0;self.models=[];self.pads=[]
    def GetReference(self):return self.reference
    def GetPosition(self):return SimpleNamespace(x=self.pos[0],y=self.pos[1])
    def GetOrientationDegrees(self):return 90
    def GetLayer(self):return self.layer
    def IsFlipped(self):return self.back
    def IsLocked(self):return False
    def Zones(self):return []
    def GetFields(self):return [self.field]
    def GetField(self,name):return self.field if name=='Reference' else None
    def GraphicalItems(self):return self.graphics
    def Pads(self):return self.pads
    def GetAttributes(self):return self.attributes
    def Models(self):return self.models


def independent_native():
    """Hand-entered world witnesses, not generated from parser observations."""
    pcb=SimpleNamespace(F_Cu=0,B_Cu=2,F_CrtYd=31,F_Fab=33,F_SilkS=37,B_SilkS=39,Edge_Cuts=44,
        SHAPE_T_RECT=1,SHAPE_T_SEGMENT=2,SHAPE_T_CIRCLE=3,SHAPE_T_ARC=4,SHAPE_T_POLY=5,
        FILL_T_NO_FILL=0,FILL_T_FILLED_SHAPE=1,FP_BOARD_ONLY=1,FP_EXCLUDE_FROM_POS_FILES=2,
        FP_EXCLUDE_FROM_BOM=4,PCB_SHAPE=NativeShape,PCB_TEXT=NativeText)
    class Formatter:
        def Format(self,item): self.item=item
        def GetStringOutput(self,clear):
            return c.sx.dump(['fp_shape',['uuid',json.dumps(self.item.m_Uuid.AsString())],
                ['stroke',['type',{-1:'default',0:'solid'}.get(self.item.style,'dash')]]])
    pcb.PCB_IO_KICAD_SEXPR=Formatter
    front=[NativeShape('court',1,31,start=[9000000,21000000],end=[11000000,19000000],width=50000),
        NativeShape('front-circle',3,33,start=[12000000,19000000],end=[12000000,17000000]),
        NativeShape('front-arc',4,33,start=[10000000,19000000],mid=[11000000,20000000],end=[10000000,21000000]),
        NativeShape('front-poly',5,33,points=[[10000000,20000000],[10000000,18000000],[11000000,19000000]],width=0,fill=1,style=0)]
    back=[NativeShape('back-poly',5,39,points=[[20000000,20000000],[20000000,18000000],[21000000,19000000]],width=0,fill=1,style=0),
        NativeShape('back-line',2,39,start=[20500000,21000000],end=[22000000,19500000])]
    fps=[NativeFootprint('front','F1',[10000000,20000000],0,front,NativeText('front-ref','F1',[10000000,20000000],37)),
         NativeFootprint('back','LOGO',[20000000,20000000],2,back,NativeText('back-ref','LOGO',[22000000,19000000],39,90,True),back=True)]
    outline_id=c.uid(c.sx.one(fixture.board(),'gr_rect'))
    edge=NativeShape('unused',1,44,start=[6000000,6000000],end=[32000000,30000000],width=50000)
    edge.m_Uuid=SimpleNamespace(AsString=lambda:outline_id)
    board=SimpleNamespace(GetCopperLayerCount=lambda:2,GetDrawings=lambda:[edge],GetFootprints=lambda:fps,
                          GetPads=lambda:[],GetTracks=lambda:[])
    fc=SimpleNamespace(observe_areas=lambda *_:dict(footprint_zone_count=0,footprint_rulearea_count=0,zones=[]))
    return board,pcb,fc,fps


class ContextGeometryTests(unittest.TestCase):
    def test_default_observation_is_frozen_and_context_ordinary_rows_do_not_change(self):
        material=raw(fixture.board());old=o.inspect(material)
        # Pre-change ordinary.py HEAD observation pin: default rows stay exact.
        self.assertEqual(hashlib.sha256(json.dumps(old,sort_keys=True).encode()).hexdigest(),
                         'bf6f867af41082d0be6b45dbec6b0f071274fb9e032716d5940abc4ff2b89185')
        self.assertEqual(old,o.inspect(material,scope=c.ORDINARY_SCOPE))
        context=o.inspect(material,scope=c.CONTEXT_SCOPE);context['scope']=c.ORDINARY_SCOPE
        self.assertEqual(old,context)

    def test_exact_rotated_fixed_shapes_and_back_artwork_are_observations_only(self):
        tree=context_board();before=copy.deepcopy(tree);observation=o.inspect(raw(tree),scope=c.CONTEXT_SCOPE)
        front=next(row for row in observation['footprints'] if row['reference']=='F1')
        back=next(row for row in observation['footprints'] if row['reference']=='LOGO')
        self.assertEqual(observation['scope'],c.CONTEXT_SCOPE);self.assertEqual(tree,before)
        self.assertFalse(front['placement_eligible']);self.assertFalse(back['placement_eligible'])
        self.assertTrue(back['artwork_only']);self.assertIsNone(back['courtyard']);self.assertEqual(back['pads'],[])
        circle=next(row for row in front['graphics'] if row['kind']=='fp_circle')
        self.assertEqual(circle['center_nm'],[12000000,19000000]);self.assertEqual(circle['end_nm'],[12000000,17000000])
        poly=next(row for row in back['graphics'] if row['kind']=='fp_poly')
        self.assertEqual(poly['points_nm'],[[20000000,20000000],[20000000,18000000],[21000000,19000000]])
        self.assertTrue(next(row for row in back['graphics'] if row['kind']=='property')['mirrored'])

    def test_added_passive_shape_fixes_two_pad_smd_without_widening_moving_geometry(self):
        tree=fixture.board();fp=next(fp for fp in c.sx.children(tree,'footprint') if fixture.base.reference(fp)=='J1')
        fp.extend(shapes());observed=o.inspect(raw(tree),scope=c.CONTEXT_SCOPE)
        self.assertFalse(next(row for row in observed['footprints'] if row['reference']=='J1')['placement_eligible'])
        self.assertTrue(next(row for row in observed['footprints'] if row['reference']=='J2')['placement_eligible'])
        with self.assertRaises(ValueError):o.inspect(raw(tree))

    def test_hazardous_and_ambiguous_source_geometry_stays_refused(self):
        for fault in ('copper','unknown','stroke_color','fill','zero_radius','huge_circle','huge_arc','collinear_arc','filled_arc','poly_arc',
                      'zero_signed_area','duplicate_point','oversize_polygon','back_pad','back_courtyard','back_model','back_not_board_only','front_no_courtyard'):
            with self.subTest(fault=fault):
                tree=context_board();front,back=c.sx.children(tree,'footprint')
                circle=c.sx.one(front,'fp_circle');arc=c.sx.one(front,'fp_arc');poly=c.sx.one(front,'fp_poly')
                if fault=='copper':c.sx.one(circle,'layer')[1]='"F.Cu"'
                if fault=='unknown':circle.append(['net','1'])
                if fault=='stroke_color':c.sx.one(circle,'stroke').append(['color','1','1','1','1'])
                if fault=='fill':c.sx.one(poly,'fill')[1]='hatch'
                if fault=='zero_radius':c.sx.one(circle,'end')[1:]=['1','2']
                if fault=='huge_circle':c.sx.one(circle,'end')[1:]=['2000','2']
                if fault=='huge_arc':
                    c.sx.one(arc,'start')[1:]=['-1','0'];c.sx.one(arc,'mid')[1:]=['0','0.000001'];c.sx.one(arc,'end')[1:]=['1','0']
                if fault=='collinear_arc':c.sx.one(arc,'mid')[1:]=['0','0']
                if fault=='filled_arc':c.sx.one(arc,'fill')[1]='solid'
                if fault=='poly_arc':c.sx.one(poly,'pts')[1]=['arc',['start','0','0'],['mid','1','0'],['end','1','1']]
                if fault=='zero_signed_area':c.sx.one(poly,'pts')[1:]=[['xy','0','0'],['xy','2','2'],['xy','0','2'],['xy','2','0']]
                if fault=='duplicate_point':c.sx.one(poly,'pts')[3]=['xy','0','0']
                if fault=='oversize_polygon':c.sx.one(poly,'pts')[1:]=[['xy',str(i),'0'] for i in range(1025)]
                if fault=='back_pad':back.append(copy.deepcopy(c.sx.children(c.sx.children(fixture.board(),'footprint')[0],'pad')[0]))
                if fault=='back_courtyard':back.append(copy.deepcopy(c.sx.one(front,'fp_rect')))
                if fault=='back_model':back.append(['model','"owned.wrl"'])
                if fault=='back_not_board_only':c.sx.one(back,'attr')[1:]=['smd']
                if fault=='front_no_courtyard':front.remove(c.sx.one(front,'fp_rect'))
                with self.assertRaises(ValueError):o.inspect(raw(tree),scope=c.CONTEXT_SCOPE)

    def test_unfilled_arc_default_and_bounded_large_immutable_artwork(self):
        tree=context_board();front,back=c.sx.children(tree,'footprint')
        arc=c.sx.one(front,'fp_arc');arc.remove(c.sx.one(arc,'fill'))
        board,pcb,fc,_=independent_native()
        native.capture(board,pcb,raw(tree),c,fc,scope=c.CONTEXT_SCOPE)
        poly=c.sx.one(back,'fp_poly')
        pts=[['xy',str(i/1000),'0'] for i in range(300)]
        pts += [['xy',str(i/1000),'1'] for i in reversed(range(300))]
        c.sx.one(poly,'pts')[1:]=pts
        observed=o.inspect(raw(tree),scope=c.CONTEXT_SCOPE)
        artwork=next(row for row in observed['footprints'] if row.get('artwork_only'))
        self.assertEqual(len(next(row for row in artwork['graphics'] if row['kind']=='fp_poly')['points_nm']),600)
        self.assertFalse(artwork['placement_eligible'])

    def test_native_witness_checks_hand_entered_asymmetric_world_geometry_and_scope(self):
        board,pcb,fc,_=independent_native();observed,proof=native.capture(board,pcb,raw(context_board()),c,fc,scope=c.CONTEXT_SCOPE)
        self.assertEqual(observed['scope'],c.CONTEXT_SCOPE);self.assertEqual(proof['native_pad_netcodes'],{})
        with self.assertRaises(ValueError):native.capture(board,pcb,raw(context_board()),c,fc)

    def test_native_context_witness_rejects_actual_geometry_metadata_and_reflection_mismatches(self):
        for fault in ('circle_center','circle_radius','arc_mid','arc_ends','polygon_point','polygon_hole','polygon_arc','polygon_extra_outline',
                      'width','fill','stroke_type','lock','layer','uuid','mirror','second_reflection','back_flip','back_attributes','back_model','back_pad'):
            with self.subTest(fault=fault):
                board,pcb,fc,fps=independent_native();circle,arc,poly=fps[0].graphics[1:];back=fps[1]
                if fault=='circle_center':circle.start[0]+=1
                if fault=='circle_radius':circle.radius_delta=1
                if fault=='arc_mid':arc.mid[0]+=1
                if fault=='arc_ends':arc.start,arc.end=arc.end,arc.start
                if fault=='polygon_point':poly.points[1][0]+=1
                if fault=='polygon_hole':poly.holes=1
                if fault=='polygon_arc':poly.arcs=1
                if fault=='polygon_extra_outline':poly.outlines=2
                if fault=='width':circle.width+=1
                if fault=='fill':circle.fill=1
                if fault=='stroke_type':circle.style=1
                if fault=='lock':circle.locked=True
                if fault=='layer':circle.layer=pcb.F_Cu
                if fault=='uuid':circle.m_Uuid=SimpleNamespace(AsString=lambda:uid('other'))
                if fault=='mirror':back.field.mirrored=False
                if fault=='second_reflection':back.graphics[0].points[2][0]=19000000
                if fault=='back_flip':back.back=False
                if fault=='back_attributes':back.attributes|=8
                if fault=='back_model':back.models.append(object())
                if fault=='back_pad':back.pads.append(SimpleNamespace(m_Uuid=SimpleNamespace(AsString=lambda:uid('extra-pad'))))
                with self.assertRaises(ValueError):native.capture(board,pcb,raw(context_board()),c,fc,scope=c.CONTEXT_SCOPE)

    def test_native_arc_endpoint_normalization_preserves_same_midpoint(self):
        board,pcb,fc,fps=independent_native();arc=fps[0].graphics[2]
        arc.start,arc.end=arc.end,arc.start;arc.swapped=True
        native.capture(board,pcb,raw(context_board()),c,fc,scope=c.CONTEXT_SCOPE)
        arc.mid[0]+=1
        with self.assertRaisesRegex(ValueError,'arc geometry'):native.capture(board,pcb,raw(context_board()),c,fc,scope=c.CONTEXT_SCOPE)


if __name__=='__main__':unittest.main()
