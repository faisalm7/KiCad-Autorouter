"""Unexecuted software controls; fabricated receipts establish no Native validity."""
import copy,importlib.util,json,tempfile,unittest,sys
from pathlib import Path
from unittest.mock import patch
DRAFT=Path(__file__).with_name('controller.py')
spec=importlib.util.spec_from_file_location('adaptive_controller_draft',DRAFT)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class PureReaderGate(unittest.TestCase):
 def test_exact_two_git_reads_get_only_fixed_ephemeral_config(self):
  calls=[];marker=object()
  with patch.object(m.subprocess,'Popen',side_effect=lambda argv,**kw:(calls.append((argv,kw)),marker)[1]):
   with m.pure_reader_guard():
    for argv in m.READ_ONLY_GIT:self.assertIs(m.subprocess.Popen(list(argv),cwd=m.ROOT,stdout=m.subprocess.PIPE),marker)
  self.assertEqual([tuple(x[0]) for x in calls],list(m.CONTROLLED_GIT))
  self.assertTrue(all(x[1]['cwd']==m.ROOT for x in calls))
 def test_native_java_network_shell_and_git_mutations_never_reach_launcher(self):
  forbidden=([str(m.c.CLI),'pcb','drc'],['java','-jar','engine.jar'],['curl','https://example.invalid'],['sh','-c','git status'],['git','reset','--hard'],['git','status'],['git','rev-parse','HEAD','--verify'])
  with patch.object(m.subprocess,'Popen') as launch:
   with m.pure_reader_guard():
    for argv in forbidden:
     with self.subTest(argv=argv),self.assertRaises(m.PureReaderViolation):m.subprocess.Popen(argv,cwd=m.ROOT)
   launch.assert_not_called()
 def test_allowed_words_cannot_smuggle_cwd_env_executable_preexec_or_output(self):
  for extra in ({'cwd':m.ROOT.parent},{'cwd':m.ROOT,'env':{}},{'cwd':m.ROOT,'executable':'/bin/sh'},{'cwd':m.ROOT,'preexec_fn':lambda:None},{'cwd':m.ROOT,'shell':True},{'cwd':m.ROOT,'stdout':123}):
   with self.subTest(extra=extra),patch.object(m.subprocess,'Popen') as launch:
    with m.pure_reader_guard(),self.assertRaises(m.PureReaderViolation):m.subprocess.Popen(['git','rev-parse','HEAD'],**extra)
    launch.assert_not_called()
 def test_audit_allows_only_controlled_git_and_blocks_direct_spawn(self):
  for argv in m.CONTROLLED_GIT:m.pure_audit('subprocess.Popen',('git',list(argv),m.ROOT,None))
  for event,args in [('subprocess.Popen',('git',['git','rev-parse','HEAD'],m.ROOT,None)),('subprocess.Popen',('java',['java'],m.ROOT,None)),('os.posix_spawn',('git',[],{})),('os.fork',())]:
   with self.subTest(event=event,args=args),self.assertRaises(m.PureReaderViolation):m.pure_audit(event,args)
  with m.pure_reader_guard(),self.assertRaises(m.PureReaderViolation):m.os.system('anything')



