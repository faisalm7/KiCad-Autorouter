"""Pure small-file/actual saved-geometry controls. Never native execution."""
import copy,importlib.util,json,math,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import driver as d
r=d.r;s=d.s;p=d.p;sx=d.sx
class Derivation(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.raw=(d.ARM/'candidate'/d.SOURCE.name).read_bytes();cls.tree=sx.parse(cls.raw.decode());cls.native=d.f.read_json(d.ARM/'result.json')['native']
 def test_fixed_actual_input_hash_and_noop_negative(self):
  self.assertEqual(d.p.sha(d.ARM/'candidate'/d.SOURCE.name),d.CANDIDATE_SHA);self.assertEqual(r.prepare(self.raw,r.CASES[0]),self.raw)
 def test_positive_translates_exactly_two_nodes_and_preserves_all_else(self):
  changed=sx.parse(r.prepare(self.raw,r.CASES[1]).decode());base_index=r.uuid_index(self.tree);new_index=r.uuid_index(changed)
  changes=[ident for ident in base_index if base_index[ident]!=new_index[ident]]
  self.assertEqual(set(changes),set(r.TARGETS));self.assertEqual(p.immutable(changed),p.immutable(self.tree))
  for ident,expected in r.TARGETS.items():
   old=base_index[ident][0];new=new_index[ident][0]
   for field in ('start','end'):
    a=list(map(float,sx.one(old,field)[1:]));b=list(map(float,sx.one(new,field)[1:]));delta=list(map(float,expected['delta']))
    for i in (0,1):self.assertAlmostEqual(b[i]-a[i],delta[i],places=12)
   a0=list(map(float,sx.one(old,'start')[1:]));b0=list(map(float,sx.one(old,'end')[1:]));a1=list(map(float,sx.one(new,'start')[1:]));b1=list(map(float,sx.one(new,'end')[1:]));self.assertAlmostEqual(math.dist(a0,b0),math.dist(a1,b1),places=12)
  self.assertAlmostEqual(math.hypot(.015,.015),.021213203435596427,places=14)
 def test_missing_duplicate_wrong_type_or_nested_targets_reject(self):
  target=next(iter(r.TARGETS))
  for kind in ('missing','duplicate','wrong_type','nested'):
   tree=copy.deepcopy(self.tree);node=r.uuid_index(tree)[target][0]
   if kind=='missing':tree.remove(node)
   if kind=='duplicate':tree.append(copy.deepcopy(node))
   if kind=='wrong_type':node[0]='arc'
   if kind=='nested':tree.remove(node);tree.append(['footprint','"invalid"',node])
   with self.subTest(kind=kind),self.assertRaises(p.Rejected):r.translate(tree)
 def test_changed_coordinate_width_net_layer_or_lock_reject(self):
  for field,value in [('start',['0','0']),('width',['.299']),('net',['55']),('layer',['"F.Cu"']),('locked',['yes'])]:
   tree=copy.deepcopy(self.tree);node=r.uuid_index(tree)[next(iter(r.TARGETS))][0];old=sx.one(node,field)
   if old is None:node.append([field,*value])
   else:old[1:]=value
   with self.subTest(field=field),self.assertRaises(p.Rejected):r.translate(tree)
 def test_actual_negative_exact_target_pairs_and_eight_opens(self):
  self.assertTrue(r.verdict(r.CASES[0],self.native,self.native))
  for key,value in [('opens',7),('blocking',1),('warnings',0),('exclusions',1)]:
   changed=copy.deepcopy(self.native);changed[key]=value
   with self.subTest(key=key):self.assertFalse(r.verdict(r.CASES[0],changed,self.native))
  changed=copy.deepcopy(self.native);next(x for x in changed['findings']if x['type']=='clearance')['items'][0]['uuid']='other';self.assertFalse(r.verdict(r.CASES[0],changed,self.native))
 def positive(self):
  changed=copy.deepcopy(self.native);changed['blocking']=0;changed['findings']=[x for x in changed['findings']if x['type']!='clearance'];return changed
 def test_positive_remains_rejected_with_eight_opens_but_passes_target_control(self):
  value=self.positive();self.assertTrue(r.verdict(r.CASES[1],value,self.native));self.assertFalse(p.native_accepted(value));self.assertEqual(value['opens'],8)
 def test_positive_new_open_blocking_exclusion_or_critical_warning_reject(self):
  for key,value in [('opens',9),('blocking',1),('exclusions',1)]:
   changed=self.positive();changed[key]=value
   with self.subTest(key=key):self.assertFalse(r.verdict(r.CASES[1],changed,self.native))
  changed=self.positive();changed['findings'].append({'type':'padstack_invalid','severity':'warning','items':[{'uuid':'new'}]});changed['warnings']+=1;self.assertFalse(r.verdict(r.CASES[1],changed,self.native))
 def test_malformed_counters_and_changed_ignored_checks_fail(self):
  for value in (True,-1,1.5):
   changed=self.positive();changed['opens']=value
   with self.assertRaises(p.Rejected):r.verdict(r.CASES[1],changed,self.native)
  changed=self.positive();changed['ignored_checks']=[]
  with self.assertRaises(p.Rejected):r.verdict(r.CASES[1],changed,self.native)
class BoundsAndPublication(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(dir=HERE);self.addCleanup(self.tmp.cleanup);self.out=Path(self.tmp.name)
 def record(self):return {'status':'completed','controls_passed':True,'routing_accepted':False,'comparison_eligible':False,'within_budget':True}
 def test_native_optin_and_reused_output_reject_before_preparation(self):
  with self.assertRaisesRegex(p.Rejected,'explicit'):d.experiment(self.out)
  with self.assertRaisesRegex(p.Rejected,'fresh'):d.experiment(self.out,run_native=True)
 def test_small_tree_cap_symlink_and_hardlink_reject(self):
  f=self.out/'x';f.write_bytes(b'abcd')
  with self.assertRaisesRegex(p.Rejected,'bounded'):d.bounded_tree(self.out,max_bytes=3)
  self.assertEqual(len(d.bounded_tree(self.out,max_bytes=4)),1)
  (self.out/'link').symlink_to(f)
  with self.assertRaises(p.Rejected):d.bounded_tree(self.out)
 def test_post_positive_publication_cancellation_invalidates(self):
  calls=0;record=self.record()
  def stable():
   nonlocal calls;calls+=1
   if calls==2:raise KeyboardInterrupt
  value=s.publish(self.out,record,stable,lambda:None);self.assertFalse(value['controls_passed']);self.assertEqual(value['status'],'cancelled');self.assertFalse(d.f.read_json(self.out/'summary.json')['controls_passed']);self.assertTrue(list(self.out.glob('invalidated-*-summary.json')))
 def test_summary_tamper_during_final_check_invalidates(self):
  calls=0;record=self.record()
  def stable():
   nonlocal calls;calls+=1
   if calls==2:p.save_json(self.out/'summary.json',{**record,'routing_accepted':True})
  value=s.publish(self.out,record,stable,lambda:None);self.assertFalse(value['controls_passed']);self.assertEqual(value['status'],'invalidated')
 def test_correction_write_failure_vacates_positive_and_partial(self):
  original=p.save_json;calls=0;record=self.record()
  def save(path,value):
   nonlocal calls;calls+=1
   if calls==1:original(path,value);raise OSError('after canonical positive')
   path.with_name(path.name+'.partial').write_text('partial');raise OSError('correction failed')
  with patch.object(p,'save_json',side_effect=save):s.publish(self.out,record,lambda:None,lambda:None)
  self.assertFalse((self.out/'summary.json').exists());self.assertFalse((self.out/'summary.json.partial').exists());self.assertFalse(record['controls_passed'])
 def test_budget_failure_after_final_readback_invalidates(self):
  record=self.record();calls=0
  def account():
   nonlocal calls;calls+=1
   if calls>=3:record['within_budget']=False
  value=s.publish(self.out,record,lambda:None,account);self.assertFalse(value['controls_passed']);self.assertEqual(value['status'],'invalidated')

class CommitAndPayload(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(dir=HERE);self.addCleanup(self.tmp.cleanup);self.out=Path(self.tmp.name).resolve()
 def test_exact_committed_bytes_accept_and_mismatch_reject(self):
  path=HERE/'recipe.py';name=str(path.relative_to(d.ROOT));files={name:p.sha(path)}
  class Response:stdout=path.read_bytes()
  with patch.object(d.subprocess,'run',return_value=Response())as run:
   self.assertEqual(d.verify_committed(files,'a'*40,lambda:10),files)
   self.assertEqual(run.call_args.args[0],['git','show','a'*40+':'+name]);self.assertEqual(run.call_args.kwargs['timeout'],5.)
  class Changed:stdout=b'uncommitted content'
  with patch.object(d.subprocess,'run',return_value=Changed()),self.assertRaisesRegex(p.Rejected,'commit exact'):d.verify_committed(files,'a'*40,lambda:10)
 def test_changed_live_bytes_and_exhausted_commit_budget_reject(self):
  name=str((HERE/'recipe.py').relative_to(d.ROOT))
  with patch.object(d.subprocess,'run')as run,self.assertRaisesRegex(p.Rejected,'changed'):d.verify_committed({name:'0'*64},'a'*40,lambda:10)
  run.assert_not_called()
  with patch.object(d.subprocess,'run')as run,self.assertRaisesRegex(p.Rejected,'budget'):d.verify_committed({name:p.sha(HERE/'recipe.py')},'a'*40,lambda:0)
  run.assert_not_called()
 def test_copy_projection_counts_four_payloads_without_large_allocation(self):
  values={case:b'abc'for case in r.CASES};self.assertEqual(d.projected_payload(7,3,values),28)
  with patch.object(d,'MAX_PROJECT_PAYLOAD_BYTES',27),self.assertRaisesRegex(p.Rejected,'projected'):d.projected_payload(7,3,values)
 def test_actual_aggregate_counts_candidate_and_native_inputs(self):
  for case in r.CASES:
   for name in ('candidate','native-drc-input'):
    path=self.out/case/name;path.mkdir(parents=True);(path/'x').write_bytes(b'ab')
  self.assertEqual(d.project_payload(self.out),8)
  with patch.object(d,'MAX_PROJECT_PAYLOAD_BYTES',7),self.assertRaisesRegex(p.Rejected,'aggregate'):d.project_payload(self.out)

if __name__=='__main__':unittest.main()
