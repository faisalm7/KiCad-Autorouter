"""Authored small-file acquisition controls; no HTTP, Native or real Git."""
import contextlib,copy,hashlib,importlib.util,io,json,sys,tempfile,time,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock
HERE=Path(__file__).absolute().parent
ROOT=next(p for p in HERE.parents if (p/'autorouter/pipeline.py').is_file())
sys.dont_write_bytecode=True;sys.path.insert(0,str(ROOT))
from experiments.licensed_acquisition_v1 import fetch as f

class FixedProtocol(unittest.TestCase):
 def setUp(self):self.plan,self.baseline,self.rows=f.load(HERE,'v8')
 def test_exact_five_source_files_and_finite_material(self):
  self.assertEqual((len(self.rows),sum(r['bytes'] for r in self.rows)),(5,347566))
  self.assertEqual({r['source_path'] for r in self.rows},{'CP2102.kicad_pcb','CP2102.kicad_sch','CP2102.kicad_pro','LICENSE','README.md'})
  self.assertEqual((self.baseline['file_count'],self.baseline['bytes']),(518,53919680))
  self.assertEqual(set(f.material_paths(ROOT,HERE,'v8')),set(f.MATERIAL)|{'shared/fetch.py','shared/test_fetch.py'})
  self.assertEqual(f.profile()['destination_root'],'expansion004');self.assertEqual(f.profile('v7')['bytes'],161071)
  for name in ('v9','../v8',True,None):
   with self.subTest(name=name),self.assertRaises(ValueError):f.profile(name)
  with self.assertRaises(ValueError):f.load(HERE,'v7')
 def test_identity_caps_scripts_and_destination_cannot_change(self):
  for key,value in [('raw_url','https://example.invalid/source'),('commit','0'*40),('repository','other/repo'),('destination','cp2102-uart/../other'),('mode','100755'),('bytes',True)]:
   changed=copy.deepcopy(self.plan);changed['projects'][0]['files'][0][key]=value
   with self.subTest(key=key),self.assertRaises(ValueError):f.validate_protocol(changed,self.baseline,'v8')
  for key,value in [('destination','.data/elsewhere'),('planned_files',6),('planned_bytes',347567)]:
   changed=copy.deepcopy(self.plan);changed[key]=value
   with self.subTest(key=key),self.assertRaises(ValueError):f.validate_protocol(changed,self.baseline,'v8')
  changed=copy.deepcopy(self.plan);changed['caps']['max_requests']=6
  with self.assertRaises(ValueError):f.validate_protocol(changed,self.baseline,'v8')
  changed=copy.deepcopy(self.plan);row=changed['projects'][0]['files'][0];row['source_path']='script.py';row['destination']='cp2102-uart/script.py';row['raw_url']='https://raw.githubusercontent.com/'+row['repository']+'/'+row['commit']+'/script.py'
  with self.assertRaisesRegex(ValueError,'script'):f.validate_protocol(changed,self.baseline,'v8')
 def test_wrapper_is_v8_default_shared_offline_contract(self):
  spec=importlib.util.spec_from_file_location('__main__',HERE/'fetch.py')
  with mock.patch.object(f,'main') as main:spec.loader.exec_module(importlib.util.module_from_spec(spec))
  main.assert_called_once_with('v8',HERE)
  stream=io.StringIO()
  with mock.patch.object(f,'inventory') as inv,mock.patch.object(f,'fetch_one',side_effect=AssertionError('no HTTP')),mock.patch.object(f,'committed',side_effect=AssertionError('no Git')),contextlib.redirect_stdout(stream):
   f.execute(SimpleNamespace(fetch=False,output='unused'),time.monotonic(),HERE,'v8')
  inv.assert_called_once_with(ROOT/'.data',self.baseline)
  self.assertEqual(json.loads(stream.getvalue())['network_requests'],0)