class HistoricalBinding(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name).resolve()
  self.matrix=self.root/'matrix';(self.matrix/'run').mkdir(parents=True)
  self.oldtools={'git_head':'old','implementation_sha256':{'autorouter/strategy.py':'oldstrategy','autorouter/pipeline.py':'core','autorouter/native.py':'native','autorouter/runner.py':'runner'},'files':{'kicad':'pinned','java':'pinned'},'kicad':'10.0.0'}
  self.now=copy.deepcopy(self.oldtools);self.now['git_head']='new';self.now['implementation_sha256']['autorouter/strategy.py']='reviewednew'
  self.rows=[dict(id=name,accepted=name!='B0',invocation_wall_seconds=20.,invocation_cpu_seconds=30.,charged_wall_seconds=30.,charged_cpu_seconds=42.) for name in m.ARMS]
  old=dict(source=str(self.root/'source/board.kicad_pcb'),source_hashes={'board.kicad_pcb':'source'},tools=self.oldtools,pins={})
  self.oldpath=self.save('old.json',old);proof=self.save('proof.json',dict(status='completed',comparison_eligible=True,workers=[]))
  inner=self.save('inner.json',dict(result_sha256=m.p.sha(proof)))
  qual=self.save('qual.json',dict(passed=True,source_current=True,result_sha256=m.p.sha(proof),reader_execution_sha256=m.p.sha(inner),final_charged_results=self.rows))
  protocol=self.matrix/'run/protocol.json';m.p.save_json(protocol,dict(inner_allowance_seconds=114.23663762499928))
  self.spec=dict(source=old['source'],source_hashes=old['source_hashes'],tools=self.now,additive_strategy_delta=m.compatibility(self.now,self.oldtools),assigned_inner_seconds=114.23663762499928,
   reference=dict(spec=str(self.oldpath),qualification=str(qual),result=str(proof),reader_execution=str(inner),matrix=str(self.matrix),common=m.uniform_reference_common(self.rows),inventories={},pins={str(x):m.p.sha(x) for x in (self.oldpath,proof,inner,qual,protocol)}))
 def save(self,name,data):
  path=self.root/name;m.p.save_json(path,data);return path
 def test_additive_strategy_delta_preserves_reference_old_head_and_accepts_binding(self):
  old,qual,proof=m.reference(self.spec);self.assertEqual(old['tools']['git_head'],'old');self.assertEqual(qual['final_charged_results'],self.rows)
 def test_nonstrategy_and_tool_changes_reject_even_with_new_delta_declaration(self):
  for kind in ('native','tool','newmodule'):
   now=copy.deepcopy(self.now)
   if kind=='native':now['implementation_sha256']['autorouter/native.py']='changed'
   elif kind=='tool':now['files']['kicad']='changed'
   else:now['implementation_sha256']['autorouter/unreviewed.py']='extra'
   with self.subTest(kind=kind),self.assertRaises(m.p.Rejected):m.compatibility(now,self.oldtools)
 def test_source_and_exact_allowance_cannot_be_replaced(self):
  for key,value in [('source_hashes',{'board.kicad_pcb':'other'}),('assigned_inner_seconds',120.),('assigned_inner_seconds',True)]:
   changed=copy.deepcopy(self.spec);changed[key]=value
   with self.subTest(key=key,value=value),self.assertRaises(m.p.Rejected):m.reference(changed)
 def test_changed_proof_bytes_are_rejected_before_metadata_is_used(self):
  proof=Path(self.spec['reference']['result']);proof.write_text(proof.read_text()+'\n')
  with self.assertRaisesRegex(m.p.Rejected,'reference pin changed'):m.reference(self.spec)
 def test_source_material_inventory_catches_late_addition(self):
  material=self.root/'source';material.mkdir();(material/'rules').write_bytes(b'original')
  self.spec['reference']['inventories'][str(material)]=m.digest(m.inventory(material));(material/'extra').write_bytes(b'extra')
  with self.assertRaisesRegex(m.p.Rejected,'reference material changed'):m.reference(self.spec)
 def test_common_cost_must_remain_uniform_over_every_reference_arm(self):
  rows=copy.deepcopy(self.rows);rows[-1]['charged_cpu_seconds']+=.5
  with self.assertRaisesRegex(m.p.Rejected,'not uniform'):m.uniform_reference_common(rows)
  changed=copy.deepcopy(self.spec);changed['reference']['common']['wall_seconds']-=1
  with self.assertRaisesRegex(m.p.Rejected,'shared costs differ'):m.reference(changed)

