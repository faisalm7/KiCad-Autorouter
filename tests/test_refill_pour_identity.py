"""Observed source/save grammar regression; these controls do not run KiCad."""
import copy
import unittest
from autorouter import board_floor as g,pipeline as p,sexpr as sx
from tests.test_pour_rule_area import board,zone


class PourRefillIdentityControls(unittest.TestCase):
    def source(self):
        tree=board()
        tree.append(['segment',['start','0','0'],['end','1','0'],['width','0.3'],
            ['layer','"F.Cu"'],['net','"N"'],
            ['uuid','"00000000-0000-0000-0000-000000001000"']])
        return tree

    def saved(self,source):
        tree=copy.deepcopy(source);area=sx.children(tree,'zone')[0]
        area[:]=[n for n in area if not isinstance(n,list) or not n or n[0] not in {'net','net_name'}]
        return tree

    def test_observed_source_marker_and_saved_omission_preserve_route_and_source(self):
        source=self.source();saved=self.saved(source);before=copy.deepcopy((source,saved))
        p.check_refill_route_nets(source,saved)
        self.assertEqual(p.transplant_fill(source,saved),source)
        self.assertEqual((source,saved),before)

    def test_original_decoder_remains_strict_and_opt_in_is_typed(self):
        source=self.source()
        with self.assertRaisesRegex(ValueError,'unqualified named'):g.source_net_identity(source)
        self.assertEqual(g.source_net_identity(source,allow_pour_only_areas=True)[0],{'N'})
        for value in (1,None,'yes',[]):
            with self.subTest(value=value),self.assertRaises(ValueError):g.source_net_identity(source,allow_pour_only_areas=value)

    def test_real_route_net_change_still_refuses(self):
        source=self.source();saved=self.saved(source);sx.one(p.routes(saved)[0],'net')[1]='"OTHER"'
        with self.assertRaisesRegex(p.Rejected,'net assignments'):p.transplant_fill(source,saved)

    def test_unknown_numbers_extra_atoms_and_conflicting_or_missing_names_refuse(self):
        for mode in ('one','unknown','leadingzero','extra','conflict','missing','duplicate','duplicate_net'):
            source=self.source();area=sx.children(source,'zone')[0]
            if mode in ('one','unknown','leadingzero'):sx.one(area,'net')[1]={'one':'1','unknown':'999','leadingzero':'00'}[mode]
            elif mode=='extra':sx.one(area,'net').append('""')
            elif mode=='conflict':sx.one(area,'net_name')[1]='"N"'
            elif mode=='missing':area.remove(sx.one(area,'net_name'))
            elif mode=='duplicate':area.append(copy.deepcopy(sx.one(area,'net_name')))
            else:area.append(copy.deepcopy(sx.one(area,'net')))
            with self.subTest(mode=mode),self.assertRaises((p.Rejected,ValueError)):p.transplant_fill(source,self.saved(source))

    def test_other_restrictions_unknown_fields_and_geometry_do_not_gain_support(self):
        for mode in ('tracks','vias','pads','footprints','unknown_flag','unknown_field','placement','bad_uuid','duplicate_uuid','wildcard'):
            source=self.source();area=sx.children(source,'zone')[0]
            if mode in ('tracks','vias','pads','footprints'):sx.one(sx.one(area,'keepout'),mode)[1]='not_allowed'
            elif mode=='unknown_flag':sx.one(area,'keepout').append(['future','allowed'])
            elif mode=='unknown_field':area.append(['future','unknown'])
            elif mode=='placement':sx.one(sx.one(area,'placement'),'enabled')[1]='yes'
            elif mode=='bad_uuid':sx.one(area,'uuid')[1]='"unknown"'
            elif mode=='duplicate_uuid':sx.one(p.routes(source)[0],'uuid')[1]=sx.one(area,'uuid')[1]
            else:sx.one(area,'layers')[1]='"*.Cu"'
            with self.subTest(mode=mode),self.assertRaises((p.Rejected,ValueError)):p.transplant_fill(source,self.saved(source))

    def test_numeric_zero_is_not_a_pad_route_or_footprint_area_alias(self):
        for mode in ('pad','route','footprint','copper'):
            source=self.source();area=sx.children(source,'zone')[0]
            if mode=='route':sx.one(p.routes(source)[0],'net')[1]='0'
            elif mode=='pad':source.append(['footprint',['pad','1',['net','0']]])
            elif mode=='footprint':source.remove(area);source.append(['footprint',area])
            else:area.remove(sx.one(area,'keepout'));area.remove(sx.one(area,'placement'))
            with self.subTest(mode=mode),self.assertRaises((p.Rejected,ValueError)):p.transplant_fill(source,self.saved(source) if mode!='footprint' else copy.deepcopy(source))

    def test_four_layer_numeric_area_marker_is_still_unsupported(self):
        source=self.source();sx.one(source,'layers')[1:]=[['0','"F.Cu"','signal'],['4','"In1.Cu"','signal'],['6','"In2.Cu"','signal'],['2','"B.Cu"','signal']]
        with self.assertRaises((p.Rejected,ValueError)):p.transplant_fill(source,self.saved(source))

    def test_quoted_zero_remains_a_distinct_named_net(self):
        source=self.source();sx.one(p.routes(source)[0],'net')[1]='"0"'
        saved=self.saved(source);p.check_refill_route_nets(source,saved)
        self.assertEqual(g.source_net_identity(source,allow_pour_only_areas=True)[0],{'0'})
        sx.one(p.routes(saved)[0],'net')[1]='0'
        with self.assertRaises(p.Rejected):p.check_refill_route_nets(source,saved)


if __name__=='__main__':unittest.main()
