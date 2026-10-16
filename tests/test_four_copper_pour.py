"""Four-layer pour source, transport and reader regressions. Native evidence is separate."""
import copy,json,sys,tempfile,types,unittest
from pathlib import Path
from unittest import mock
from autorouter import pour_rule_area as m,pour_rule_area_native as worker,sexpr as sx,floor_context as fc,pipeline as p
from experiments.four_copper_class_transport_v1 import fixture
from test_pour_rule_area import zone,entry,dsn,raw
NAMES=('F.Cu','In1.Cu','In2.Cu','B.Cu')
IDS=(0,4,6,2)

def source():
    tree=sx.parse(fixture.files()[fixture.STEM+'.kicad_pcb'].decode())
    area=zone(layers=('In2.Cu',));area.remove(sx.one(area,'net'));area.remove(sx.one(area,'net_name'))
    area.append(['fill',['island_removal_mode','0']]);tree.append(area)
    tree.append(['zone',['net','"GND"'],['uuid','"00000000-0000-0000-0000-000000000099"'],
                 ['layers',*[json.dumps(n) for n in NAMES]]])
    return tree

def native_record(path,tree,version='10.0.0'):
    areas=m.qualify(tree)
    return dict(schema=2,policy=m.FOUR_AUDIT_POLICY,native_version=version,source=str(path),
      board_sha256=m.sha(path.read_bytes()),project_sha256=m.sha(path.with_suffix('.kicad_pro').read_bytes()),
      board_saved=False,source_areas=areas,passed=True,
      native_areas=[{k:v for k,v in a.items() if k!='source_zone_ast_sha256'} for a in areas],
      native_zone_uuids=sorted(m._atom(z,'uuid') for z in sx.children(tree,'zone')),
      copper_layers=[dict(id=code,name=name,type='signal',index=i) for i,(code,name) in enumerate(zip(IDS,NAMES))],
      native_area_nets=[dict(uuid=a['uuid'],netcode=0,netname='',island_removal_mode=0) for a in areas],
      fill_checks=[dict(row,native_fill_outline_count=0,intersection=[],passed=True) for row in m.fill_matrix(tree,areas)])

