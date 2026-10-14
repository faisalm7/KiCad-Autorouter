"""Unexecuted draft controls: authored payloads, no GET/native/engine work."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock
from scripts import fetch_led_demo as demo
from tests import test_uv_demo_fetch as uv_controls


class NavigationFetchControls(unittest.TestCase):
    transport=uv_controls.UVFetchControls.transport

    def setUp(self):
        scratch=demo.ROOT/'.cache';scratch.mkdir(exist_ok=True)
        temp=tempfile.TemporaryDirectory(dir=scratch);self.addCleanup(temp.cleanup)
        self.root=Path(temp.name).resolve();self.calls=[];self.payloads={}
        for name in (*demo.MATERIAL,*demo.ARC_MATERIAL):
            path=self.root/name;path.parent.mkdir(parents=True,exist_ok=True)
            path.write_bytes((demo.ROOT/name).read_bytes())
        self.public=demo.fixed_profile('navigation-switch');self.cfg=copy.deepcopy(self.public)
        self.cfg['default_output']='.data/navigation-switch-demo-test'
        for row in self.cfg['rows']:
            prefix=('authored Navigation fixture '+row['source_path']+'\n').encode()
            raw=prefix+b'x'*(row['bytes']-len(prefix));self.payloads[row['source_path']]=raw
            row['sha256']=demo.shared.sha(raw)
            row['git_blob_sha1']=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
        patch=mock.patch.object(demo,'NAV_PROFILE',self.cfg);patch.start();self.addCleanup(patch.stop)
        self.out=self.root/self.cfg['default_output'];self.cache=self.root/demo.NAV_CACHE_DIRECTORY
        self.proof_names={k:k for k in demo.NAV_CACHE_PINS};self.fixture_pins={}
        patch=mock.patch.object(demo,'NAV_CACHE_PINS',self.fixture_pins);patch.start();self.addCleanup(patch.stop)

    def cache_inputs(self, *, summary_change=None, tree_change=None, manifest_change=None):
        self.cache.mkdir(parents=True,exist_ok=True)
        rows={r['source_path']:r for r in self.cfg['rows']};documents=[]
        for name in demo.NAV_NOTICE_NAMES:
            row=rows[name];raw=self.payloads[name];(self.cache/name).write_bytes(raw)
            documents.append(dict(path=name,url=row['raw_url'],bytes=len(raw),sha256=demo.shared.sha(raw)))
        summary=dict(repository=self.cfg['repository'],commit=self.cfg['commit'],tree_sha=self.cfg['commit'],
            source_url='https://github.com/'+self.cfg['repository']+'/tree/'+self.cfg['commit'],
            metadata_complete=True,board_payloads_downloaded=0,status='metadata_only_not_acquired',metadata_documents=documents)
        tree=dict(sha=self.cfg['commit'],truncated=False,tree=[dict(path=r['source_path'],type='blob',mode=r['mode'],
            size=r['bytes'],sha=r['git_blob_sha1']) for r in self.cfg['rows']])
        if summary_change:summary_change(summary)
        if tree_change:tree_change(tree)
        for name,doc in [('summary.json',summary),('tree.json',tree)]:
            path=self.cache/name;path.write_text(json.dumps(doc));self.fixture_pins[demo.NAV_CACHE_DIRECTORY+'/'+name]=demo.shared.sha(path.read_bytes())
        manifest_files={str(path.relative_to(self.root/'.runs/corpus-next-001')):demo.shared.sha(path.read_bytes()) for path in self.cache.iterdir()}
        manifest=dict(schema=1,files=manifest_files)
        if manifest_change:manifest_change(manifest)
        name='.runs/corpus-next-001/metadata-sha256.json';path=self.root/name
        path.write_text(json.dumps(manifest));self.fixture_pins[name]=demo.shared.sha(path.read_bytes())

    def fetch(self,reuse=False,transport=None):
        return demo.fetch_demo(self.cfg['default_output'],profile_id='navigation-switch',fetch=True,
            root=self.root,transport=transport or self.transport,reuse_navigation_notices=reuse)

    def assert_packet(self,result):
        self.assertEqual(result['status'],'acquired_unqualified');self.assertTrue(result['source_files_exact'])
        self.assertTrue(result['cache_inputs_current']);self.assertTrue(result['within_budget'])
        self.assertFalse(result['accepted']);self.assertFalse(result['native_accepted']);self.assertFalse(result['independent_ancestry_established'])
        self.assertEqual((result['engine_jobs'],result['native_jobs'],result['models_downloaded']),(0,0,0))
        original=demo.verify_project(self.out/'project',profile_id='navigation-switch')
        native=demo.verify_project(self.out/'native-project',profile_id='navigation-switch',native_packet=True)
        self.assertEqual((original['file_count'],original['bytes']),(5,969575))
        self.assertEqual((native['file_count'],native['bytes']),(7,976987))
        self.assertFalse((self.out/'responses').exists());self.assertEqual(result['response_layout'],'project')
        self.assertLess(result['output_bytes'],2*1024**2)
        for name,raw in self.payloads.items():self.assertEqual((self.out/'project'/name).read_bytes(),raw)
        for name,origin in self.cfg['native_packet_notice_copies'].items():
            self.assertEqual((self.out/'native-project'/name).read_bytes(),self.payloads[origin])
        for row in result['requests']:self.assertEqual(row['artifact'],'project/'+row['source_path'])

    def test_fixed_counts_pins_finite_caps_and_plan_without_cache_reads(self):
        self.assertEqual((self.public['file_count'],self.public['bytes'],self.public['native_packet_files'],self.public['native_packet_bytes']),
            (5,969575,7,976987))
        self.assertEqual((self.public['wall_budget_seconds'],self.public['cpu_budget_seconds'],self.public['output_byte_cap'],self.public['max_requests']),
            (300,300,2*1024**2,5))
        self.assertEqual(self.public['commit'],'b64c0dac2134d69963bf28120305bd79aad3c8ac')
        self.assertEqual(self.public['directories'],['Hardware'])
        self.assertEqual(sum(r['bytes'] for r in self.public['rows']),969575)
        for row in self.public['rows']:
            self.assertEqual(row['raw_url'],'https://raw.githubusercontent.com/'+self.public['repository']+'/'+self.public['commit']+'/'+row['source_path'])
        for reuse,count in ((False,5),(True,3)):
            plan=demo.fetch_demo(self.cfg['default_output'],profile_id='navigation-switch',root=self.root,
                transport=lambda *args:self.fail('plan transported'),reuse_navigation_notices=reuse)
            self.assertEqual((plan['network_requests'],plan['planned_network_requests']),(0,count))
            self.assertEqual(plan['planned_cached_notices'],2 if reuse else 0)
        self.assertFalse(self.cache.exists());self.assertFalse((self.root/'.data').exists())

    def test_default_fresh_transport_has_five_gets_and_no_cache_access(self):
        with mock.patch.object(demo,'navigation_notice_cache',side_effect=AssertionError('default read cache')):
            result=self.fetch()
        self.assert_packet(result)
        self.assertEqual((result['new_network_requests'],result['received_bytes'],result['transfer_count']),(5,969575,5))
        self.assertEqual(len(self.calls),5);self.assertIsNone(result['prior_cache_acquisition'])

    def test_explicit_cache_two_notices_are_not_new_http_or_zero_old_cost(self):
        self.cache_inputs();result=self.fetch(True);self.assert_packet(result)
        self.assertEqual((result['new_network_requests'],result['received_bytes'],result['transfer_count']),(3,962163,5))
        self.assertEqual((result['reused_input_files'],result['reused_input_bytes']),(2,7412))
        self.assertEqual(set(self.calls),set(self.payloads)-set(demo.NAV_NOTICE_NAMES))
        prior=result['prior_cache_acquisition'];self.assertIsNone(prior['wall_seconds']);self.assertIsNone(prior['full_cpu_seconds'])
        self.assertFalse(prior['comparative_accounting_complete']);self.assertIn('not zero',prior['cost_status'])
        for row in result['requests']:
            if row['transport']=='verified_cache':
                self.assertNotIn('http_status',row);self.assertEqual(row['received_bytes'],0)
                self.assertEqual(row['status'],'verified_cache_copied')

    def test_missing_or_changed_notice_or_receipt_never_falls_back(self):
        self.fixture_pins.update(self.proof_names)
        with self.assertRaises(Exception):self.fetch(True)
        self.assertFalse(self.calls);self.assertFalse(self.out.exists())
        self.cache_inputs();body=self.cache/'LICENSE.md';raw=body.read_bytes();body.write_bytes(b'z'+raw[1:])
        with self.assertRaisesRegex(ValueError,'payload hash'):self.fetch(True)
        self.assertFalse(self.calls);self.assertFalse(self.out.exists())
        body.write_bytes(raw);summary=self.cache/'summary.json';summary.write_bytes(summary.read_bytes()+b' ')
        with self.assertRaisesRegex(ValueError,'metadata pin'):self.fetch(True)
        self.assertFalse(self.calls);self.assertFalse(self.out.exists())

    def test_aliased_cache_body_rejects_before_output(self):
        self.cache_inputs();path=self.cache/'README.md';target=self.root/'other';target.write_bytes(path.read_bytes())
        path.unlink();path.symlink_to(target)
        with self.assertRaises(Exception):self.fetch(True)
        self.assertFalse(self.calls);self.assertFalse(self.out.exists())

    def test_pinned_summary_url_tree_duplicate_and_manifest_mismatch_reject(self):
        controls=[dict(summary_change=lambda s:s['metadata_documents'][0].update(url='https://example.invalid/notice')),
            dict(tree_change=lambda t:t['tree'].append(copy.deepcopy(t['tree'][0]))),
            dict(manifest_change=lambda m:m['files'].update({'metadata/sparkfun__SparkFun_Qwiic_Navigation_Switch/LICENSE.md':'0'*64}))]
        for change in controls:
            with self.subTest(change=next(iter(change))):
                self.cache_inputs(**change)
                with self.assertRaises(ValueError):self.fetch(True)
                self.assertFalse(self.calls);self.assertFalse(self.out.exists())

    def test_cache_drift_during_and_after_publication_invalidates(self):
        self.cache_inputs();path=self.cache/'README.md'
        def drift(row,record,target,allowance,remaining):
            raw=self.transport(row,record,target,allowance,remaining)
            path.write_bytes(path.read_bytes()+b' ');return raw
        with self.assertRaises(Exception):self.fetch(True,drift)
        self.assertEqual(len(self.calls),1);self.assertFalse(demo.publication.read_json(self.out/'result.json')['cache_inputs_current'])
        self.cfg['default_output']='.data/navigation-switch-demo-tail';self.out=self.root/self.cfg['default_output']
        path.write_bytes(self.payloads['README.md']);real=demo.publication.publish;calls=[]
        def tail(output,record,*args,**kwargs):
            result=real(output,record,*args,**kwargs);calls.append(True)
            if len(calls)==1:(self.cache/'summary.json').write_bytes((self.cache/'summary.json').read_bytes()+b' ')
            return result
        with mock.patch.object(demo.publication,'publish',side_effect=tail),self.assertRaises(Exception):self.fetch(True)
        result=demo.publication.read_json(self.out/'result.json')
        self.assertEqual(result['status'],'invalidated');self.assertFalse(result['accepted']);self.assertFalse(result['cache_inputs_current'])
        self.assertTrue(result['source_files_exact'])  # Immutable copied population remains literally exact.
        self.assertTrue(list(self.out.glob('invalidated-result-*')))

    def test_direct_hardware_parent_replacement_blocks_delayed_writer(self):
        victim=self.root/'victim';victim.mkdir()
        def replaced(row,record,target,allowance,remaining):
            if row['source_path'].startswith('Hardware/'):
                hardware=self.out/'project/Hardware';hardware.rename(self.out/'project/Hardware-preserved')
                hardware.symlink_to(victim,target_is_directory=True)
                with target.open('xb') as stream:stream.write(self.payloads[row['source_path']])
            return self.transport(row,record,target,allowance,remaining)
        with self.assertRaises(Exception):self.fetch(False,replaced)
        self.assertEqual(list(victim.iterdir()),[])
        self.assertFalse((self.out/'native-project').exists())

    def test_wrong_profile_bad_flag_and_nonfixed_hierarchy_reject_before_output(self):
        for profile,flag in (('led',True),('uv-dosimeter',True),('navigation-switch',1)):
            with self.subTest(profile=profile,flag=flag),self.assertRaisesRegex(ValueError,'Navigation-only'):
                demo.fetch_demo(demo.fixed_profile(profile)['default_output'],profile_id=profile,root=self.root,fetch=True,
                    transport=self.transport,reuse_navigation_notices=flag)
        self.cfg['directories'].append('extra')
        with self.assertRaisesRegex(ValueError,'hierarchy'):self.fetch()
        self.assertFalse(self.calls);self.assertFalse((self.root/'.data').exists())

    def test_original_diagnostic_registry_is_portable_refill_only(self):
        from experiments.original_project_native_v1 import driver
        self.assertEqual(driver.CASES['navigation-switch'],('portable-demo',self.public['board_path'],self.public['commit'],None))
        self.assertIn('navigation-switch',driver.REFILLED_ORIGINALS)

    def test_cpu_exhaustion_stops_after_first_transfer_without_acceptance(self):
        elapsed=[0.0]
        def exhausted(row,record,target,allowance,remaining):
            raw=self.transport(row,record,target,allowance,remaining);elapsed[0]=301.0;return raw
        with mock.patch.object(demo,'cpu',side_effect=lambda:elapsed[0]),self.assertRaises(TimeoutError):
            self.fetch(False,exhausted)
        self.assertEqual(len(self.calls),1);self.assertFalse((self.out/'native-project').exists())

    def test_output_cap_rejection_does_not_increase_limit_or_drop_originals(self):
        self.cfg['output_byte_cap']=self.cfg['bytes']+self.cfg['native_packet_bytes']-1
        with self.assertRaises(ValueError):self.fetch()
        self.assertEqual(self.cfg['output_byte_cap'],1946561)
        self.assertEqual(demo.verify_project(self.out/'project',profile_id='navigation-switch')['file_count'],5)
        self.assertFalse(any(json.loads(path.read_text()).get('accepted') is True for path in self.out.glob('*result*.json')))


if __name__=='__main__':unittest.main()
