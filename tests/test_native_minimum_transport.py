"""Authored target/transport consistency controls. No Native execution or claim."""
import copy,json,shutil,tempfile,unittest
from pathlib import Path
from autorouter import board_floor as g,pipeline as p,adapter as a,native_edge as edge,sexpr as sx,floor_context as fc
ROOT=Path(__file__).resolve().parents[1]
FIX=ROOT/'tests/fixtures/board-floor'

class MinimumInputs(unittest.TestCase):
 def setUp(self):
  self.project=json.loads((FIX/'fixture.kicad_pro').read_text())
  self.project['net_settings']['classes'][0].update(track_width=.25,clearance=.2,via_diameter=.8,via_drill=.4)
  self.project['board']['design_settings']['rules'].update(min_track_width=.2,min_clearance=0,min_via_diameter=.4,min_through_hole_diameter=.3,min_via_annular_width=.05,min_copper_edge_clearance=0)
  self.task=g.task_from_source(sx.read(FIX/'fixture.kicad_pcb'))
  self.native=json.loads((FIX/'export-context.json').read_text())
  self.native['floors_nm']={k:g.millimetres(self.project['board']['design_settings']['rules'][k],zero=True) for k in g.FLOORS}
  for row in self.native['nets']:row.update(width_nm=250000,clearance_nm=200000,via_diameter_nm=800000,via_drill_nm=400000)
  tree=g._parse_dsn((FIX/'native.dsn').read_text());structure=sx.one(tree,'structure');library=sx.one(tree,'library')
  sx.one(structure,'rule')[1][1]='250';sx.one(sx.children(sx.one(tree,'network'),'class')[0],'rule')[1][1]='250'
  old='Via[0-1]_600:300_um';new='Via[0-1]_800:400_um'
  sx.one(structure,'via')[1]='"'+new+'"';sx.one(sx.one(sx.children(sx.one(tree,'network'),'class')[0],'circuit'),'use_via')[1]='"'+new+'"'
  stack=next(x for x in sx.children(library,'padstack') if sx.unquote(x[1])==old);stack[1]='"'+new+'"'
  for shape in sx.children(stack,'shape'):sx.one(shape,'circle')[2]='800'
  self.raw=g._dump_dsn(tree).encode();self.project_bytes=json.dumps(self.project).encode();self.task_bytes=(sx.dump(self.task)+'\n').encode()
  self.bind()
 def bind(self):
  self.native.update(dsn_sha256=g.sha(self.raw),project_sha256=g.sha(self.project_bytes),board_sha256=g.sha(self.task_bytes))
 def transform(self):return g.transform(self.raw,self.native,self.project_bytes,self.task_bytes,target_policy=g.MINIMUM_POLICY)
 def test_exact_minimum_edit_and_original_preference_tradeoff(self):
  original=copy.deepcopy((self.raw,self.native,self.project_bytes,self.task_bytes))
  encoded,record=self.transform();context=g.qualify(self.project,self.native,self.task,target_policy=g.MINIMUM_POLICY)
  tree=g._parse_dsn(encoded.decode());before=g._parse_dsn(self.raw.decode())
  self.assertEqual(context['derived_nm'],{'width_nm':200000,'clearance_nm':200000,'via_diameter_nm':400000,'via_drill_nm':300000})
  self.assertEqual(tree,g.expected_edit(before,context));self.assertTrue(g.verify_edit(before,tree,context)['passed'])
  self.assertEqual(sx.one(sx.one(tree,'structure'),'rule')[2:], [['clearance','200'],['clearance','200',['type','smd_smd']]])
  self.assertEqual(record['preference_tradeoff']['typed_smd_clearance_nm'],{'original':50000,'guided':200000})
  self.assertTrue(record['preference_tradeoff']['width_via_and_smd_clearance_change']);self.assertFalse(record['routing_accepted'])
  self.assertEqual(original,(self.raw,self.native,self.project_bytes,self.task_bytes))
 def test_default_policy_retains_old_targets_and_receipt_shape(self):
  default,record=g.transform(self.raw,self.native,self.project_bytes,self.task_bytes)
  explicit,explicit_record=g.transform(self.raw,self.native,self.project_bytes,self.task_bytes,target_policy=g.POLICY)
  self.assertEqual((default,record),(explicit,explicit_record));self.assertEqual(record['derived_nm'],record['raw_nm']);self.assertNotIn('preference_tradeoff',record)
 def test_hard_minima_missing_zero_nonfinite_negative_and_offgrid_refuse(self):
  raw={'width_nm':250000,'clearance_nm':200000,'via_diameter_nm':800000,'via_drill_nm':400000};floors=self.native['floors_nm']
  for key in g.FLOORS:
   if key=='min_clearance':continue
   for bad in (0,-1,True,float('nan'),floors[key]+1):
    changed=dict(floors);changed[key]=bad
    with self.subTest(key=key,bad=bad),self.assertRaises(ValueError):g.derive(raw,changed,target_policy=g.MINIMUM_POLICY)
   changed=dict(floors);del changed[key]
   with self.assertRaises(ValueError):g.derive(raw,changed,target_policy=g.MINIMUM_POLICY)
  with self.assertRaises(ValueError):g.derive(raw,{**floors,'min_clearance':200400},target_policy=g.MINIMUM_POLICY)
 def test_stale_input_and_duplicate_net_identity_refuse(self):
  for part in ('dsn','project','task','context'):
   with self.subTest(part=part),self.assertRaises(ValueError):
    g.transform(self.raw+(b' ' if part=='dsn' else b''),{**self.native,**({'project_sha256':'0'*64} if part=='context' else {})},self.project_bytes+(b' ' if part=='project' else b''),self.task_bytes+(b' ' if part=='task' else b''),target_policy=g.MINIMUM_POLICY)
  tree=copy.deepcopy(self.task);tree.extend([['net','1','"duplicate"'],['net','1','"duplicate"']]);self.task_bytes=(sx.dump(tree)+'\n').encode();self.bind()
  with self.assertRaises(ValueError):self.transform()
 def test_every_nonallowed_ast_change_and_via_collision_refuse(self):
  encoded,_=self.transform();context=g.qualify(self.project,self.native,self.task,target_policy=g.MINIMUM_POLICY);raw=g._parse_dsn(self.raw.decode())
  for part in ('boundary','plane','pin','padstack','placement','net'):
   changed=g._parse_dsn(encoded.decode())
   if part=='boundary':sx.one(sx.one(changed,'structure'),'boundary')[1][-1]='123'
   elif part=='plane':sx.one(changed,'structure').append(['plane','GND',['polygon','F.Cu','0','0','0','1','0','1','1']])
   elif part=='pin':sx.children(sx.children(sx.one(changed,'library'),'image')[0],'pin')[0][-1]='1'
   elif part=='padstack':sx.children(sx.children(sx.one(changed,'library'),'padstack')[0],'shape')[0][1][-1]='123'
   elif part=='placement':sx.children(sx.children(sx.one(changed,'placement'),'component')[0],'place')[0][2]='123'
   else:sx.children(sx.one(changed,'network'),'net')[0][1]='changed'
   with self.subTest(part=part),self.assertRaises(ValueError):g.verify_edit(raw,changed,context)
  raw=copy.deepcopy(raw);stack=copy.deepcopy(sx.children(sx.one(raw,'library'),'padstack')[-1]);stack[1]='"Via[0-1]_400:300_um"';sx.one(raw,'library').append(stack)
  with self.assertRaises(ValueError):g.expected_edit(raw,context)
 def test_ordinary_scope_and_generated_dimensions(self):
  context=g.qualify(self.project,self.native,self.task,target_policy=g.MINIMUM_POLICY)
  declared=sx.children(self.task,'net');name=self.native['nets'][0]['name']
  net=next(n[1] for n in declared if sx.unquote(n[2])==name) if declared else '"'+name+'"'
  candidate=copy.deepcopy(self.task)+[['segment',['net',net],['width','.2']],['via',['net',net],['size','.4'],['drill','.3'],['layers','"F.Cu"','"B.Cu"']]]
  self.assertEqual(g.audit_generated_routes(candidate,context)['counts']['via'],1)
  for field,value in (('width','.1998'),('size','.3998'),('drill','.3002')):
   changed=copy.deepcopy(candidate);route=changed[-2] if field=='width' else changed[-1];sx.one(route,field)[1]=value
   with self.subTest(field=field),self.assertRaises(ValueError):g.audit_generated_routes(changed,context)
  changed=copy.deepcopy(self.project);changed['net_settings']['classes'][0]['tuning_profile']='explicit'
  with self.assertRaises(ValueError):g.qualify(changed,self.native,self.task,target_policy=g.MINIMUM_POLICY)
  changed=copy.deepcopy(self.task);sx.children(changed,'footprint')[0].append(['clearance','.1'])
  with self.assertRaises(ValueError):g.qualify(self.project,self.native,changed,target_policy=g.MINIMUM_POLICY)

