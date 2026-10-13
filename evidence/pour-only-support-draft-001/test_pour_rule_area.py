"""Pure controls using authored interchange ASTs; no native-export assertion."""
import copy
import hashlib
import unittest
from pathlib import Path
import sys
HERE=Path(__file__).absolute().parent
ROOT=next(p for p in HERE.parents if (p/'autorouter/pipeline.py').is_file())
sys.dont_write_bytecode=True;sys.path.insert(0,str(ROOT));sys.path.insert(0,str(HERE))
import pour_rule_area as m
s=m.sx

def zone(number=1,x=10,layers=('F.Cu',),placement='disabled'):
    z=['zone',['net','0'],['net_name','""'],['layers',*['"'+v+'"' for v in layers]],['uuid','"00000000-0000-0000-0000-'+str(number).zfill(12)+'"'],
       ['keepout',*[[f,'not_allowed' if f=='copperpour' else 'allowed'] for f in m.FLAGS]],
       ['polygon',['pts',['xy',str(x),'10'],['xy',str(x+5),'10'],['xy',str(x+5),'15'],['xy',str(x),'15']]]]
    if placement=='disabled':z.append(['placement',['enabled','no'],['sheetname','"/"']])
    elif placement=='short':z.append(['placement',['enabled','no']])
    elif placement=='enabled':z.append(['placement',['enabled','yes'],['sheetname','"/"']])
    return z

def board(zones=None):
    return ['kicad_pcb',['version','20241229'],['layers',['0','"F.Cu"','signal'],['2','"B.Cu"','signal']],*(zones if zones is not None else [zone()])]

def entry(z,layer,kind='keepout',name='""'):
    points=s.one(s.one(z,'polygon'),'pts')[1:]
    coords=[str(v) for pt in points+[points[0]] for v in (m.pt.nm(pt[1],1000),-m.pt.nm(pt[2],1000))]
    return [kind,name,['polygon',layer,'0',*coords]]

def dsn(zones=None):
    tree=m._parse_dsn('(pcb "owned" (parser (string_quote ") (host_version "prospective-not-observed")) (resolution um 10) (unit um) (structure (layer F.Cu (type signal)) (layer B.Cu (type signal)) (future_atom original)) (network (net "N" (pins J1-1 J2-1))) (library) (wiring (future_copper never_touch)))')
    st=s.one(tree,'structure')
    for z in zones if zones is not None else [zone()]:
        for layer in (s.one(z,'layer') or s.one(z,'layers'))[1:]:st.append(entry(z,s.unquote(layer)))
    return tree

def raw(tree):return (s.dump(tree)+'\n').encode()
def exchange(b,t):return m.correct(raw(b),m._dump_dsn(t).encode())

