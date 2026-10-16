"""Scoring-contract falsifiers only; actual native routing is separate evidence."""
import ast,copy,json,os,signal,stat,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from autorouter import strategy as s,pipeline as p,floor_route as f,engine_angle as angle,preferences as pref,handoff as h,local_settings as ls
from tests import test_engine_optimizer as opt,test_engine_fanout as fanout


class PruningScoring(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name).resolve()
  self.path=self.root/'incumbent/result.json';self.path.parent.mkdir()
  self.inc={'scoring_variant':'via_high','engine_profile':'tuned','adapter':'both','scope':'whole_board_unlocked_routing',
    'source':'owned-source','source_hashes':{'board':'exact'},'tools':{'frozen':'exact'}}
  self.inc['engine_budget']=p.engine_profile_settings('tuned',90.,scoring_variant='via_high')
  self.inc.update(budget_seconds=120.,cpu_budget_seconds=120.)
  self.inc['engine_budget'].update(outer_task_wall_budget_seconds=120.,outer_task_cpu_budget_seconds=120.)
  self.inc['steps']=[{'name':'engine','cpu_seconds':1,'argv':p.engine_argv(self.path.parent,self.inc['engine_budget']['argv']),'cwd':str(self.path.parent),
    'status':'success','exit_code':0,'cleanup_complete':True}]
  p.save_json(self.path.parent/'engine-process.json',self.inc['steps'][0])
  p.save_json(self.path,self.inc)
  self.parent={key:copy.deepcopy(self.inc[key]) for key in ('source','source_hashes','tools')}
  self.parent.update(incumbent_scoring_variant='via_high',incumbent_receipt_sha256=p.sha(self.path),steps=[dict(self.inc['steps'][0],phase='incumbent')])
  self.parent['strategy']='native_validated_zone_net_pruning'
  self.marker=self.root/'pruning-scoring.json'
  p.save_json(self.marker,{'schema':1,'strategy':self.parent['strategy'],'incumbent_scoring_variant':'via_high'})
  self.parent['incumbent_scoring_contract']={'file':self.marker.name,'sha256':p.sha(self.marker)}
 def test_explicit_preset_requires_actual_incumbent_validation(self):
  with patch.object(p,'check_minimum_width_record',return_value=None),patch.object(p,'check_result') as check:
   s.check_incumbent_scoring(self.root,self.parent);check.assert_called_once_with(self.path)
 def test_marker_downgrade_wrong_preset_or_receipt_and_worker_change_reject(self):
  for mutation in ('missing-preset','wrong-preset','missing-pin','wrong-pin','worker'):
   data=copy.deepcopy(self.parent)
   if mutation=='missing-preset':del data['incumbent_scoring_variant']
   elif mutation=='wrong-preset':data['incumbent_scoring_variant']='via_low'
   elif mutation=='missing-pin':del data['incumbent_receipt_sha256']
   elif mutation=='wrong-pin':data['incumbent_receipt_sha256']='wrong'
   else:data['steps'][0]['cpu_seconds']=.5
   with self.subTest(mutation=mutation),self.assertRaises(p.Rejected):s.check_incumbent_scoring(self.root,data)
 def test_different_source_profile_scope_or_tools_are_not_free_incumbents(self):
  for key,value in [('source','other'),('source_hashes',{}),('tools',{}),('scope','partial_completion'),('engine_profile','standard')]:
   inc=copy.deepcopy(self.inc);inc[key]=value;p.save_json(self.path,inc);data=copy.deepcopy(self.parent);data['incumbent_receipt_sha256']=p.sha(self.path)
   with self.subTest(key=key),self.assertRaises(p.Rejected):s.check_incumbent_scoring(self.root,data)
 def test_legacy_default_is_preserved_but_unknown_preset_never_creates_output(self):
  self.inc['scoring_variant']=None
  self.inc['engine_budget']=p.engine_profile_settings('tuned',90.)
  self.inc['engine_budget'].update(outer_task_wall_budget_seconds=120.,outer_task_cpu_budget_seconds=120.)
  self.inc['steps'][0]['argv']=p.engine_argv(self.path.parent,self.inc['engine_budget']['argv'])
  p.save_json(self.path.parent/'engine-process.json',self.inc['steps'][0]);p.save_json(self.path,self.inc);data=copy.deepcopy(self.parent)
  data['steps']=[dict(self.inc['steps'][0],phase='incumbent')]
  del data['incumbent_scoring_variant'];del data['incumbent_receipt_sha256']
  del data['incumbent_scoring_contract'];self.marker.unlink()
  with patch.object(p,'check_minimum_width_record',return_value=None),patch.object(p,'check_result') as check:s.check_incumbent_scoring(self.root,data);check.assert_called_once_with(self.path)
  for preset in ('invented',True,[]):
   out=self.root/'no-output'
   with self.subTest(preset=preset),self.assertRaises(p.Rejected):s.prune(self.root/'absent-source',out,incumbent_scoring=preset)
   self.assertFalse(out.exists())
 def test_relabelled_high_incumbent_cannot_be_downgraded_to_legacy_default(self):
  self.inc['scoring_variant']=None;p.save_json(self.path,self.inc);data=copy.deepcopy(self.parent)
  del data['incumbent_scoring_variant'];del data['incumbent_receipt_sha256'];del data['incumbent_scoring_contract'];self.marker.unlink()
  with patch.object(p,'check_minimum_width_record',return_value=None),self.assertRaisesRegex(p.Rejected,'execution journal'):
   s.check_incumbent_scoring(self.root,data)
 def test_coherently_edited_full_command_and_cwd_cannot_escape_router_flags(self):
  for change in ('output','jar','sandbox','cwd'):
   inc=copy.deepcopy(self.inc);worker=inc['steps'][0]
   if change=='cwd':worker['cwd']=str(self.root/'other')
   elif change=='output':worker['argv'][-1]=str(self.root/'other.ses')
   elif change=='jar':worker['argv'][worker['argv'].index('-jar')+1]='other.jar'
   else:worker['argv'][0]='other-supervisor'
   p.save_json(self.path,inc);p.save_json(self.path.parent/'engine-process.json',worker)
   data=copy.deepcopy(self.parent);data['incumbent_receipt_sha256']=p.sha(self.path);data['steps']=[dict(worker,phase='incumbent')]
   with self.subTest(change=change),patch.object(p,'check_minimum_width_record',return_value=None),self.assertRaisesRegex(p.Rejected,'execution journal'):
    s.check_incumbent_scoring(self.root,data)
 def test_symlink_contract_rejects_before_any_marker_digest(self):
  target=self.root/'owned-target';target.write_text('{}');self.marker.unlink();self.marker.symlink_to(target)
  with (patch.object(p,'sha',side_effect=AssertionError('digest must not follow marker symlink')),
        self.assertRaises(p.Rejected)):
   s.check_incumbent_scoring(self.root,self.parent)


