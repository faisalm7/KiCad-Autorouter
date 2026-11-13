"""Hand-entered conservative proxy controls; no actual Native bbox proof."""
import copy
import hashlib
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from autorouter import placement_annotations as a
from experiments.placement_native_proposal_v1 import contract, ordinary_native


def uid(number): return '00000000-0000-4000-8000-%012x' % number
A, B, C = uid(1), uid(2), uid(3)


def scene():
    return dict(schema=1, policy=a.POLICY, scope=a.SCOPE, source_board_sha256='1'*64,
        outline_nm=[0,0,10000,10000],silk_clearance_nm=100,
        footprint_anchors_nm={A:[2000,2000],B:[7000,2000],C:[7000,7000]},movable_owners=[A,B],
        rows=[dict(uuid=uid(10),owner=A,kind='silk',bbox_nm=[-100,-100,100,100]),
              dict(uuid=uid(11),owner=A,kind='mask',bbox_nm=[300,-100,500,100],mask_expansion_nm=50),
              dict(uuid=uid(12),owner=B,kind='silk',bbox_nm=[-100,-100,100,100]),
              dict(uuid=uid(13),owner=C,kind='mask',bbox_nm=[0,0,300,300],mask_expansion_nm=0),
              dict(uuid=uid(14),owner=None,kind='silk',bbox_nm=[8000,8000,8500,8500])])


class Box:
    def __init__(self, values):self.values=values
    def GetLeft(self):return self.values[0]
    def GetTop(self):return self.values[1]
    def GetRight(self):return self.values[2]
    def GetBottom(self):return self.values[3]


class Shape:
    def __init__(self,number,owner,box,*,layer=37):
        self.m_Uuid=SimpleNamespace(AsString=lambda:uid(number));self.owner=owner
        self.box=box;self.layer=layer;self.box_calls=[]
    def GetParentFootprint(self):return self.owner
    def GetLayer(self):return self.layer
    def GetBoundingBox(self,*args):self.box_calls.append(args);return Box(self.box)


class Text(Shape):
    def __init__(self,number,owner,box,position,*,visible=True):
        super().__init__(number,owner,box);self.position=position;self.visible=visible
    def GetPosition(self):return SimpleNamespace(x=self.position[0],y=self.position[1])
    def IsVisible(self):return self.visible


class Pad(Shape):
    def __init__(self,number,owner,box,position,*,expansion=50):
        super().__init__(number,owner,box,layer=0);self.position=position;self.expansion=expansion
        self.layers=[0,1,2];self.expansion_calls=[]
    def GetPosition(self):return SimpleNamespace(x=self.position[0],y=self.position[1])
    def GetLayerSet(self):return SimpleNamespace(Seq=lambda:self.layers)
    def GetSolderMaskExpansion(self,layer):self.expansion_calls.append(layer);return self.expansion


class Footprint:
    def __init__(self,number,position):
        self.m_Uuid=SimpleNamespace(AsString=lambda:uid(number));self.position=position;self.graphics=[];self.fields=[]
    def GetPosition(self):return SimpleNamespace(x=self.position[0],y=self.position[1])
    def GraphicalItems(self):return self.graphics
    def GetFields(self):return self.fields


def capture_scene():
    """Independent Native-style bbox/owner values, separate source-witness seam."""
    raw=b'owned source bytes for a pure capture seam'
    fpa=Footprint(1,[2000,2000]);fpb=Footprint(2,[7000,2000])
    field=Text(10,fpa,[1900,1800,2100,1900],[2000,1850])
    hidden=Text(12,fpb,[6900,1800,7100,1900],[7000,1850],visible=False)
    line=Shape(11,fpa,[1800,2000,2100,2100]);fpa.fields=[field];fpa.graphics=[line];fpb.fields=[hidden]
    pad=Pad(20,fpa,[2250,1950,2350,2050],[2300,2000])
    board_text=Text(30,None,[7900,7900,8100,8100],[8000,8000])
    board=SimpleNamespace(GetDesignSettings=lambda:SimpleNamespace(m_SilkClearance=100),
        GetFootprints=lambda:[fpa,fpb],GetPads=lambda:[pad],GetDrawings=lambda:[board_text])
    pcb=SimpleNamespace(F_SilkS=37,F_Mask=1,F_Cu=0,PCB_TEXT=Text,PCB_SHAPE=Shape)
    expected=dict(scope=contract.CONTEXT_SCOPE,source_board_sha256=hashlib.sha256(raw).hexdigest(),
        outline=dict(bounds_nm=[0,0,10000,10000],primitives=[]),graphics=[dict(uuid=uid(30),kind='gr_text',layer='F.SilkS',position_nm=[8000,8000])],
        footprints=[dict(uuid=A,position_nm=[2000,2000],placement_eligible=True,courtyard=dict(primitives=[]),
            graphics=[dict(uuid=uid(10),kind='property',layer='F.SilkS',position_nm=[2000,1850]),
                      dict(uuid=uid(11),kind='fp_line',layer='F.SilkS')],
            pads=[dict(uuid=uid(20),position_nm=[2300,2000],layers=['F.Cu','F.Mask','F.Paste'])]),
            dict(uuid=B,position_nm=[7000,2000],placement_eligible=False,courtyard=None,
                graphics=[dict(uuid=uid(12),kind='property',layer='F.SilkS',position_nm=[7000,1850])],pads=[])])
    return board,pcb,raw,expected,SimpleNamespace(fpa=fpa,fpb=fpb,field=field,hidden=hidden,line=line,pad=pad,board_text=board_text)