class InnerPure(unittest.TestCase):
 def test_inner_source_and_complete_four_layer_matrix_are_immutable(self):
  tree=source();before=copy.deepcopy(tree);areas=m.qualify(tree);matrix=m.fill_matrix(tree,areas)
  self.assertEqual([r['layer'] for r in matrix],list(NAMES));self.assertEqual([r['applicable'] for r in matrix],[False,False,True,False])
  self.assertEqual(areas[0]['layers'],['In2.Cu']);self.assertEqual(tree,before)
 def test_exact_inner_dsn_removal_keeps_other_layer_obstacle(self):
  tree=source();area=sx.children(tree,'zone')[0];d=dsn([]);st=sx.one(d,'structure')
  st[1:3]=[['layer',name,['type','signal'],['property',['index',str(i)]]] for i,name in enumerate(NAMES)]
  removed=entry(area,'In2.Cu');retained=entry(area,'In1.Cu');st.extend([removed,retained]);before=copy.deepcopy((tree,d))
  out,receipt=m.correct(raw(tree),m._dump_dsn(d).encode());wanted=copy.deepcopy(d);sx.one(wanted,'structure').remove(removed)
  self.assertEqual(m._parse_dsn(out.decode()),wanted);self.assertEqual(receipt['removed_count'],1);self.assertEqual((tree,d),before)
 def test_only_observed_omitted_net_explicit_mode_zero_source_form(self):
  for change in ('numeric_zero','positive_net','named_net','missing_mode','mode1','mode2','mode00','mode_float','duplicate','unknown'):
   tree=source();a=sx.children(tree,'zone')[0];fill=sx.one(a,'fill')
   if change=='numeric_zero':a.append(['net','0'])
   elif change=='positive_net':a.append(['net','1'])
   elif change=='named_net':a.append(['net','"GND"'])
   elif change=='missing_mode':fill.remove(sx.one(fill,'island_removal_mode'))
   elif change.startswith('mode'):sx.one(fill,'island_removal_mode')[1]={'mode1':'1','mode2':'2','mode00':'00','mode_float':'0.0'}[change]
   elif change=='duplicate':fill.append(['island_removal_mode','0'])
   else:fill.append(['future_fill','0'])
   with self.subTest(change=change),self.assertRaises(ValueError):m.qualify(tree)
 def test_unchanged_decoder_rejects_numeric_zero_on_area_and_pad(self):
  from autorouter import board_floor
  tree=source();before=copy.deepcopy(tree)
  names,_=board_floor.source_net_identity(tree);self.assertIn('GND',names);self.assertEqual(tree,before)
  for owner in ('area','pad'):
   bad=copy.deepcopy(tree)
   target=sx.children(bad,'zone')[0] if owner=='area' else sx.children(sx.children(bad,'footprint')[0],'pad')[0]
   prior=sx.one(target,'net')
   if prior is not None:target.remove(prior)
   target.append(['net','0'])
   with self.subTest(owner=owner),self.assertRaises(ValueError):board_floor.source_net_identity(bad)
 def test_two_layer_omitted_net_or_island_mode_still_refuse(self):
  from test_pour_rule_area import board
  for change in ('omitted','island'):
   tree=board();a=sx.children(tree,'zone')[0]
   if change=='omitted':a.remove(sx.one(a,'net'))
   else:a.append(['fill',['island_removal_mode','0']])
   with self.subTest(change=change),self.assertRaises(ValueError):m.qualify(tree)
 def test_source_context_does_not_enable_four_layer_placement_by_default(self):
  area=sx.children(source(),'zone')[0]
  with self.assertRaises(ValueError):m.pt.source_zones(['kicad_pcb',area])
  for context in (('F.Cu','In2.Cu','In1.Cu','B.Cu'),('F.Cu','In1.Cu','In2.Cu','B.Cu','In3.Cu')):
   with self.subTest(context=context),self.assertRaises(ValueError):m.pt.source_zones(['kicad_pcb',area],copper_layers=context)
 def test_swapped_physical_ids_undeclared_area_and_foreign_saved_fill_refuse(self):
  for change in ('ids','area','fill'):
   tree=source()
   if change=='ids':sx.one(tree,'layers')[2][0]='6'
   elif change=='area':sx.one(sx.children(tree,'zone')[0],'layers')[1]='"In3.Cu"'
   else:sx.children(tree,'zone')[1].append(['filled_polygon',['layer','"In3.Cu"'],['pts']])
   with self.subTest(change=change),self.assertRaises(ValueError):m.fill_matrix(tree,m.qualify(tree))
 def test_saved_matrix_rejects_intrusion_downgrade_or_missing_row(self):
  with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as temp:
   path=Path(temp)/'owned.kicad_pcb';tree=source();sx.write(path,tree);path.with_suffix('.kicad_pro').write_text('{}')
   good=native_record(path,tree);self.assertTrue(m.verify_native_record(good,path))
   # Same XY overlap on an inapplicable layer is retained, not a false rejection.
   good['fill_checks'][1]['intersection']=[{'observed':True}];self.assertTrue(m.verify_native_record(good,path))
   for change in ('intrusion','missing','swap','policy','net','bool_net','island','bool_island','layer','extra'):
    bad=copy.deepcopy(good)
    if change=='intrusion':bad['fill_checks'][2]['intersection']=[{'observed':True}]
    elif change=='missing':bad['fill_checks'].pop()
    elif change=='swap':bad['fill_checks'][1],bad['fill_checks'][2]=bad['fill_checks'][2],bad['fill_checks'][1]
    elif change=='policy':bad['schema']=1;bad['policy']=m.AUDIT_POLICY
    elif change=='net':bad['native_area_nets'][0]['netcode']=1
    elif change=='bool_net':bad['native_area_nets'][0]['netcode']=False
    elif change=='island':bad['native_area_nets'][0]['island_removal_mode']=1
    elif change=='bool_island':bad['native_area_nets'][0]['island_removal_mode']=False
    elif change=='layer':bad['copper_layers'][1]['id']=6
    else:bad['extra']=True
    with self.subTest(change=change),self.assertRaises(ValueError):m.verify_native_record(bad,path)
 def test_only_actual_qualified_native_version_1000_is_readable(self):
  with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as temp:
   path=Path(temp)/'owned.kicad_pcb';tree=source();sx.write(path,tree);path.with_suffix('.kicad_pro').write_text('{}')
   self.assertTrue(m.verify_native_record(native_record(path,tree),path))
   for version in ('10.0.7','10.0.8',None):
    with self.subTest(version=version),self.assertRaises(ValueError):m.verify_native_record(native_record(path,tree,version),path)
   with self.assertRaises(TypeError):m.verify_native_record(native_record(path,tree),path,native_version='10.0.7')

