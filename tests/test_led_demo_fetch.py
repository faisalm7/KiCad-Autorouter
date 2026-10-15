"""Public LED lifecycle tests; synthetic transport fixture, no cache/network/native."""
import copy,hashlib,json,tempfile,time,unittest
from pathlib import Path
from unittest import mock
from scripts import fetch_led_demo as demo

class LedFetchControls(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(dir=demo.ROOT/'tests',prefix='led-fetch-test-');self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
  for name in demo.MATERIAL:
   q=self.root/name;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes((demo.ROOT/name).read_bytes())
  self.public_rows=copy.deepcopy(demo.ROWS);rows=copy.deepcopy(demo.ROWS);self.payloads={}
  for row in rows:
   prefix=('pure transport fixture '+row['source_path']+'\n').encode();raw=prefix+b'x'*(row['bytes']-len(prefix));self.payloads[row['source_path']]=raw
   row['sha256']=hashlib.sha256(raw).hexdigest();row['git_blob_sha1']=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
  patch=mock.patch.object(demo,'ROWS',tuple(rows));patch.start();self.addCleanup(patch.stop)
  self.called=[]
 def transport(self,row,record,path,allowance,remaining):
  remaining();self.called.append(row['raw_url']);raw=self.payloads[row['source_path']]
  with path.open('xb') as stream:stream.write(raw)
  record.update(received_bytes=len(raw),response_sha256=demo.shared.sha(raw),url=row['raw_url'],status='response_received',http_status=200,wall_seconds=0.0)
  return raw
 def fetch(self,transport=None):return demo.fetch_demo('.data/led-demo-test',fetch=True,root=self.root,transport=transport or self.transport)
 def test_fixed_public_rows_equal_frozen_v7_identity(self):
  rows=json.loads((demo.ROOT/'experiments/licensed_acquisition_v7/protocol.json').read_text())['projects'][0]['files'];keys=('source_path','repository','commit','mode','raw_url','bytes','sha256','git_blob_sha1')
  self.assertEqual([{k:r[k] for k in keys} for r in self.public_rows],[{k:r[k] for k in keys} for r in rows]);self.assertEqual(sum(r['bytes'] for r in self.public_rows),161071)
 def test_sunx_plan_keeps_existing_prl_and_complete_notice_packet(self):
  cfg=demo.fixed_profile('sunx-v21');rows=cfg['rows'];by={r['source_path']:r for r in rows}
  self.assertEqual((len(rows),sum(r['bytes'] for r in rows)),(6,190664))
  self.assertIn('sunx/sunx.kicad_prl',by)
  self.assertEqual(by['sunx/sunx.kicad_prl']['sha256'],'06b428e24ace7b1ebd945ffed42ab7593611d402902643a66ca172456c34a3f6')
  self.assertEqual(cfg['native_packet_files'],len(rows)+len(cfg['native_packet_notice_copies']))
  self.assertEqual(cfg['native_packet_bytes'],cfg['bytes']+sum(by[n]['bytes'] for n in cfg['native_packet_notice_copies'].values()))
  self.assertEqual((cfg['max_requests'],cfg['network_byte_cap']),(6,190670))
  result=demo.fetch_demo(cfg['default_output'],profile_id='sunx-v21',root=self.root,transport=lambda *a:self.fail('offline plan transported'))
  self.assertEqual((result['action'],result['network_requests'],result['planned_network_requests']),('plan_only',0,6))
  self.assertFalse((self.root/'.data').exists())
  from experiments.original_project_native_v1 import driver
  self.assertEqual(driver.CASES['sunx-v21'],('portable-demo',cfg['board_path'],cfg['commit'],None))
  self.assertIn('sunx-v21',driver.REFILLED_ORIGINALS)
 def test_clean_checkout_plan_has_no_data_cache_git_or_network_requirement(self):
  result=demo.fetch_demo('.data/led-demo-test',root=self.root,transport=lambda *a:(_ for _ in ()).throw(AssertionError('no network')))
  self.assertEqual(result['action'],'plan_only');self.assertEqual(result['network_requests'],0);self.assertFalse((self.root/'.data').exists());self.assertFalse((self.root/'.git').exists());self.assertFalse((self.root/'.runs').exists())
 def test_exact_five_files_and_receipt_in_clean_checkout(self):
  result=self.fetch();out=self.root/'.data/led-demo-test'
  self.assertEqual((result['status'],result['new_network_requests'],result['received_bytes']),('acquired_unqualified',5,161071));self.assertTrue(result['source_files_exact']);self.assertTrue(result['within_budget']);self.assertFalse(result['accepted']);self.assertFalse(result['native_accepted']);self.assertEqual(len(self.called),5)
  self.assertEqual(set(demo.shared.inventory(out)['files']),{'project/'+r['source_path'] for r in demo.ROWS}|{'result.json'})
  for name,raw in self.payloads.items():self.assertEqual((out/'project'/name).read_bytes(),raw)
  self.assertEqual(demo.publication.read_json(out/'result.json'),result)
 def test_unsafe_or_preexisting_output_preserves_existing_source(self):
  for name in ['../outside','.data/../led-demo-test','.data/other','.data/led-demo-A','/tmp/led-demo-test','.data/led-demo-test/child']:
   with self.subTest(name=name),self.assertRaises(ValueError):demo.fetch_demo(name,fetch=True,root=self.root,transport=self.transport)
  out=self.root/'.data/led-demo-test';out.mkdir(parents=True);(out/'original').write_bytes(b'owner')
  with self.assertRaisesRegex(ValueError,'exists'):self.fetch()
  self.assertEqual((out/'original').read_bytes(),b'owner');self.assertFalse(self.called)
 def test_wrong_hash_or_oversize_retains_failure_and_stops_requests(self):
  for mode in ['hash','size']:
   with self.subTest(mode=mode):
    name='.data/led-demo-'+mode
    def bad(row,record,path,allowance,remaining):
     raw=self.payloads[row['source_path']];raw=(b'x'+raw[1:]) if mode=='hash' else raw+b'x'
     with path.open('xb') as stream:stream.write(raw)
     record.update(received_bytes=len(raw),response_sha256=demo.shared.sha(raw));return raw
    result=demo.fetch_demo(name,fetch=True,root=self.root,transport=bad)
    self.assertEqual(result['status'],'failed');self.assertFalse(result['source_files_exact']);self.assertEqual(result['new_network_requests'],1);self.assertIn('payload',result['first_failure']);self.assertTrue((self.root/name/'project/LICENSE').exists());self.assertFalse((self.root/name/'project/README.md').exists())
 def test_changed_completed_source_invalidates_receipt_and_keeps_first_cause(self):
  def stale(row,record,path,allowance,remaining):
   raw=self.transport(row,record,path,allowance,remaining)
   if len(self.called)==2:(self.root/'.data/led-demo-test/project/LICENSE').write_bytes(b'changed')
   return raw
  with self.assertRaises(ValueError):self.fetch(stale)
  result=demo.publication.read_json(self.root/'.data/led-demo-test/result.json');self.assertEqual(result['status'],'invalidated');self.assertFalse(result['source_files_exact']);self.assertIn('completed source file changed',result['first_failure']);self.assertEqual(len(self.called),2)
 def test_changed_runtime_source_fails_before_third_get(self):
  def stale(row,record,path,allowance,remaining):
   raw=self.transport(row,record,path,allowance,remaining)
   if len(self.called)==2:(self.root/demo.MATERIAL[0]).write_bytes(b'changed')
   return raw
  with self.assertRaises(ValueError):self.fetch(stale)
  result=demo.publication.read_json(self.root/'.data/led-demo-test/result.json');self.assertFalse(result['accepted']);self.assertIn('implementation changed',result['first_failure']);self.assertEqual(len(self.called),2)
 def test_replaced_directory_never_writes_replacement_or_corrects_it(self):
  moved=self.root/'retained-output'
  def replace(row,record,path,allowance,remaining):
   out=self.root/'.data/led-demo-test';out.rename(moved);out.mkdir();(out/'owner').write_bytes(b'owner')
   return self.transport(row,record,path,allowance,remaining)
  with self.assertRaises(Exception):self.fetch(replace)
  self.assertEqual(list((self.root/'.data/led-demo-test').iterdir()),[self.root/'.data/led-demo-test/owner']);self.assertEqual((self.root/'.data/led-demo-test/owner').read_bytes(),b'owner');self.assertFalse((moved/'project/LICENSE').exists())
 def test_cancelled_partial_payload_is_retained_and_never_accepted(self):
  def cancel(row,record,path,allowance,remaining):
   with path.open('xb') as stream:stream.write(b'partial')
   record.update(received_bytes=7,response_sha256=demo.shared.sha(b'partial'));raise KeyboardInterrupt('deliberate cancellation')
  result=self.fetch(cancel);self.assertEqual(result['status'],'cancelled');self.assertFalse(result['source_files_exact']);self.assertFalse(result['accepted']);self.assertEqual(result['new_network_requests'],1);self.assertEqual((self.root/'.data/led-demo-test/project/LICENSE').read_bytes(),b'partial')
 def test_mutating_publisher_cannot_leave_positive_receipt(self):
  original=demo.publication.p.save_json;calls=[]
  def mutate(path,record):
   original(path,record);calls.append(path)
   if len(calls)==1:
    changed=demo.publication.read_json(path);changed['status']='acquired_unqualified';changed['accepted']=True;original(path,changed)
  with mock.patch.object(demo.publication.p,'save_json',side_effect=mutate):result=self.fetch()
  receipt=demo.publication.read_json(self.root/'.data/led-demo-test/result.json');self.assertEqual(receipt['status'],'invalidated');self.assertFalse(receipt['accepted']);self.assertEqual(receipt,result);self.assertTrue(list((self.root/'.data/led-demo-test').glob('invalidated-result-*')))
 def test_verify_project_is_readonly_exact_and_rejects_extra_source(self):
  self.fetch();project=self.root/'.data/led-demo-test/project';before=demo.shared.inventory(project)
  self.assertEqual(demo.verify_project(project)['file_count'],5);self.assertEqual(demo.shared.inventory(project),before)
  (project/'PushButtonLed.kicad_dru').write_bytes(b'(version 1)')
  with self.assertRaisesRegex(ValueError,'exact five'):demo.verify_project(project)
 def test_replaced_project_never_writes_new_owner_directory(self):
  moved=self.root/'retained-project'
  def replace(row,record,path,allowance,remaining):
   project=self.root/'.data/led-demo-test/project';project.rename(moved);project.mkdir();(project/'owner').write_bytes(b'owner')
   return self.transport(row,record,path,allowance,remaining)
  with self.assertRaises(Exception):self.fetch(replace)
  project=self.root/'.data/led-demo-test/project';self.assertEqual(list(project.iterdir()),[project/'owner']);self.assertEqual((project/'owner').read_bytes(),b'owner');self.assertFalse((moved/'LICENSE').exists())
 def test_full_cpu_exhaustion_after_payload_cannot_leave_success(self):
  clock=[0.0]
  def expensive(row,record,path,allowance,remaining):
   raw=self.transport(row,record,path,allowance,remaining);clock[0]=demo.SECONDS+1;return raw
  with mock.patch.object(demo,'cpu',side_effect=lambda:clock[0]),self.assertRaises(TimeoutError):self.fetch(expensive)
  receipt=demo.publication.read_json(self.root/'.data/led-demo-test/result.json');self.assertFalse(receipt['accepted']);self.assertFalse(receipt['within_budget']);self.assertIn('wall/CPU budget exhausted',receipt['first_failure']);self.assertEqual(receipt['new_network_requests'],1)
 def test_final_tail_staleness_after_publisher_archives_positive(self):
  real=demo.publication.publish;calls=[]
  def mutate_after(output,record,*args,**kwargs):
   calls.append(output);value=real(output,record,*args,**kwargs)
   if len(calls)==1:(output/'project/README.md').write_bytes(b'changed after published')
   return value
  with mock.patch.object(demo.publication,'publish',side_effect=mutate_after),self.assertRaises(ValueError):self.fetch()
  receipt=demo.publication.read_json(self.root/'.data/led-demo-test/result.json');self.assertEqual(receipt['status'],'invalidated');self.assertFalse(receipt['accepted']);self.assertFalse(receipt['source_files_exact']);self.assertTrue(list((self.root/'.data/led-demo-test').glob('invalidated-result-*')))
if __name__=='__main__':unittest.main()