class ActualCostAndPublication(unittest.TestCase):
 def setUp(self):
  self.rows=[dict(id=name,accepted=name!='B0',invocation_wall_seconds=20.,invocation_cpu_seconds=30.,charged_wall_seconds=30.,charged_cpu_seconds=42.) for name in m.ARMS]
  self.raw=dict(id='C_adaptive',accepted=True,invocation_wall_seconds=40.,invocation_cpu_seconds=50.,observations=[dict(final_delivery_accepted=True)])
  self.outer=dict(wall_seconds=45.,full_cpu_seconds=60.);self.prep=dict(wall_seconds=2.,full_cpu_seconds=3.);self.sample=dict(wall_seconds=7.,full_cpu_seconds=8.);self.common=m.uniform_reference_common(self.rows)
 def charged(self,**kw):
  return m.charged_rows(kw.get('rows',self.rows),kw.get('raw',self.raw),kw.get('outer',self.outer),self.common,self.prep,self.sample,kw.get('cap',300.),True)
 def test_solver_cost_is_own_only_but_every_method_pays_all_new_common(self):
  result,common=self.charged();self.assertEqual(common,dict(wall_seconds=23.,full_cpu_seconds=30.));self.assertEqual((result[0]['charged_wall_seconds'],result[0]['charged_cpu_seconds']),(53.,72.));self.assertEqual((result[-1]['charged_wall_seconds'],result[-1]['charged_cpu_seconds']),(73.,92.));self.assertFalse(result[0]['accepted']);self.assertEqual(self.rows[0]['charged_wall_seconds'],30.)
  raw=dict(self.raw,invocation_wall_seconds=50.,invocation_cpu_seconds=60.);outer=dict(wall_seconds=55.,full_cpu_seconds=70.);more,_=self.charged(raw=raw,outer=outer)
  self.assertEqual(more[:-1],result[:-1]);self.assertEqual(more[-1]['charged_cpu_seconds'],result[-1]['charged_cpu_seconds']+10.)
 def test_complete_reader_cpu_replaces_sample_and_can_reject_only_fresh_arm(self):
  rows,_=self.charged();whole=dict(wall_seconds=9.,full_cpu_seconds=12.);final=m.replace_reader_cost(rows,self.sample,whole,94.)
  self.assertEqual((final[-1]['charged_wall_seconds'],final[-1]['charged_cpu_seconds']),(75.,96.));self.assertFalse(final[-1]['accepted']);self.assertFalse(final[-1]['observations'][0]['final_delivery_accepted']);self.assertTrue(final[1]['accepted']);self.assertEqual(rows[-1]['charged_cpu_seconds'],92.)
 def test_omitted_outer_or_reader_cpu_is_not_clamped_into_a_pass(self):
  with self.assertRaisesRegex(m.p.Rejected,'omit adaptive'):self.charged(outer=dict(wall_seconds=45.,full_cpu_seconds=49.))
  rows,_=self.charged()
  with self.assertRaisesRegex(m.p.Rejected,'omit sampled'):m.replace_reader_cost(rows,self.sample,dict(wall_seconds=9.,full_cpu_seconds=7.),300.)
 def test_tail_checks_cpu_independently_of_wall_and_overall_cap(self):
  m.check_tail((21.,35.),(20.,20.),60.,15.)
  for now,cap in [((21.,35.0001),60.),((21.,35.),34.9)]:
   with self.subTest(now=now,cap=cap),self.assertRaises(m.p.Rejected):m.check_tail(now,(20.,20.),cap,15.)
 def test_callback_cannot_change_positive_snapshot_or_hide_cpu_overrun(self):
  with tempfile.TemporaryDirectory() as tmp:
   path=Path(tmp).resolve()/'execution.json';record={'passed':True};m.p.save_json(path,record)
   def forge():record['extra']='changed';m.p.save_json(path,record)
   with patch.object(m,'elapsed',return_value=(1.,1.)),self.assertRaisesRegex(m.p.Rejected,'changed during'):m.finish_publication(path,record,forge,(0.,0.),60.,2.)
   record={'passed':True};m.p.save_json(path,record)
   with patch.object(m,'elapsed',return_value=(1.,2.01)),self.assertRaisesRegex(m.p.Rejected,'guard'):m.finish_publication(path,record,lambda:None,(0.,0.),60.,2.)
 def test_stale_source_callback_propagates_rejection_before_delivery(self):
  with tempfile.TemporaryDirectory() as tmp:
   path=Path(tmp).resolve()/'execution.json';record={'passed':True};m.p.save_json(path,record)
   def stale():raise m.p.Rejected('source changed')
   with self.assertRaisesRegex(m.p.Rejected,'source changed'):m.finish_publication(path,record,stale,(0.,0.),60.,2.)


 def test_actual_qualification_late_correction_clears_nested_delivery_flags(self):
  # Execute the real qualify() branch with substituted worker/stability/tail
  # failure. No pipeline/Native child is invoked by this authored fixture.
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp).resolve();read=root/'read';read.mkdir();out=root/'qualification'
   rows,_=self.charged()
   result=dict(status='completed',comparison_eligible=True,workers=[],results=rows,
    observed_reader_wall_seconds=self.sample['wall_seconds'],observed_reader_full_cpu_seconds=self.sample['full_cpu_seconds'])
   m.p.save_json(read/'result.json',result)
   spec=dict(limits=dict(reader=60.,delivered=300.),paths=dict(read=str(read),qualification=str(out)),controller_source=str(DRAFT))
   process=dict(status='success',exit_code=0,cleanup_complete=True,log_truncated=False)
   with patch.object(m,'run',return_value=process),patch.object(m,'stable'),patch.object(m,'elapsed',return_value=(9.,12.)),patch.object(m,'finish_publication',side_effect=m.p.Rejected('authored late qualification failure')),patch.object(m,'comparisons',return_value=[dict(authored=True)]):
    self.assertEqual(m.qualify(root/'protocol.json',spec,'pin'),2)
   retained=m.f.read_json(out/'execution.json')
   self.assertFalse(retained['passed']);self.assertEqual(retained['comparisons'],[])
   self.assertTrue(retained['final_charged_results'])
   self.assertFalse(any(row['accepted'] for row in retained['final_charged_results']))
   flags=[observation['final_delivery_accepted'] for row in retained['final_charged_results'] for observation in row.get('observations',[])]
   self.assertTrue(flags);self.assertFalse(any(flags))
   self.assertEqual(retained['process'],process)

