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
 def test_ir_plan_pins_complete_source_notice_packet_and_original_gate(self):
  cfg=demo.fixed_profile('ir-obstacle');rows=cfg['rows'];by={r['source_path']:r for r in rows}
  self.assertEqual(cfg['commit'],'6399dfd3bd8d2f48878a9a7c5b2f2e7a76a2b899')
  self.assertEqual(set(by),{'LICENSE','README.md','KiCad/IR_Sensor.kicad_pcb','KiCad/IR_Sensor.kicad_pro','KiCad/IR_Sensor.kicad_sch'})
  self.assertEqual((len(rows),sum(r['bytes'] for r in rows)),(5,222901))
  self.assertEqual(by['KiCad/IR_Sensor.kicad_pcb']['sha256'],'f52eca1575d9438b803a672088de98436e9a299b6014a3bbafca963974431774')
  self.assertEqual(by['LICENSE']['sha256'],'7a9ff699e91b9acf1cf6747e72f82fab1ec25ead316ece85e14b8043200ebb74')
  self.assertEqual(cfg['native_packet_notice_copies'],{'KiCad/_licenses/creator/LICENSE':'LICENSE','KiCad/_licenses/creator/README.md':'README.md'})
  self.assertEqual((cfg['native_packet_files'],cfg['native_packet_bytes']),(7,227145))
  self.assertEqual(cfg['native_packet_bytes'],cfg['bytes']+sum(by[n]['bytes'] for n in cfg['native_packet_notice_copies'].values()))
  self.assertEqual((cfg['max_requests'],cfg['network_byte_cap'],cfg['max_single_response_bytes']),(5,222906,159648))
  self.assertEqual((cfg['wall_budget_seconds'],cfg['cpu_budget_seconds'],cfg['output_byte_cap']),(300,300,2*1024**2))
  self.assertFalse(any(path.endswith('.kicad_prl') for path in by))
  result=demo.fetch_demo(cfg['default_output'],profile_id='ir-obstacle',root=self.root,transport=lambda *a:self.fail('offline plan transported'))
  self.assertEqual((result['action'],result['network_requests'],result['planned_network_requests'],result['planned_bytes']),('plan_only',0,5,222901))
  self.assertFalse((self.root/'.data').exists())
  cfg['rows'][0]['sha256']='0'*64
  self.assertEqual(demo.fixed_profile('ir-obstacle')['rows'][0]['sha256'],'7a9ff699e91b9acf1cf6747e72f82fab1ec25ead316ece85e14b8043200ebb74')
  from experiments.original_project_native_v1 import driver
  self.assertEqual(driver.CASES['ir-obstacle'],('portable-demo','KiCad/IR_Sensor.kicad_pcb','6399dfd3bd8d2f48878a9a7c5b2f2e7a76a2b899',None))
  self.assertIn('ir-obstacle',driver.REFILLED_ORIGINALS)
 def test_universal_shift_fixed_plan_retains_prl_orphan_and_both_notices(self):
  cfg=demo.fixed_profile('universal-shift-interface');by={r['source_path']:r for r in cfg['rows']}
  self.assertEqual(cfg['commit'],'02a2698f962e3cd7c16d58167a455ad01c97e1b0')
  self.assertEqual((len(by),cfg['bytes'],sum(r['bytes'] for r in by.values())),(7,821075,821075))
  self.assertEqual(by['KiCad/Interface Board/USR_LED_Board.kicad_pcb']['sha256'],'4554afb88a6708b565cf2fe90a50a443d9b2ab0be80c306dff954af0e1dfa289')
  self.assertIn('KiCad/Interface Board/USR_LED_Board.kicad_prl',by);self.assertIn('KiCad/Interface Board/.kicad_sch',by)
  self.assertEqual((cfg['native_packet_files'],cfg['native_packet_bytes']),(9,829542))
  self.assertEqual(set(cfg['native_packet_notice_copies'].values()),{'LICENSE','README.md'})
  self.assertEqual((cfg['max_requests'],cfg['network_byte_cap'],cfg['max_single_response_bytes']),(7,821082,648487))
  self.assertEqual(cfg['output_byte_cap'],4*1024**2);self.assertLess(2*cfg['bytes']+cfg['native_packet_bytes'],cfg['output_byte_cap'])
  result=demo.fetch_demo(cfg['default_output'],profile_id=cfg['profile_id'],root=self.root,transport=lambda *a:self.fail('offline plan transported'))
  self.assertEqual((result['action'],result['network_requests'],result['planned_network_requests'],result['planned_bytes']),('plan_only',0,7,821075));self.assertFalse((self.root/'.data').exists())
  cfg['rows'][0]['sha256']='0'*64;self.assertNotEqual(demo.fixed_profile('universal-shift-interface')['rows'][0]['sha256'],'0'*64)
  from experiments.original_project_native_v1 import driver
  self.assertEqual(driver.CASES['universal-shift-interface'],('portable-demo','KiCad/Interface Board/USR_LED_Board.kicad_pcb','02a2698f962e3cd7c16d58167a455ad01c97e1b0',None));self.assertIn('universal-shift-interface',driver.REFILLED_ORIGINALS)
 def authored_universal_shift(self):
  # Authored transport-only text: not downloaded boards or Native evidence.
  cfg=demo.fixed_profile('universal-shift-interface');payloads={}
  for name in demo.ARC_MATERIAL:
   q=self.root/name;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes((demo.ROOT/name).read_bytes())
  for row in cfg['rows']:
   raw=('authored fixed-packet fixture '+row['source_path']+'\n').encode();payloads[row['source_path']]=raw
   row.update(bytes=len(raw),sha256=demo.shared.sha(raw),git_blob_sha1=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest())
  cfg['bytes']=sum(r['bytes'] for r in cfg['rows']);cfg['network_byte_cap']=cfg['bytes']+7;cfg['max_single_response_bytes']=max(r['bytes'] for r in cfg['rows'])+1
  cfg['native_packet_bytes']=cfg['bytes']+sum(len(payloads[n]) for n in cfg['native_packet_notice_copies'].values())
  patch=mock.patch.object(demo,'UNIVERSAL_SHIFT_PROFILE',cfg);patch.start();self.addCleanup(patch.stop)
  def transport(row,record,path,allowance,remaining):
   remaining();self.called.append(row['source_path']);raw=payloads[row['source_path']]
   with path.open('xb') as stream:stream.write(raw)
   record.update(received_bytes=len(raw),response_sha256=demo.shared.sha(raw),url=row['raw_url'],status='response_received',http_status=200,wall_seconds=0.0);return raw
  return cfg,payloads,transport
 def test_universal_shift_authored_full_capture_preserves_every_original(self):
  cfg,payloads,transport=self.authored_universal_shift();r=demo.fetch_demo(cfg['default_output'],fetch=True,profile_id=cfg['profile_id'],root=self.root,transport=transport)
  self.assertEqual((r['status'],r['new_network_requests']),('acquired_unqualified',7));self.assertFalse(r['accepted']);self.assertFalse(r['native_accepted'])
  base,files=demo.capture_native_source(cfg['profile_id'],root=self.root)
  self.assertEqual(len(files),9)
  for name,raw in payloads.items():self.assertEqual(files[name],raw)
  for name,origin in cfg['native_packet_notice_copies'].items():self.assertEqual(files[name],payloads[origin])
  self.assertEqual(demo.verify_project(base,profile_id=cfg['profile_id'],native_packet=True)['bytes'],cfg['native_packet_bytes'])
 def test_universal_shift_authored_missing_orphan_bad_notice_and_symlink_refuse(self):
  cfg,payloads,transport=self.authored_universal_shift();demo.fetch_demo(cfg['default_output'],fetch=True,profile_id=cfg['profile_id'],root=self.root,transport=transport)
  base=self.root/cfg['default_output']/'native-project';orphan=base/'KiCad/Interface Board/.kicad_sch';raw=orphan.read_bytes();orphan.unlink()
  with self.assertRaises(ValueError):demo.verify_project(base,profile_id=cfg['profile_id'],native_packet=True)
  orphan.symlink_to(base/'LICENSE')
  with self.assertRaises(ValueError):demo.verify_project(base,profile_id=cfg['profile_id'],native_packet=True)
  orphan.unlink();orphan.write_bytes(raw);notice=base/'KiCad/Interface Board/_licenses/creator/LICENSE';notice.write_bytes(b'changed notice')
  with self.assertRaises(ValueError):demo.capture_native_source(cfg['profile_id'],root=self.root)
 def test_universal_shift_authored_late_prl_change_keeps_failed_receipt(self):
  cfg,payloads,transport=self.authored_universal_shift();real=demo.publication.publish;calls=[]
  def stale(output,record,*args,**kwargs):
   value=real(output,record,*args,**kwargs);calls.append(output)
   if len(calls)==1:(output/'project/KiCad/Interface Board/USR_LED_Board.kicad_prl').write_bytes(b'late changed PRL')
   return value
  with mock.patch.object(demo.publication,'publish',side_effect=stale),self.assertRaises(ValueError):demo.fetch_demo(cfg['default_output'],fetch=True,profile_id=cfg['profile_id'],root=self.root,transport=transport)
  r=demo.publication.read_json(self.root/cfg['default_output']/'result.json');self.assertEqual(r['status'],'invalidated');self.assertFalse(r['accepted']);self.assertFalse(r['source_files_exact']);self.assertEqual(r['new_network_requests'],7);self.assertIn('source_verification_error',r);self.assertTrue(list((self.root/cfg['default_output']).glob('invalidated-result-*')))
  self.assertEqual((self.root/cfg['default_output']/'project/KiCad/Interface Board/USR_LED_Board.kicad_prl').read_bytes(),b'late changed PRL')
  with self.assertRaises(ValueError):demo.capture_native_source(cfg['profile_id'],root=self.root)
 def test_ds18b20_fixed_plan_pins_root_originals_and_single_readme_notice(self):
  cfg=demo.fixed_profile('ds18b20');by={r['source_path']:r for r in cfg['rows']}
  expected={
   'D18BS20.kicad_pcb':(71761,'1a9fa83e2df4732fd5adf5e41ce56187716da712','2ce74b0cfa4863e15ff282ed6e77d628bd3f13756886fdd133cd20c5e7404f13'),
   'D18BS20.kicad_prl':(2397,'c45da2cae6176f44d32c25fb75c8cf08676776e0','4c5470c0b19738593564947670c111aca22badbc28229ba0e38ceb5262fb8dbe'),
   'D18BS20.kicad_pro':(15222,'d3e7ae00176cb90a793178d4e02aa44a035048b7','e6343efeaf6ee42a2d6f6a78b06780d6d1855271be9b4eaed0121bdc70a53924'),
   'D18BS20.kicad_sch':(24879,'3751af4e257e475fafea212385771c761034336a','f846b9dfdebd175031214cb40169ae4c3f7f8c70b1b9158b172cad1bca87ea2a'),
   'README.md':(5259,'96cfa10b5aa5c775158646cf6d030c3ae6a20e5b','c50d1cad5fe162059fd15a455b39712460ad04977de4962d37cc269257ac7a5e')}
  commit='c5420f538a77e0af03974031a5ee1c36a5b5e0a1'
  self.assertEqual((cfg['repository'],cfg['commit'],cfg['board_path'],cfg['directories']),('ampnics/DS18B20',commit,'D18BS20.kicad_pcb',[]))
  self.assertEqual({n:(r['bytes'],r['git_blob_sha1'],r['sha256']) for n,r in by.items()},expected)
  for name,row in by.items():
   self.assertEqual((row['repository'],row['commit'],row['mode'],row['destination']),('ampnics/DS18B20',commit,'100644','ds18b20/'+name))
   self.assertEqual(row['raw_url'],'https://raw.githubusercontent.com/ampnics/DS18B20/'+commit+'/'+name)
  self.assertEqual((cfg['file_count'],cfg['bytes'],sum(r['bytes'] for r in by.values())),(5,119518,119518))
  self.assertEqual(cfg['native_packet_notice_copies'],{'_licenses/creator/README.md':'README.md'})
  self.assertEqual((cfg['output_prefix'],cfg['default_output']),('ds18b20-demo-','.data/ds18b20-demo-001'))
  self.assertEqual((cfg['native_packet_files'],cfg['native_packet_bytes']),(6,124777))
  self.assertEqual((cfg['max_requests'],cfg['network_byte_cap'],cfg['max_single_response_bytes']),(5,119523,71762))
  self.assertEqual((cfg['wall_budget_seconds'],cfg['cpu_budget_seconds'],cfg['output_byte_cap']),(300,300,2*1024**2))
  self.assertLess(2*cfg['bytes']+cfg['native_packet_bytes'],cfg['output_byte_cap'])
  result=demo.fetch_demo(cfg['default_output'],profile_id='ds18b20',root=self.root,transport=lambda *a:self.fail('offline plan transported'))
  self.assertEqual((result['action'],result['network_requests'],result['planned_network_requests'],result['planned_files'],result['planned_bytes']),('plan_only',0,5,5,119518))
  self.assertFalse((self.root/'.data').exists());self.assertFalse((self.root/'.runs').exists())
  cfg['rows'][0]['sha256']='0'*64;cfg['native_packet_notice_copies']['_licenses/creator/LICENSE']='README.md'
  self.assertEqual(demo.fixed_profile('ds18b20')['rows'][0]['sha256'],expected['D18BS20.kicad_pcb'][2])
  self.assertEqual(demo.fixed_profile('ds18b20')['native_packet_notice_copies'],{'_licenses/creator/README.md':'README.md'})
  from experiments.original_project_native_v1 import driver
  self.assertEqual(driver.CASES['ds18b20'],('portable-demo','D18BS20.kicad_pcb',commit,None));self.assertIn('ds18b20',driver.REFILLED_ORIGINALS)
 def authored_ds18b20(self):
  # Authored transport-only bytes exercise the root/single-notice shape, not CAD.
  cfg=demo.fixed_profile('ds18b20');payloads={}
  for name in demo.ARC_MATERIAL:
   q=self.root/name;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes((demo.ROOT/name).read_bytes())
  for row in cfg['rows']:
   raw=('authored DS18B20 packet fixture '+row['source_path']+'\n').encode();payloads[row['source_path']]=raw
   row.update(bytes=len(raw),sha256=demo.shared.sha(raw),git_blob_sha1=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest())
  cfg['bytes']=sum(r['bytes'] for r in cfg['rows']);cfg['network_byte_cap']=cfg['bytes']+len(cfg['rows']);cfg['max_single_response_bytes']=max(r['bytes'] for r in cfg['rows'])+1
  cfg['native_packet_bytes']=cfg['bytes']+len(payloads['README.md'])
  patch=mock.patch.object(demo,'DS18B20_PROFILE',cfg);patch.start();self.addCleanup(patch.stop)
  def transport(row,record,path,allowance,remaining):
   remaining();self.called.append(row['source_path']);raw=payloads[row['source_path']]
   with path.open('xb') as stream:stream.write(raw)
   record.update(received_bytes=len(raw),response_sha256=demo.shared.sha(raw),url=row['raw_url'],status='response_received',http_status=200,wall_seconds=0.0);return raw
  return cfg,payloads,transport
 def test_ds18b20_authored_capture_has_exact_five_originals_and_six_packet_files(self):
  cfg,payloads,transport=self.authored_ds18b20();r=demo.fetch_demo(cfg['default_output'],fetch=True,profile_id='ds18b20',root=self.root,transport=transport)
  self.assertEqual((r['status'],r['new_network_requests'],r['received_bytes']),('acquired_unqualified',5,cfg['bytes']))
  self.assertEqual(self.called,[row['source_path'] for row in cfg['rows']]);self.assertTrue(r['source_files_exact']);self.assertTrue(r['within_budget']);self.assertFalse(r['accepted']);self.assertFalse(r['native_accepted'])
  out=self.root/cfg['default_output'];source=out/'project';base,files=demo.capture_native_source('ds18b20',root=self.root)
  original={n:{'bytes':len(raw),'sha256':demo.shared.sha(raw)} for n,raw in payloads.items()}
  packet={**original,'_licenses/creator/README.md':original['README.md']}
  source_before=demo.shared.inventory(source);packet_before=demo.shared.inventory(base)
  self.assertEqual((source_before['files'],source_before['directories']),(original,[]))
  self.assertEqual((packet_before['files'],packet_before['directories']),(packet,['_licenses','_licenses/creator']))
  self.assertEqual(files,{**payloads,'_licenses/creator/README.md':payloads['README.md']})
  self.assertEqual((demo.verify_project(source,profile_id='ds18b20')['file_count'],demo.verify_project(base,profile_id='ds18b20',native_packet=True)['file_count']),(5,6))
  self.assertEqual(demo.verify_project(base,profile_id='ds18b20',native_packet=True)['bytes'],cfg['native_packet_bytes'])
  self.assertEqual((demo.shared.inventory(source),demo.shared.inventory(base)),(source_before,packet_before))
 def test_ds18b20_authored_root_prl_readme_and_only_notice_fail_closed(self):
  cfg,payloads,transport=self.authored_ds18b20();demo.fetch_demo(cfg['default_output'],fetch=True,profile_id='ds18b20',root=self.root,transport=transport)
  out=self.root/cfg['default_output'];clean={scope:demo.shared.inventory(out/scope) for scope in ('project','native-project')}
  cases=[('project','D18BS20.kicad_prl','missing'),('native-project','D18BS20.kicad_prl','missing'),
   ('project','D18BS20.kicad_prl','changed'),('project','README.md','changed'),('native-project','README.md','changed'),('native-project','_licenses/creator/README.md','changed'),
   ('project','LICENSE','extra'),('native-project','_licenses/creator/LICENSE','extra'),('native-project','D18BS20.kicad_dru','extra'),
   ('project','README.md','symlink'),('native-project','_licenses/creator/README.md','symlink')]
  for scope,name,kind in cases:
   with self.subTest(scope=scope,name=name,kind=kind):
    base=out/scope;target=base/name;raw=target.read_bytes() if target.exists() else None
    if kind=='missing':target.unlink()
    elif kind=='symlink':target.unlink();target.symlink_to(out/'native-project/README.md')
    else:target.write_bytes(b'changed pinned fixture' if kind=='changed' else b'invented extra file')
    try:
     with self.assertRaises(ValueError):demo.verify_project(base,profile_id='ds18b20',native_packet=scope=='native-project')
     with self.assertRaises(ValueError):demo.capture_native_source('ds18b20',root=self.root)
     if kind=='missing':self.assertFalse(target.exists())
     elif kind=='symlink':self.assertTrue(target.is_symlink());self.assertEqual(target.read_bytes(),payloads['README.md'])
     else:self.assertEqual(target.read_bytes(),b'changed pinned fixture' if kind=='changed' else b'invented extra file')
    finally:
     if target.exists() or target.is_symlink():target.unlink()
     if raw is not None:target.write_bytes(raw)
    self.assertEqual({s:demo.shared.inventory(out/s) for s in clean},clean)
 def test_ds18b20_authored_late_only_notice_change_invalidates_without_repair(self):
  cfg,payloads,transport=self.authored_ds18b20();real=demo.publication.publish;calls=[];originals=[]
  def stale(output,record,*args,**kwargs):
   value=real(output,record,*args,**kwargs);calls.append(output)
   if len(calls)==1:
    originals.append(demo.shared.inventory(output/'project'))
    (output/'native-project/_licenses/creator/README.md').write_bytes(b'late changed only notice')
   return value
  with mock.patch.object(demo.publication,'publish',side_effect=stale),self.assertRaises(ValueError):demo.fetch_demo(cfg['default_output'],fetch=True,profile_id='ds18b20',root=self.root,transport=transport)
  out=self.root/cfg['default_output'];r=demo.publication.read_json(out/'result.json')
  self.assertEqual(r['status'],'invalidated');self.assertFalse(r['accepted']);self.assertFalse(r['native_accepted']);self.assertFalse(r['source_files_exact']);self.assertEqual(r['new_network_requests'],5)
  self.assertIn('source_verification_error',r);self.assertTrue(list(out.glob('invalidated-result-*')))
  self.assertEqual(demo.shared.inventory(out/'project'),originals[0]);self.assertEqual((out/'native-project/_licenses/creator/README.md').read_bytes(),b'late changed only notice')
  with self.assertRaises(ValueError):demo.capture_native_source('ds18b20',root=self.root)
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
