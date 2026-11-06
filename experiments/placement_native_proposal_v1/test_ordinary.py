"""Owned pure ordinary-format geometry controls; no Native support claim."""
import copy
import hashlib
import unittest

from . import contract as c, ordinary as o, ordinary_fixture as fixture
from .test_contract import fixture as old_fixture, raw, identity


class OrdinarySourceContract(unittest.TestCase):
    def setUp(self):
        self.tree = fixture.board()
        self.raw = raw(self.tree)
        self.options = dict(scope=c.ORDINARY_SCOPE, selected=fixture.selected(), region_nm=[7000000,7000000,31000000,13000000])
        self.observation = c.inspect_board(self.raw, scope=c.ORDINARY_SCOPE)

    def fp(self, tree, ref='J1'):
        return next(fp for fp in c.sx.children(tree, 'footprint') if fixture.base.reference(fp) == ref)

    def row(self, ref='J1'):
        return next(row for row in self.observation['footprints'] if row['reference'] == ref)

    def inspect(self, tree):
        return c.inspect_board(raw(tree), scope=c.ORDINARY_SCOPE)

    def test_cardinal_pad_world_centres_angles_and_courtyard_are_exact(self):
        row = self.row(); pad = next(p for p in row['pads'] if p['offset_nm'][0] < 0)
        self.assertEqual(row['angle'], 90)
        self.assertEqual(pad['position_nm'], [12000000,10825000])
        self.assertEqual(pad['offset_nm'], [-825000,0])
        self.assertEqual(pad['angle'], 90)
        self.assertEqual(pad['size_nm'], [800000,950000])
        self.assertEqual(pad['roundrect_rratio'], .25)
        self.assertEqual(pad['drill_nm'], [0,0])
        self.assertEqual(row['courtyard']['bounds_nm'], [11270000,8520000,12730000,11480000])
        self.assertTrue(row['placement_eligible'])
        self.assertEqual(len(row['courtyard']['primitives']), 4)
        self.assertEqual(self.observation['source_board_sha256'], hashlib.sha256(self.raw).hexdigest())

    def test_asymmetric_sloped_fixed_obstacle_uses_true_bbox_centre_not_anchor(self):
        facts = c.facts_from_observation(self.observation, **self.options)
        row = self.row('J5'); fixed = next(v for v in facts['components'] if v['id'] == row['uuid'])
        self.assertFalse(row['placement_eligible'])
        self.assertEqual(row['position_nm'], [12000000,24000000])
        self.assertEqual(fixed['position_mm'], [12.1,24])
        self.assertAlmostEqual(fixed['size_mm'][0], 2.85)
        self.assertAlmostEqual(fixed['pads'][0]['offset_mm'][0], -.1)
        self.assertEqual(fixed['rotation_deg'], 0)
        self.assertIn(row['uuid'], facts['fixed_components'])
        self.assertTrue(any(p['local_start_nm'][0] == 1450000 or p['local_end_nm'][0] == 1450000
                            for p in row['courtyard']['primitives']))
        with self.assertRaisesRegex(ValueError, 'fixed in ordinary'):
            c.facts_from_observation(self.observation, **dict(self.options, selected=[row['uuid']]))

    def test_fixed_half_nm_centre_is_not_quantized_or_moved(self):
        fp = self.fp(self.tree,'J5')
        for line in c.sx.children(fp,'fp_line'):
            if c.atom(line,'layer') != 'F.CrtYd': continue
            for key in ('start','end'):
                point = c.sx.one(line,key)
                if point[1] == '1.5': point[1] = '1.500001'
        observation = self.inspect(self.tree)
        facts = c.facts_from_observation(observation, **self.options)
        candidate = c.constraints.original_alternative(facts)
        result,moves = c.quantized_translation(facts,candidate,observation=observation)
        fixed = next(row for row in result['transforms'] if row['component_id'] == c.uid(fp))
        self.assertEqual(fixed['x_mm'], 12.1000005)
        self.assertEqual(result,candidate)
        self.assertEqual(moves[fixture.selected()[0]], [12000000,10000000])

    def test_source_angles_and_every_non_xy_field_survive_translation(self):
        before = copy.deepcopy(self.tree)
        moves = {fixture.selected()[0]: [14000000,10000000], fixture.selected()[1]: [24000000,10000000]}
        translated = c.translated_tree(self.raw,moves,**self.options)
        self.assertEqual(c.sx.one(self.fp(translated),'at'), ['at','14','10','90'])
        self.assertEqual(c.sx.one(self.fp(translated,'J2'),'at'), ['at','24','10','270'])
        self.assertTrue(c.check_translation(self.raw,raw(translated),moves,**self.options)['exact_immutable_AST'])
        self.assertEqual(self.tree,before)
        for field in ('angle','model','graphic','pad','route','fixed'):
            changed = copy.deepcopy(translated)
            if field == 'angle': c.sx.one(self.fp(changed),'at')[3] = '0'
            if field == 'model': self.fp(changed).append(['model','"unknown"'])
            if field == 'graphic': c.sx.one(c.sx.children(self.fp(changed),'fp_line')[-1],'end')[1]='0.5'
            if field == 'pad': c.sx.one(c.sx.children(self.fp(changed),'pad')[0],'roundrect_rratio')[1]='0.2'
            if field == 'route': c.sx.one(c.sx.one(changed,'segment'),'width')[1]='0.5'
            if field == 'fixed': c.sx.one(self.fp(changed,'J5'),'at')[1]='12.2'
            with self.subTest(field=field),self.assertRaisesRegex(ValueError,'beyond selected'):
                c.check_translation(self.raw,raw(changed),moves,**self.options)

    def test_quantized_translation_uses_world_pad_offsets_and_real_anchor_moves(self):
        facts = c.facts_from_observation(self.observation,**self.options)
        row = next(v for v in facts['components'] if v['id']==fixture.selected()[0])
        self.assertEqual(sorted(p['offset_mm'] for p in row['pads']), [[0,-.825],[0,.825]])
        candidate = c.constraints.original_alternative(facts)
        next(v for v in candidate['transforms'] if v['component_id']==fixture.selected()[0])['x_mm']=14.00000049
        result,moves = c.quantized_translation(facts,candidate,observation=self.observation)
        self.assertEqual(moves[fixture.selected()[0]], [14000000,10000000])
        self.assertEqual(c.validate_moves(self.observation,moves,**self.options),result)
        false = copy.deepcopy(self.observation);false['footprints'][0]['courtyard']['bounds_nm'][0]+=1
        with self.assertRaisesRegex(ValueError,'proxy/source facts differ'):
            c.quantized_translation(facts,candidate,observation=false)

    def test_known_passive_metadata_and_rect_fill_variants_are_observed_not_executed(self):
        fp = self.fp(self.tree)
        fp.append(['property','"ki_fp_filters"','"R_*"'])
        fp.append(['model','"${UNRESOLVED}/model.wrl"',['offset',['xyz','0','0','0']],
                   ['scale',['xyz','1','1','1']],['rotate',['xyz','0','0','0']]])
        c.sx.one(c.sx.one(self.tree,'gr_rect'),'fill')[1]='no'
        observation = self.inspect(self.tree)
        row = next(r for r in observation['footprints'] if r['uuid']==c.uid(fp))
        self.assertEqual(row['metadata_properties'],[{'name':'ki_fp_filters','value':'R_*'}])
        self.assertEqual(row['models'][0]['path'],'${UNRESOLVED}/model.wrl')
        self.assertEqual(observation['outline']['primitives'][0]['fill'],'none')
        self.assertTrue(observation['graphics'])

    def test_four_line_board_rectangle_preserves_exact_ids(self):
        edge = c.sx.one(self.tree,'gr_rect');self.tree.remove(edge)
        for i,(a,b) in enumerate((((0,0),(38,0)),((38,0),(38,30)),((38,30),(0,30)),((0,30),(0,0)))):
            self.tree.append(['gr_line',['start',*map(str,a)],['end',*map(str,b)],
                ['stroke',['width','0.05'],['type','solid']],['layer','"Edge.Cuts"'],['uuid','"'+identity('outline'+str(i))+'"']])
        observation=self.inspect(self.tree)
        self.assertEqual(observation['outline']['bounds_nm'],[0,0,38000000,30000000])
        self.assertEqual(len(observation['outline']['primitives']),4)
        self.tree.append(copy.deepcopy(self.tree[-1]))
        with self.assertRaises(ValueError):self.inspect(self.tree)

    def test_locked_tracked_and_fixed_parts_cannot_be_moved(self):
        fp=self.fp(self.tree);fp.append(['locked','yes'])
        with self.assertRaisesRegex(ValueError,'fixed in ordinary'):
            c.facts_from_observation(self.inspect(self.tree),**self.options)
        tree=fixture.board()
        tree.append(['segment',['start','6','6'],['end','6.5','6'],['width','.2'],['layer','"F.Cu"'],
                     ['net','"ROUTE_A"'],['uuid','"'+identity('tracked-selected')+'"']])
        observed=self.inspect(tree)
        moves={fixture.selected()[0]:[14000000,10000000],fixture.selected()[1]:[24000000,10000000]}
        with self.assertRaisesRegex(ValueError,'Fixed/locked/unselected/tracked'):
            c.validate_moves(observed,moves,**self.options)

    def test_geometry_and_hazardous_unknown_fields_refuse(self):
        for fault in ('back','angle','custom','layers','ratio','padfield','coppergraphic','edgegraphic','arc','group','keepout','via','unknown','courtgap','duplicate'):
            tree=fixture.board();fp=self.fp(tree);pad=c.sx.children(fp,'pad')[0]
            if fault=='back':c.sx.one(fp,'layer')[1]='"B.Cu"'
            if fault=='angle':c.sx.one(fp,'at')[3]='45'
            if fault=='custom':pad[3]='custom'
            if fault=='layers':c.sx.one(pad,'layers').append('"B.Cu"')
            if fault=='ratio':c.sx.one(pad,'roundrect_rratio')[1]='NaN'
            if fault=='padfield':pad.append(['clearance','0'])
            if fault=='coppergraphic':c.sx.one(c.sx.children(fp,'fp_line')[-1],'layer')[1]='"F.Cu"'
            if fault=='edgegraphic':c.sx.one(c.sx.children(fp,'fp_line')[-1],'layer')[1]='"Edge.Cuts"'
            if fault=='arc':fp.append(['fp_arc'])
            if fault=='group':tree.append(['group','"group"'])
            if fault=='keepout':c.sx.one(tree,'zone').append(['keepout',['tracks','not_allowed']])
            if fault=='via':tree.append(['via'])
            if fault=='unknown':fp.append(['zone_connect','0'])
            if fault=='courtgap':c.sx.one(c.sx.children(fp,'fp_line')[0],'end')[1]='1.49'
            if fault=='duplicate':c.sx.one(pad,'uuid')[1]=c.sx.one(fp,'uuid')[1]
            with self.subTest(fault=fault),self.assertRaises(ValueError):self.inspect(tree)

    def test_pth_rect_fixed_absolute_angle_and_layer_flags(self):
        fp=self.fp(self.tree,'J3');pad=c.sx.one(fp,'pad');pad[3]='rect'
        c.sx.one(pad,'at').append('270')
        pad.extend([['remove_unused_layers','no'],['keep_end_layers','no']])
        observed=self.inspect(self.tree);row=next(r for r in observed['footprints'] if r['reference']=='J3')
        self.assertFalse(row['placement_eligible']);self.assertEqual(row['pads'][0]['angle'],270)
        self.assertEqual(row['pads'][0]['shape'],'rect');self.assertFalse(row['pads'][0]['remove_unused_layers'])
        c.sx.one(pad,'remove_unused_layers')[1]='sometimes'
        with self.assertRaises(ValueError):self.inspect(self.tree)

    def test_boundaries_and_old_scope_behavior_remain_explicit(self):
        with self.assertRaises(ValueError):c.inspect_board(self.raw)
        legacy=old_fixture();observed=c.inspect_board(legacy)
        self.assertNotIn('scope',observed)
        self.assertNotIn('placement_eligible',observed['footprints'][0])
        self.assertNotIn('offset_nm',observed['footprints'][0]['pads'][0])
        with self.assertRaises(ValueError):c.scope_options(scope=c.ORDINARY_SCOPE)
        for rows in (['not-an-angle'],['nan'],['90.1']):
            with self.assertRaises(ValueError):o.angle(rows[0])


if __name__=='__main__':unittest.main()