class ActualWorkerCancellation(unittest.TestCase):
 def test_actual_worker_preserves_cancelled_invocation_and_returns130_only_for_cancellation(self):
  cases=[({'status':'cancelled','steps':[]},False,130),
         ({'status':'rejected','steps':[{'status':'cancelled'}]},False,130),
         ({'status':'rejected','steps':[]},True,130),
         ({'status':'drc_rejected','steps':[]},False,0),
         ({'status':'quality_rejected','steps':[]},False,0)]
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp).resolve()
   for i,(data,raw_cancelled,expected) in enumerate(cases):
    with self.subTest(status=data['status'],raw_cancelled=raw_cancelled):
     native=root/str(i);native.mkdir()
     spec=dict(paths=dict(native=str(native)),source=str(root/'board.kicad_pcb'),assigned_inner_seconds=114.)
     raw=dict(id='C_adaptive',status=data['status'],cancelled=raw_cancelled,accepted=False)
     with patch.object(m.strategy,'prune',return_value=data) as solve,patch.object(m.q,'summarize',return_value=raw),patch.object(m,'stable'):
      self.assertEqual(m.worker(root/'protocol.json',spec,'pin'),expected)
     retained=m.f.read_json(native/'invocation.json')
     self.assertFalse(retained['accepted'])
     self.assertEqual(retained['status'],'cancelled' if expected==130 else data['status'])
     self.assertTrue(retained.get('cancelled') is True if expected==130 else retained['cancelled'] is False)
     solve.assert_called_once_with(Path(spec['source']),native/'C_adaptive',114.,proposal_policy='adaptive')