class MinimumReader(MinimumInputs):
 def setUp(self):
  super().setUp();base=ROOT/'.runs';base.mkdir(exist_ok=True);tmp=tempfile.TemporaryDirectory(dir=base);self.addCleanup(tmp.cleanup);self.folder=Path(tmp.name)
  source=self.folder/'source';source.mkdir();self.source=source/'fixture.kicad_pcb';self.source.write_bytes((FIX/'fixture.kicad_pcb').read_bytes());self.source.with_suffix('.kicad_pro').write_bytes(self.project_bytes)
  self.snapshot=self.folder/'snapshot';shutil.copytree(source,self.snapshot);retained=self.folder/'retained';retained.mkdir();self.native_input=retained/self.source.name;self.native_input.write_bytes(self.task_bytes);self.native_input.with_suffix('.kicad_pro').write_bytes(self.project_bytes)
  self.native.update(source=str(self.native_input),input_hashes_before=p.tree_hash(retained),input_hashes_after=p.tree_hash(retained),mode='export',limits=fc.LIMITS)
  (self.folder/'native.dsn').write_bytes(self.raw);p.save_json(self.folder/'minimum-export-context.json',self.native)
  code=self.folder/'code';code.mkdir();implementation={}
  for path in (ROOT/'autorouter').glob('*.py'):shutil.copy2(path,code/path.name);implementation['autorouter/'+path.name]=p.sha(path)
  self.data={'source':str(self.source),'source_hashes':p.tree_hash(self.snapshot),'native_dsn_sha256':g.sha(self.raw),'native_minimum_export_context_sha256':p.sha(self.folder/'minimum-export-context.json'),'accepted':False,'production_support_qualified':False,'scope':'whole_board_unlocked_routing','adapter':'graphics','tools':{'implementation_sha256':implementation}}
  self.produce()
 def produce(self):
  guided,contract=p.native_minimum_contract(self.folder,self.data);(self.folder/'minimum-preferences.dsn').write_bytes(guided);p.save_json(self.folder/'minimum-preferences.json',contract)
  self.data['native_minimum_preferences']={'file':'minimum-preferences.json','sha256':p.sha(self.folder/'minimum-preferences.json'),'policy':g.MINIMUM_POLICY}
  adapted,record=a.adapt_bytes(guided,self.data['adapter'],[]);corrected,edge_record=edge.correct(adapted,p.native_edge_context(self.snapshot/self.source.name))
  (self.folder/'edge-adapter-input.dsn').write_bytes(adapted);(self.folder/'task.dsn').write_bytes(corrected);p.save_json(self.folder/'obstacles.json',[]);p.save_json(self.folder/'native-edge-correction.json',edge_record)
  self.data.update(adapter_transformations=record,native_edge_correction=edge_record)
 def check(self):return p.check_native_minimum_transport(self.folder,self.data)
 def test_independent_exact_chain_for_both_adapters(self):
  self.assertIsInstance(self.check(),dict);self.data['adapter']='both';self.produce();self.assertIsInstance(self.check(),dict)
 def test_missing_single_evidence_members_refuse(self):
  for name in ('minimum-preferences.dsn','minimum-preferences.json','minimum-export-context.json','native-edge-correction.json','edge-adapter-input.dsn'):
   path=self.folder/name;raw=path.read_bytes();path.unlink()
   with self.subTest(name=name),self.assertRaises((p.Rejected,ValueError,FileNotFoundError)):self.check()
   path.write_bytes(raw)
 def test_total_proof_deletion_and_forged_unmodified_chain_refuse(self):
  for name in ('minimum-preferences.dsn','minimum-preferences.json','minimum-export-context.json'):(self.folder/name).unlink()
  self.data.pop('native_minimum_preferences');self.data.pop('native_minimum_export_context_sha256')
  adapted,record=a.adapt_bytes(self.raw,self.data['adapter'],[]);corrected,e=edge.correct(adapted,p.native_edge_context(self.snapshot/self.source.name))
  (self.folder/'edge-adapter-input.dsn').write_bytes(adapted);(self.folder/'task.dsn').write_bytes(corrected);p.save_json(self.folder/'native-edge-correction.json',e);self.data.update(adapter_transformations=record,native_edge_correction=e)
  self.assertIsInstance(p.check_native_edge_transport(self.folder,self.data),dict)
  with self.assertRaisesRegex(p.Rejected,'mandatory'):self.check()
 def test_rehashed_guidance_task_context_and_native_dsn_mutations_refuse(self):
  for name in ('minimum-preferences.dsn','task.dsn','native.dsn','minimum-export-context.json'):
   path=self.folder/name;raw=path.read_bytes();old=copy.deepcopy(self.data)
   if name.endswith('.json'):
    d=json.loads(raw);d['floors_nm']['min_track_width']=250000;p.save_json(path,d);self.data['native_minimum_export_context_sha256']=p.sha(path)
   else:path.write_bytes(raw.replace(b'(width 200)',b'(width 100)',1) if name!='native.dsn' else raw+b'\n')
   if name=='native.dsn':self.data['native_dsn_sha256']=p.sha(path)
   with self.subTest(name=name),self.assertRaises((p.Rejected,ValueError)):self.check()
   path.write_bytes(raw);self.data=old
 def test_code_scope_and_pour_relabel_refuse(self):
  path=self.folder/'code/board_floor.py';raw=path.read_bytes();path.write_bytes(raw+b'\n');self.data['tools']['implementation_sha256']['autorouter/board_floor.py']=p.sha(path)
  with self.assertRaises(p.Rejected):self.check()
  path.write_bytes(raw);self.data['tools']['implementation_sha256']['autorouter/board_floor.py']=p.sha(path)
  for key,value in (('scope','partial_completion'),('adapter','none'),('pour_dsn_correction',{}),('protected_routes',1),('accepted',True)):
   old=copy.deepcopy(self.data);self.data[key]=value
   with self.subTest(key=key),self.assertRaises(p.Rejected):self.check()
   self.data=old
 def test_rehashed_padstack_and_proof_still_refuse(self):
  guided=self.folder/'minimum-preferences.dsn';proof=self.folder/'minimum-preferences.json';raw=guided.read_bytes();before=proof.read_bytes();old=copy.deepcopy(self.data)
  self.assertIn(b'(circle F.Cu 400)',raw);changed=raw.replace(b'(circle F.Cu 400)',b'(circle F.Cu 600)',1);guided.write_bytes(changed)
  data=json.loads(before);data['transformation']['output_sha256']=g.sha(changed);p.save_json(proof,data);self.data['native_minimum_preferences']['sha256']=p.sha(proof)
  with self.assertRaises(p.Rejected):self.check()
  guided.write_bytes(raw);proof.write_bytes(before);self.data=old
  task=self.folder/'task.dsn';raw=task.read_bytes();self.assertIn(b'(rect F.Cu -1000 -1000 1000 1000)',raw);task.write_bytes(raw.replace(b'(rect F.Cu -1000 -1000 1000 1000)',b'(rect F.Cu -900 -1000 1000 1000)',1))
  with self.assertRaises(p.Rejected):self.check()
 def test_locked_snapshot_and_custom_rule_companion_refuse(self):
  path=self.snapshot/self.source.name;raw=path.read_bytes();tree=sx.parse(raw.decode());tree.append(['segment','locked']);sx.write(path,tree);self.data['source_hashes']=p.tree_hash(self.snapshot)
  with self.assertRaises(ValueError):self.check()
  path.write_bytes(raw);rule=path.with_suffix('.kicad_dru');rule.write_text('(version 1)');self.data['source_hashes']=p.tree_hash(self.snapshot)
  with self.assertRaises(p.Rejected):self.check()
 def test_export_source_outside_retained_runs_refuses(self):
  cache=ROOT/'.cache';cache.mkdir(exist_ok=True);tmp=tempfile.TemporaryDirectory(dir=cache);self.addCleanup(tmp.cleanup);other=Path(tmp.name)
  for path in self.native_input.parent.iterdir():shutil.copy2(path,other/path.name)
  context_path=self.folder/'minimum-export-context.json';context=json.loads(context_path.read_text());context['source']=str(other/self.native_input.name);p.save_json(context_path,context);self.data['native_minimum_export_context_sha256']=p.sha(context_path)
  with self.assertRaisesRegex(p.Rejected,'retained run copy'):self.check()
 def test_export_input_source_and_normal_receipt_boundary(self):
  path=self.native_input.with_suffix('.kicad_pro');raw=path.read_bytes();path.write_bytes(raw+b'\n')
  with self.assertRaises(p.Rejected):self.check()
  path.write_bytes(raw);self.data['accepted']=True;p.save_json(self.folder/'result.json',self.data)
  with self.assertRaisesRegex(p.Rejected,'not a normal routing receipt'):p.check_result(self.folder/'result.json')

if __name__=='__main__':unittest.main(verbosity=2)
