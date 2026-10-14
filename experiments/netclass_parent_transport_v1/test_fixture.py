"""Recipe consistency only; native transport and routing remain unexecuted."""
import copy,json,math,unittest
from unittest.mock import patch
from autorouter import sexpr as sx,pipeline as p
from experiments.netclass_parent_transport_v1 import fixture as f

class FixtureRecipe(unittest.TestCase):
 def test_deterministic_exact_seed_capture_notices_and_stale_seed_rejection(self):
  seed={n:(f.ROOT/f.SEED/n).read_bytes() for n in f.PINS}
  files,recipe=f.prepare();self.assertEqual((files,recipe),f.prepare())
  self.assertEqual(set(files),set(f.PINS));self.assertEqual(recipe['schematic'],{'available':False,'path':None,'parity_unavailable':True});self.assertFalse(recipe['native_accepted'])
  for name in ['PROVENANCE.md','_licenses/LICENSE.README','_licenses/LICENSE.CC-BY-SA-4.0']:self.assertEqual(files[name],seed[name])
  self.assertEqual(seed,{n:(f.ROOT/f.SEED/n).read_bytes() for n in f.PINS})
  real=f.io.bounded
  def changed(path,cap):
   raw=real(path,cap)
   return b'X'+raw[1:] if path.name=='fixture.kicad_pcb' else raw
  with patch.object(f.io,'bounded',side_effect=changed),self.assertRaisesRegex(ValueError,'stale board-floor seed'):f.prepare()
  with self.assertRaises(ValueError):f.prepare(protected=1)
 def test_class_dimensions_priorities_partial_merge_and_all_original_rules_preserved(self):
  source=json.loads((f.ROOT/f.SEED/'fixture.kicad_pro').read_text());files,recipe=f.prepare();project=json.loads(files['fixture.kicad_pro'])
  unchanged=copy.deepcopy(project);unchanged['net_settings']=source['net_settings'];self.assertEqual(unchanged,source)
  self.assertEqual(project['board']['design_settings']['rules'],recipe['source_floors']);self.assertEqual(source['board']['design_settings']['rules'],recipe['source_floors'])
  floors=recipe['source_floors'];self.assertEqual([floors[k] for k in ['min_track_width','min_clearance','min_via_diameter','min_through_hole_diameter','min_via_annular_width']],[.3,.3,1.5,.3,.3])
  classes={c['name']:c for c in project['net_settings']['classes']}
  for name,width,priority in [('Default',.4,2147483647),('POWER',.6,1),('SIGNAL',.5,0)]:
   c=classes[name];self.assertEqual([c[k] for k in ['track_width','clearance','via_diameter','via_drill','priority']],[width,.35,1.5,.6,priority]);self.assertGreaterEqual((c['via_diameter']-c['via_drill'])/2,floors['min_via_annular_width'])
  for name in ['POWER','SIGNAL']:self.assertNotIn('diff_pair_width',classes[name]);self.assertNotIn('microvia_drill',classes[name])
  self.assertEqual(project['net_settings']['netclass_patterns'],[{'netclass':'POWER','pattern':'/PWR_*'},{'netclass':'SIGNAL','pattern':'/SIG_*'}]);self.assertIsNone(project['net_settings']['netclass_assignments'])
 def test_three_isolated_ordinary_pairs_power_requires_layer_transition_no_extra_features(self):
  files,_=f.prepare();tree=sx.parse(files['fixture.kicad_pcb'].decode());self.assertEqual(p.routes(tree),[]);self.assertEqual(sx.children(tree,'zone'),[])
  fps=sx.children(tree,'footprint');self.assertEqual(len(fps),6);pairs={};uuids=[]
  def census(node):
   if isinstance(node,list):
    if node and node[0]=='uuid':uuids.append(sx.unquote(node[1]))
    for child in node:census(child)
  census(tree);self.assertEqual(len(uuids),len(set(uuids)))
  for fp in fps:
   pads=sx.children(fp,'pad');self.assertEqual(len(pads),1);pad=pads[0];self.assertEqual(pad[2:4],['smd','rect']);self.assertEqual(sx.one(pad,'size'),['size','2','2']);self.assertEqual(sx.one(pad,'at'),['at','0','0']);self.assertIsNone(sx.one(pad,'primitives'))
   net=sx.unquote(sx.one(pad,'net')[1]);pairs.setdefault(net,[]).append(sx.unquote(sx.one(fp,'layer')[1]))
  self.assertEqual(pairs,{'/PWR_PAIR':['F.Cu','B.Cu'],'/SIG_PAIR':['F.Cu','F.Cu'],'/DEFAULT_PAIR':['F.Cu','F.Cu']})
  seed=sx.read(f.ROOT/f.SEED/'fixture.kicad_pcb');self.assertEqual(sx.children(tree,'gr_line'),sx.children(seed,'gr_line'));self.assertEqual(sx.one(tree,'setup'),sx.one(seed,'setup'));self.assertEqual(sx.one(tree,'layers'),sx.one(seed,'layers'))
 def test_protected_variant_exact_original_locked_stub_and_same_immutable_geometry(self):
  basic,basic_recipe=f.prepare();files,recipe=f.prepare(protected=True);a=sx.parse(basic['fixture.kicad_pcb'].decode());b=sx.parse(files['fixture.kicad_pcb'].decode())
  self.assertEqual(p.immutable(a),p.immutable(b));self.assertEqual(basic['fixture.kicad_pro'],files['fixture.kicad_pro']);self.assertEqual(basic_recipe['immutable_geometry_sha256'],recipe['immutable_geometry_sha256'])
  self.assertIsNone(basic_recipe['protected_route']);self.assertEqual(len(p.routes(b)),1);route=p.routes(b)[0];self.assertTrue(p.locked(route));self.assertEqual(route[0],'segment')
  self.assertEqual(sx.one(route,'width'),['width','0.6']);self.assertEqual(sx.one(route,'layer'),['layer','"F.Cu"']);self.assertEqual(sx.one(route,'net'),['net','"/PWR_PAIR"']);self.assertEqual(sx.unquote(sx.one(route,'uuid')[1]),recipe['protected_route']['uuid'])
  axy=list(map(float,sx.one(route,'start')[1:]));bxy=list(map(float,sx.one(route,'end')[1:]));self.assertEqual(math.hypot(bxy[0]-axy[0],bxy[1]-axy[1]),5);self.assertEqual(axy,[10,10]);self.assertEqual(bxy,[15,10])
  seed=sx.read(f.ROOT/f.SEED/'fixture.kicad_pcb');project=json.loads((f.ROOT/f.SEED/'fixture.kicad_pro').read_text());before=copy.deepcopy((seed,project));f.fixture(seed,project,protected=True);self.assertEqual((seed,project),before)
if __name__=='__main__':unittest.main()