class OperationalCeiling(unittest.TestCase):
 def test_exact_operational_transformation_and_explicit_manifest_declaration(self):
  before=(m.ROOT/m.CACHE_BEFORE).read_bytes();after=before.replace(b'16*1024**3',b'18*1024**3').replace(b'16 GiB',b'18 GiB')
  self.assertEqual(m.cache_ceiling_bytes(before,after),m.hashlib.sha256(after).hexdigest())
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp).resolve();(root/'autorouter').mkdir();(root/'before.py').write_bytes(before);(root/'autorouter/pipeline.py').write_bytes(after)
   old=dict(git_head='old',implementation_sha256={'autorouter/strategy.py':'oldstrategy','autorouter/pipeline.py':m.CACHE_BEFORE_SHA256,'autorouter/native.py':'native'},files={'kicad':'same'})
   now=copy.deepcopy(old);now['git_head']='new';now['implementation_sha256'].update({'autorouter/strategy.py':'newstrategy','autorouter/pipeline.py':m.hashlib.sha256(after).hexdigest()})
   with patch.object(m,'ROOT',root),patch.object(m,'CACHE_BEFORE','before.py'):
    operational=m.cache_ceiling_delta(now,old)
    with self.assertRaises(m.p.Rejected):m.compatibility(now,old)
    self.assertEqual(m.compatibility(now,old,operational),{'autorouter/strategy.py':dict(reference='oldstrategy',current='newstrategy')})
    changed=copy.deepcopy(operational);changed['scope']='arbitrary change'
    with self.assertRaises(m.p.Rejected):m.compatibility(now,old,changed)
    changed=copy.deepcopy(now);changed['implementation_sha256']['autorouter/native.py']='weakened'
    with self.assertRaises(m.p.Rejected):m.compatibility(changed,old,operational)
 def test_nonexact_pipeline_or_missing_mutated_preserved_pin_rejects(self):
  before=(m.ROOT/m.CACHE_BEFORE).read_bytes();after=before.replace(b'16*1024**3',b'18*1024**3').replace(b'16 GiB',b'18 GiB')
  for altered in (after+b'\n',after.replace(b'18*1024**3',b'19*1024**3'),after.replace(b'18 GiB',b'19 GiB'),before):
   with self.subTest(sha=m.hashlib.sha256(altered).hexdigest()),self.assertRaises(m.p.Rejected):m.cache_ceiling_bytes(before,altered)
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp).resolve();(root/'autorouter').mkdir();(root/'autorouter/pipeline.py').write_bytes(after)
   old=dict(implementation_sha256={'autorouter/pipeline.py':m.CACHE_BEFORE_SHA256});now=dict(implementation_sha256={'autorouter/pipeline.py':m.hashlib.sha256(after).hexdigest()})
   with patch.object(m,'ROOT',root),patch.object(m,'CACHE_BEFORE','before.py'):
    with self.assertRaises(FileNotFoundError):m.cache_ceiling_delta(now,old)
    (root/'before.py').write_bytes(before+b'\n')
    with self.assertRaisesRegex(m.p.Rejected,'preserved'):m.cache_ceiling_delta(now,old)

