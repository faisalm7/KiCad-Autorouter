"""Owned synthetic wire controls; these polygons are not captured font data."""
import copy
import unittest
import uuid

from autorouter import placement_annotations as a


def uid(name): return str(uuid.uuid5(uuid.NAMESPACE_URL, 'owned-annotation-geometry:' + name))
TEXT, CIRCLE = uid('text-owner'), uid('fixed-circle-owner')


def context():
    return dict(schema=2, policy=a.GEOMETRY_POLICY, scope=a.THT_BASELINE_SCOPE,
        source_board_sha256='a'*64, outline_nm=[0, 0, 40000000, 40000000], silk_clearance_nm=0,
        footprint_anchors_nm={TEXT:[10000000,10000000], CIRCLE:[20000000,10000000]},
        movable_owners=[TEXT], rows=[
            dict(uuid=uid('text'), owner=TEXT, kind='silk', bbox_nm=[1000000,1000000,5000000,5000000],
                geometry=dict(kind='default-text-outer-polygons-v1', error_nm=1000,
                    outer_contours_nm=[[[1000000,1000000],[5000000,1000000],[1000000,5000000]]],
                    holes_filled=True, holes_count=0, font_name='', text='X', effective_pen_width_nm=100000)),
            dict(uuid=uid('circle'), owner=CIRCLE, kind='silk', bbox_nm=[-7050001,2949999,-2949999,7050001],
                geometry=dict(kind='unfilled-circle-v1', center_nm=[-5000000,5000000],
                              end_nm=[-3000000,5000000], stroke_nm=100000))])


class AnnotationGeometry(unittest.TestCase):
    def test_refines_empty_box_corner_without_changing_legacy_policy(self):
        value=context();before=copy.deepcopy(value)
        checked=a.check_moves(value,{TEXT:[9900000,10000000]})
        self.assertTrue(checked['prefilter_passed']);self.assertTrue(checked['native_validation_required'])
        self.assertEqual(checked['policy'],a.GEOMETRY_POLICY);self.assertEqual(value,before)
        old=copy.deepcopy(value);old.update(schema=1,policy=a.POLICY)
        for row in old['rows']:del row['geometry']
        with self.assertRaisesRegex(ValueError,'annotation conflict'):
            a.check_moves(old,{TEXT:[9900000,10000000]})

    def test_real_ring_contact_refuses_even_though_source_boxes_already_overlap(self):
        with self.assertRaisesRegex(ValueError,'annotation conflict'):
            a.check_moves(context(),{TEXT:[12000000,12000000]})

    def test_mask_and_unsupported_geometry_keep_conservative_boxes(self):
        for fault in ('mask','no-text-geometry','no-circle-geometry','fallback'):
            value=context()
            if fault=='mask':
                value['rows'][0].pop('geometry');value['rows'][0].update(kind='mask',mask_expansion_nm=0)
            elif fault=='fallback':
                value['rows'][0].pop('geometry');value['rows'][0]['geometry_fallback']='Unsupported font; conservative box retained.'
            else:value['rows'][0 if fault=='no-text-geometry' else 1].pop('geometry')
            with self.subTest(fault=fault),self.assertRaisesRegex(ValueError,'annotation conflict'):
                a.check_moves(value,{TEXT:[9900000,10000000]})

    def test_circle_motion_and_wrong_owner_roles_cannot_gain_refinement(self):
        value=context()
        with self.assertRaisesRegex(ValueError,'captured movable'):
            a.check_moves(value,{CIRCLE:[20000001,10000000]})
        deltas={None:[0,0],TEXT:[0,0],CIRCLE:[1,0]}
        self.assertFalse(a._separated_geometry(*value['rows'],value,deltas))
        for fault in ('moving-circle','fixed-text'):
            bad=copy.deepcopy(value)
            if fault=='moving-circle':bad['movable_owners'].append(CIRCLE)
            else:bad['movable_owners']=[]
            with self.subTest(fault=fault),self.assertRaises(ValueError):a.validate(bad)

    def test_source_box_must_cover_every_outward_vertex_and_circle_extremum(self):
        for row,axis in ((0,2),(1,0),(1,1),(1,2),(1,3)):
            bad=context();bad['rows'][row]['bbox_nm'][axis]+=1 if axis<2 else -1
            with self.subTest(row=row,axis=axis),self.assertRaisesRegex(ValueError,'proxy box'):
                a.validate(bad)

    def test_unknown_partial_cross_schema_and_non_integer_payloads_refuse(self):
        for fault in ('none','unknown','partial','schema1','scope','policy','bool-error','false-holes',
                      'font','empty-text','bool-width','float-point','self-crossing','ambiguous-fallback'):
            value=context();g=value['rows'][0]['geometry']
            if fault=='none':value['rows'][0]['geometry']=None
            if fault=='unknown':g['kind']='trust-the-model'
            if fault=='partial':del g['outer_contours_nm']
            if fault=='schema1':value.update(schema=1,policy=a.POLICY)
            if fault=='scope':value['scope']=a.SCOPE
            if fault=='policy':value['policy']=a.POLICY
            if fault=='bool-error':g['error_nm']=True
            if fault=='false-holes':g['holes_filled']=False
            if fault=='font':g['font_name']='unknown-font'
            if fault=='empty-text':g['text']=''
            if fault=='bool-width':g['effective_pen_width_nm']=True
            if fault=='float-point':g['outer_contours_nm'][0][0][0]=1000000.0
            if fault=='self-crossing':g['outer_contours_nm']=[[[1000000,1000000],[5000000,5000000],[1000000,5000000],[5000000,1000000]]]
            if fault=='ambiguous-fallback':value['rows'][0]['geometry_fallback']='Cannot be both.'
            with self.subTest(fault=fault),self.assertRaises(ValueError):a.validate(value)

    def test_exact_global_translation_preserves_decision_and_source_binding(self):
        value=context();shift=[-1000000,1000000]
        for owner in value['footprint_anchors_nm']:
            value['footprint_anchors_nm'][owner]=[n+shift[i]for i,n in enumerate(value['footprint_anchors_nm'][owner])]
        value['outline_nm']=[n+shift[i%2]for i,n in enumerate(value['outline_nm'])]
        result=a.check_moves(value,{TEXT:[8900000,11000000]})
        self.assertTrue(result['prefilter_passed']);self.assertEqual(result['source_board_sha256'],'a'*64)


if __name__=='__main__':unittest.main()
