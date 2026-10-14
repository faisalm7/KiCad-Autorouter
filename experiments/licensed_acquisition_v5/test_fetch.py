"""Cache-dependent offline acquisition controls; not native or clean-install proof."""
from pathlib import Path
import copy,importlib.util,sys,tempfile,time,unittest
from unittest import mock
HERE=Path(__file__).absolute().parent
ROOT=next(p for p in HERE.parents if (p/'autorouter/pipeline.py').is_file())
sys.dont_write_bytecode=True;sys.path.insert(0,str(ROOT))
from experiments.licensed_acquisition_v1 import fetch as f
CACHED=ROOT/'.runs/modern-board-leads-001/inputs/nushackers__hsp-pcb-intro'

class Controls(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(dir=HERE,prefix='test-scratch-');self.addCleanup(self.tmp.cleanup)
  self.root=Path(self.tmp.name);(self.root/'.git').mkdir();(self.root/'.git/HEAD').write_text('0'*40)
  (self.root/'.data').mkdir();(self.root/'.data/original').write_bytes(b'original');(self.root/'.runs').mkdir()
  self.here=self.root/f.profile('v5')['directory']
  for name,target in f.material_paths(self.root,self.here,'v5').items():
   source=Path(f.__file__) if name=='shared/fetch.py' else ROOT/'experiments/licensed_acquisition_v1/test_fetch.py' if name=='shared/test_fetch.py' else HERE/name
   target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(source.read_bytes())
  self.recorded={str(path.relative_to(self.root)):path.read_bytes() for path in f.material_paths(self.root,self.here,'v5').values()}
  self.plan,self.baseline,self.rows=f.load(self.here,'v5');self.small=f.inventory(self.root/'.data');self.out=self.root/'.runs/output'
 def git(self,root,args):
  return b'0'*40 if args==['rev-parse','HEAD'] else self.recorded[args[1].split(':',1)[1]]
 def transport(self,row,record,path,allowance,remaining):
  remaining();raw=f.bounded(CACHED/f.safe(row['source_path']));path.write_bytes(raw)
  record.update(received_bytes=len(raw),response_sha256=f.sha(raw),status='response_received');return raw
 def acquire(self):
  with mock.patch.object(f,'git',side_effect=self.git):
   runtime=f.committed(self.root,self.here,'v5')
   return f.acquire(self.root,self.here,self.out,self.plan,self.small,self.rows,runtime,time.monotonic(),self.transport,'v5')
 def test_fixed_census_and_legacy_profile_contracts(self):
  self.assertEqual((len(self.rows),sum(r['bytes'] for r in self.rows)),(9,146916))
  self.assertEqual((self.baseline['file_count'],self.baseline['bytes']),(370,40462341))
  self.assertEqual(f.profile()['destination_root'],'expansion004');self.assertEqual(f.profile('v4')['bytes'],135772)
  self.assertEqual(self.plan['capacity_change']['post_acquisition_expected_files'],379)
  self.assertEqual(self.plan['capacity_change']['post_acquisition_expected_bytes'],40609257)
  with self.assertRaises(ValueError):f.load(self.here,'v1')
  with self.assertRaises(ValueError):f.validate_protocol(self.plan,self.baseline,'v4')
  with self.assertRaises(ValueError):f.profile('v9')
 def test_protocol_cannot_relax_identity_or_caps(self):
  for key,value in [('destination','nus-usb-led/other'),('raw_url','https://example.invalid/board'),('mode','100755'),('commit','0'*40),('bytes',0)]:
   changed=copy.deepcopy(self.plan);changed['projects'][0]['files'][0][key]=value
   with self.subTest(key=key),self.assertRaises(ValueError):f.validate_protocol(changed,self.baseline,'v5')
  changed=copy.deepcopy(self.plan);changed['caps']['max_requests']=10
  with self.assertRaises(ValueError):f.validate_protocol(changed,self.baseline,'v5')
 def test_wrapper_selects_only_v5(self):
  spec=importlib.util.spec_from_file_location('__main__',HERE/'fetch.py')
  with mock.patch.object(f,'main') as main:spec.loader.exec_module(importlib.util.module_from_spec(spec))
  main.assert_called_once_with('v5',HERE)
 def test_shared_controller_and_notice_recipe_material_are_bound(self):
  with mock.patch.object(f,'git',side_effect=self.git):runtime=f.committed(self.root,self.here,'v5')
  self.assertEqual(set(runtime['files']),set(f.MATERIAL)|{'shared/fetch.py','shared/test_fetch.py','native_snapshot.py'})
  def late(root,args):
   raw=self.git(root,args)
   if args[0]=='show' and args[1].endswith('native_snapshot.py'):(self.here/'native_snapshot.py').write_bytes(b'late change')
   return raw
  with mock.patch.object(f,'git',side_effect=late),self.assertRaisesRegex(ValueError,'after metadata'):f.committed(self.root,self.here,'v5')
 def test_exact_nine_mock_payloads_preserve_paths_and_remain_unqualified(self):
  result=self.acquire();self.assertEqual(result['status'],'acquired_unqualified');self.assertEqual((result['acquired_files'],result['acquired_bytes']),(9,146916))
  self.assertEqual((self.root/'.data/original').read_bytes(),b'original')
  for key in ('native_executed','engine_executed','dependency_closure_verified','independent_families_established'):self.assertIs(result[key],False)
  for row in self.rows:self.assertEqual((self.root/'.data/expansion008'/row['destination']).read_bytes(),(CACHED/f.safe(row['source_path'])).read_bytes())
  self.assertFalse((self.root/'.data/expansion007').exists())
 def notice(self):
  spec=importlib.util.spec_from_file_location('notice_draft',self.here/'native_snapshot.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
 def test_native_snapshot_preserves_topology_rules_areas_and_models(self):
  self.acquire();notice=self.notice();before=f.inventory(self.root/'.data');files=notice.capture(self.root)
  self.assertEqual((len(files),sum(map(len,files.values()))),(11,156713))
  for dest,source in notice.COPIES.items():self.assertEqual(files[dest],files[source])
  self.assertEqual(files['src/fp-lib-table'],(CACHED/'src/fp-lib-table').read_bytes())
  self.assertIn(b'${KIPRJMOD}/footprints/usb_led.pretty',files['src/fp-lib-table'])
  original=(CACHED/'src/usb_led.kicad_pcb').read_bytes();self.assertEqual(files['src/usb_led.kicad_pcb'],original)
  self.assertEqual(original.count(b'(model '),6);self.assertIn(b'(copperpour not_allowed)',original);self.assertIn(b'knockout',original)
  from experiments.placement_handoff_native_v1.driver import copy_bytes
  copy_bytes(files,self.root/'.runs/native-snapshot');self.assertEqual(f.inventory(self.root/'.data'),before)
  target=self.root/'.runs/native-snapshot/src/footprints/usb_led.pretty/SW_Push_1P1T_XKB_TS-1187A.kicad_mod'
  self.assertEqual(target.read_bytes(),files['src/footprints/usb_led.pretty/SW_Push_1P1T_XKB_TS-1187A.kicad_mod'])
 def test_notice_capture_rejects_changed_footprint_and_added_file(self):
  self.acquire();notice=self.notice();source=self.root/'.data/expansion008/nus-usb-led'
  path=source/'src/footprints/usb_led.pretty/SW_Push_1P1T_XKB_TS-1187A.kicad_mod';raw=path.read_bytes();path.write_bytes(raw+b' ')
  with self.assertRaises(ValueError):notice.capture(self.root)
  path.write_bytes(raw);(source/'unexpected').write_bytes(b'unknown')
  with self.assertRaises(ValueError):notice.capture(self.root)
 def test_existing_destination_refused_without_transport(self):
  (self.root/'.data/expansion008').mkdir()
  with mock.patch.object(f,'git',side_effect=self.git):runtime=f.committed(self.root,self.here,'v5')
  transport=mock.Mock()
  with self.assertRaisesRegex(ValueError,'fresh'):
   f.acquire(self.root,self.here,self.out,self.plan,self.small,self.rows,runtime,time.monotonic(),transport,'v5')
  transport.assert_not_called()
if __name__=='__main__':unittest.main(verbosity=2)
