"""Fixed UV acquisition/cache controls; authored bytes, no GET/native execution."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock
from scripts import fetch_led_demo as demo


class UVFetchControls(unittest.TestCase):
    def setUp(self):
        scratch=demo.ROOT/'.cache';scratch.mkdir(exist_ok=True)
        temp=tempfile.TemporaryDirectory(dir=scratch);self.addCleanup(temp.cleanup)
        self.root=Path(temp.name).resolve()
        for name in (*demo.MATERIAL,*demo.ARC_MATERIAL):
            path=self.root/name;path.parent.mkdir(parents=True,exist_ok=True)
            path.write_bytes((demo.ROOT/name).read_bytes())
        self.public=demo.fixed_profile('uv-dosimeter');self.cfg=copy.deepcopy(self.public)
        self.payloads={};self.calls=[]
        for row in self.cfg['rows']:
            prefix=('authored UV fixture '+row['source_path']+'\n').encode()
            raw=prefix+b'x'*(row['bytes']-len(prefix));self.payloads[row['source_path']]=raw
            row['sha256']=demo.shared.sha(raw)
            row['git_blob_sha1']=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
        patch=mock.patch.object(demo,'UV_PROFILE',self.cfg);patch.start();self.addCleanup(patch.stop)
        self.out=self.root/'.data/uv-dosimeter-demo-test'
        self.cache=self.root/demo.UV_CACHE_DIRECTORY
        self.proof_name=self.cache/'fetch-result.json'

    def cache_inputs(self):
        rows={row['source_path']:row for row in self.cfg['rows']}; requests=[]
        for name in demo.UV_LICENSE_NAMES:
            row=rows[name];raw=self.payloads[name];path=self.cache/'licenses'/name
            path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
            requests.append(dict(source_path=name,bytes=len(raw),received_bytes=len(raw),
                git_blob_sha1=row['git_blob_sha1'],sha256=row['sha256'],response_sha256=row['sha256'],
                url=row['raw_url'],final_url=row['raw_url'],http_status=200,payload_verified=True))
        proof=dict(passed=True,source_profile_sha256=demo.UV_CACHE_PROFILE_SHA256,
            new_network_requests=3,received_bytes=35778,requests=requests,
            wall_seconds=0.1,full_cpu_seconds=0.01,bootstrap_emission_allowance_seconds=2)
        self.proof_name.write_text(json.dumps(proof))
        patch=mock.patch.object(demo,'UV_CACHE_RECEIPT_SHA256',demo.shared.sha(self.proof_name.read_bytes()))
        patch.start();self.addCleanup(patch.stop)

    def transport(self,row,record,path,allowance,remaining):
        remaining();self.calls.append(row['source_path']);raw=self.payloads[row['source_path']]
        with path.open('xb') as stream:stream.write(raw)
        record.update(received_bytes=len(raw),response_sha256=demo.shared.sha(raw),url=row['raw_url'],
            status='response_received',http_status=200,wall_seconds=0.0)
        return raw

    def fetch(self,reuse=False,transport=None):
        return demo.fetch_demo('.data/uv-dosimeter-demo-test',profile_id='uv-dosimeter',fetch=True,
            root=self.root,transport=transport or self.transport,reuse_uv_licenses=reuse)

    def test_fixed_profile_limits_paths_notices_and_no_get_plan(self):
        self.assertEqual((self.public['file_count'],self.public['bytes'],self.public['max_requests'],self.public['output_byte_cap']),
                         (11,502046,11,2*1024**2))
        self.assertEqual(self.public['commit'],'63153ac5ca9879299f57e3fb68df606bf78d96f8')
        self.assertEqual(self.public['native_packet_files'],14)
        self.assertEqual(self.public['native_packet_bytes'],535087)
        self.assertEqual(self.public['directories'],['docs','hardware','hardware/Moje_wearable.pretty'])
        docs=next(row for row in self.public['rows'] if row['source_path']=='docs/LICENSE')
        self.assertEqual(docs['sha256'],'28a9529c7d0bb4dc51f4bf5c116a3d16ef247a052f7591466768ddf563fd1cf5')
        for row in self.public['rows']:
            self.assertEqual(row['raw_url'],'https://raw.githubusercontent.com/'+self.public['repository']+'/'+self.public['commit']+'/'+row['source_path'])
        for reuse,count in ((False,11),(True,8)):
            plan=demo.fetch_demo('.data/uv-dosimeter-demo-test',profile_id='uv-dosimeter',root=self.root,
                transport=lambda *args:self.fail('plan transported'),reuse_uv_licenses=reuse)
            self.assertEqual(plan['network_requests'],0);self.assertEqual(plan['planned_network_requests'],count)
            self.assertFalse((self.root/'.data').exists());self.assertFalse(self.cache.exists())

    def assert_packet(self,result):
        self.assertEqual(result['status'],'acquired_unqualified');self.assertTrue(result['source_files_exact'])
        self.assertTrue(result['cache_inputs_current'])
        self.assertTrue(result['within_budget']);self.assertFalse(result['accepted']);self.assertFalse(result['native_accepted'])
        original=demo.verify_project(self.out/'project',profile_id='uv-dosimeter')
        native=demo.verify_project(self.out/'native-project',profile_id='uv-dosimeter',native_packet=True)
        self.assertEqual((original['file_count'],original['bytes']),(11,502046))
        self.assertEqual((native['file_count'],native['bytes']),(14,535087))
        for name,raw in self.payloads.items():self.assertEqual((self.out/'project'/name).read_bytes(),raw)
        for name,origin in self.cfg['native_packet_notice_copies'].items():
            self.assertEqual((self.out/'native-project'/name).read_bytes(),self.payloads[origin])

    def test_default_fresh_transport_never_looks_for_cache(self):
        result=self.fetch();self.assert_packet(result)
        self.assertEqual((result['new_network_requests'],result['received_bytes'],result['transfer_count']), (11,502046,11))
        self.assertEqual(result['reused_input_files'],0);self.assertEqual(len(self.calls),11)
        self.assertIsNone(result['prior_cache_acquisition'])

    def test_three_cached_licenses_are_not_new_http_responses(self):
        self.cache_inputs();result=self.fetch(True);self.assert_packet(result)
        self.assertEqual((result['new_network_requests'],result['received_bytes'],result['transfer_count']), (8,466268,11))
        self.assertEqual((result['reused_input_files'],result['reused_input_bytes']),(3,35778))
        self.assertEqual(set(self.calls),set(self.payloads)-set(demo.UV_LICENSE_NAMES))
        self.assertEqual(result['prior_cache_acquisition']['new_network_requests'],3)
        cached=[row for row in result['requests'] if row['transport']=='verified_cache']
        self.assertEqual(len(cached),3)
        for row in cached:
            self.assertEqual(row['received_bytes'],0);self.assertNotIn('http_status',row)
            self.assertEqual(row['status'],'verified_cache_copied')
        self.assertLess(result['output_bytes'],2*1024**2)

    def test_missing_corrupt_or_aliased_cache_has_no_network_fallback(self):
        with self.assertRaises(Exception):self.fetch(True)
        self.assertFalse(self.calls);self.assertFalse(self.out.exists())
        self.cache_inputs();path=self.cache/'licenses/LICENSE';raw=path.read_bytes()
        path.write_bytes(b'z'+raw[1:])
        with self.assertRaisesRegex(ValueError,'payload hash'):self.fetch(True)
        self.assertFalse(self.calls);self.assertFalse(self.out.exists())
        path.write_bytes(raw);target=self.root/'target';target.write_bytes(raw);path.unlink();path.symlink_to(target)
        with self.assertRaises(Exception):self.fetch(True)
        self.assertFalse(self.calls);self.assertFalse(self.out.exists())

    def test_changed_proof_is_refused_before_first_transport(self):
        self.cache_inputs();self.proof_name.write_bytes(self.proof_name.read_bytes()+b' ')
        with self.assertRaisesRegex(ValueError,'receipt pin'):self.fetch(True)
        self.assertFalse(self.calls);self.assertFalse(self.out.exists())

    def test_cache_drift_during_and_after_publication_invalidates(self):
        self.cache_inputs();path=self.cache/'licenses/hardware/LICENSE'
        def drift(row,record,target,allowance,remaining):
            raw=self.transport(row,record,target,allowance,remaining)
            path.write_bytes(path.read_bytes()+b' ');return raw
        with self.assertRaises(Exception):self.fetch(True,drift)
        self.assertEqual(len(self.calls),1)
        self.assertFalse(demo.publication.read_json(self.out/'result.json')['source_files_exact'])
        # Distinct output retains the original failed attempt.
        self.out=self.root/'.data/uv-dosimeter-demo-tail';path.write_bytes(self.payloads['hardware/LICENSE'])
        real=demo.publication.publish;calls=[]
        def tail(output,record,*args,**kwargs):
            result=real(output,record,*args,**kwargs);calls.append(True)
            if len(calls)==1:self.proof_name.write_bytes(self.proof_name.read_bytes()+b' ')
            return result
        with mock.patch.object(demo.publication,'publish',side_effect=tail),self.assertRaises(Exception):
            demo.fetch_demo('.data/uv-dosimeter-demo-tail',profile_id='uv-dosimeter',fetch=True,root=self.root,
                transport=self.transport,reuse_uv_licenses=True)
        result=demo.publication.read_json(self.out/'result.json')
        self.assertEqual(result['status'],'invalidated');self.assertTrue(result['source_files_exact'])
        self.assertFalse(result['cache_inputs_current']);self.assertFalse(result['accepted'])
        self.assertEqual(demo.verify_project(self.out/'project',profile_id='uv-dosimeter')['file_count'],11)
        self.assertEqual(demo.verify_project(self.out/'native-project',profile_id='uv-dosimeter',native_packet=True)['file_count'],14)
        self.assertTrue(list(self.out.glob('invalidated-result-*')))

    def test_wrong_profile_and_bad_flag_type_reject_before_output(self):
        for profile,flag in (('led',True),('cellscan',True),('uv-dosimeter',1)):
            cfg=demo.fixed_profile(profile)
            with self.assertRaisesRegex(ValueError,'UV-only'):
                demo.fetch_demo(cfg['default_output'],profile_id=profile,root=self.root,fetch=True,reuse_uv_licenses=flag)
        self.assertFalse((self.root/'.data').exists());self.assertFalse(self.calls)

    def test_failed_uncached_transfer_keeps_actual_network_and_cached_costs(self):
        self.cache_inputs()
        def cancel(row,record,path,allowance,remaining):
            self.calls.append(row['source_path'])
            with path.open('xb') as stream:stream.write(b'partial')
            record.update(received_bytes=7,response_sha256=demo.shared.sha(b'partial'))
            raise KeyboardInterrupt('authored cancellation')
        result=self.fetch(True,cancel)
        self.assertEqual(result['status'],'cancelled');self.assertFalse(result['source_files_exact'])
        self.assertEqual((result['new_network_requests'],result['received_bytes']),(1,7))
        self.assertEqual(result['reused_input_files'],1)
        self.assertFalse((self.out/'native-project').exists())



if __name__=='__main__':unittest.main()
