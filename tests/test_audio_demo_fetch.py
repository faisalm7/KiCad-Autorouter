"""Proposed authored-byte Audio acquisition controls; no GET/native execution."""
import copy,hashlib,json,tempfile,unittest
from pathlib import Path
from unittest import mock
from scripts import fetch_led_demo as demo
from tests import test_navigation_demo_fetch as nav_controls


class AudioFetchControls(unittest.TestCase):
    transport=nav_controls.NavigationFetchControls.transport

    def setUp(self):
        scratch=demo.ROOT/'.cache';scratch.mkdir(exist_ok=True)
        temp=tempfile.TemporaryDirectory(dir=scratch);self.addCleanup(temp.cleanup)
        self.root=Path(temp.name).resolve();self.calls=[];self.payloads={}
        for name in (*demo.MATERIAL,*demo.ARC_MATERIAL):
            path=self.root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes((demo.ROOT/name).read_bytes())
        self.public=demo.fixed_profile('audio-player-my1690x');self.cfg=copy.deepcopy(self.public)
        self.cfg['default_output']='.data/audio-player-my1690x-demo-test'
        for row in self.cfg['rows']:
            prefix=('authored '+('stale Eagle placeholder ' if row['source_path']=='Hardware/README.md' else '')+row['source_path']+'\n').encode()
            raw=prefix+b'x'*(row['bytes']-len(prefix));self.payloads[row['source_path']]=raw
            row['sha256']=demo.shared.sha(raw);row['git_blob_sha1']=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
        self.out=self.root/self.cfg['default_output'];self.cache=self.root/demo.AUDIO_CACHE_DIRECTORY
        self.fixture_pins={};self.metadata_pins={}
        for name,value in [('AUDIO_PROFILE',self.cfg),('AUDIO_CACHE_PINS',self.fixture_pins),('AUDIO_METADATA_PINS',self.metadata_pins),
            ('NAV_CACHE_DIRECTORY',demo.AUDIO_CACHE_DIRECTORY)]:
            patch=mock.patch.object(demo,name,value);patch.start();self.addCleanup(patch.stop)

    def cache_inputs(self):
        # Reuse the existing root-summary/tree/manifest fixture constructor.
        nav_controls.NavigationFetchControls.cache_inputs(self)
        name='Hardware/README.md';row=next(x for x in self.cfg['rows'] if x['source_path']==name)
        base=self.root/demo.AUDIO_METADATA_DIRECTORY;relative='metadata/'+self.cfg['repository'].replace('/','__')+'/'+name
        path=base/relative;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(self.payloads[name])
        request=dict(repository=self.cfg['repository'],source_path=name,url=row['raw_url'],final_url=row['raw_url'],
            http_status=200,payload_verified=True,bytes=row['bytes'],received_bytes=row['bytes'],sha256=row['sha256'],
            response_sha256=row['sha256'],artifact=relative,status='response_received')
        receipt=dict(passed=True,failures=[],new_primary_requests=3,received_bytes=28855,new_geometry_payloads=0,new_native_or_engine_jobs=0,
            requests=[request,dict(received_bytes=23767,source_path='docs/hardware_overview.md'),dict(received_bytes=4796,source_path='docs/hardware_overview.md')])
        (base/'metadata-receipt.json').write_text(json.dumps(receipt));receipt_pin=demo.shared.sha((base/'metadata-receipt.json').read_bytes())
        execution=dict(receipt_sha256=receipt_pin,wall_seconds=.9511280409933534,full_cpu_seconds=.173402,
            process=dict(status='success',exit_code=0,cleanup_complete=True,log_truncated=False))
        (base/'metadata-execution.json').write_text(json.dumps(execution));execution_pin=demo.shared.sha((base/'metadata-execution.json').read_bytes())
        closure=dict(passed=True,metadata_receipt_sha256=receipt_pin,metadata_execution_sha256=execution_pin,
            conservative_preparation_bootstrap_emission_allowance_seconds=3,actual_metadata_outer_wall_seconds=execution['wall_seconds'],
            actual_metadata_outer_full_cpu_seconds=execution['full_cpu_seconds'])
        (base/'closure.json').write_text(json.dumps(closure))
        self.metadata_pins.update({name:demo.shared.sha((base/name).read_bytes()) for name in ('metadata-receipt.json','metadata-execution.json','closure.json')})

    def fetch(self,reuse=False,transport=None):
        return demo.fetch_demo(self.cfg['default_output'],profile_id='audio-player-my1690x',root=self.root,fetch=True,
            transport=transport or self.transport,reuse_audio_notices=reuse)

    def assert_packet(self,result):
        self.assertEqual(result['status'],'acquired_unqualified');self.assertTrue(result['source_files_exact']);self.assertTrue(result['cache_inputs_current'])
        self.assertFalse(result['accepted']);self.assertFalse(result['native_accepted']);self.assertFalse(result['independent_ancestry_established'])
        self.assertTrue(result['within_budget']);self.assertLess(result['output_bytes'],3*1024**2);self.assertFalse((self.out/'responses').exists())
        original=demo.verify_project(self.out/'project',profile_id='audio-player-my1690x')
        packet=demo.verify_project(self.out/'native-project',profile_id='audio-player-my1690x',native_packet=True)
        self.assertEqual((original['file_count'],original['bytes'],packet['file_count'],packet['bytes']),(7,1272977,9,1278659))
        for name,raw in self.payloads.items():self.assertEqual((self.out/'project'/name).read_bytes(),raw)
        self.assertEqual((self.out/'project/Hardware/README.md').read_bytes(),self.payloads['Hardware/README.md'])
        self.assertEqual((self.out/'project/Hardware/SparkFun_Audio_Player_Breakout_MY1690X-16S.kicad_prl').read_bytes(),self.payloads['Hardware/SparkFun_Audio_Player_Breakout_MY1690X-16S.kicad_prl'])

    def test_exact_pins_source_prl_stale_readme_caps_and_no_io_plan(self):
        self.assertEqual((self.public['file_count'],self.public['bytes'],self.public['native_packet_files'],self.public['native_packet_bytes']),(7,1272977,9,1278659))
        self.assertEqual((self.public['output_byte_cap'],self.public['wall_budget_seconds'],self.public['cpu_budget_seconds']),(3*1024**2,300,300))
        self.assertEqual(self.public['commit'],'49d66d63eb43105b7dbe437cc9299c637c69c61d')
        self.assertEqual(next(r for r in self.public['rows'] if r['source_path']=='Hardware/README.md')['sha256'],'6add188e18eb48c055d25c6cb3c9e2865bcec753e4da3b3bc97602b7f613f683')
        self.assertTrue(any('stale Eagle' in x for x in self.public['warnings']))
        for reuse,count in ((False,7),(True,4)):
            plan=demo.fetch_demo(self.cfg['default_output'],profile_id='audio-player-my1690x',root=self.root,reuse_audio_notices=reuse)
            self.assertEqual((plan['network_requests'],plan['planned_network_requests'],plan['planned_cached_notices']),(0,count,3 if reuse else 0))
        self.assertFalse(self.cache.exists());self.assertFalse((self.root/'.data').exists())
        self.assertEqual(demo.fixed_profile('navigation-switch')['output_byte_cap'],2*1024**2)
        self.assertEqual(demo.fixed_profile('uv-dosimeter')['output_byte_cap'],2*1024**2)

    def test_default_fresh_seven_and_cache_three_keep_exact_packet_and_provenance(self):
        with mock.patch.object(demo,'audio_notice_cache',side_effect=AssertionError('default cache access')):fresh=self.fetch()
        self.assert_packet(fresh);self.assertEqual((fresh['new_network_requests'],fresh['received_bytes']),(7,1272977))
        self.assertIsNone(fresh['prior_cache_acquisition'])
        self.cfg['default_output']='.data/audio-player-my1690x-demo-cached';self.out=self.root/self.cfg['default_output'];self.calls=[]
        self.cache_inputs();result=self.fetch(True);self.assert_packet(result)
        self.assertEqual((result['new_network_requests'],result['received_bytes'],result['reused_input_files'],result['reused_input_bytes']),(4,1267003,3,5974))
        prior=result['prior_cache_acquisition'];self.assertIsNone(prior['wall_seconds']);self.assertIsNone(prior['full_cpu_seconds']);self.assertFalse(prior['comparative_accounting_complete'])
        self.assertEqual(prior['additional_metadata_batch']['bootstrap_emission_allowance_seconds'],3)
        self.assertEqual(prior['additional_metadata_batch']['original_batch_bytes'],28855)
        cached=[x for x in result['requests'] if x['transport']=='verified_cache'];self.assertEqual(len(cached),3)
        for request in cached:self.assertNotIn('http_status',request);self.assertEqual(request['received_bytes'],0)
        hardware=next(x for x in cached if x['source_path']=='Hardware/README.md')
        self.assertEqual(hardware['prior_receipt'],dict(file=demo.AUDIO_METADATA_DIRECTORY+'/metadata-receipt.json',sha256=self.metadata_pins['metadata-receipt.json']))

    def test_missing_or_corrupt_metadata_has_no_network_fallback(self):
        with self.assertRaises(Exception):self.fetch(True)
        self.assertFalse(self.calls);self.assertFalse(self.out.exists())
        self.cache_inputs();body=self.root/demo.AUDIO_METADATA_DIRECTORY/'metadata'/self.cfg['repository'].replace('/','__')/'Hardware/README.md'
        body.write_bytes(b'z'+body.read_bytes()[1:])
        with self.assertRaisesRegex(ValueError,'payload hash'):self.fetch(True)
        self.assertFalse(self.calls);self.assertFalse(self.out.exists())

    def test_late_hardware_receipt_drift_invalidates_but_copied_bytes_remain_exact(self):
        self.cache_inputs();real=demo.publication.publish;calls=[]
        def drift(*args,**kwargs):
            result=real(*args,**kwargs);calls.append(True)
            if len(calls)==1:
                path=self.root/demo.AUDIO_METADATA_DIRECTORY/'closure.json';path.write_bytes(path.read_bytes()+b' ')
            return result
        with mock.patch.object(demo.publication,'publish',side_effect=drift),self.assertRaises(Exception):self.fetch(True)
        result=demo.publication.read_json(self.out/'result.json')
        self.assertEqual(result['status'],'invalidated');self.assertFalse(result['accepted']);self.assertFalse(result['cache_inputs_current']);self.assertTrue(result['source_files_exact'])
        self.assertTrue(list(self.out.glob('invalidated-result-*')))

    def test_audio_reuse_wrong_profile_bad_type_and_complete_packet_cap_fail_closed(self):
        for profile,flag in (('navigation-switch',True),('uv-dosimeter',True),('audio-player-my1690x',1)):
            with self.assertRaisesRegex(ValueError,'Audio-only'):
                demo.fetch_demo(demo.fixed_profile(profile)['default_output'],profile_id=profile,fetch=True,root=self.root,reuse_audio_notices=flag)
        self.assertFalse(self.calls);self.assertFalse((self.root/'.data').exists())
        self.cfg['output_byte_cap']=2*1024**2
        with self.assertRaises(ValueError):self.fetch()
        self.assertEqual(demo.verify_project(self.out/'project',profile_id='audio-player-my1690x')['file_count'],7)
        self.assertFalse(any(json.loads(p.read_text()).get('accepted') for p in self.out.glob('*result*.json')))


if __name__=='__main__':unittest.main()
