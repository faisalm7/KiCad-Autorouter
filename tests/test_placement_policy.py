"""Synthetic schema3 receipts backed by copied retained fixture bytes.

Rewrites process/settings declarations to test consistency, never a claim that
new production code ran KiCad. Original diagnostic evidence is untouched.
"""
import copy,json,shutil,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from autorouter import pipeline as p,sexpr as sx,board_floor as g,floor_route as f,placement_clearance as pc
ROOT=next(x for x in Path(__file__).resolve().parents if (x/'MASTER_PROMPT.md').is_file())
FIX=ROOT/'evidence/placement-search-fixture-001'

class Receipt(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent);self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.out=self.root/'run';self.out.mkdir()
  self.source=self.root/'source/fixture.kicad_pcb';shutil.copytree(FIX/'snapshot',self.source.parent)
  old=json.loads((FIX/'result.json').read_text());oldout=Path(old['candidate']).parent.parent;oldsource=old['source']
  for name in ('snapshot','candidate','floor-export-input','refill','source-drc-input','final-drc-input'):shutil.copytree(FIX/name,self.out/name)
  for path in FIX.iterdir():
   if path.is_file() and path.name not in {'result.json','SCOPE.md','files.json','route-meta.json','search-guidance.json','placement-transform.json'}:shutil.copy2(path,self.out/path.name)
  def relocate(value):
   if isinstance(value,str):return value.replace(str(oldout),str(self.out)).replace(oldsource,str(self.source)).replace(str(oldout.parents[1]/'autorouter'),str(p.c.ROOT/'autorouter'))
   if isinstance(value,list):return [relocate(x) for x in value]
   if isinstance(value,dict):return {relocate(k):relocate(v) for k,v in value.items()}
   return value
  for path in self.out.glob('*.json'):path.write_text(json.dumps(relocate(json.loads(path.read_text()))))
  audit=f.read_json(self.out/'floor-final-audit.json');audit['native_context_sha256']=p.sha(self.out/'floor-final-context.json');(self.out/'floor-final-audit.json').write_text(json.dumps(audit))
  data=relocate(old);self.candidate=self.out/'candidate/fixture.kicad_pcb';self.receipt=self.out/'result.json'
  (self.out/'area-context.json').rename(self.out/'placement-area-context.json')
  (self.out/'floor-area-export-process.json').rename(self.out/'floor-export-process.json')
  (self.out/'pre-adapter.dsn').unlink()
  hashes=p.tree_hash(self.source.parent)
  task=sx.read(self.out/'floor-export-input/fixture.kicad_pcb')
  guided,contract=f.policy_contract((self.out/'native.dsn').read_bytes(),f.read_json(self.out/'floor-export-context.json'),self.source.with_suffix('.kicad_pro').read_bytes(),task,hashes)
  (self.out/'floor-guided.dsn').write_bytes(guided);(self.out/'floor-policy.json').write_text(json.dumps(contract))
  outputs,composition=pc.derive_chain(self.out,self.source.name,hashes)
  for name,raw in outputs.items():(self.out/name).write_bytes(raw)
  p.save_json(self.out/'placement-policy.json',composition)
  implementation={};(self.out/'code').mkdir()
  for path in Path(pc.__file__).parent.glob('*.py'):
   shutil.copy2(path,self.out/'code'/path.name);implementation['autorouter/'+path.name]=p.sha(path)
  tools=copy.deepcopy(data['tools']);tools['implementation_sha256']=implementation;tools['git_head']='a'*40
  pins=json.loads((ROOT/'toolchain.lock.json').read_text())['tools'];tools['files']={str(p.c.resolve_tool_path(pin['path'])):pin['sha256'] for pin in pins.values()}
  shutil.copy2(ROOT/'toolchain.lock.json',self.out/'placement-toolchain.lock.json')
  freeze={'schema':1,'policy':pc.POLICY,'git_head':tools['git_head'],'files_sha256':{**implementation,'toolchain.lock.json':p.sha(self.out/'placement-toolchain.lock.json')}}
  p.save_json(self.out/'placement-source-freeze.json',freeze)
  settings=p.engine_profile_settings('completion-only',data['engine_budget']['remaining_outer_wall_seconds_at_assignment'],strict_class_targets=True,scoring_variant='via_default')
  settings.update(outer_task_wall_budget_seconds=data['budget_seconds'],outer_task_cpu_budget_seconds=data['cpu_budget_seconds'])
  for step in data['steps']:
   name=step['name']
   if name=='floor-area-export':
    name='floor-export';step['name']=name
    step['argv']=f.context_argv('export',self.out/'floor-export-input/fixture.kicad_pcb',self.out/'floor-export-context.json',self.out/'native.dsn',self.out/'placement-area-context.json')
   if name=='engine':step['argv']=f.engine_argv(self.out,settings['argv'])
   path=self.out/(name+'-process.json');value=f.read_json(path)
   value.update(name=name,argv=step['argv']);path.write_text(json.dumps(value))
  self.data={'schema':3,'input_policy':pc.POLICY,'status':'routing_accepted','accepted':True,'physical_electrical_validation':False,
    'baseline':'completion_only_probe','adapter':'both','engine_profile':'completion-only','scoring_variant':'via_default','planning_parameters':pc.parameters(),
    'scope':'whole_board_unlocked_routing','source':str(self.source),'source_hashes':hashes,'candidate':str(self.candidate),
    'candidate_sha256':p.sha(self.candidate),'task_sha256':p.sha(self.out/'floor-export-input/fixture.kicad_pcb'),
    'native_dsn_sha256':p.sha(self.out/'native.dsn'),'floor_guided_dsn_sha256':p.sha(self.out/'floor-guided.dsn'),'task_dsn_sha256':p.sha(self.out/'task.dsn'),
    'floor_policy':{'file':'floor-policy.json','sha256':p.sha(self.out/'floor-policy.json')},
    'placement_policy':{'file':'placement-policy.json','sha256':p.sha(self.out/'placement-policy.json')},
    'placement_source_freeze':{'file':'placement-source-freeze.json','sha256':p.sha(self.out/'placement-source-freeze.json')},
    'native_report_sha256':p.sha(self.out/'final-drc.json'),'native':data['native'],'source_drc':data['source_drc'],
    'invariants_unchanged':True,'whole_project_drc_clean':data['native']['warnings']==0,'metrics':data['metrics'],
    'tools':tools,'engine_budget':settings,'steps':data['steps'],'budget_seconds':data['budget_seconds'],'cpu_budget_seconds':data['cpu_budget_seconds'],
    'wall_seconds':data['wall_seconds'],'parent_cpu_seconds':data['parent_cpu_seconds'],
    'child_cpu_seconds':sum(step['cpu_seconds'] for step in data['steps']),'monitor_cpu_seconds':sum(step['monitor_cpu_seconds'] for step in data['steps']),
    'total_cpu_seconds':data['total_cpu_seconds']}
  self.data['control_child_cpu_seconds']=self.data['total_cpu_seconds']-sum(self.data[key] for key in ('parent_cpu_seconds','child_cpu_seconds','monitor_cpu_seconds'))
  self.save()
 def save(self):self.data['floor_evidence_hashes']=f.evidence_inventory(self.out);self.receipt.write_text(json.dumps(self.data))
 def check(self):return p.check_result(self.receipt)
 def test_receipt_digest_rejects_oversize_before_payload_read(self):
  import os
  original=os.fstat
  def oversize(fd):
   fields=list(original(fd));fields[6]=sx.MAX_BYTES+1;return os.stat_result(fields)
  with patch.object(pc.os,'fstat',oversize),self.assertRaisesRegex(p.Rejected,'bounded regular'):self.check()
 def test_full_schema3_consistency_only(self):self.assertEqual(self.check()['input_policy'],pc.POLICY)
 def test_schema_claim_downgrades_fail(self):
  for key,value in [('schema',2),('schema',1),('input_policy','native'),('input_policy',f.POLICY),('input_policy',None),('planning_parameters',None),('engine_profile','standard'),('scoring_variant',None),('scoring_variant','via_low'),('strategy','repair'),('guidance_policy',pc.POLICY)]:
   old=copy.deepcopy(self.data)
   if value is None:self.data.pop(key,None)
   else:self.data[key]=value
   self.save()
   with self.subTest(key=key,value=value),self.assertRaises((p.Rejected,ValueError)):self.check()
   self.data=old
 def test_all_new_markers_removed_still_old_floor_chain_rejects(self):
  for path in list(self.out.iterdir()):
   if path.name.startswith(('placement-','planning-')):path.unlink()
  for key in list(self.data):
   if key.startswith(('placement_','planning_')):self.data.pop(key)
  self.data.update(schema=2,input_policy=f.POLICY,scoring_variant=None);self.save()
  with self.assertRaises((p.Rejected,ValueError)):self.check()
 def test_duplicate_selector_and_nonfinite_outer_rejected(self):
  raw=self.receipt.read_text();self.receipt.write_text(raw[:-1]+',"schema":1}')
  with self.assertRaises(p.Rejected):self.check()
  self.receipt.write_text(raw[:-1]+',"surplus":NaN}')
  with self.assertRaises(p.Rejected):self.check()
 def test_native_receipt_duplicate_fields_rejected_after_rehash(self):
  path=self.out/'metrics.json';raw=path.read_text();path.write_text(raw[:-1]+',"version":"10.0.0"}');self.save()
  with self.assertRaises(p.Rejected):self.check()
 def test_consistent_process_and_settings_via_low_tamper_fails(self):
  settings=p.engine_profile_settings('completion-only',self.data['engine_budget']['remaining_outer_wall_seconds_at_assignment'],strict_class_targets=True,scoring_variant='via_low')
  settings.update(outer_task_wall_budget_seconds=self.data['budget_seconds'],outer_task_cpu_budget_seconds=self.data['cpu_budget_seconds']);self.data['engine_budget']=settings
  argv=f.engine_argv(self.out,settings['argv']);next(x for x in self.data['steps'] if x['name']=='engine')['argv']=argv
  path=self.out/'engine-process.json';value=f.read_json(path);value['argv']=argv;path.write_text(json.dumps(value));self.save()
  with self.assertRaisesRegex(p.Rejected,'engine configuration'):self.check()
 def test_rehashed_observer_process_cannot_substitute_snapshot(self):
  argv=next(x for x in self.data['steps'] if x['name']=='floor-export')['argv'];argv[4]=str(self.out/'code/floor_context.py')
  path=self.out/'floor-export-process.json';value=f.read_json(path);value['argv']=argv;path.write_text(json.dumps(value));self.save()
  with self.assertRaisesRegex(p.Rejected,'process provenance'):self.check()
 def test_final_staleness_candidate_source_context_code_and_receipt(self):
  real=pc.final_freshness
  for relative in ('candidate/fixture.kicad_pcb','floor-export-context.json','code/placement_clearance.py','result.json','../source/fixture.kicad_pro'):
   path=self.out/relative;raw=path.read_bytes()
   def mutate(directory,data):path.write_bytes(raw+b' ');return real(directory,data)
   with self.subTest(relative=relative),patch.object(pc,'final_freshness',mutate),self.assertRaises((p.Rejected,ValueError)):self.check()
   path.write_bytes(raw)
 def test_missing_new_modules_cannot_pass_rehashed_code_inventory(self):
  (self.out/'code/placement_clearance.py').unlink();self.data['tools']['implementation_sha256'].pop('autorouter/placement_clearance.py');self.save()
  with self.assertRaisesRegex(p.Rejected,'implementation provenance'):self.check()
 def test_handoff_refuses_new_policy(self):
  from autorouter.handoff import review_copy
  with self.assertRaisesRegex(p.Rejected,'handoff'):review_copy(self.receipt,self.root/'gui')
  self.assertFalse((self.root/'gui').exists())
 def test_cleanliness_claim_must_match_zero_warning_fixture(self):
  self.data['whole_project_drc_clean']=False;self.save()
  with self.assertRaisesRegex(p.Rejected,'cleanliness'):self.check()

if __name__=='__main__':unittest.main()