class StrongerIncumbentControls(unittest.TestCase):
 # Reuse setup/record factories only; no inherited test population or Native run.
 raw=opt.EnginePlanningClearanceControls.raw
 settings=opt.EngineOptimizerControls.settings
 publication_fixture=fanout.EngineFanoutControls.publication_fixture

 def scratch(self):
  context=tempfile.TemporaryDirectory();self.addCleanup(context.cleanup)
  self.root=Path(context.name).resolve();child=self.root/'incumbent';child.mkdir();return child

 def scene(self):
  child,inc=opt.EngineOptimizerControls.record(self)
  (child/'task.dsn').write_bytes(self.raw());(child/angle.RECORD).unlink();(child/angle.INPUT).unlink()
  inc.update(engine_planning_clearance_margin_nm=20000,engine_angle_binding=angle.prepare(child,clearance_margin_nm=20000),source_hashes={'owned':'exact'},tools={'frozen':'exact'})
  p.save_json(child/'result.json',inc)
  parent=dict(strategy='native_validated_zone_net_pruning',adapter='both',scope='whole_board_unlocked_routing',
   engine_profile='tuned',incumbent_baseline='B2_free_angle_clearance20',incumbent_policy=s.STRONG_INCUMBENT_POLICY,
   incumbent_scoring_variant='via_default',incumbent_receipt_sha256=p.sha(child/'result.json'),
   source=inc['source'],source_hashes=copy.deepcopy(inc['source_hashes']),tools=copy.deepcopy(inc['tools']),
   budget_seconds=180,cpu_budget_seconds=180,finalization_reserve_seconds=25.,finalization_cpu_reserve_seconds=25.,
   steps=[dict(row,phase='incumbent') for row in inc['steps']])
  marker=self.root/'pruning-scoring.json';p.save_json(marker,dict(schema=1,strategy=parent['strategy'],incumbent_scoring_variant='via_default'))
  parent['incumbent_scoring_contract']=dict(file=marker.name,sha256=p.sha(marker))
  overrides=dict(adapter='both',profile='tuned',seconds=180,scoring_preference='via_default')
  preset=self.root/'pruning-preferences.json';preset.write_bytes(pref.snapshot(None,overrides))
  parent.update(pruning_preferences_policy=s.PRUNING_PREFERENCES_POLICY,pruning_preferences=dict(file=preset.name,sha256=p.sha(preset),effective=pref.resolve(None,overrides)))
  policy=self.root/'pruning-incumbent-policy.json';p.save_json(policy,s._incumbent_policy_contract(self.root,inc))
  parent['incumbent_policy_binding']=dict(file=policy.name,sha256=p.sha(policy))
  return child,inc,parent

 def test_default_request_keeps_original_configuration_and_invalid_optins_create_no_job(self):
  self.assertIsNone(s._incumbent_route_options(None,None))
  self.assertIsNone(s._incumbent_route_options(None,'via_high','unchanged-preset',{}))
  expected=dict(_fanout_enabled=False,_optimizer_enabled=False,_engine_clearance_margin_nm=20000)
  self.assertEqual(s._incumbent_route_options(s.STRONG_INCUMBENT_POLICY,'via_default'),expected)
  cases=[dict(_incumbent_policy=value) for value in (True,False,0,1,[],{},'other')]
  cases += [dict(incumbent_scoring=value) for value in (None,'via_high','via_low')]
  cases += [dict(settings_path='/missing'),dict(preference_overrides={})]
  for change in cases:
   args=dict(_incumbent_policy=s.STRONG_INCUMBENT_POLICY,incumbent_scoring='via_default');args.update(change)
   with self.subTest(change=change),patch.object(p,'Job',side_effect=AssertionError('no Job')),self.assertRaises(p.Rejected):
    s.prune('/missing/source','/missing/output',**args)

 def test_parent_binds_actual_child_profile_journal_and_shared_result_without_root_dsn(self):
  child,inc,parent=self.scene()
  self.assertFalse((self.root/'task.dsn').exists());self.assertEqual(parent['engine_profile'],'tuned')
  for key in ('engine_angle_binding','engine_fanout_override','engine_optimizer_override','engine_planning_clearance_margin_nm','engine_budget'):self.assertNotIn(key,parent)
  with patch.object(p,'check_minimum_width_record',return_value=None),patch.object(p,'check_result') as check,patch.object(ls,'check_normal_policy') as metadata:
   s.check_incumbent_scoring(self.root,parent);check.assert_called_once_with(child/'result.json');metadata.assert_called_once()
  self.assertEqual(f.read_json(child/'engine-process.json'),inc['steps'][0])

 def test_parent_marker_erasure_wrong_type_child_pin_and_root_impersonation_refuse(self):
  child,inc,good=self.scene();policy=self.root/'pruning-incumbent-policy.json';raw=policy.read_bytes()
  for mode in ('policy','binding','both_and_file','type','pin','root_angle','root_flag','allowance','reserve'):
   data=copy.deepcopy(good)
   if mode=='policy':data.pop('incumbent_policy')
   elif mode=='binding':data.pop('incumbent_policy_binding')
   elif mode=='both_and_file':data.pop('incumbent_policy');data.pop('incumbent_policy_binding');policy.unlink()
   elif mode=='type':data['incumbent_policy']=True
   elif mode=='pin':data['incumbent_receipt_sha256']='wrong'
   elif mode=='root_angle':data['engine_angle_binding']=inc['engine_angle_binding']
   elif mode=='root_flag':data['engine_optimizer_override']=False
   elif mode=='allowance':data['budget_seconds']=130
   else:data['finalization_reserve_seconds']=15
   try:
    with self.subTest(mode=mode),patch.object(p,'check_result',side_effect=AssertionError('reject before child Native reader')),self.assertRaises(p.Rejected):s.check_incumbent_scoring(self.root,data)
   finally:
    if not policy.exists():policy.write_bytes(raw)

 def test_qualified_child_clearance_flags_journal_and_contract_mutation_refuse(self):
  for mode in ('margin_type','margin','optimizer','fanout','proof','journal','worker'):
   child,inc,parent=self.scene()
   if mode=='margin_type':inc['engine_planning_clearance_margin_nm']=20000.
   elif mode=='margin':inc['engine_planning_clearance_margin_nm']=19999
   elif mode=='optimizer':inc['engine_optimizer_override']=True
   elif mode=='fanout':inc['engine_fanout_override']=True
   elif mode=='proof':(child/angle.INPUT).write_bytes(b'changed actual engine input')
   elif mode=='journal':(child/'engine-process.json').write_text('{}')
   else:inc['steps'][0]['argv'][-1]='wrong.ses'
   p.save_json(child/'result.json',inc);parent['incumbent_receipt_sha256']=p.sha(child/'result.json')
   # Coherently refresh just declared contract/pin; actual engine proof/journal must still reject.
   policy=self.root/'pruning-incumbent-policy.json';p.save_json(policy,s._incumbent_policy_contract(self.root,inc));parent['incumbent_policy_binding']['sha256']=p.sha(policy)
   parent['steps']=[dict(row,phase='incumbent') for row in inc['steps']]
   with self.subTest(mode=mode),patch.object(p,'check_minimum_width_record',return_value=None),patch.object(p,'check_result',side_effect=p.Rejected('synthetic full Native evidence unavailable')) as full,self.assertRaises(p.Rejected):
    s.check_incumbent_scoring(self.root,parent)
   # Actual shared engine-angle/settings/journal replay refuses before the Native reader.
   full.assert_not_called()

 def publish_pruning_stable(self,case,late=None):
  raw=(p.c.ROOT/'autorouter/strategy.py').read_bytes()
  prune=next(row for row in ast.parse(raw).body if isinstance(row,ast.FunctionDef) and row.name=='prune')
  closures=[row for row in ast.walk(prune) if isinstance(row,ast.FunctionDef) and row.name=='stable'];self.assertEqual(len(closures),1)
  owner={};h.capture_destination(owner,case.run);seen=[]
  def incumbent_readback(directory,data):
   self.assertEqual(directory,case.run);seen.append('child-readback')
   if late is not None and len(seen)==1:late()
  env=dict(s.__dict__);env.update(report=case.data,output=case.run,source=case.source,captured=None,owner=owner,
   pref=pref,owned_destination=h.owned_destination,original_fresh=s._check_original,incumbent_options={},
   check_incumbent_scoring=incumbent_readback)
  exec(compile(ast.fix_missing_locations(ast.Module(body=closures,type_ignores=[])),str(p.c.ROOT/'autorouter/strategy.py'),'exec'),env)
  result=f.publish(case.run,case.data,env['stable'],lambda:None,lambda:100,result_checker=lambda path:{'current':True})
  return result,seen

 def test_actual_pruning_stable_keeps_unchanged_owned_prl_current(self):
  case=self.publication_fixture('tuned',False);result,seen=self.publish_pruning_stable(case)
  self.assertTrue(result['accepted']);self.assertTrue(seen)

 @unittest.skipUnless(sys.platform=='darwin' and hasattr(os,'chflags'),'actual Mac PRL flags required')
 def test_actual_pruning_stable_rejects_flag_only_late_fault_after_incumbent_readback(self):
  case=self.publication_fixture('tuned',False);target=case.run/'final-drc-input'/case.source.with_suffix('.kicad_prl').name
  raw=target.read_bytes();flags=target.stat().st_flags;before=f.evidence_inventory(case.run)
  def late():
   os.chflags(target,stat.UF_IMMUTABLE,follow_symlinks=False);self.assertEqual(target.read_bytes(),raw);self.assertEqual(f.evidence_inventory(case.run),before)
  handlers={sig:signal.getsignal(sig) for sig in (signal.SIGINT,signal.SIGTERM)}
  def interrupted(*_):raise KeyboardInterrupt
  try:
   for sig in handlers:signal.signal(sig,interrupted)
   result,seen=self.publish_pruning_stable(case,late)
   if result.get('status')=='cancelled':raise KeyboardInterrupt
   self.assertTrue(seen);self.assertFalse(result['accepted']);self.assertEqual(result['status'],'invalidated');self.assertIn('flags',result['reason'])
  finally:
   try:os.chflags(target,flags,follow_symlinks=False)
   finally:
    for sig,handler in handlers.items():signal.signal(sig,handler)
  self.assertEqual(target.stat().st_flags,flags)

 def test_coherent_parent_erasure_and_tuned_relabel_cannot_hide_actual_free_angle_engine(self):
  for remove_proof_files in (False,True):
   child,inc,parent=self.scene();parent.pop('incumbent_policy');parent.pop('incumbent_policy_binding');(self.root/'pruning-incumbent-policy.json').unlink()
   parent['incumbent_baseline']='B2_tuned';inc['engine_profile']='tuned'
   for key in ('engine_fanout_override','engine_optimizer_override','engine_planning_clearance_margin_nm','engine_angle_binding'):inc.pop(key)
   if remove_proof_files:
    (child/angle.RECORD).unlink();(child/angle.INPUT).unlink()
   p.save_json(child/'result.json',inc);parent['incumbent_receipt_sha256']=p.sha(child/'result.json')
   with self.subTest(remove_proof_files=remove_proof_files),patch.object(p,'check_minimum_width_record',return_value=None),patch.object(p,'check_result',side_effect=AssertionError('shared engine checker must refuse first')),self.assertRaises(p.Rejected):
    s.check_incumbent_scoring(self.root,parent)

 def test_child_receipt_mutation_during_shared_readback_rejects_before_final_prl(self):
  child,inc,parent=self.scene()
  def late(path):
   changed=f.read_json(path);changed['late_receipt_edit']=True;p.save_json(path,changed);return {'current':True}
  with patch.object(p,'check_minimum_width_record',return_value=None),patch.object(p,'check_result',side_effect=late),patch.object(ls,'check_normal_policy',side_effect=AssertionError('late child hash must reject first')),self.assertRaisesRegex(p.Rejected,'contract changed'):
   s.check_incumbent_scoring(self.root,parent)

 def test_actual_shared_result_entry_valid_parent_reaches_next_mandatory_gate(self):
  child,inc,parent=self.scene();receipt=self.root/'result.json';p.save_json(receipt,parent)
  class NextMandatoryGate(Exception):pass
  with patch.object(p,'check_minimum_width_record',return_value=None),patch.object(p,'check_result',return_value={'current':True}) as child_read,patch.object(ls,'check_normal_policy'),patch.object(p,'native_minimum_markers',side_effect=NextMandatoryGate) as next_gate,self.assertRaises(NextMandatoryGate):
   p._check_result_uncached(receipt)
  child_read.assert_called_with(child/'result.json');next_gate.assert_called_once()
  self.assertFalse((self.root/angle.INPUT).exists());self.assertFalse((self.root/angle.RECORD).exists())

 def test_actual_entry_root_or_orphan_angle_evidence_cannot_hide_in_parent(self):
  for mode in ('root_input','root_record','root_binding','root_profile','root_journal_angle','root_journal_ordinary','wrong_cwd','wrong_phase','extra_arg','orphan_row','extra_incumbent_row'):
   child,inc,parent=self.scene();receipt=self.root/'result.json'
   if mode=='root_input':(self.root/angle.INPUT).write_bytes(b'owned extra root evidence')
   elif mode=='root_record':(self.root/angle.RECORD).write_text('{}')
   elif mode=='root_binding':parent['engine_angle_binding']=inc['engine_angle_binding']
   elif mode=='root_profile':parent['engine_profile']=angle.PROFILE
   elif mode in ('root_journal_angle','root_journal_ordinary'):
    row=copy.deepcopy(inc['steps'][0]);row['cwd']=str(self.root)
    if mode=='root_journal_ordinary':row['argv']=['owned-ordinary-root-engine']
    p.save_json(self.root/'engine-process.json',row)
   elif mode=='wrong_cwd':parent['steps'][0]['cwd']=str(self.root)
   elif mode=='wrong_phase':parent['steps'][0]['phase']='trial'
   elif mode=='extra_arg':parent['steps'][0]['argv'].append('extra')
   elif mode=='orphan_row':
    row=copy.deepcopy(parent['steps'][0]);row.pop('phase');parent['steps'].append(row)
   else:parent['steps'].append(copy.deepcopy(parent['steps'][0]))
   p.save_json(receipt,parent)
   with self.subTest(mode=mode),patch.object(p,'check_minimum_width_record',return_value=None),patch.object(p,'check_result',return_value={'current':True}),patch.object(ls,'check_normal_policy'),patch.object(p,'native_minimum_markers',side_effect=AssertionError('must reject before next gate')),self.assertRaises(p.Rejected):
    p._check_result_uncached(receipt)

 def test_actual_entry_rejects_root_angle_file_created_during_child_readback(self):
  child,inc,parent=self.scene();receipt=self.root/'result.json';p.save_json(receipt,parent)
  def late(path):
   self.assertEqual(path,child/'result.json');(self.root/angle.INPUT).write_bytes(b'late owned root evidence');return {'current':True}
  with patch.object(p,'check_minimum_width_record',return_value=None),patch.object(p,'check_result',side_effect=late),patch.object(ls,'check_normal_policy'),patch.object(p,'native_minimum_markers',side_effect=AssertionError('must reject late root evidence before next gate')),self.assertRaises(p.Rejected):
   p._check_result_uncached(receipt)
