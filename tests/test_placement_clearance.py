"""Pure fixed-policy controls using retained native exports; no new native run."""
import copy,json,shutil,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from autorouter import placement_clearance as pc,placement_transform as pt,board_floor as g,sexpr as sx,pipeline as p,floor_route as f
ROOT=next(x for x in Path(__file__).resolve().parents if (x/'MASTER_PROMPT.md').is_file())
FIX=ROOT/'evidence/placement-routing-fixture-002'

class ActualExport(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent);self.addCleanup(self.tmp.cleanup);self.out=Path(self.tmp.name)
  for name in ('snapshot','floor-export-input'):shutil.copytree(FIX/name,self.out/name)
  for name in ('native.dsn','floor-export-context.json'):shutil.copy2(FIX/name,self.out/name)
  shutil.copy2(FIX/'area-context.json',self.out/'placement-area-context.json')
  self.name='fixture.kicad_pcb';self.hashes=p.tree_hash(self.out/'snapshot');board=self.out/'floor-export-input'/self.name
  for name in ('floor-export-context.json','placement-area-context.json'):
   value=f.read_json(self.out/name);value['source']=str(board);p.save_json(self.out/name,value)
  self.task=sx.read(board);native=f.read_json(self.out/'floor-export-context.json');raw=(self.out/'native.dsn').read_bytes();project=(self.out/'snapshot/fixture.kicad_pro').read_bytes()
  guided,contract=f.policy_contract(raw,native,project,self.task,self.hashes)
  (self.out/'floor-guided.dsn').write_bytes(guided);p.save_json(self.out/'floor-policy.json',contract)
  self.context=g.qualify(json.loads(project),native,self.task)
  self.outputs,self.composition=pc.derive_chain(self.out,self.name,self.hashes)
  for name,raw in self.outputs.items():(self.out/name).write_bytes(raw)
  p.save_json(self.out/'placement-policy.json',self.composition)
  self.data={'source':str(self.out/'snapshot'/self.name),'source_hashes':self.hashes,'planning_parameters':pc.parameters(),'placement_policy':{'file':'placement-policy.json','sha256':p.sha(self.out/'placement-policy.json')}}
 def check(self):return pc.check_chain(self.out,self.data)
 def test_actual_export_full_chain_original_floor_unchanged(self):
  self.check();self.assertEqual(self.composition['removal']['removed_count'],2)
  self.assertEqual(self.composition['planning']['original_derived_nm'],self.context['derived_nm'])
  self.assertEqual(self.composition['planning']['planning_clearance_nm'],320000)
  self.assertEqual(f.read_json(self.out/'floor-policy.json')['transformation']['derived_nm']['clearance_nm'],300000)
 def test_fixed_policy_matches_measured_v2_bytes(self):
  # Fixed new planning AST must match the retained actual 20µm diagnostic output.
  import importlib.util
  path=ROOT/'experiments/placement_diagnostic_v2/search_guidance.py'
  spec=importlib.util.spec_from_file_location('frozen_search',path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
  expected,_=module.transform(self.outputs['placement-guided.dsn'],self.context,'placement-search-v2-margin20um-default')
  self.assertEqual(self.outputs['planning-guided.dsn'],expected)
 def test_exactly_three_atoms_and_original_context_immutable(self):
  raw=self.outputs['placement-guided.dsn'];original=g._parse_dsn(raw.decode());before=copy.deepcopy(self.context)
  planned=g._parse_dsn(self.outputs['planning-guided.dsn'].decode());changes=[]
  def compare(a,b):
   if isinstance(a,list):
    self.assertIsInstance(b,list);self.assertEqual(len(a),len(b))
    for x,y in zip(a,b):compare(x,y)
   elif a!=b:changes.append((a,b))
  compare(original,planned);self.assertEqual(changes,[('300','320')]*3);self.assertEqual(self.context,before)
 def test_width_via_net_and_smd_changes_fail_despite_output_rehash(self):
  for kind in ('width','via','net','smd'):
   tree=g._parse_dsn(self.outputs['planning-guided.dsn'].decode());structure=sx.one(tree,'structure')
   if kind=='width':sx.one(structure,'rule')[1][1]='301'
   elif kind=='via':sx.one(structure,'via')[1]='"OTHER"'
   elif kind=='net':sx.children(sx.one(tree,'network'),'net')[0][1]='"OTHER"'
   else:pc.clearance_nodes(tree)[1][1]='321'
   original=g._parse_dsn(self.outputs['placement-guided.dsn'].decode())
   with self.subTest(kind=kind),self.assertRaisesRegex(ValueError,'nondeclared'):pc.verify_edit(original,tree,self.context)
 def test_rehashed_outer_chain_cannot_hide_planned_width_tamper(self):
  path=self.out/'planning-guided.dsn';path.write_bytes(path.read_bytes().replace(b'(width 300)',b'(width 301)'))
  receipt=f.read_json(self.out/'placement-policy.json');receipt['outputs_sha256'][path.name]=p.sha(path);receipt['planning']['output_sha256']=p.sha(path)
  p.save_json(self.out/'placement-policy.json',receipt);self.data['placement_policy']['sha256']=p.sha(self.out/'placement-policy.json')
  with self.assertRaisesRegex(p.Rejected,'bytes differ'):self.check()
 def test_rehashed_native_preferences_and_observer_flags_fail(self):
  for name,mutate in [('floor-export-context.json',lambda x:x['nets'][0].update(width_nm=300000)),('placement-area-context.json',lambda x:x['zones'][0]['disallow'].update(tracks=True))]:
   path=self.out/name;raw=path.read_bytes();value=f.read_json(path);mutate(value);p.save_json(path,value)
   with self.subTest(name=name),self.assertRaises((p.Rejected,ValueError)):pc.derive_chain(self.out,self.name,self.hashes)
   path.write_bytes(raw)
 def test_each_chain_stage_cannot_be_swapped(self):
  for name in ('floor-guided.dsn','placement-guided.dsn','planning-guided.dsn','task.dsn'):
   path=self.out/name;raw=path.read_bytes();path.write_bytes((self.out/'native.dsn').read_bytes())
   with self.subTest(name=name),self.assertRaises((p.Rejected,ValueError)):self.check()
   path.write_bytes(raw)
 def test_changed_rule_severity_source_and_task_fail(self):
  for sub in ('snapshot','floor-export-input'):
   path=self.out/sub/'fixture.kicad_pro';raw=path.read_bytes();value=json.loads(raw);value['board']['design_settings']['rule_severities']['clearance']='ignore';path.write_text(json.dumps(value))
   with self.subTest(sub=sub),self.assertRaises((p.Rejected,ValueError)):self.check()
   path.write_bytes(raw)
 def test_every_genuine_flag_disabled_no_area_legacy_refused(self):
  source=sx.read(self.out/'snapshot'/self.name)
  for flag in pt.FLAGS:
   tree=copy.deepcopy(source);sx.one(sx.one(sx.children(tree,'zone')[0],'keepout'),flag)[1]='not_allowed'
   with self.subTest(flag=flag),self.assertRaises((p.Rejected,ValueError)):pc.narrow_source(tree)
  tree=copy.deepcopy(source);sx.one(sx.one(sx.children(tree,'zone')[0],'placement'),'enabled')[1]='no'
  with self.assertRaises((p.Rejected,ValueError)):pc.narrow_source(tree)
  tree=copy.deepcopy(source);tree.append(['module','"old"'])
  with self.assertRaises((p.Rejected,ValueError)):pc.narrow_source(tree)
 def test_policy_dispatch_rejects_profile_partial_adapter_or_override_before_work(self):
  base=dict(source='missing',output='missing',seconds=60,keep_existing=False,adapter='both',engine_profile='completion-only',guidance_policy=pc.POLICY)
  for updates in ({'keep_existing':True},{'adapter':'none'},{'engine_profile':'standard'},{'engine_profile':'tuned'},{'scoring_variant':'via_default'},{'scoring_variant':'via_low'}):
   with self.subTest(updates=updates),patch.object(f,'_route') as worker,self.assertRaises(p.Rejected):p.route(**{**base,**updates})
   worker.assert_not_called()
 def test_export_argv_old_unchanged_new_only_one_extra_arg(self):
  board=self.out/'floor-export-input'/self.name
  old=f.context_argv('export',board,self.out/'floor-export-context.json',self.out/'native.dsn')
  new=f.context_argv('export',board,self.out/'floor-export-context.json',self.out/'native.dsn',self.out/'placement-area-context.json')
  self.assertEqual(new,old+[str(self.out/'placement-area-context.json')])
  with self.assertRaises(p.Rejected):f.context_argv('final',board,self.out/'floor.json',area_output=self.out/'area.json')
 def test_native_dsn_descriptor_cap_precedes_floor_policy_parse(self):
  import os
  real=os.fstat;target=(self.out/'native.dsn').stat().st_ino
  def oversize(fd):
   value=real(fd)
   if value.st_ino==target:
    fields=list(value);fields[6]=20*1024*1024+1;return os.stat_result(fields)
   return value
  with patch.object(pc.os,'fstat',oversize),patch.object(f,'policy_contract') as contract,self.assertRaisesRegex(p.Rejected,'bounded regular'):
   pc.derive_chain(self.out,self.name,self.hashes)
  contract.assert_not_called()
 def test_required_commit_gate_rejects_uncommitted_bytes(self):
  tools={'implementation_sha256':{'autorouter/placement_clearance.py':'0'*64},'git_head':'a'*40}
  with patch.object(pc.subprocess,'run',return_value=type('Result',(),{'stdout':b'uncommitted'})()),self.assertRaisesRegex(p.Rejected,'commit exact'):pc.capture_freeze(tools)

if __name__=='__main__':unittest.main()