class Controls(unittest.TestCase):
    def reject(self,b=None,t=None):
        with self.assertRaises(ValueError):exchange(board() if b is None else b,dsn() if t is None else t)
    def test_root_pour_only_both_layers_exact_delete_and_full_ast_preservation(self):
        z=zone(layers=('F.Cu','B.Cu'));b=board([z]);t=dsn([z]);other=entry(zone(2,40),'F.Cu',name='"retained"');s.one(t,'structure').append(other)
        before=copy.deepcopy((b,t));out,r=exchange(b,t);expected=copy.deepcopy(t);st=s.one(expected,'structure');st[:]=[n for n in st if n not in [entry(z,'F.Cu'),entry(z,'B.Cu')]]
        self.assertEqual(m._parse_dsn(out.decode()),expected);self.assertEqual((b,t),before);self.assertEqual(r['removed_count'],2)
        self.assertEqual(r['kept_keepout_count'],1);self.assertFalse(r['routing_accepted']);self.assertFalse(r['native_fill_verified']);self.assertFalse(r['native_observation_verified'])
        self.assertEqual(r['output_sha256'],hashlib.sha256(out).hexdigest());self.assertEqual(r['source_board_sha256'],hashlib.sha256(raw(b)).hexdigest())
    def test_absent_and_short_disabled_placement_supported_without_source_mutation(self):
        for placement in ('absent','short','disabled'):
            z=zone(placement=placement);b=board([z]);before=copy.deepcopy(b)
            with self.subTest(placement=placement):self.assertEqual(exchange(b,dsn([z]))[1]['removed_count'],1);self.assertEqual(b,before)
    def test_unrestricted_area_is_exact_noop_and_mixed_area_is_retained(self):
        a=zone(2,40);s.one(a,'keepout')[4][1]='allowed';b=board([a]);data=b'(prospective uninterpreted no-op input)\n'
        out,r=m.correct(raw(b),data);self.assertEqual(out,data);self.assertEqual(r['removed_count'],0)
        z=zone();out,r=exchange(board([z,a]),dsn([z,a]));self.assertEqual(r['removed_count'],1);self.assertIn(entry(a,'F.Cu'),s.one(m._parse_dsn(out.decode()),'structure'))
    def test_each_other_restriction_remains_blocked(self):
        for flag in ('tracks','vias','pads','footprints'):
            z=zone();s.one(s.one(z,'keepout'),flag)[1]='not_allowed'
            with self.subTest(flag=flag):self.reject(board([z]),dsn([z]))
    def test_missing_duplicate_extra_and_malformed_flags_rejected(self):
        for mode in ('missing','duplicate','extra','malformed'):
            z=zone();ko=s.one(z,'keepout')
            if mode=='missing':ko.pop()
            elif mode=='duplicate':ko[-1]=copy.deepcopy(ko[1])
            elif mode=='extra':ko.append(['future','allowed'])
            else:ko[1][1]=['allowed']
            with self.subTest(mode=mode):self.reject(board([z]))
    def test_enabled_placement_unknown_guidance_and_duplicate_enabled_rejected(self):
        for mode in ('enabled','unknown','duplicate'):
            z=zone(placement='enabled' if mode=='enabled' else 'disabled');p=s.one(z,'placement')
            if mode=='unknown':p.append(['future','"x"'])
            elif mode=='duplicate':p.append(['enabled','no'])
            with self.subTest(mode=mode):self.reject(board([z]))
    def test_bound_net_and_nonempty_net_name_rejected(self):
        for change in (['net','1'],['net','""'],['net_name','"GND"']):
            z=zone();s.one(z,change[0])[:]=change
            with self.subTest(change=change):self.reject(board([z]))
    def test_unknown_restricted_zone_and_nested_metadata_rejected(self):
        for field in (['future_source',['safety','unknown']],['fill',['future','1']],['fill',['thermal_gap','0.5'],['thermal_gap','0.7']],['hatch','edge','NaN'],['connect_pads',['unknown','0']]):
            z=zone();z.append(field)
            with self.subTest(field=field):self.reject(board([z]))
    def test_holes_arcs_duplicate_polygon_and_invalid_simple_outlines_rejected(self):
        for mode in ('arc','hole','duplicate','bowtie','collinear','nonfinite'):
            z=zone();p=s.one(z,'polygon');pts=s.one(p,'pts')
            if mode=='arc':pts[1]=['arc',['start','0','0'],['mid','1','1'],['end','2','0']]
            elif mode=='hole':p.append(['pts',['xy','1','1'],['xy','2','1'],['xy','2','2']])
            elif mode=='duplicate':z.append(copy.deepcopy(p))
            elif mode=='bowtie':pts[2],pts[3]=pts[3],pts[2]
            elif mode=='collinear':pts.insert(2,['xy','12','10'])
            else:pts[1][1]='Infinity'
            with self.subTest(mode=mode):self.reject(board([z]))
    def test_layer_net_and_uuid_ambiguity_rejected(self):
        for mode in ('wildcard','undeclared','duplicate_layer','duplicate_selector','bad_uuid','uuid_collision'):
            z=zone();b=board([z])
            if mode=='wildcard':s.one(z,'layers')[1]='"*.Cu"'
            elif mode=='undeclared':s.one(b,'layers').pop(1)
            elif mode=='duplicate_layer':s.one(z,'layers').append('"F.Cu"')
            elif mode=='duplicate_selector':z.append(['layer','"F.Cu"'])
            elif mode=='bad_uuid':s.one(z,'uuid')[1]='"unknown"'
            else:b.append(['footprint','"owned"',copy.deepcopy(s.one(z,'uuid'))])
            with self.subTest(mode=mode):self.reject(b)
    def test_footprint_restriction_and_legacy_alias_rejected(self):
        self.reject(board([])+[['footprint','"x"',zone()]])
        self.reject(board()+[['module','"legacy"']])
    def test_missing_duplicate_colliding_and_wrong_type_export_rejected(self):
        for mode in ('missing','duplicate','named','wire','signal','reordered','nonzero_width','wrong_layer'):
            t=dsn();st=s.one(t,'structure');node=st[-1]
            if mode=='missing':st.pop()
            elif mode=='duplicate':st.append(copy.deepcopy(node))
            elif mode=='named':node[1]='"named"'
            elif mode=='wire':node[0]='wire_keepout'
            elif mode=='signal':node[2][1]='signal'
            elif mode=='nonzero_width':node[2][2]='1'
            elif mode=='wrong_layer':node[2][1]='B.Cu'
            else:
                coords=node[2][3:];node[2][3:]=coords[2:-2]+coords[:2]+coords[2:4]
            with self.subTest(mode=mode):self.reject(t=t)
    def test_ring_equivalent_duplicate_export_and_source_are_collisions(self):
        z=zone();t=dsn();n=copy.deepcopy(s.one(t,'structure')[-1]);pairs=[n[2][i:i+2] for i in range(3,len(n[2]),2)][:-1];pairs=pairs[1:]+pairs[:1];n[2][3:]=[v for p in pairs+[pairs[0]] for v in p];s.one(t,'structure').append(n);self.reject(t=t)
        other=zone(2);pts=s.one(s.one(other,'polygon'),'pts');pts[1:]=pts[2:]+pts[1:2];s.one(s.one(other,'keepout'),'copperpour')[1]='allowed'
        self.reject(board([z,other]),dsn([z]))
    def test_other_dsn_atom_or_keepout_survives_while_unknown_provenance_blocks(self):
        t=dsn();extra=entry(zone(2,40),'B.Cu',kind='via_keepout',name='"known-extra"');s.one(t,'structure').append(extra)
        out,_=exchange(board(),t);self.assertIn(extra,s.one(m._parse_dsn(out.decode()),'structure'));self.assertIn(['wiring',['future_copper','never_touch']],m._parse_dsn(out.decode()))
        t=dsn();s.one(t,'library').append(['image','"x"',entry(zone(2,40),'F.Cu')]);self.reject(t=t)
        t=dsn();s.one(t,'structure').append(['future_keepout','"x"',['rect','F.Cu','0','0','1','1']]);self.reject(t=t)
    def test_unit_change_and_layer_declaration_collision_rejected(self):
        t=dsn();s.one(t,'unit')[1]='mm';self.reject(t=t)
        t=dsn();s.one(t,'structure').append(['layer','F.Cu',['type','signal']]);self.reject(t=t)
    def test_actual_pinned_nus_source_qualifies_without_native_export_claim(self):
        path=ROOT/'.data/expansion008/nus-usb-led/src/usb_led.kicad_pcb';data=path.read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(),'a8e69c14ceec9dd0954c3027cc89ca6bbb9c0b0ec3aeede5feacfdd47736f362')
        before=hashlib.sha256(data).hexdigest();rows=m.qualify(s.parse(data.decode()))
        self.assertEqual(len(rows),1);self.assertEqual(rows[0]['uuid'],'1abd2188-f015-4692-bf4a-117c7482b9fc');self.assertEqual(rows[0]['layers'],['F.Cu'])
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),before)
if __name__=='__main__':unittest.main(verbosity=2)