class AuthoredAcquisition(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(dir=HERE,prefix='test-scratch-');self.addCleanup(self.tmp.cleanup)
  self.root=Path(self.tmp.name);(self.root/'.data').mkdir();(self.root/'.data/original').write_bytes(b'original');(self.root/'.runs').mkdir();(self.root/'.git').mkdir();(self.root/'.git/HEAD').write_text('0'*40)
  self.here=self.root/f.profile('v8')['directory']
  for name,target in f.material_paths(self.root,self.here,'v8').items():
   source=ROOT/'experiments/licensed_acquisition_v1'/name.split('/',1)[1] if name.startswith('shared/') else HERE/name
   target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(source.read_bytes())
  plan=f.decode(f.bounded(HERE/'protocol.json'));baseline=f.inventory(self.root/'.data');self.payloads={}
  for row in plan['projects'][0]['files']:
   raw=('authored temporary '+row['source_path']+'\n').encode();self.payloads[row['source_path']]=raw;row.update(bytes=len(raw),sha256=f.sha(raw),git_blob_sha1=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest())
  total=sum(map(len,self.payloads.values()));plan.update(planned_bytes=total,baseline_sha256=f.sha((json.dumps(baseline,indent=2,sort_keys=True)+'\n').encode()));plan['projects'][0]['bytes']=total
  plan['capacity_change'].update(preexisting_files=1,preexisting_bytes=8,post_acquisition_expected_files=6,post_acquisition_expected_bytes=8+total)
  (self.here/'existing-data-inventory.json').write_text(json.dumps(baseline,indent=2,sort_keys=True)+'\n');(self.here/'protocol.json').write_text(json.dumps(plan,indent=2,sort_keys=True)+'\n')
  selected=copy.deepcopy(f.profile('v8'));selected.update(bytes=total,protocol_sha256=f.sha(f.bounded(self.here/'protocol.json')))
  patch=mock.patch.dict(f.PROFILES,{'v8':selected});patch.start();self.addCleanup(patch.stop)
  self.plan,self.baseline,self.rows=f.load(self.here,'v8');self.recorded={str(path.relative_to(self.root)):path.read_bytes() for path in f.material_paths(self.root,self.here,'v8').values()};self.out=self.root/'.runs/output';self.calls=[]
 def git(self,root,args):return b'0'*40 if args==['rev-parse','HEAD'] else self.recorded[args[1].split(':',1)[1]]
 def transport(self,row,rec,path,allowance,remaining):
  remaining();raw=self.payloads[row['source_path']];self.calls.append(row['source_path']);self.assertGreaterEqual(allowance,len(raw));path.write_bytes(raw);rec.update(status='response_received',received_bytes=len(raw),response_sha256=f.sha(raw),url='authored://no-network');return raw
 def acquire(self,transport=None):
  with mock.patch.object(f,'git',side_effect=self.git):
   runtime=f.committed(self.root,self.here,'v8');return f.acquire(self.root,self.here,self.out,self.plan,self.baseline,self.rows,runtime,time.monotonic(),transport or self.transport,'v8')
 def test_five_authored_payloads_preserve_sources_and_remain_unqualified(self):
  result=self.acquire();self.assertEqual(result['status'],'acquired_unqualified');self.assertEqual((result['acquired_files'],result['acquired_bytes']),(5,sum(map(len,self.payloads.values()))));self.assertEqual(len(self.calls),5)
  for row in self.rows:self.assertEqual((self.root/'.data/expansion011'/row['destination']).read_bytes(),self.payloads[row['source_path']])
  self.assertEqual((self.root/'.data/original').read_bytes(),b'original')
  for key in ('native_executed','engine_executed','dependency_closure_verified','redistribution_approved','independent_families_established'):self.assertIs(result[key],False)
 def test_payload_drift_keeps_failed_receipt_no_retry_or_fallback(self):
  def corrupt(row,rec,path,allowance,remaining):
   raw=self.transport(row,rec,path,allowance,remaining);raw=b'!'+raw[1:];path.write_bytes(raw);rec['response_sha256']=f.sha(raw);return raw
  with self.assertRaisesRegex(ValueError,'payload hash'):self.acquire(corrupt)
  self.assertEqual(len(self.calls),1);self.assertEqual(f.decode(f.bounded(self.out/'receipt.json'))['status'],'failed');self.assertEqual((self.root/'.data/original').read_bytes(),b'original');self.assertTrue((self.out/'response-000.bin').exists())
 def test_existing_destination_and_symlink_refuse_without_transport(self):
  target=self.root/'.data/expansion011';target.mkdir()
  with self.assertRaisesRegex(ValueError,'fresh'):self.acquire()
  self.assertEqual(self.calls,[]);target.rmdir();target.symlink_to(self.root/'.data',target_is_directory=True)
  with self.assertRaisesRegex(ValueError,'symlink'):self.acquire()
  self.assertEqual(self.calls,[])
 def test_late_material_drift_invalidates_failed_run(self):
  target=self.here/'STATIC_AUDIT.md';original=target.read_bytes()
  def late(row,rec,path,allowance,remaining):
   raw=self.transport(row,rec,path,allowance,remaining);target.write_bytes(original+b'changed');return raw
  with self.assertRaises(ValueError):self.acquire(late)
  self.assertEqual(f.decode(f.bounded(self.out/'receipt.json'))['status'],'failed');self.assertEqual((self.root/'.data/original').read_bytes(),b'original')
 def test_preexisting_source_drift_refused_before_transport(self):
  (self.root/'.data/original').write_bytes(b'changed')
  with self.assertRaisesRegex(ValueError,'inventory changed'):self.acquire()
  self.assertEqual(self.calls,[]);self.assertEqual(f.decode(f.bounded(self.out/'receipt.json'))['status'],'failed')
if __name__=='__main__':unittest.main(verbosity=2)
