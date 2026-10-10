"""Pure independently declared scenes; no native or engine subprocesses."""
import copy,importlib.util,json,sys,unittest
from pathlib import Path
from autorouter import placement_transform as m
s=m.sx
FLAGS=['tracks','vias','pads','copperpour','footprints']

def recipe(number=1,x=10,prohibit=None,enabled=True):
 uid=f'00000000-0000-0000-0000-{number:012d}';points=[[x,10],[x+5,10],[x+5,15],[x,15]]
 zone=['zone',['net','0'],['net_name','""'],['layers','"F.Cu"','"B.Cu"'],['uuid','"'+uid+'"'],['name','"area'+str(number)+'"'],
       ['keepout',*[[flag,'not_allowed' if flag==prohibit else 'allowed'] for flag in FLAGS]],['placement',['enabled','yes' if enabled else 'no'],['sheetname','"/Scene/"']],
       ['polygon',['pts',*[['xy',str(a),str(b)] for a,b in points]]]]
 native={'uuid':uid,'name':'area'+str(number),'parent':'board','is_rule_area':True,'placement_enabled':enabled,'placement_source_type':'SHEETNAME','placement_source':'/Scene/',
         'disallow':{f:f==prohibit for f in FLAGS},'layers':['F.Cu','B.Cu'],'outlines_nm':[[[a*1000000,b*1000000] for a,b in points]],'holes':[0],'arc_count':0,'outline_closed':[True]}
 kind='wire_keepout' if prohibit=='tracks' else 'via_keepout' if prohibit=='vias' else 'keepout'
 entries=[[kind,'""',['polygon',layer,'0',*[str(v) for a,b in points+[points[0]] for v in (a*1000,-b*1000)]]] for layer in ('F.Cu','B.Cu')]
 return zone,native,entries

def scene(recipes=None):
 recipes=recipes or [recipe()]
 edges=[((0,0),(100,0)),((100,0),(100,100)),((100,100),(0,100)),((0,100),(0,0))]
 board=['kicad_pcb',['layers',['0','"F.Cu"','signal'],['2','"B.Cu"','signal']],*[['gr_line',['start',*map(str,a)],['end',*map(str,b)],['layer','"Edge.Cuts"']] for a,b in edges],*[x[0] for x in recipes]]
 tree=m._parse_dsn('(pcb "scene" (parser (string_quote ") (host_version "10.0.0")) (resolution um 10) (unit um) (structure (boundary (path pcb 0 0 0 100000 0 100000 -100000 0 -100000 0 0))) (network (net "N" (pins J1-1 J2-1))) (library))')
 s.one(tree,'structure').extend(e for r in recipes for e in r[2])
 files={'board.kicad_pcb':(s.dump(board)+'\n').encode(),'board.kicad_pro':b'{}','notice.txt':b'Owned synthetic test'}
 raw=m._dump_dsn(tree).encode();h=m.inventory(files)
 obs={'context_schema':1,'native_version':'10.0.0','units':'integer nanometres','source':'/immutable/project/board.kicad_pcb','board_sha256':h['board.kicad_pcb'],'project_sha256':h['board.kicad_pro'],'dsn_sha256':m.sha(raw),'input_hashes_before':h,'input_hashes_after':dict(h),'board_saved':False,'footprint_rulearea_count':0,'footprint_zone_count':0,'zones':[r[1] for r in recipes]}
 return {'original_files':files,'native_input_files':copy.deepcopy(files),'board_name':'board.kicad_pcb','observation':obs,'raw_dsn':raw,'guided_dsn':raw}

def change_board(c,fn,original=True):
 tree=s.parse(c['native_input_files']['board.kicad_pcb'].decode());fn(tree);data=(s.dump(tree)+'\n').encode();c['native_input_files']['board.kicad_pcb']=data
 if original:c['original_files']['board.kicad_pcb']=data
 h=m.inventory(c['native_input_files']);c['observation'].update(board_sha256=h['board.kicad_pcb'],input_hashes_before=h,input_hashes_after=dict(h))
def change_dsn(c,fn):
 tree=m._parse_dsn(c['raw_dsn'].decode());fn(tree);data=m._dump_dsn(tree).encode();c.update(raw_dsn=data,guided_dsn=data);c['observation']['dsn_sha256']=m.sha(data)

