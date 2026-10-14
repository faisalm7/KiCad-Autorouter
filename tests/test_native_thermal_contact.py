"""Authored contact proposal metadata only; no actual Native/acceptance claim."""
import copy,hashlib,unittest
from autorouter import sexpr as sx,thermal_geometry as geom,thermal
from autorouter import thermal_contact as contact

def scene():
    poly=[[-2000000,-2000000],[2000000,-2000000],[2000000,2000000],[-2000000,2000000]]
    tree=['kicad_pcb',['net','0','""'],['net','1','"GND"'],
      ['footprint','"owned"',['uuid','"fp"'],['at','0','0'],['property','"Reference"','"R1"'],
       ['pad','"2"','smd','roundrect',['at','0','0','90'],['size','.6','.5'],['layers','"F.Cu"'],['roundrect_rratio','.25'],['net','1','"GND"'],['uuid','"pad"']]],
      ['zone',['net','1'],['layers','"F.Cu"','"B.Cu"'],['uuid','"zone"'],
       ['filled_polygon',['layer','"F.Cu"'],['pts',*(["xy",geom.mm(x),geom.mm(y)] for x,y in poly)]]]]
    raw=(sx.dump(tree)+'\n').encode();finding={'type':'starved_thermal','severity':'error','description':'Thermal relief connection to zone incomplete (layer F.Cu; zone min spoke count 2; actual 1)','items':[{'uuid':'zone'},{'uuid':'pad'}]}
    native={'opens':0,'blocking':1,'warnings':0,'exclusions':0,'ignored_checks':[],'findings':[finding]}
    shape={'id':0,'on_layer':True,'flash_layer':True,'shape_is_circle':False,'shape_is_rect':False,'shape_is_roundrect':True,'size_nm':[600000,500000],'offset_nm':[0,0],'shape_position_nm':[0,0]}
    pad={'uuid':'pad','net_code':1,'position_nm':[0,0],'orientation_degrees':90,'is_pth':False,'drill_size_nm':[0,0],'effective_hole':{'width_nm':0},'layers':[shape]}
    body={'native_outline_index':0,'zone_uuid':'zone','net_code':1,'layer_id':0,'hole_count':0,'holes_nm':[],'native_outer_closed':True,'native_self_intersecting':False,'native_total_arc_count':0,'outer_nm':poly}
    g={'schema':1,'mode':contact.POLICY,'native_version':'10.0.0','api_error_count':0,'source_unchanged':True,'board_saved':False,'board_sha256':hashlib.sha256(raw).hexdigest(),'finding':finding,'layers':[{'id':0,'canonical':'F.Cu'}],'reported_layer':'F.Cu','zone_copper_layers':['F.Cu','B.Cu'],'bodies':[body],'target_pad_uuid':'pad','zone_uuid':'zone','net_code':1,'net_name':'GND','pads':[pad],'class':{'width_nm':200000},'native_max_error_nm':5000}
    return raw,native,g

def propose(raw,native,g):
    if contact.report_layer(g)[1]!=native['findings'][0] or thermal.sole_thermal(native) is None:raise geom.Unsupported('sole actual-bound report required by caller')
    if hashlib.sha256(raw).hexdigest()!=g['board_sha256']:raise geom.Unsupported('stale actual source')
    contact.fill_binding(sx.parse(raw.decode()),g,sx)
    return contact.propose(g,remaining_seconds=lambda:10,binding_verified=True)

class NativeThermalContactControls(unittest.TestCase):
    def test_samebody_smd_four_native_local_rays_without_acceptance(self):
        raw,native,g=scene();before=copy.deepcopy((raw,native,g));r=propose(raw,native,g)
        self.assertEqual(len(r['proposals']),4);self.assertEqual(r['proposals'][0]['end_nm'],[0,405001]);self.assertEqual(r['proposals'][1]['end_nm'],[-355001,0])
        self.assertTrue(all(p['start_nm']==[0,0] and p['saved_outline_index']==0 and p['layer']=='F.Cu' for p in r['proposals']))
        self.assertFalse(r['routing_accepted']);self.assertFalse(r['whole_body_certificate_qualified']);self.assertFalse(r['ampacity_qualified']);self.assertEqual(before,(raw,native,g))
        contact.verify_proposals(g,r,remaining_seconds=lambda:10)
        broken=copy.deepcopy(r);broken['proposals'][0]['end_nm'][0]+=1
        with self.assertRaises(geom.Unsupported):contact.verify_proposals(g,broken,remaining_seconds=lambda:10)
        with self.assertRaises(geom.Unsupported):contact.propose(g,remaining_seconds=lambda:10)

    def test_other_findings_missing_layer_wrong_mode_and_stale_source_refuse(self):
        for fault in ('opens','extra','wording','layer','mode','stale'):
            raw,native,g=scene()
            if fault=='opens':native['opens']=1
            elif fault=='extra':native['blocking']=2;native['findings'].append({'type':'clearance','severity':'error','items':[]})
            elif fault=='wording':native['findings'][0]['description']='thermal layer unknown'
            elif fault=='layer':g['reported_layer']='B.Cu'
            elif fault=='mode':g['mode']='legacy-certificate'
            else:raw+=b' '
            with self.subTest(fault=fault),self.assertRaises(geom.Unsupported):propose(raw,native,g)

    def test_unsupported_shape_offset_rotation_api_and_fill_mismatch_refuse(self):
        for fault in ('shape','offset','rotation','api','fill'):
            raw,native,g=scene();pad=g['pads'][0]
            if fault=='shape':pad['layers'][0]['shape_is_roundrect']=False
            elif fault=='offset':pad['layers'][0]['offset_nm']=[1,0]
            elif fault=='rotation':pad['orientation_degrees']=45
            elif fault=='api':g['api_error_count']=1
            else:g['bodies'][0]['outer_nm'][0][0]-=1
            with self.subTest(fault=fault),self.assertRaises(geom.Unsupported):propose(raw,native,g)

    def test_endpoint_margin_and_exhaustion_never_fake_a_proposal(self):
        raw,native,g=scene();tree=sx.parse(raw.decode());zone=sx.children(tree,'zone')[0];zone[-1][2]=['pts',['xy','-.1','-.1'],['xy','.1','-.1'],['xy','.1','.1'],['xy','-.1','.1']]
        raw=(sx.dump(tree)+'\n').encode();g['board_sha256']=hashlib.sha256(raw).hexdigest();g['bodies'][0]['outer_nm']=[[-100000,-100000],[100000,-100000],[100000,100000],[-100000,100000]]
        self.assertEqual(propose(raw,native,g)['proposals'],[])
        with self.assertRaises(geom.Unsupported):contact.propose(g,remaining_seconds=lambda:0,binding_verified=True)
if __name__=='__main__':unittest.main()
