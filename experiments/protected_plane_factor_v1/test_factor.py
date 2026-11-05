"""Constructed transforms only; no Native, engine or admission proof."""
import copy
import unittest
from autorouter import adapter,default_targets,native_edge,sexpr as sx
from experiments.protected_plane_factor_v1 import factor
from tests.test_default_targets import fixtures,inputs,SOURCE


class ProtectedPlaneFactorControls(unittest.TestCase):
    def setUp(self):
        native,mapping,project,task=fixtures(fixed=True)
        self.native,self.mapping,self.project,self.task=inputs(native,mapping,project,task)
        self.guided,self.derivation=default_targets.transform(self.native,self.mapping,self.project,self.task,source=SOURCE)
        self.obstacles=[dict(layer='F.Cu',bbox_mm=[2,2,3,3])]
        self.context=native_edge.derive_context(self.task,self.project)
        self.both,_=adapter.adapt_bytes(self.guided,'both',self.obstacles)
        self.final,self.edge=native_edge.correct(self.both,self.context)

    def args(self):
        return dict(export_source=SOURCE,captured_default=self.guided,captured_derivation=copy.deepcopy(self.derivation),
            obstacles=copy.deepcopy(self.obstacles),edge_context=copy.deepcopy(self.context),
            captured_both_before_edge=self.both,captured_both=self.final,captured_both_edge=copy.deepcopy(self.edge))

    def call(self,**changes):
        args=self.args();args.update(changes)
        return factor.transform(self.native,self.mapping,self.project,self.task,**args)

    def test_only_planes_change_with_lawful_targets_graphics_wiring_and_edges_retained(self):
        before=copy.deepcopy((self.native,self.mapping,self.project,self.task,self.obstacles,self.context))
        raw,record=self.call();new=adapter._parse_dsn(raw.decode());old=adapter._parse_dsn(self.final.decode())
        self.assertEqual(factor.plane_projection(new),old)
        for name in ('placement','network','library','wiring'):
            self.assertEqual(sx.one(new,name),sx.one(old,name))
        self.assertTrue(sx.children(sx.one(new,'wiring'),'wire'))
        self.assertTrue(sx.children(sx.one(new,'wiring'),'via'))
        self.assertEqual(self.derivation['derived_nm']['width_nm'],300000)
        self.assertEqual(record['default_target_derivation'],self.derivation)
        self.assertFalse(record['product_scope_admitted']);self.assertFalse(record['reran_old_both'])
        self.assertEqual(before,(self.native,self.mapping,self.project,self.task,self.obstacles,self.context))

    def test_captured_default_both_edge_or_native_map_changes_refuse_before_new_cell(self):
        for key,value in [('captured_default',self.guided+b' '),('captured_both',self.final+b' '),
                          ('captured_both_before_edge',self.both+b' '),('captured_both_edge',dict(self.edge,applied=True)),
                          ('captured_derivation',dict(self.derivation,policy='changed'))]:
            with self.subTest(key=key),self.assertRaises(ValueError):self.call(**{key:value})
        changed=copy.deepcopy(self.mapping);changed['board_sha256']='0'*64
        with self.assertRaises(ValueError):factor.transform(self.native,changed,self.project,self.task,**self.args())

    def test_zero_graphics_does_not_remove_plane_or_admit_normal_Default_scope(self):
        both,_=adapter.adapt_bytes(self.guided,'both',[]);final,edge=native_edge.correct(both,self.context)
        raw,record=self.call(obstacles=[],captured_both_before_edge=both,captured_both=final,captured_both_edge=edge)
        self.assertEqual(record['adapter_transformations']['graphics_keepouts_added'],0)
        self.assertEqual(record['factor_plane_count'],1)
        self.assertEqual(factor.plane_projection(adapter._parse_dsn(raw.decode())),adapter._parse_dsn(final.decode()))
        self.assertFalse(record['product_scope_admitted'])


if __name__=='__main__':unittest.main()