class Controls(unittest.TestCase):
 def reject(self,c):
  with self.assertRaises(ValueError):m.transform(**c)
 def test_positive_exact_delete_only(self):
  c=scene();before=copy.deepcopy(c);out,r=m.transform(**c);expected=m._parse_dsn(c['guided_dsn'].decode());st=s.one(expected,'structure');st[:]=[n for n in st if not isinstance(n,list) or n[0]!='keepout'];self.assertEqual(m._parse_dsn(out.decode()),expected);self.assertEqual(r['removed_count'],2);self.assertFalse(r['routing_accepted']);self.assertEqual(c,before)
 def test_mixed_true_obstacles_preserved_exactly(self):
  c=scene([recipe(),recipe(2,30,'tracks',False),recipe(3,50,'vias',False),recipe(4,70,'pads',False)]);out,r=m.transform(**c)
  self.assertEqual(r['removed_count'],2);self.assertEqual(r['kept_keepout_count'],6);self.assertEqual([x['node'] for x in m.keepouts(m._parse_dsn(out.decode()))],[x['node'] for x in m.keepouts(m._parse_dsn(c['raw_dsn'].decode()))][2:])
 def test_all_five_prohibitions_prevent_removal(self):
  for flag in FLAGS:
   with self.subTest(flag=flag):self.reject(scene([recipe(prohibit=flag)]))
 def test_native_flag_contradiction(self):
  for flag in FLAGS:
   c=scene();c['observation']['zones'][0]['disallow'][flag]=True
   with self.subTest(flag=flag):self.reject(c)
 def test_disabled_no_eligible(self):self.reject(scene([recipe(enabled=False)]))
 def test_disabled_all_allowed_retained_when_disjoint(self):
  out,r=m.transform(**scene([recipe(),recipe(2,30,enabled=False)]));self.assertEqual(r['kept_keepout_count'],2)
 def test_missing_duplicate_extra_source_flags(self):
  for mode in ('missing','duplicate','extra'):
   c=scene()
   def mutate(b):
    k=s.one(s.children(b,'zone')[0],'keepout')
    if mode=='missing':k.pop()
    elif mode=='duplicate':k[-1]=k[1]
    else:k.append(['future_allow','allowed'])
   change_board(c,mutate)
   with self.subTest(mode=mode):self.reject(c)
 def test_missing_duplicate_extra_native_rows(self):
  for mode in ('missing','duplicate','extra'):
   c=scene();rows=c['observation']['zones']
   if mode=='missing':rows.clear()
   elif mode=='duplicate':rows.append(copy.deepcopy(rows[0]))
   else:rows[0]['newflag']=False
   with self.subTest(mode=mode):self.reject(c)
 def test_strict_native_boolean(self):
  for key in ('is_rule_area','placement_enabled'):
   c=scene();c['observation']['zones'][0][key]=1;self.reject(c)
  c=scene();c['observation']['zones'][0]['disallow']['tracks']=0;self.reject(c)
 def test_unknown_native_enum_units(self):
  c=scene();c['observation']['zones'][0]['placement_source_type']='UNKNOWN';self.reject(c)
  c=scene();c['observation']['units']='millimetres';self.reject(c)
 def test_source_identity_or_hash(self):
  for key in ('source','board_sha256','project_sha256','dsn_sha256'):
   c=scene();c['observation'][key]='wrong';self.reject(c)
 def test_native_input_stale_inventory(self):
  c=scene();c['native_input_files']['notice.txt']=b'changed';self.reject(c)
 def test_native_input_route_change_is_not_stripping(self):
  c=scene();change_board(c,lambda b:b.append(['segment',['start','1','1'],['end','2','2']]),original=False);self.reject(c)
 def test_native_input_exact_route_stripping_allowed(self):
  c=scene();b=s.parse(c['original_files']['board.kicad_pcb'].decode());b.append(['segment',['start','1','1'],['end','2','2']]);c['original_files']['board.kicad_pcb']=(s.dump(b)+'\n').encode();out,r=m.transform(**c);self.assertEqual(r['removed_count'],2)
 def test_custom_rule_rejected_even_empty(self):
  c=scene();c['original_files']['board.kicad_dru']=b'';c['native_input_files']['board.kicad_dru']=b'';self.reject(c)
 def test_missing_project(self):
  c=scene();del c['original_files']['board.kicad_pro'];self.reject(c)
 def test_legacy_module_alias_rejected_even_without_zone(self):
  for node in (['module','"legacy"'],['module','"legacy"',recipe()[0]]):
   with self.subTest(node=node):
    c=scene();change_board(c,lambda b:b.append(copy.deepcopy(node)))
    with self.assertRaisesRegex(ValueError,'legacy module'):m.transform(**c)
 def test_legacy_module_alias_in_native_input_rejected(self):
  c=scene();change_board(c,lambda b:b.append(['module','"legacy"',recipe()[0]]),original=False)
  with self.assertRaisesRegex(ValueError,'legacy module'):m.transform(**c)
 def test_source_zone_census_rejects_legacy_alias_directly(self):
  for node in (['module','"legacy"'],['module','"legacy"',recipe()[0]]):
   with self.subTest(node=node):
    board=s.parse(scene()['original_files']['board.kicad_pcb'].decode());board.append(node)
    with self.assertRaisesRegex(ValueError,'legacy module'):m.source_zones(board)
 def test_footprint_zone(self):
  c=scene();change_board(c,lambda b:b.append(['footprint','"x"',recipe()[0]]));self.reject(c)
 def test_source_cutout_or_nonrectangular_or_footprint_edge(self):
  for mode in ('cutout','slant','footprint'):
   c=scene()
   def mutate(b):
    if mode=='cutout':b.append(['gr_circle',['center','50','50'],['end','55','50'],['layer','"Edge.Cuts"']])
    elif mode=='slant':s.one(s.children(b,'gr_line')[0],'end')[2]='1'
    else:b.append(['footprint','"f"',['fp_line',['layer','"Edge.Cuts"']]])
   change_board(c,mutate)
   with self.subTest(mode=mode):self.reject(c)
 def test_dsn_boundary_changed(self):
  c=scene();change_dsn(c,lambda t:s.one(s.one(t,'structure'),'boundary')[1].__setitem__(3,'1'));self.reject(c)
 def test_missing_or_duplicate_or_extra_dsn_keepout(self):
  for mode in ('missing','duplicate','extra'):
   c=scene()
   def mutate(t):
    st=s.one(t,'structure')
    if mode=='missing':st.pop()
    elif mode=='duplicate':st.append(copy.deepcopy(st[-1]))
    else:st.extend(recipe(2,50)[2])
   change_dsn(c,mutate)
   with self.subTest(mode=mode):self.reject(c)
 def test_overlapping_genuine_rulearea(self):self.reject(scene([recipe(),recipe(2,12,'tracks',False)]))
 def test_duplicate_polygon_zone_uuid(self):self.reject(scene([recipe(),recipe(2,10,'tracks',False)]))
 def test_dsn_shape_layer_y_width_or_window(self):
  for mode in ('layer','y','width','window'):
   c=scene()
   def mutate(t):
    k=s.children(s.one(t,'structure'),'keepout')[0]
    if mode=='layer':k[2][1]='In1.Cu'
    elif mode=='y':k[2][4]='10000'
    elif mode=='width':k[2][2]='1'
    else:k.append(['window',['polygon','F.Cu','0','1','1','2','1','2','2','1','1']])
   change_dsn(c,mutate)
   with self.subTest(mode=mode):self.reject(c)
 def test_native_geometry_hole_arc_or_position(self):
  for mode in ('hole','arc','point','open'):
   c=scene();row=c['observation']['zones'][0]
   if mode=='hole':row['holes']=[1]
   elif mode=='arc':row['arc_count']=1
   elif mode=='point':row['outlines_nm'][0][0][0]+=1
   else:row['outline_closed']=[False]
   with self.subTest(mode=mode):self.reject(c)
 def test_unknown_non_target_keepout_kind(self):
  c=scene();change_dsn(c,lambda t:s.children(s.one(t,'structure'),'keepout')[0].__setitem__(0,'place_keepout'));self.reject(c)
 def test_wrong_genuine_type_rejected(self):
  c=scene([recipe(),recipe(2,30,'vias',False)]);change_dsn(c,lambda t:s.children(s.one(t,'structure'),'via_keepout')[0].__setitem__(0,'keepout'));self.reject(c)
 def test_guidance_cannot_change_keepouts(self):
  c=scene();t=m._parse_dsn(c['guided_dsn'].decode());s.one(t,'structure').pop();c['guided_dsn']=m._dump_dsn(t).encode();self.reject(c)
 def test_translation_and_zone_order_no_name_heuristic(self):
  a=scene([recipe(8,40),recipe(2,60)]);b=scene([recipe(2,65),recipe(8,45)]);ra=m.transform(**a)[1];rb=m.transform(**b)[1];self.assertEqual({x['source_zone_uuid'] for x in ra['removed']},{x['source_zone_uuid'] for x in rb['removed']});self.assertEqual(ra['removed_count'],rb['removed_count'])
 def test_copper_zone_overlap_is_not_keepout_collision(self):
  c=scene();z,n,_=recipe(2,12);z[:]=[x for x in z if not isinstance(x,list) or x[0] not in {'keepout','placement'}];n['is_rule_area']=False;n['placement_enabled']=False
  change_board(c,lambda b:b.append(z));c['observation']['zones'].append(n);self.assertEqual(m.transform(**c)[1]['removed_count'],2)
 def test_duplicate_source_singleton(self):
  for key in ('uuid','layers','polygon','placement','keepout'):
   c=scene()
   def change(b):
    z=s.children(b,'zone')[0];z.append(copy.deepcopy(s.one(z,key)))
   change_board(c,change)
   with self.subTest(key=key):self.reject(c)
 def test_duplicate_native_identity_with_equal_population(self):
  c=scene([recipe(),recipe(2,30)]);c['observation']['zones'][1]['uuid']=c['observation']['zones'][0]['uuid'];self.reject(c)
 def test_extra_typed_structure_objects_reject(self):
  for kind in ('keepout','wire_keepout','via_keepout'):
   c=scene()
   def change(t):
    extra=recipe(2,50)[2][0];extra[0]=kind;s.one(t,'structure').append(extra)
   change_dsn(c,change)
   with self.subTest(kind=kind):self.reject(c)
 def test_submicrometre_nearmatch_rejected(self):
  c=scene();change_dsn(c,lambda t:s.children(s.one(t,'structure'),'keepout')[0][2].__setitem__(3,'10000.001'));self.reject(c)
 def test_alternative_polygon_winding_or_closure_rejected(self):
  for mode in ('reverse','unclosed','extra-close'):
   c=scene()
   def change(t):
    p=s.children(s.one(t,'structure'),'keepout')[0][2];pts=list(zip(p[3::2],p[4::2]))
    if mode=='reverse':pts=list(reversed(pts))
    elif mode=='unclosed':pts.pop()
    else:pts.append(pts[0])
    p[3:]=[v for pair in pts for v in pair]
   change_dsn(c,change)
   with self.subTest(mode=mode):self.reject(c)
 def test_image_keepout_rejected(self):
  c=scene();change_dsn(c,lambda t:s.one(t,'library').append(['image','"i"',['keepout','""',['circle','F.Cu','20']]]));self.reject(c)
 def test_case_insensitive_custom_rule_suffix(self):
  c=scene();c['original_files']['board.KICAD_DRU']=b'(version 1)';c['native_input_files']['board.KICAD_DRU']=b'(version 1)';self.reject(c)
 def test_casefold_and_unicode_normalization_inventory_collisions(self):
  for names in [('NOTICE.txt','notice.txt'),('caf\u00e9.txt','cafe\u0301.txt')]:
   with self.subTest(names=names):
    with self.assertRaises(ValueError):m.inventory({name:b'x' for name in names})
 def test_unquoted_edge_extra_and_footprint_rejected(self):
  for mode in ('extra','footprint'):
   c=scene()
   def change(b):
    edge=['gr_line',['start','20','20'],['end','30','20'],['layer','Edge.Cuts']]
    if mode=='extra':b.append(edge)
    else:b.append(['footprint','"f"',edge])
   change_board(c,change)
   with self.subTest(mode=mode):self.reject(c)
 def test_uniform_unquoted_edge_atoms_have_same_semantics(self):
  c=scene()
  def change(b):
   for line in s.children(b,'gr_line'):s.one(line,'layer')[1]='Edge.Cuts'
  change_board(c,change);self.assertEqual(m.transform(**c)[1]['removed_count'],2)
 def test_singular_zone_layer_multiple_atoms_rejected(self):
  c=scene();change_board(c,lambda b:s.one(s.children(b,'zone')[0],'layers').__setitem__(0,'layer'));self.reject(c)
 def test_non_simple_polygon(self):
  c=scene();change_board(c,lambda b:s.one(s.one(s.children(b,'zone')[0],'polygon'),'pts').__setitem__(3,['xy','10','10']));self.reject(c)

if __name__=='__main__':unittest.main()
