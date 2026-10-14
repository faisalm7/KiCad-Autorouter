"""Authored portable acquisition controls only; no actual board/HTTP/Native proof."""
import copy,hashlib,json,tempfile,unittest
from pathlib import Path
from unittest import mock
from scripts import fetch_led_demo as demo
from tests import test_uv_demo_fetch as uv_controls

class FlipperFetchControls(unittest.TestCase):
    transport=uv_controls.UVFetchControls.transport
    def setUp(self):
        scratch=demo.ROOT/'.cache';scratch.mkdir(exist_ok=True);temp=tempfile.TemporaryDirectory(dir=scratch);self.addCleanup(temp.cleanup)
        self.root=Path(temp.name).resolve();self.calls=[];self.payloads={}
        for name in (*demo.MATERIAL,*demo.ARC_MATERIAL):
            p=self.root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((demo.ROOT/name).read_bytes())
        self.public=demo.fixed_profile('pico-flipper');self.cfg=copy.deepcopy(self.public);self.cfg['default_output']='.data/pico-flipper-demo-test'
        for row in self.cfg['rows']:
            prefix=('authored Flipper syntax fixture '+row['source_path']+'\n').encode();raw=prefix+b'x'*(row['bytes']-len(prefix));self.payloads[row['source_path']]=raw
            row.update(sha256=demo.shared.sha(raw),git_blob_sha1=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest())
        change=mock.patch.object(demo,'FLIPPER_PROFILE',self.cfg);change.start();self.addCleanup(change.stop)
        self.pins={};change=mock.patch.object(demo,'FLIPPER_CACHE_PINS',self.pins);change.start();self.addCleanup(change.stop)
        self.out=self.root/self.cfg['default_output'];self.cache=self.root/demo.FLIPPER_CACHE_DIRECTORY
    def cache_inputs(self,change=None):
        self.cache.mkdir(parents=True,exist_ok=True);rows={r['source_path']:r for r in self.cfg['rows']};docs=[]
        for name in demo.FLIPPER_NOTICE_NAMES:
            raw=self.payloads[name];(self.cache/name).write_bytes(raw);docs.append(dict(path=name,url=rows[name]['raw_url'],bytes=len(raw),sha256=demo.shared.sha(raw)))
        summary=dict(repository=self.cfg['repository'],commit=self.cfg['commit'],source_url='https://github.com/'+self.cfg['repository']+'/tree/'+self.cfg['commit'],tree_sha=self.cfg['commit'],metadata_complete=True,board_payloads_downloaded=0,status='metadata_only_not_acquired',metadata_documents=docs)
        tree=dict(sha=self.cfg['commit'],truncated=False,tree=[dict(path=r['source_path'],type='blob',mode=r['mode'],size=r['bytes'],sha=r['git_blob_sha1']) for r in self.cfg['rows']])
        if change:change(summary,tree)
        for name,doc in [('summary.json',summary),('tree.json',tree)]:
            p=self.cache/name;p.write_text(json.dumps(doc));self.pins[demo.FLIPPER_CACHE_DIRECTORY+'/'+name]=demo.shared.sha(p.read_bytes())
        manifest=dict(schema=1,files={str(p.relative_to(self.root/'.runs/corpus-next-001')):demo.shared.sha(p.read_bytes()) for p in self.cache.iterdir()})
        name='.runs/corpus-next-001/metadata-sha256.json';p=self.root/name;p.write_text(json.dumps(manifest));self.pins[name]=demo.shared.sha(p.read_bytes())
    def fetch(self,reuse=False,transport=None):
        return demo.fetch_demo(self.cfg['default_output'],profile_id='pico-flipper',fetch=True,root=self.root,transport=transport or self.transport,reuse_flipper_notices=reuse)
    def packet(self,result):
        self.assertEqual(result['status'],'acquired_unqualified');self.assertTrue(result['source_files_exact']);self.assertTrue(result['cache_inputs_current']);self.assertTrue(result['within_budget'])
        self.assertFalse(result['accepted']);self.assertFalse(result['native_accepted']);self.assertFalse(result['independent_ancestry_established'])
        self.assertEqual((result['native_jobs'],result['engine_jobs'],result['models_downloaded']),(0,0,0))
        a=demo.verify_project(self.out/'project',profile_id='pico-flipper');b=demo.verify_project(self.out/'native-project',profile_id='pico-flipper',native_packet=True)
        self.assertEqual((a['file_count'],a['bytes'],b['file_count'],b['bytes']),(5,1111660,7,1119094))
        for name,raw in self.payloads.items():self.assertEqual((self.out/'project'/name).read_bytes(),raw)
        self.assertLess(result['output_bytes'],4*1024**2);self.assertGreater(result['output_bytes'],2*1024**2)
        self.assertFalse((self.out/'responses').exists())
    def test_fixed_five_pins_and_offline_plans_keep_legacy_default(self):
        self.assertEqual((self.public['file_count'],self.public['bytes'],self.public['native_packet_files'],self.public['native_packet_bytes']),(5,1111660,7,1119094))
        self.assertEqual((self.public['wall_budget_seconds'],self.public['cpu_budget_seconds'],self.public['output_byte_cap'],self.public['max_requests']),(300,300,4*1024**2,5))
        self.assertEqual(self.public['commit'],'50f29ca0f4a3703f07c40d846c40da844663a85c');self.assertEqual(demo.fixed_profile()['bytes'],161071)
        self.assertEqual(demo.fixed_profile('navigation-switch')['output_byte_cap'],2*1024**2)
        with mock.patch.object(demo,'flipper_notice_cache',side_effect=AssertionError('plan reads cache')):
            for reuse,gets in [(False,5),(True,3)]:
                p=demo.fetch_demo(self.cfg['default_output'],profile_id='pico-flipper',root=self.root,reuse_flipper_notices=reuse,transport=lambda *args:self.fail('plan transported'))
                self.assertEqual((p['network_requests'],p['planned_network_requests'],p['planned_cached_notices']),(0,gets,2 if reuse else 0))
        self.assertFalse((self.root/'.data').exists())
    def test_default_fresh_five_vs_explicit_two_cached_notices(self):
        with mock.patch.object(demo,'flipper_notice_cache',side_effect=AssertionError('default read cache')):r=self.fetch()
        self.packet(r);self.assertEqual((r['new_network_requests'],r['received_bytes'],r['transfer_count']),(5,1111660,5));self.assertIsNone(r['prior_cache_acquisition'])
        self.calls=[];self.cfg['default_output']='.data/pico-flipper-demo-cache';self.out=self.root/self.cfg['default_output'];self.cache_inputs();r=self.fetch(True);self.packet(r)
        self.assertEqual((r['new_network_requests'],r['received_bytes'],r['reused_input_files'],r['reused_input_bytes'],r['transfer_count']),(3,1104226,2,7434,5))
        self.assertEqual(set(self.calls),set(self.payloads)-set(demo.FLIPPER_NOTICE_NAMES));self.assertIsNone(r['prior_cache_acquisition']['wall_seconds']);self.assertIsNone(r['prior_cache_acquisition']['full_cpu_seconds']);self.assertFalse(r['prior_cache_acquisition']['comparative_accounting_complete'])
    def test_bad_cache_scope_and_aliased_notice_refuse_without_fallback(self):
        self.cache_inputs(lambda summary,tree:summary.update(commit='0'*40))
        with self.assertRaises(ValueError):self.fetch(True)
        self.assertFalse(self.calls);self.assertFalse(self.out.exists());self.cache_inputs()
        p=self.cache/'README.md';other=self.root/'other';other.write_bytes(p.read_bytes());p.unlink();p.symlink_to(other)
        with self.assertRaises(Exception):self.fetch(True)
        self.assertFalse(self.calls);self.assertFalse(self.out.exists())
    def test_late_cache_drift_is_retained_failed_not_acquired(self):
        self.cache_inputs()
        def drift(row,record,target,allowance,remaining):
            raw=self.transport(row,record,target,allowance,remaining);p=self.cache/'README.md';p.write_bytes(p.read_bytes()+b' ');return raw
        with self.assertRaises(Exception):self.fetch(True,drift)
        self.assertEqual(len(self.calls),1);r=demo.publication.read_json(self.out/'result.json');self.assertFalse(r['accepted']);self.assertFalse(r['cache_inputs_current']);self.assertNotEqual(r['status'],'acquired_unqualified')
    def test_two_mib_cannot_succeed_by_omitting_sources_or_notices(self):
        self.cfg['output_byte_cap']=2*1024**2
        with self.assertRaises(Exception):self.fetch()
        self.assertEqual(demo.verify_project(self.out/'project',profile_id='pico-flipper')['file_count'],5)
        self.assertEqual(self.cfg['output_byte_cap'],2*1024**2)
        self.assertFalse(any(json.loads(p.read_text()).get('accepted') is True for p in self.out.glob('*result*.json')))
    def test_wrong_profile_flag_hierarchy_and_original_registry(self):
        for profile,flag in [('led',True),('navigation-switch',True),('pico-flipper',1)]:
            with self.subTest(profile=profile,flag=flag),self.assertRaisesRegex(ValueError,'Flipper-only'):
                demo.fetch_demo(demo.fixed_profile(profile)['default_output'],profile_id=profile,root=self.root,fetch=True,reuse_flipper_notices=flag,transport=self.transport)
        self.cfg['directories'].append('extra')
        with self.assertRaisesRegex(ValueError,'hierarchy'):self.fetch()
        self.assertFalse(self.calls);self.assertFalse((self.root/'.data').exists())
        from experiments.original_project_native_v1 import driver
        self.assertEqual(driver.CASES['pico-flipper'],('portable-demo',self.public['board_path'],self.public['commit'],None));self.assertIn('pico-flipper',driver.REFILLED_ORIGINALS)
if __name__=='__main__':unittest.main()