class NativeAlgorithmDoubles(unittest.TestCase):
 """Run actual worker logic with scalar/polygon doubles, never pcbnew."""
 def exercise(self,*,bad_net=False,bad_layer=False,intrusion=False,bad_mode=False,version="10.0.0"):
  tree=source();area=m.qualify(tree)[0];aid=area['uuid'];zid=m._atom(sx.children(tree,'zone')[1],'uuid')
  path=Path('/owned/four.kicad_pcb');captured=raw(tree);project=b'{}';calls=[]
  class Poly:
   def __init__(self,arg=None):self.layer=arg;self.hit=False
   def OutlineCount(self):return 1 if self.hit else 0
   def BooleanIntersection(self,other):self.hit=intrusion and self.layer==6
   def COutline(self,i):return types.SimpleNamespace(PointCount=lambda:3,IsClosed=lambda:True,CPoint=lambda j:types.SimpleNamespace(x=j,y=j))
   def HoleCount(self,i):return 0
  class Zone:
   def __init__(self,uid):self.m_Uuid=types.SimpleNamespace(AsString=lambda:uid);self.id=uid
   def IsOnLayer(self,l):return l==6 if self.id==aid else l in IDS
   def GetFilledPolysList(self,l):calls.append(l);return l
   def Outline(self):return Poly()
   def GetNetCode(self):return 1 if bad_net else 0
   def GetNetname(self):return ''
   def GetIslandRemovalMode(self):return 1 if bad_mode else 0
  board=types.SimpleNamespace(GetCopperLayerCount=lambda:4,GetLayerID=lambda name:dict(zip(NAMES,IDS))[name],
    GetLayerName=lambda code:('wrong' if bad_layer else dict(zip(IDS,NAMES))[code]),
    IsLayerEnabled=lambda code:True,GetLayerType=lambda code:0,Zones=lambda:[Zone(aid),Zone(zid)])
  shim=types.SimpleNamespace(F_Cu=0,In1_Cu=4,In2_Cu=6,B_Cu=2,LT_SIGNAL=0,SHAPE_POLY_SET=Poly,
    LayerName=lambda code:dict(zip(IDS,NAMES))[code],GetBuildVersion=lambda:version,ISLAND_REMOVAL_MODE_ALWAYS=0)
  observed={k:v for k,v in area.items() if k!='source_zone_ast_sha256'}
  def observe(*args,**kwargs):
   self.assertEqual(kwargs,{'copper_layers':NAMES});return {'footprint_zone_count':0,'zones':[copy.deepcopy(observed)]}
  with mock.patch.dict(sys.modules,{'pcbnew':shim}),mock.patch.object(Path,'read_bytes',lambda self:captured if self==path else project),mock.patch.object(fc,'observe_areas',observe):
   result=worker.audit(board,path,(m.sha(captured),m.sha(project)))
  self.assertEqual(calls,list(IDS));return result
 def test_complete_enum_matrix_and_net_zero_positive(self):
  result=self.exercise();self.assertTrue(result['passed']);self.assertEqual(len(result['fill_checks']),4)
  self.assertEqual(result['native_area_nets'][0]['netcode'],0)
 def test_actual_worker_logic_rejects_foreign_layer_or_positive_net(self):
  for kwargs in ({'bad_layer':True},{'bad_net':True},{'bad_mode':True},{'version':'10.0.7'}):
   with self.subTest(kwargs=kwargs),self.assertRaises(ValueError):self.exercise(**kwargs)
 def test_saved_inner_intrusion_fails_even_without_drc(self):
  result=self.exercise(intrusion=True);self.assertFalse(result['passed']);self.assertFalse(result['fill_checks'][2]['passed'])
