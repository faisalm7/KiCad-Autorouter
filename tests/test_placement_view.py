"""Pure SVG display controls; no Native, source mutation or approval claim."""
import copy
import unittest
import xml.etree.ElementTree as ET

from autorouter.placement_view import render


def observation():
    def footprint(identity, x, y, *, locked=False):
        return dict(uuid=identity,reference=identity,position_nm=[x,y],angle=0,side='front',locked=locked,
            courtyard=dict(bounds_nm=[x-2_800_000,y-1_300_000,x+2_800_000,y+1_300_000]),
            pads=[dict(uuid=identity+'-'+str(i),number=str(i),net='NET'+str(i),
                position_nm=[x+offset,y],offset_nm=[offset,0],size_nm=[1_600_000]*2,drill_nm=[800_000]*2)
                  for i,offset in ((1,-1_270_000),(2,1_270_000))])
    return dict(schema=1,outline=dict(bounds_nm=[0,0,40_000_000,30_000_000]),
        footprints=[footprint('J1',10_000_000,10_000_000),footprint('J2',27_000_000,10_000_000),
                    footprint('J3',20_000_000,20_000_000,locked=True)],
        routes=[dict(uuid='trace',kind='segment',net='KEEP',start_nm=[10_000_000,20_000_000],
            end_nm=[20_000_000,20_000_000],width_nm=300_000,layer='F.Cu',locked=True)],route_count=1,
        zones=[dict(uuid='zone',is_rule_area=False,holes=[0],arc_count=0,outline_closed=[True],
            outlines_nm=[[[5_000_000,24_000_000],[35_000_000,24_000_000],[35_000_000,28_000_000],[5_000_000,28_000_000]]])])


class PlacementViewTests(unittest.TestCase):
    def setUp(self):
        self.observation=observation()
        self.moves={'J1':[13_000_000,11_000_000],'J2':[24_000_000,9_000_000]}
        self.region=[4_000_000,5_000_000,36_000_000,15_000_000]

    def svg(self, **kwargs):
        return render(self.observation,self.moves,['J1','J2'],self.region,**kwargs)

    def rows(self, svg, role):
        return [node for node in ET.fromstring(svg).iter() if node.get('data-role')==role]

    def test_deterministic_detached_source_and_identity_sorted_display(self):
        before=copy.deepcopy((self.observation,self.moves,self.region))
        first=self.svg();self.assertEqual(first,self.svg())
        self.assertEqual((self.observation,self.moves,self.region),before)
        self.observation['footprints'].reverse()
        self.assertEqual(first,self.svg())
        self.assertIn('Geometry draft — Native validation required',first)
        self.assertIn('no validation, approval or execution authority',first)

    def test_actual_pad_offsets_translate_with_selected_anchor_and_ghost_stays(self):
        svg=self.svg()
        original={node.get('data-pad'):node for node in self.rows(svg,'original-selected-pad')}
        proposed={node.get('data-pad'):node for node in self.rows(svg,'proposed-selected-pad')}
        self.assertEqual(original['J1-1'].get('data-centre-nm'),'8730000,10000000')
        self.assertEqual(original['J1-2'].get('data-centre-nm'),'11270000,10000000')
        self.assertEqual(proposed['J1-1'].get('data-centre-nm'),'11730000,11000000')
        self.assertEqual(proposed['J1-2'].get('data-centre-nm'),'14270000,11000000')
        self.assertEqual(original['J1-1'].get('r'),proposed['J1-1'].get('r'))
        self.assertGreater(float(proposed['J1-1'].get('cy')),float(original['J1-1'].get('cy')))
        self.assertEqual([node.text for node in self.rows(svg,'proposed-xy')],['13, 11','24, 9'])

    def test_fixed_copper_width_zone_and_fixed_parts_never_follow_selected_moves(self):
        first=self.svg()
        self.moves={'J1':[14_000_000,10_000_000],'J2':[23_000_000,10_000_000]}
        second=self.svg()
        for role in ('preserved-segment','zone','fixed','fixed-pad','fixed-drill'):
            self.assertEqual([node.attrib for node in self.rows(first,role)],
                             [node.attrib for node in self.rows(second,role)])
        route=self.rows(first,'preserved-segment')[0]
        self.assertEqual(route.get('data-start-nm'),'10000000,20000000')
        self.assertEqual(route.get('data-end-nm'),'20000000,20000000')
        self.assertEqual(route.get('data-width-nm'),'300000')
        scale=(float(route.get('x2'))-float(route.get('x1')))/10_000_000
        self.assertAlmostEqual(float(route.get('stroke-width')),300_000*scale,places=5)

    def test_small_positive_width_is_not_rounded_to_zero_on_large_board(self):
        self.observation['outline']['bounds_nm']=[-2_000_000_000,-2_000_000_000,2_000_000_000,2_000_000_000]
        self.observation['routes'][0]['width_nm']=1
        route=self.rows(self.svg(),'preserved-segment')[0]
        self.assertGreater(float(route.get('stroke-width')),0)
        self.assertEqual(route.get('data-width-nm'),'1')

    def test_xml_escaping_cannot_create_active_or_external_svg_content(self):
        malicious='J<&"\'><script href="https://invalid/">x</script>'
        self.observation['footprints'][0]['reference']=malicious
        self.observation['footprints'][0]['uuid']=malicious
        self.moves={malicious:self.moves['J1'],'J2':self.moves['J2']}
        svg=render(self.observation,self.moves,[malicious,'J2'],self.region,title=malicious,state=malicious)
        root=ET.fromstring(svg)
        self.assertEqual(root.find('{http://www.w3.org/2000/svg}title').text,malicious)
        self.assertIn('&lt;script',svg)
        for node in root.iter():
            self.assertIn(node.tag.rsplit('}',1)[-1],{'svg','title','desc','rect','text','polygon','line','circle'})
            self.assertFalse(any(key.lower().startswith('on') or 'href' in key.lower() for key in node.attrib))
        for bad in ('\x00','\ud800','x'*161):
            with self.subTest(bad=repr(bad)),self.assertRaises(ValueError):self.svg(title=bad)

    def test_nonfinite_oversized_ambiguous_coordinates_and_moves_refuse(self):
        for bad in (float('nan'),float('inf'),10**400,True,'1',2_000_000_001):
            with self.subTest(bad=str(bad)),self.assertRaises(ValueError):
                render(self.observation,{'J1':[bad,10_000_000],'J2':self.moves['J2']},['J1','J2'],self.region)
        for selected,moves in ((['J1','J1'],{'J1':[1,2]}),(['missing'],{'missing':[1,2]}),
                               (['J1'],{'J1':[1,2],'J2':[3,4]})):
            with self.subTest(selected=selected),self.assertRaises(ValueError):
                render(self.observation,moves,selected,self.region)

    def test_population_and_unsupported_geometry_refuse(self):
        for key,count in (('footprints',17),('routes',65),('zones',33)):
            value=copy.deepcopy(self.observation);value[key]=[value[key][0]]*count
            with self.subTest(key=key),self.assertRaises(ValueError):
                render(value,self.moves,['J1','J2'],self.region)
        for mutate in (lambda v:v['routes'][0].update(kind='arc'),
                       lambda v:v['zones'][0].update(holes=[1]),
                       lambda v:v['footprints'][0]['pads'][0].update(size_nm=[1_000_000,2_000_000]),
                       lambda v:v.update(route_count=2)):
            value=copy.deepcopy(self.observation);mutate(value)
            with self.assertRaises(ValueError):render(value,self.moves,['J1','J2'],self.region)


if __name__=='__main__':
    unittest.main()
