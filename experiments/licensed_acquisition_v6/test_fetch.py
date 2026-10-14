"""Cache-dependent pure controls; no native, network or real Git execution."""
import copy,json,sys,tempfile,time,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock
HERE=Path(__file__).absolute().parent
ROOT=next(p for p in HERE.parents if (p/'autorouter/pipeline.py').is_file())
sys.dont_write_bytecode=True;sys.path.insert(0,str(ROOT))
from experiments.licensed_acquisition_v1 import fetch as f
from experiments.licensed_acquisition_v6 import cache_transport,native_snapshot
PROPOSED={'protocol_sha256':'876b0b80dee374bd17606d3537568358b94ce689ece4c956bfd61f2e4ea89ff8','destination_root':'expansion009','directory':'experiments/licensed_acquisition_v6','output_prefix':'licensed-acquisition-009-run-','files':10,'bytes':741742,'identities':[('als311-clock','ugolnikovE/als311-clock','494ab6baf40746d313fe11379425900ebe97c319')]}
class Controls(unittest.TestCase):
 def setUp(self):
  self.registration=mock.patch.dict(f.PROFILES,{'v6':PROPOSED});self.registration.start();self.addCleanup(self.registration.stop)
  self.tmp=tempfile.TemporaryDirectory(dir=ROOT/'.runs/clock-profile-preparation-001',prefix='test-scratch-');self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
  (self.root/'.data').mkdir();(self.root/'.data/original').write_bytes(b'original');(self.root/'.runs').mkdir();self.plan,self.baseline,self.rows=f.load(HERE,'v6')
  names=set(self.plan['cache_reuse']['metadata'])|{x['raw_path'] for x in self.plan['cache_reuse']['files'].values()}
  for name in names:
   path=self.root/f.safe(name);path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(f.bounded(ROOT/name))
  self.cache=cache_transport.Cache(self.root,self.plan,self.rows)
 def acquire(self):
  baseline=f.inventory(self.root/'.data');runtime={'head':'0'*40,'files':{},'git_identity':{}}
  with mock.patch.object(f,'committed',return_value=runtime),mock.patch.object(f,'material'):
   return f.acquire(self.root,HERE,self.root/'.runs/result',self.plan,baseline,self.rows,runtime,time.monotonic(),self.cache.transport,'v6')
 def test_profile_census_caps_and_prior_contracts(self):
  self.assertEqual((len(self.rows),sum(x['bytes'] for x in self.rows)),(10,741742));self.assertEqual((self.baseline['file_count'],self.baseline['bytes']),(379,40609257))
  self.assertEqual((f.profile('v1')['bytes'],f.profile('v5')['bytes']),(5016162,146916))
  with self.assertRaises(ValueError):f.profile('v9')
  changed=copy.deepcopy(self.plan);changed['caps']['max_requests']=11
  with self.assertRaises(ValueError):f.validate_protocol(changed,self.baseline,'v6')
  for key,val in [('raw_url','https://example.invalid/board'),('destination','als311-clock/other'),('commit','0'*40),('mode','100755')]:
   changed=copy.deepcopy(self.plan);changed['projects'][0]['files'][0][key]=val
   with self.subTest(key=key),self.assertRaises(ValueError):f.validate_protocol(changed,self.baseline,'v6')
 def test_actual_cached_acquisition_calls_no_network_preserves_original(self):
  with mock.patch.object(f,'fetch_one',side_effect=AssertionError('no HTTP')):result=self.acquire()
  self.assertEqual(result['status'],'acquired_unqualified');self.assertEqual((result['acquired_files'],result['acquired_bytes']),(10,741742));self.assertEqual((self.root/'.data/original').read_bytes(),b'original')
  self.assertTrue(all(r['network_requests']==r['network_bytes']==0 and r['status']=='cached_payload_reused' for r in result['requests']))
  for row in self.rows:f.payload(row,f.bounded(self.root/'.data/expansion009'/row['destination']))
  self.assertIs(result['native_executed'],False);self.assertIs(result['engine_executed'],False)
 def test_changed_raw_cache_and_metadata_fail_before_payload(self):
  name=next(iter(self.plan['cache_reuse']['files'].values()))['raw_path'];path=self.root/name;raw=path.read_bytes();path.write_bytes(raw+b' ')
  with self.assertRaises(ValueError):self.cache.verify()
  path.write_bytes(raw);meta=next(iter(self.plan['cache_reuse']['metadata']));(self.root/meta).write_bytes(b'changed')
  with self.assertRaises(ValueError):self.cache.verify()
 def test_unknown_row_or_preexisting_destination_never_overwrites(self):
  row=copy.deepcopy(self.rows[0]);row['destination']='other/file'
  with self.assertRaises(ValueError):self.cache.transport(row,{},self.root/'.runs/raw',f.CAP,lambda:300)
  self.assertFalse((self.root/'.runs/raw').exists());(self.root/'.data/expansion009').mkdir();runtime={}
  with self.assertRaisesRegex(ValueError,'fresh'):f.acquire(self.root,HERE,self.root/'.runs/result',self.plan,f.inventory(self.root/'.data'),self.rows,runtime,time.monotonic(),self.cache.transport,'v6')
 def test_capture_complete_hierarchy_and_notice_topology(self):
  self.acquire();before=f.inventory(self.root/'.data');files=native_snapshot.capture(self.root)
  self.assertEqual((len(files),sum(map(len,files.values()))),(12,753605))
  for dest,origin in native_snapshot.COPIES.items():self.assertEqual(files[dest],files[origin])
  self.assertEqual(len([n for n in files if n.endswith('.kicad_sch')]),5);self.assertEqual(files['hardware/NOTICE'],f.bounded(self.root/'.data/expansion009/als311-clock/hardware/NOTICE'))
  self.assertIn(b'LOGO',files['hardware/hardware.kicad_pcb']);self.assertIn(b'USB_C no silk',files['hardware/hardware.kicad_pcb'])
  from experiments.placement_handoff_native_v1.driver import copy_bytes
  copy_bytes(files,self.root/'.runs/packet');self.assertEqual(f.inventory(self.root/'.data'),before)
 def test_capture_rejects_missing_sheet_extra_rule_or_changed_notice(self):
  self.acquire();source=self.root/'.data/expansion009/als311-clock';sheet=source/'hardware/ds3231.kicad_sch';raw=sheet.read_bytes();sheet.write_bytes(raw+b' ')
  with self.assertRaises(ValueError):native_snapshot.capture(self.root)
  sheet.write_bytes(raw);(source/'hardware/hardware.kicad_dru').write_bytes(b'(version 1)')
  with self.assertRaises(ValueError):native_snapshot.capture(self.root)
 def test_capture_missing_managed_source_does_not_fall_back_to_cache(self):
  with self.assertRaises((ValueError,FileNotFoundError)):native_snapshot.capture(self.root)
if __name__=='__main__':unittest.main(verbosity=2)
