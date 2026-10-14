"""Focused cached-source controls; no HTTP/native or real Git execution."""
import copy,json,sys,tempfile,time,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock
HERE=Path(__file__).absolute().parent
ROOT=next(p for p in HERE.parents if (p/'autorouter/pipeline.py').is_file())
sys.dont_write_bytecode=True;sys.path.insert(0,str(ROOT))
from experiments.licensed_acquisition_v1 import fetch as f
from experiments.licensed_acquisition_v6.cache_transport import Cache
from experiments.licensed_acquisition_v7 import fetch as driver,native_snapshot
PROPOSED={'bytes': 161071, 'destination_root': 'expansion010', 'directory': 'experiments/licensed_acquisition_v7', 'files': 5, 'identities': [('push-button-led', 'gurusaeth12/push-button-led-kicad', '29c46b7c03d2afd9fe3a58fe2070309b12f94b42')], 'output_prefix': 'licensed-acquisition-010-run-', 'protocol_sha256': '8a1d89b9f924b1d25d3ff9af855a8e486ced7d01046982fe70ab0322765ab42e'}
KW={'repository':'gurusaeth12/push-button-led-kicad','commit':'29c46b7c03d2afd9fe3a58fe2070309b12f94b42','file_count':5,'profile_metadata_name':'cache-source-profile.json','transport_name':'fixed-led-verified-cached-response-v1'}
class Controls(unittest.TestCase):
 def setUp(self):
  self.registration=mock.patch.dict(f.PROFILES,{'v7':PROPOSED});self.registration.start();self.addCleanup(self.registration.stop)
  self.tmp=tempfile.TemporaryDirectory(dir=ROOT/'.runs/led-profile-preparation-001',prefix='test-scratch-');self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
  (self.root/'.data').mkdir();(self.root/'.data/original').write_bytes(b'original');(self.root/'.runs').mkdir();self.plan,self.baseline,self.rows=f.load(HERE,'v7')
  names=set(self.plan['cache_reuse']['metadata'])|{x['raw_path'] for x in self.plan['cache_reuse']['files'].values()}
  for name in names:
   path=self.root/f.safe(name);path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(f.bounded(ROOT/name))
  self.cache=Cache(self.root,self.plan,self.rows,**KW)
 def acquire(self,transport=None):
  baseline=f.inventory(self.root/'.data');runtime={'head':'0'*40,'files':{},'git_identity':{}}
  with mock.patch.object(f,'committed',return_value=runtime),mock.patch.object(f,'material'):
   return f.acquire(self.root,HERE,self.root/'.runs/result',self.plan,baseline,self.rows,runtime,time.monotonic(),transport or self.cache.transport,'v7')
 def test_fixed_identity_path_caps_and_prior_contracts(self):
  self.assertEqual((len(self.rows),sum(x['bytes'] for x in self.rows)),(5,161071));self.assertEqual((self.baseline['file_count'],self.baseline['bytes']),(389,41350999))
  self.assertEqual((f.profile('v1')['bytes'],f.profile('v6')['bytes']),(5016162,741742))
  with self.assertRaises(ValueError):f.profile('v8')
  changed=copy.deepcopy(self.plan);changed['caps']['max_requests']=6
  with self.assertRaises(ValueError):f.validate_protocol(changed,self.baseline,'v7')
  for key,val in [('raw_url','https://example.invalid/board'),('destination','push-button-led/../other'),('commit','0'*40),('mode','100755'),('bytes',0)]:
   changed=copy.deepcopy(self.plan);changed['projects'][0]['files'][0][key]=val
   with self.subTest(key=key),self.assertRaises(ValueError):f.validate_protocol(changed,self.baseline,'v7')
 def test_plan_only_reads_real_frozen_baseline_without_network_or_git(self):
  before=f.inventory(ROOT/'.data')
  with mock.patch.object(f,'fetch_one',side_effect=AssertionError('no HTTP')),mock.patch.object(f,'committed',side_effect=AssertionError('no Git')):
   result=driver.execute(SimpleNamespace(reuse_cache=False,output=''),time.monotonic())
  self.assertEqual((result['planned_files'],result['planned_bytes'],result['post_acquisition_data_files']),(5,161071,394));self.assertTrue(result['cache_lineage_verified']);self.assertEqual(f.inventory(ROOT/'.data'),before)
 def test_cached_acquisition_preserves_bytes_no_network_and_retains_receipt(self):
  with mock.patch.object(f,'fetch_one',side_effect=AssertionError('no HTTP')):result=self.acquire()
  self.assertEqual((result['status'],result['acquired_files'],result['acquired_bytes']),('acquired_unqualified',5,161071));self.assertEqual((self.root/'.data/original').read_bytes(),b'original')
  self.assertTrue(all(r['network_requests']==r['network_bytes']==0 and r['transport']=='fixed-led-verified-cached-response-v1' for r in result['requests']))
  for row in self.rows:f.payload(row,f.bounded(self.root/'.data/expansion010'/row['destination']))
  self.assertFalse(result['native_executed']);self.assertFalse(result['engine_executed'])
 def test_stale_raw_metadata_path_and_transport_cap(self):
  name=next(iter(self.plan['cache_reuse']['files'].values()))['raw_path'];path=self.root/name;raw=path.read_bytes();path.write_bytes(raw+b' ')
  with self.assertRaises(ValueError):self.cache.verify()
  path.write_bytes(raw);meta=next(iter(self.plan['cache_reuse']['metadata']));path=self.root/meta;raw=path.read_bytes();path.write_bytes(b'changed')
  with self.assertRaises(ValueError):self.cache.verify()
  path.write_bytes(raw);changed=copy.deepcopy(self.plan);changed['cache_reuse']['files'][self.rows[0]['destination']]['raw_path']='../outside'
  with self.assertRaises(ValueError):Cache(self.root,changed,self.rows,**KW)
  with self.assertRaisesRegex(ValueError,'allowance'):self.cache.transport(self.rows[0],{},self.root/'.runs/raw',self.rows[0]['bytes']-1,lambda:300)
  self.assertFalse((self.root/'.runs/raw').exists())
 def test_unknown_rows_preexisting_destination_and_cache_identity_reject(self):
  row=copy.deepcopy(self.rows[0]);row['destination']='other/file'
  with self.assertRaises(ValueError):self.cache.transport(row,{},self.root/'.runs/raw',f.CAP,lambda:300)
  with self.assertRaises(ValueError):Cache(self.root,self.plan,self.rows,**{**KW,'repository':'other/repo'})
  (self.root/'.data/expansion010').mkdir()
  with self.assertRaisesRegex(ValueError,'fresh'):self.acquire()
  self.assertFalse((self.root/'.runs/result').exists())
 def test_post_acquisition_cache_change_invalidates_positive_receipt(self):
  result=self.acquire();info=next(iter(self.plan['cache_reuse']['files'].values()));path=self.root/info['raw_path'];path.write_bytes(path.read_bytes()+b' ')
  with self.assertRaises(ValueError):f.publish(self.root/'.runs/result',result,self.cache.verify,lambda:300)
  receipt=f.decode(f.bounded(self.root/'.runs/result/receipt.json'));self.assertEqual(receipt['status'],'failed');self.assertTrue((self.root/'.runs/result/receipt.invalidated.json').exists());self.assertEqual((self.root/'.data/original').read_bytes(),b'original')
 def test_capture_original_and_notice_packet_source_unchanged(self):
  self.acquire();before=f.inventory(self.root/'.data');files=native_snapshot.capture(self.root)
  self.assertEqual((len(files),sum(map(len,files.values()))),(7,165201))
  for dest,origin in native_snapshot.COPIES.items():self.assertEqual(files[dest],files[origin])
  self.assertEqual(len([n for n in files if n.endswith('.kicad_sch')]),1);self.assertIn(b'20260206',files['PushButtonLed.kicad_pcb']);self.assertIn(b'missing_tuning_profile',files['PushButtonLed.kicad_pro']);self.assertIn(b'KICAD10_3DMODEL_DIR',files['PushButtonLed.kicad_pcb'])
  from experiments.placement_handoff_native_v1.driver import copy_bytes
  copy_bytes(files,self.root/'.runs/packet');self.assertEqual(f.inventory(self.root/'.data'),before)
 def test_capture_missing_managed_source_stale_or_extra_rules_fails(self):
  with self.assertRaises((ValueError,FileNotFoundError)):native_snapshot.capture(self.root)
  self.acquire();source=self.root/'.data/expansion010/push-button-led';path=source/'LICENSE';raw=path.read_bytes();path.write_bytes(raw+b' ')
  with self.assertRaises(ValueError):native_snapshot.capture(self.root)
  path.write_bytes(raw);(source/'PushButtonLed.kicad_dru').write_bytes(b'(version 1)')
  with self.assertRaises(ValueError):native_snapshot.capture(self.root)
if __name__=='__main__':unittest.main(verbosity=2)
