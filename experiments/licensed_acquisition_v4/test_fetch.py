"""Offline controls for finite v3; ROOT also runs all unchanged legacy controls."""
from pathlib import Path
import copy,importlib.util,json,sys,tempfile,time,unittest
from unittest import mock
HERE=Path(__file__).absolute().parent
ROOT=next(p for p in HERE.parents if (p/'autorouter/pipeline.py').is_file())
sys.dont_write_bytecode=True;sys.path.insert(0,str(ROOT))
from experiments.licensed_acquisition_v1 import fetch as f
CACHED=ROOT/'.runs/ordinary-board-lead-003/static-source/ArdujoyC64'

class Controls(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(dir=HERE,prefix='test-scratch-');self.addCleanup(self.tmp.cleanup)
  self.root=Path(self.tmp.name);(self.root/'.git').mkdir();(self.root/'.git/HEAD').write_text('0'*40)
  (self.root/'.data').mkdir();(self.root/'.data/original').write_bytes(b'original');(self.root/'.runs').mkdir()
  self.here=self.root/f.profile('v4')['directory']
  for name,target in f.material_paths(self.root,self.here,'v4').items():
   source=Path(f.__file__) if name=='shared/fetch.py' else ROOT/'experiments/licensed_acquisition_v1/test_fetch.py' if name=='shared/test_fetch.py' else HERE/name
   target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(source.read_bytes())
  self.recorded={str(path.relative_to(self.root)):path.read_bytes() for path in f.material_paths(self.root,self.here,'v4').values()}
  self.plan,self.baseline,self.rows=f.load(self.here,'v4');self.small=f.inventory(self.root/'.data');self.out=self.root/'.runs/output'
 def git(self,root,args):
  return b'0'*40 if args==['rev-parse','HEAD'] else self.recorded[args[1].split(':',1)[1]]
 def transport(self,row,record,path,allowance,remaining):
  remaining();raw=f.bounded(CACHED/Path(row['source_path']).name);path.write_bytes(raw)
  record.update(received_bytes=len(raw),response_sha256=f.sha(raw),status='response_received');return raw
 def acquire(self):
  with mock.patch.object(f,'git',side_effect=self.git):
   runtime=f.committed(self.root,self.here,'v4')
   return f.acquire(self.root,self.here,self.out,self.plan,self.small,self.rows,runtime,time.monotonic(),self.transport,'v4')
 def test_fixed_census_preserves_v1_v2_v3_defaults(self):
  self.assertEqual((len(self.rows),sum(row['bytes'] for row in self.rows)),(6,135772))
  self.assertEqual((self.baseline['file_count'],self.baseline['bytes']),(364,40326569))
  self.assertEqual(f.profile()['destination_root'],'expansion004');self.assertEqual(f.profile('v2')['files'],14)
  self.assertTrue(all(row['sha256'] for row in self.rows));self.assertEqual(self.plan['capacity_change']['post_acquisition_expected_bytes'],40462341)
  with self.assertRaises(ValueError):f.load(self.here,'v1')
  with self.assertRaises(ValueError):f.validate_protocol(self.plan,self.baseline,'v2')
  with self.assertRaises(ValueError):f.profile('v5')
 def test_protocol_mutations_cannot_relax_identity_or_caps(self):
  for key,value in [('destination','devobordo/devboard.kicad_pcb'),('raw_url','https://example.invalid/board'),('mode','100755'),('commit','0'*40)]:
   changed=copy.deepcopy(self.plan);changed['projects'][0]['files'][0][key]=value
   with self.subTest(key=key),self.assertRaises(ValueError):f.validate_protocol(changed,self.baseline,'v4')
  changed=copy.deepcopy(self.plan);changed['caps']['max_requests']=7
  with self.assertRaises(ValueError):f.validate_protocol(changed,self.baseline,'v4')
 def test_wrapper_has_only_explicit_v4(self):
  spec=importlib.util.spec_from_file_location('__main__',HERE/'fetch.py')
  with mock.patch.object(f,'main') as main:spec.loader.exec_module(importlib.util.module_from_spec(spec))
  main.assert_called_once_with('v4',HERE)
 def test_shared_and_notice_recipe_material_are_committed(self):
  with mock.patch.object(f,'git',side_effect=self.git):runtime=f.committed(self.root,self.here,'v4')
  self.assertEqual(set(runtime['files']),set(f.MATERIAL)|{'shared/fetch.py','shared/test_fetch.py','native_snapshot.py'})
  def late(root,args):
   raw=self.git(root,args)
   if args[0]=='show' and args[1].endswith('native_snapshot.py'):(self.here/'native_snapshot.py').write_bytes(b'late change')
   return raw
  with mock.patch.object(f,'git',side_effect=late),self.assertRaisesRegex(ValueError,'after metadata'):f.committed(self.root,self.here,'v4')
 def test_exact_six_mock_payloads_are_unqualified_and_preserve_paths(self):
  result=self.acquire();self.assertEqual(result['status'],'acquired_unqualified');self.assertEqual(result['acquired_files'],6)
  self.assertEqual(result['acquired_bytes'],135772);self.assertEqual((self.root/'.data/original').read_bytes(),b'original')
  for flag in ('native_executed','engine_executed','dependency_closure_verified','independent_families_established'):self.assertIs(result[flag],False)
  for row in self.rows:self.assertEqual((self.root/'.data/expansion007'/row['destination']).read_bytes(),(CACHED/Path(row['source_path']).name).read_bytes())
  self.assertFalse((self.root/'.data/expansion004').exists())
 def test_notice_capture_and_existing_copy_helper_preserve_original_models(self):
  self.acquire();spec=importlib.util.spec_from_file_location('notice_draft',HERE/'native_snapshot.py');notice=importlib.util.module_from_spec(spec);spec.loader.exec_module(notice)
  before=f.inventory(self.root/'.data');files=notice.capture(self.root)
  self.assertEqual(len(files),8);self.assertEqual(sum(map(len,files.values())),142265)
  for dest,source in notice.COPIES.items():self.assertEqual(files[dest],files[source])
  original=(CACHED/'Ardujoy_HW.kicad_pcb').read_bytes();self.assertEqual(files['Ardujoy_HW/Ardujoy_HW.kicad_pcb'],original)
  self.assertEqual(original.count(b'(model '),7)
  from experiments.placement_handoff_native_v1.driver import copy_bytes
  copy_bytes(files,self.root/'.runs/native-snapshot')
  self.assertEqual(f.inventory(self.root/'.data'),before)
  (self.root/'.data/expansion007/ardujoy-c64/LICENSE').write_bytes(b'changed')
  with self.assertRaises(ValueError):notice.capture(self.root)
 def test_existing_destination_refused_without_transport(self):
  (self.root/'.data/expansion007').mkdir()
  with mock.patch.object(f,'git',side_effect=self.git):runtime=f.committed(self.root,self.here,'v4')
  with mock.patch.object(f,'fetch_one') as transport,self.assertRaisesRegex(ValueError,'fresh'):
   f.acquire(self.root,self.here,self.out,self.plan,self.small,self.rows,runtime,time.monotonic(),transport,'v4')
  transport.assert_not_called()
if __name__=='__main__':unittest.main(verbosity=2)