class RetainedPredecessor(unittest.TestCase):
 def prior_spec(self):
  prior=m.f.read_json(m.ROOT/'.runs/ir-adaptive-001-protocol.json')
  return dict(case='ir',source=prior['source'],source_hashes=prior['source_hashes'],assigned_inner_seconds=prior['assigned_inner_seconds'],predecessor=m.failed_predecessor('ir'))
 def test_actual_ir_failed_cost_is_two_operations_uniform_all_six_and_arc_zero(self):
  spec=self.prior_spec();cost=m.predecessor_common(spec)
  self.assertAlmostEqual(cost['wall_seconds'],19.151949457998853);self.assertAlmostEqual(cost['full_cpu_seconds'],14.702242)
  self.assertEqual(spec['predecessor']['operations'],2);self.assertFalse(spec['predecessor']['accepted']);self.assertFalse(spec['predecessor']['new_native_execution']);self.assertFalse(spec['predecessor']['new_engine_execution'])
  rows=[dict(id=name,accepted=True,invocation_wall_seconds=20.,invocation_cpu_seconds=30.,charged_wall_seconds=30.,charged_cpu_seconds=42.) for name in m.ARMS]
  raw=dict(id='C_adaptive',accepted=True,invocation_wall_seconds=40.,invocation_cpu_seconds=50.)
  args=(rows,raw,dict(wall_seconds=45.,full_cpu_seconds=60.),m.uniform_reference_common(rows),dict(wall_seconds=2.,full_cpu_seconds=3.),dict(wall_seconds=7.,full_cpu_seconds=8.),300.,True)
  old,base=m.charged_rows(*args);new,added=m.charged_rows(*args,predecessor_cost=cost)
  self.assertEqual(len(new),6)
  for before,after in zip(old,new):
   self.assertAlmostEqual(after['charged_wall_seconds']-before['charged_wall_seconds'],cost['wall_seconds']);self.assertAlmostEqual(after['charged_cpu_seconds']-before['charged_cpu_seconds'],cost['full_cpu_seconds'])
  self.assertAlmostEqual(added['wall_seconds']-base['wall_seconds'],cost['wall_seconds']);self.assertEqual(rows[0]['charged_wall_seconds'],30.)
  self.assertIsNone(m.failed_predecessor('arc'));self.assertEqual(m.predecessor_common(dict(case='arc',predecessor=None)),dict(wall_seconds=0.,full_cpu_seconds=0.))
  with self.assertRaises(m.p.Rejected):m.predecessor_common(dict(case='arc',predecessor=spec['predecessor']))
 def test_missing_or_mutated_predecessor_record_pins_and_cost_reject(self):
  spec=self.prior_spec()
  variants=[]
  changed=copy.deepcopy(spec);del changed['predecessor'];variants.append(changed)
  changed=copy.deepcopy(spec);changed['predecessor']['cost']['full_cpu_seconds']-=1;variants.append(changed)
  changed=copy.deepcopy(spec);changed['predecessor']['pins'].pop(next(iter(changed['predecessor']['pins'])));variants.append(changed)
  changed=copy.deepcopy(spec);changed['predecessor']['pins'][next(iter(changed['predecessor']['pins']))]='0'*64;variants.append(changed)
  for changed in variants:
   with self.subTest(keys=changed.keys()),self.assertRaisesRegex(m.p.Rejected,'predecessor record'):m.predecessor_common(changed)
  original=m.p.sha
  for name in m.IR_PREDECESSOR_PINS:
   target=m.ROOT/name
   def mutated(path):return '0'*64 if Path(path)==target else original(path)
   with self.subTest(path=name),patch.object(m.p,'sha',side_effect=mutated),self.assertRaisesRegex(m.p.Rejected,'predecessor pin'):m.failed_predecessor('ir')
 def test_missing_actual_prior_file_and_native_steps_cannot_be_reclassified(self):
  original=m.h.real_path;target=m.ROOT/'.runs/ir-adaptive-001-native/execution.json'
  def missing(path,*args,**kwargs):
   if Path(path)==target:raise FileNotFoundError(str(target))
   return original(path,*args,**kwargs)
  with patch.object(m.h,'real_path',side_effect=missing),self.assertRaises(FileNotFoundError):m.failed_predecessor('ir')
  original_read=m.f.read_json;target=m.ROOT/'.runs/ir-adaptive-001-native/C_adaptive/result.json'
  for update in ({'steps':[{'status':'success'}]},{'trials':[{'id':'trial-001'}]},{'incumbent':{'accepted':False}},{'candidate_sha256':'candidate'},{'native_report_sha256':'native'}):
   def changed(path):
    data=original_read(path)
    if Path(path)==target:data.update(update)
    return data
   with self.subTest(update=update),patch.object(m.f,'read_json',side_effect=changed),self.assertRaisesRegex(m.p.Rejected,'Native/routing work'):m.failed_predecessor('ir')
 def test_prior_source_hashes_and_exact_allowance_still_required(self):
  spec=self.prior_spec()
  for key,value in [('source','other'),('source_hashes',{}),('assigned_inner_seconds',120.)]:
   changed=copy.deepcopy(spec);changed[key]=value
   with self.subTest(key=key),self.assertRaisesRegex(m.p.Rejected,'source/allocation'):m.predecessor_common(changed)

if __name__=='__main__':unittest.main()
