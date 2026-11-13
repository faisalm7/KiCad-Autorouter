"""Owned pure source/intent controls; fabricated fixtures are never Native proof."""
import copy
from decimal import localcontext
import hashlib
import json
import unittest

from autorouter import placement_annotations as annotations, placement_intent as intent
from autorouter import placement_gui as pg
from experiments.constrained_placement_v1 import constraints
from experiments.placement_native_proposal_v1 import contract as c, ordinary_fixture as fixture
from tests.test_placement_tht_scope import board, raw, fp


def blocked_board():
    tree=board()
    route=copy.deepcopy(c.sx.children(tree,'segment')[0])
    c.sx.one(route,'uuid')[1]=json.dumps(fixture.uid('retained-under-body'))
    c.sx.one(route,'start')[1:]=['11.3','10']
    c.sx.one(route,'end')[1:]=['12.7','10']
    c.sx.one(route,'width')[1]='0.1'
    tree.append(route)
    return tree


class SourceCopperBaseline(unittest.TestCase):
    def setUp(self):
        self.tree=blocked_board();self.source=raw(self.tree)
        self.selected=fixture.selected();self.region=[7000000,7000000,31000000,13000000]
        self.options=dict(scope=c.THT_BASELINE_SCOPE,selected=self.selected,region_nm=self.region)
        self.observation=c.inspect_board(self.source,scope=c.THT_BASELINE_SCOPE)

    def facts(self):return c.facts_from_observation(self.observation,**self.options)

    def context(self):
        return dict(schema=1,policy=annotations.POLICY,scope=c.THT_BASELINE_SCOPE,
            source_board_sha256=hashlib.sha256(self.source).hexdigest(),
            outline_nm=self.observation['outline']['bounds_nm'],silk_clearance_nm=0,
            footprint_anchors_nm={r['uuid']:r['position_nm'] for r in self.observation['footprints']},
            movable_owners=self.selected,rows=[])

    def inspection(self):
        receipt='0'*64
        native=dict(opens=0,blocking=0,warnings=1,exclusions=0,findings=[],ignored_checks=[])
        return dict(source='/owned/pure-fixture.kicad_pcb',observation=self.observation,components=[],
            native_context=dict(receipt='/owned/pure-inspection.json',receipt_sha256=receipt,context_sha256='1'*64),
            annotation_context=self.context(),
            native_source_baseline=dict(policy=constraints.SELECTED_COPPER_BASELINE_POLICY,
                receipt_sha256=receipt,source_board_sha256=hashlib.sha256(self.source).hexdigest(),
                native=native,native_validation_performed=True))

    def test_new_scope_keeps_same_geometry_and_preserves_old_strict_start(self):
        old=c.inspect_board(self.source,scope=c.THT_SCOPE);old['scope']=c.THT_BASELINE_SCOPE
        self.assertEqual(self.observation,old)
        with self.assertRaisesRegex(ValueError,'keepout'):
            c.facts_from_observation(c.inspect_board(self.source,scope=c.THT_SCOPE),
                scope=c.THT_SCOPE,selected=self.selected,region_nm=self.region)
        facts=self.facts();self.assertEqual(facts['schema'],3)
        self.assertEqual(facts['selected_copper_baseline_policy'],constraints.SELECTED_COPPER_BASELINE_POLICY)
        constraints.validate_alternative(facts,constraints.original_alternative(facts))

    def test_unchanged_source_allowed_but_changed_pose_stays_strict_and_exact(self):
        anchors={r['uuid']:r['position_nm']for r in self.observation['footprints']}
        moves={key:list(anchors[key])for key in self.selected}
        c.validate_moves(self.observation,moves,**self.options)
        moves[self.selected[0]][0]+=1
        with self.assertRaisesRegex(ValueError,'keepout'):
            c.validate_moves(self.observation,moves,**self.options)
        moves[self.selected[0]][0]+=1_999_999
        c.validate_moves(self.observation,moves,**self.options)
        candidate=raw(c.translated_tree(self.source,moves,**self.options))
        self.assertTrue(c.check_translation(self.source,candidate,moves,**self.options)['exact_immutable_AST'])

    def test_offset_native_annotations_use_actual_footprint_anchors(self):
        facts=self.facts();facts['annotation_context']=self.context()
        facts=constraints.prepare(facts)
        self.assertEqual(facts['proxy_anchor_offsets_twice_nm'][self.selected[0]],[0,-200000])
        original=constraints.original_alternative(facts)
        constraints.validate_alternative(facts,original)
        pose=copy.deepcopy(original)
        for row in pose['transforms']:
            if row['component_id']==self.selected[0]:row['x_mm']+=2
        checked,moves=c.quantized_translation(facts,pose,observation=self.observation)
        self.assertEqual(moves[self.selected[0]],[14000000,10000000])
        constraints.validate_alternative(facts,checked)
        bad=copy.deepcopy(facts);bad['proxy_anchor_offsets_twice_nm'][self.selected[0]][1]+=1
        with self.assertRaisesRegex(ValueError,'anchor'):constraints.prepare(bad)

    def test_settings_bind_policy_and_do_not_claim_group_support(self):
        settings=intent.settings(self.selected,self.region,scope=c.THT_BASELINE_SCOPE)
        self.assertEqual(settings['selected_copper_baseline_policy'],constraints.SELECTED_COPPER_BASELINE_POLICY)
        self.assertEqual(intent.validate_settings(settings),settings)
        for fault in ('missing','other'):
            bad=dict(settings)
            if fault=='missing':del bad['selected_copper_baseline_policy']
            else:bad['selected_copper_baseline_policy']='ignore-copper'
            with self.subTest(fault=fault),self.assertRaises(ValueError):intent.validate_settings(bad)
        with self.assertRaisesRegex(ValueError,'not qualified'):
            intent.settings(self.selected,self.region,scope=c.THT_BASELINE_SCOPE,
                            copper_policy=intent.COPPER_POLICY,group_policy=intent.GROUP_POLICY)

    def test_real_bound_native_baseline_required_by_intent_not_inferred_from_geometry(self):
        settings=intent.settings(self.selected,self.region,scope=c.THT_BASELINE_SCOPE)
        inspection=self.inspection()
        for fault in ('missing','blocking','bool','receipt','source','policy','not-run'):
            changed=copy.deepcopy(inspection)
            if fault=='missing':changed.pop('native_source_baseline')
            else:
                value=changed['native_source_baseline']
                if fault=='blocking':value['native']['blocking']=1
                if fault=='bool':value['native']['blocking']=False
                if fault=='receipt':value['receipt_sha256']='2'*64
                if fault=='source':value['source_board_sha256']='3'*64
                if fault=='policy':value['policy']='ignore-copper'
                if fault=='not-run':value['native_validation_performed']=False
            with self.subTest(fault=fault),self.assertRaisesRegex(ValueError,'same-source Native'):
                intent._facts_context(changed,settings,None,self.observation)
        facts=intent._facts_context(inspection,settings,None,self.observation)
        self.assertEqual(facts['schema'],3)
        changed=copy.deepcopy(inspection);changed['annotation_context']['scope']=c.THT_SCOPE
        with self.assertRaisesRegex(ValueError,'exact reviewed geometry scope'):
            intent._facts_context(changed,settings,None,self.observation)

    def test_native_source_findings_are_presented_as_source_not_placement_approval(self):
        text=pg.source_native_findings(self.inspection())
        self.assertIn('0 blocking',text);self.assertIn('1 warnings',text)
        self.assertIn('source inspected placement pending',text)
        self.assertIn('does not approve a route',text)

    def test_source_translation_and_quantization_ignore_low_Decimal_precision(self):
        facts=self.facts();pose=constraints.original_alternative(facts)
        anchors={r['uuid']:r['position_nm']for r in self.observation['footprints']}
        moves={key:list(anchors[key])for key in self.selected}
        moves[self.selected[0]][0]+=2_000_001
        with localcontext()as ctx:
            ctx.prec=6
            data=raw(c.translated_tree(self.source,moves,**self.options))
            self.assertEqual(c.sx.one(fp(c.read_board(data),'J1'),'at')[1],'14.000001')
            c.validate_moves(self.observation,moves,**self.options)


if __name__=='__main__':unittest.main()