class AnnotationControls(unittest.TestCase):
    def test_safe_translation_preserves_context_and_has_no_acceptance_authority(self):
        context=scene();before=copy.deepcopy(context);proof=a.check_moves(context,{A:[3000,3000]})
        self.assertEqual(context,before);self.assertTrue(proof['prefilter_passed'])
        self.assertTrue(proof['native_validation_required']);self.assertNotIn('accepted',proof)
        self.assertEqual(proof['moved_owners'],[A])

    def test_new_silk_silk_and_silk_mask_overlap_refuse(self):
        for target in ([7000,2000],[7000,7000],[8200,8200]):
            with self.subTest(target=target),self.assertRaisesRegex(ValueError,'annotation conflict'):
                a.check_moves(scene(),{A:target})

    def test_moving_mask_against_fixed_silk_is_checked(self):
        with self.assertRaisesRegex(ValueError,uid(11)+' / '+uid(12)):
            a.check_moves(scene(),{A:[6600,2000]})

    def test_touching_clearance_boxes_refuse_conservatively(self):
        # Moving silk ends at6800; fixed silk starts6900, exactly100nm away.
        context=scene();context['rows']=[context['rows'][0],context['rows'][2]]
        with self.assertRaises(ValueError):a.check_moves(context,{A:[6700,2000]})
        self.assertTrue(a.check_moves(context,{A:[6699,2000]})['prefilter_passed'])

    def test_original_proxy_overlap_requires_identical_relative_owner_displacement(self):
        context=scene();context['footprint_anchors_nm'][B]=[2000,2000]
        context['rows']=[context['rows'][0],context['rows'][2]]
        self.assertTrue(a.check_moves(context,{})['prefilter_passed'])
        with self.assertRaises(ValueError):a.check_moves(context,{A:[2001,2000]})
        proof=a.check_moves(context,{A:[3000,2000],B:[3000,2000]})
        self.assertEqual(proof['inherited_proxy_overlaps_retained'],1)
        self.assertTrue(a.check_moves(context,{A:[3000,2000]})['prefilter_passed'])

    def test_same_component_inherited_overlap_moves_together_and_masks_do_not_conflict(self):
        context=scene();context['rows']=context['rows'][:2];context['rows'][1]['bbox_nm']=[-50,-50,50,50]
        self.assertEqual(a.check_moves(context,{A:[3000,3000]})['inherited_proxy_overlaps_retained'],1)
        context=scene();context['rows']=[context['rows'][1],context['rows'][3]]
        self.assertTrue(a.check_moves(context,{A:[6700,7000]})['prefilter_passed'])

    def test_every_moving_silk_stays_in_original_board_with_clearance(self):
        for target in ([0,3000],[3000,0],[10000,3000],[3000,10000]):
            with self.subTest(target=target),self.assertRaisesRegex(ValueError,'original board'):
                a.check_moves(scene(),{A:target})
        self.assertTrue(a.check_moves(scene(),{A:[200,3000]})['prefilter_passed'])

    def test_unbound_fixed_rotated_or_malformed_moves_refuse(self):
        for moves in ({uid(99):[3000,3000]},{C:[3000,3000]},{A:[True,3000]},{A:[float('inf'),3000]},
                      {A:[3.5,3000]},{A:[3000]},{A:[3000,3000,90]},{A:dict(x=3000,y=3000,rotation=90)},
                      {A:[a.MAX_NM+1,3000]},[],{A:(3000,3000)}):
            with self.subTest(moves=moves),self.assertRaises(ValueError):a.check_moves(scene(),moves)

    def test_context_unknown_identity_owner_geometry_kind_size_or_policy_refuses(self):
        for fault in ('schema_bool','scope','sha','unknown','duplicate_uuid','owner_uuid_collision','unknown_owner','owner_bool',
                      'missing_anchor','bad_anchor','movable_duplicate','unknown_movable','kind','extra_row','bool_nm','nan_nm',
                      'oversize_nm','inverted_box','unbounded_world','too_many_rows','mask_expansion','clearance_bool','clearance_large'):
            with self.subTest(fault=fault):
                context=scene();row=context['rows'][0]
                if fault=='schema_bool':context['schema']=True
                if fault=='scope':context['scope']='ordinary-front-preserve-v1'
                if fault=='sha':context['source_board_sha256']='bad'
                if fault=='unknown':context['unknown']=0
                if fault=='duplicate_uuid':context['rows'][1]['uuid']=row['uuid']
                if fault=='owner_uuid_collision':row['uuid']=A
                if fault=='unknown_owner':row['owner']=uid(99)
                if fault=='owner_bool':row['owner']=False
                if fault=='missing_anchor':del context['footprint_anchors_nm'][A]
                if fault=='bad_anchor':context['footprint_anchors_nm'][A]=[2000,False]
                if fault=='movable_duplicate':context['movable_owners'].append(A)
                if fault=='unknown_movable':context['movable_owners'].append(uid(99))
                if fault=='kind':row['kind']='electrical_clearance'
                if fault=='extra_row':row['native_accepted']=True
                if fault=='bool_nm':row['bbox_nm'][0]=False
                if fault=='nan_nm':row['bbox_nm'][0]=float('nan')
                if fault=='oversize_nm':row['bbox_nm'][0]=-a.MAX_NM-1
                if fault=='inverted_box':row['bbox_nm']=[100,0,0,100]
                if fault=='unbounded_world':row['bbox_nm']=[a.MAX_NM-1,0,a.MAX_NM,1]
                if fault=='too_many_rows':context['rows']*=a.MAX_ROWS
                if fault=='mask_expansion':context['rows'][1]['mask_expansion_nm']=True
                if fault=='clearance_bool':context['silk_clearance_nm']=True
                if fault=='clearance_large':context['silk_clearance_nm']=a.MAX_CLEARANCE_NM+1
                with self.assertRaises(ValueError):a.validate(context)
        with patch.object(a,'MAX_CONTEXT_BYTES',10),self.assertRaisesRegex(ValueError,'byte ceiling'):a.validate(scene())

    def test_capture_first_uses_existing_geometry_witness_then_native_boxes_and_exact_mask_layer(self):
        board,pcb,raw,expected,objects=capture_scene();before=copy.deepcopy(expected)
        def witnessed(*args,**kwargs):
            self.assertFalse(objects.pad.box_calls);self.assertFalse(objects.field.box_calls)
            return expected,{}
        with patch.object(ordinary_native,'capture',side_effect=witnessed) as witness:
            context=a.capture(board,pcb,raw)
        witness.assert_called_once();self.assertEqual(witness.call_args.kwargs,{'scope':contract.CONTEXT_SCOPE})
        self.assertEqual(witness.call_args.args[:4],(board,pcb,raw,contract));self.assertEqual(expected,before)
        self.assertEqual(context['movable_owners'],[A]);rows={row['uuid']:row for row in context['rows']}
        self.assertNotIn(uid(12),rows);self.assertEqual(objects.hidden.box_calls,[])
        self.assertEqual(rows[uid(10)]['bbox_nm'],[-100,-200,100,-100])
        self.assertEqual(rows[uid(20)]['bbox_nm'],[200,-100,400,100])
        self.assertEqual(rows[uid(20)]['mask_expansion_nm'],50)
        self.assertEqual(objects.pad.box_calls,[(pcb.F_Cu,)]);self.assertEqual(objects.pad.expansion_calls,[pcb.F_Cu])
        self.assertIsNone(rows[uid(30)]['owner']);self.assertEqual(context['source_board_sha256'],hashlib.sha256(raw).hexdigest())

    def test_failed_source_witness_never_reads_extra_native_data(self):
        with patch.object(ordinary_native,'capture',side_effect=ValueError('source/native differs')):
            with self.assertRaisesRegex(ValueError,'source/native differs'):a.capture(object(),object(),b'owned')

    def test_capture_refuses_missing_changed_ambiguous_or_unbounded_native_rows(self):
        for fault in ('pad_owner','pad_position','pad_layers','mask_bool','mask_float','mask_collapse','bbox_bool',
                      'field_owner','field_position','field_uuid','missing_field','extra_field','duplicate_graphic','anchor','visibility'):
            with self.subTest(fault=fault):
                board,pcb,raw,expected,objects=capture_scene()
                if fault=='pad_owner':objects.pad.owner=objects.fpb
                if fault=='pad_position':objects.pad.position[0]+=1
                if fault=='pad_layers':objects.pad.layers.remove(pcb.F_Mask)
                if fault=='mask_bool':objects.pad.expansion=True
                if fault=='mask_float':objects.pad.expansion=50.5
                if fault=='mask_collapse':objects.pad.expansion=-1000
                if fault=='bbox_bool':objects.field.box[0]=False
                if fault=='field_owner':objects.field.owner=objects.fpb
                if fault=='field_position':objects.field.position[0]+=1
                if fault=='field_uuid':objects.field.m_Uuid=SimpleNamespace(AsString=lambda:uid(99))
                if fault=='missing_field':objects.fpa.fields=[]
                if fault=='extra_field':objects.fpa.fields.append(Text(99,objects.fpa,[0,0,1,1],[0,0]))
                if fault=='duplicate_graphic':objects.fpa.graphics.append(objects.line)
                if fault=='anchor':objects.fpa.position[0]+=1
                if fault=='visibility':objects.field.visible=1
                with patch.object(ordinary_native,'capture',return_value=(expected,{})),self.assertRaises(ValueError):
                    a.capture(board,pcb,raw)


if __name__=='__main__':unittest.main()
