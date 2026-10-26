"""Draft authored-byte custody controls; no actual HTTP, Native or support proof."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock
from scripts import fetch_led_demo as demo
from tests import test_uv_demo_fetch as uv_controls


class AP3012KFetchControls(unittest.TestCase):
    transport = uv_controls.UVFetchControls.transport

    def setUp(self):
        scratch = demo.ROOT/'.cache'
        scratch.mkdir(exist_ok=True)
        temp = tempfile.TemporaryDirectory(dir=scratch)
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        self.calls = []
        self.payloads = {}
        for name in (*demo.MATERIAL, *demo.ARC_MATERIAL):
            path = self.root/name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes((demo.ROOT/name).read_bytes())
        self.public = demo.fixed_profile('ap3012k-boost')
        self.cfg = copy.deepcopy(self.public)
        self.cfg['default_output'] = '.data/ap3012k-boost-demo-test'
        for row in self.cfg['rows']:
            prefix = ('authored AP3012K custody fixture '+row['source_path']+'\n').encode()
            raw = prefix+b'x'*(row['bytes']-len(prefix))
            self.payloads[row['source_path']] = raw
            row.update(sha256=demo.shared.sha(raw),
                git_blob_sha1=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest())
        patch = mock.patch.object(demo, 'AP3012K_PROFILE', self.cfg)
        patch.start()
        self.addCleanup(patch.stop)
        self.out = self.root/self.cfg['default_output']

    def fetch(self, transport=None):
        return demo.fetch_demo(self.cfg['default_output'], profile_id='ap3012k-boost',
            root=self.root, fetch=True, transport=transport or self.transport)

    def assert_packet(self, result):
        self.assertEqual(result['status'], 'acquired_unqualified')
        self.assertTrue(result['source_files_exact'])
        self.assertTrue(result['within_budget'])
        self.assertFalse(result['accepted'])
        self.assertFalse(result['native_accepted'])
        self.assertFalse(result['independent_ancestry_established'])
        self.assertEqual((result['native_jobs'], result['engine_jobs'], result['models_downloaded']), (0, 0, 0))
        self.assertEqual((result['new_network_requests'], result['received_bytes'], result['transfer_count']),
            (8, 4515310, 8))
        self.assertIsNone(result['prior_cache_acquisition'])
        original = demo.verify_project(self.out/'project', profile_id='ap3012k-boost')
        packet = demo.verify_project(self.out/'native-project', profile_id='ap3012k-boost', native_packet=True)
        self.assertEqual((original['file_count'], original['bytes'], packet['file_count'], packet['bytes']),
            (8, 4515310, 10, 4522786))
        self.assertGreaterEqual(result['output_bytes'], 9038096)
        self.assertLess(result['output_bytes'], demo.shared.CAP)
        self.assertFalse((self.out/'responses').exists())
        for name, raw in self.payloads.items():
            self.assertEqual((self.out/'project'/name).read_bytes(), raw)
            self.assertEqual((self.out/'native-project'/name).read_bytes(), raw)
        for name, origin in self.cfg['native_packet_notice_copies'].items():
            self.assertEqual((self.out/'native-project'/name).read_bytes(), self.payloads[origin])

    def test_exact_profile_pins_PRL_cache_notices_and_unchanged_global_caps(self):
        cfg = self.public
        by = {row['source_path']:row for row in cfg['rows']}
        self.assertEqual((cfg['commit'], cfg['file_count'], cfg['bytes'], cfg['native_packet_bytes']),
            ('2150213414cbaf2031fed3081900049d023473f1', 8, 4515310, 4522786))
        self.assertEqual((cfg['max_requests'], cfg['network_byte_cap'], cfg['max_single_response_bytes']),
            (8, 4515318, 3642500))
        self.assertEqual((cfg['wall_budget_seconds'], cfg['cpu_budget_seconds'], cfg['output_byte_cap']),
            (300, 300, demo.shared.CAP))
        self.assertEqual(demo.shared.CAP, 10*1024**2)
        self.assertEqual(demo.fixed_profile()['bytes'], 161071)
        self.assertEqual(demo.fixed_profile('pico-flipper')['output_byte_cap'], 4*1024**2)
        expected = {
            'LICENSE.md':(2887, '779c526bbfbeabc5aafe9bf871f22b8189ab91ab'),
            'README.md':(4589, '0edd8b653f7b443b134b07673b33eca72291f956'),
            'Hardware/README.md':(292, '8ff294343ad0fc2d90cb9a0ea0097ce2fc69351f'),
            'Hardware/SparkFun_Qwiic_5V_Boost_AP3012K.kicad_pcb':(608612, '794c42a1686de8bc3b819958d1e6061450be7a28'),
            'Hardware/SparkFun_Qwiic_5V_Boost_AP3012K.kicad_pro':(15148, '7d37205dd60cedffa64ef35092cc663fb0c86f31'),
            'Hardware/SparkFun_Qwiic_5V_Boost_AP3012K.kicad_prl':(1335, 'ad898a3111f1c687417b94a741a81bd3a154dc67'),
            'Hardware/SparkFun_Qwiic_5V_Boost_AP3012K.kicad_sch':(239948, '9aa8a40f67b4ec4553ceb955081e6b48b00ef2e7'),
            'Hardware/fp-info-cache':(3642499, 'e6d2dd4bc0e52ef5c4bb4d20c45a213a0ce8e2d3')}
        self.assertEqual({name:(row['bytes'], row['git_blob_sha1']) for name,row in by.items()}, expected)
        self.assertEqual({name for name,row in by.items() if 'sha256' in row},
            {'LICENSE.md', 'README.md', 'Hardware/README.md'})
        for name, row in by.items():
            self.assertEqual(row['mode'], '100644')
            self.assertEqual(row['raw_url'], 'https://raw.githubusercontent.com/'+cfg['repository']+'/'+cfg['commit']+'/'+name)
        self.assertIn('no unrestricted rerouting', demo.AP3012K_RIGHTS)
        self.assertFalse(cfg['native_validation_performed_by_fetch'])
        cfg['rows'][0]['git_blob_sha1'] = '0'*40
        self.assertNotEqual(demo.fixed_profile('ap3012k-boost')['rows'][0]['git_blob_sha1'], '0'*40)

    def test_offline_plan_has_eight_transfers_and_no_output_or_cache_requirement(self):
        plan = demo.fetch_demo(self.cfg['default_output'], profile_id='ap3012k-boost', root=self.root,
            transport=lambda *args:self.fail('plan transported'))
        self.assertEqual((plan['action'], plan['network_requests'], plan['planned_network_requests'], plan['planned_bytes']),
            ('plan_only', 0, 8, 4515310))
        self.assertFalse((self.root/'.data').exists())
        self.assertFalse((self.root/'.runs').exists())

    def test_full_sized_packet_keeps_PRL_cache_and_readonly_capture(self):
        result = self.fetch()
        self.assert_packet(result)
        before = demo.shared.inventory(self.out)
        base, files = demo.capture_native_source('ap3012k-boost', root=self.root)
        self.assertEqual(base, self.out/'native-project')
        self.assertEqual(files, {**self.payloads,
            **{name:self.payloads[origin] for name,origin in self.cfg['native_packet_notice_copies'].items()}})
        self.assertEqual(demo.shared.inventory(self.out), before)

    def test_mandatory_PRL_cache_and_notice_missing_changed_or_symlinked_refuse(self):
        self.fetch()
        base = self.out/'native-project'
        for name in ('Hardware/SparkFun_Qwiic_5V_Boost_AP3012K.kicad_prl', 'Hardware/fp-info-cache',
                'Hardware/README.md', 'Hardware/_licenses/creator/LICENSE.md'):
            for fault in ('missing', 'changed', 'symlink'):
                with self.subTest(name=name, fault=fault):
                    path = base/name
                    raw = path.read_bytes()
                    path.unlink()
                    if fault == 'changed':path.write_bytes(b'z'+raw[1:])
                    elif fault == 'symlink':path.symlink_to(base/'README.md')
                    with self.assertRaises(ValueError):demo.capture_native_source('ap3012k-boost', root=self.root)
                    if fault != 'missing':path.unlink()
                    path.write_bytes(raw)
        self.assertEqual((self.out/'project/Hardware/fp-info-cache').read_bytes(), self.payloads['Hardware/fp-info-cache'])

    def test_wrong_cache_blob_without_SHA_stops_and_keeps_failed_bytes(self):
        next(row for row in self.cfg['rows'] if row['source_path']=='Hardware/fp-info-cache').pop('sha256')
        self.payloads['Hardware/fp-info-cache'] = b'z'+self.payloads['Hardware/fp-info-cache'][1:]
        result = self.fetch()
        self.assertEqual(result['status'], 'failed')
        self.assertEqual(len(self.calls), 8)
        self.assertIn('payload hash', result['first_failure'])
        self.assertFalse(result['source_files_exact'])
        self.assertFalse(result['accepted'])
        self.assertFalse((self.out/'native-project').exists())
        self.assertEqual((self.out/'project/Hardware/fp-info-cache').read_bytes(), self.payloads['Hardware/fp-info-cache'])

    def test_collision_namespace_hierarchy_and_wrong_reuse_flags_refuse(self):
        self.out.mkdir(parents=True)
        (self.out/'owner').write_bytes(b'keep')
        with self.assertRaises(ValueError):self.fetch()
        self.assertEqual((self.out/'owner').read_bytes(), b'keep')
        for name in ('../outside', '.data/led-demo-wrong', '.data/ap3012k-boost-demo-a/child'):
            with self.assertRaises(ValueError):
                demo.fetch_demo(name, profile_id='ap3012k-boost', root=self.root, fetch=True, transport=self.transport)
        for flag in ('reuse_uv_licenses', 'reuse_navigation_notices', 'reuse_audio_notices', 'reuse_flipper_notices'):
            with self.assertRaises(ValueError):
                demo.fetch_demo('.data/ap3012k-boost-demo-other', profile_id='ap3012k-boost', root=self.root,
                    fetch=True, transport=self.transport, **{flag:True})
        self.cfg['directories'].append('Hardware/foreign.pretty')
        with self.assertRaisesRegex(ValueError, 'hierarchy'):
            demo.fetch_demo('.data/ap3012k-boost-demo-other', profile_id='ap3012k-boost', root=self.root,
                fetch=True, transport=self.transport)
        self.assertFalse(self.calls)

    def test_replaced_hardware_parent_blocks_delayed_writer(self):
        victim = self.root/'victim'
        victim.mkdir()
        def replaced(row, record, target, allowance, remaining):
            if row['source_path'].startswith('Hardware/'):
                hardware = self.out/'project/Hardware'
                hardware.rename(self.out/'project/retained-Hardware')
                hardware.symlink_to(victim, target_is_directory=True)
            return self.transport(row, record, target, allowance, remaining)
        with self.assertRaises(Exception):self.fetch(replaced)
        self.assertEqual(list(victim.iterdir()), [])
        self.assertFalse((self.out/'native-project').exists())

    def test_late_native_PRL_drift_invalidates_receipt_and_preserves_original(self):
        real = demo.publication.publish
        calls = []
        def stale(output, record, *args, **kwargs):
            value = real(output, record, *args, **kwargs)
            calls.append(output)
            if len(calls)==1:
                (output/'native-project/Hardware/SparkFun_Qwiic_5V_Boost_AP3012K.kicad_prl').write_bytes(b'late drift')
            return value
        with mock.patch.object(demo.publication, 'publish', side_effect=stale), self.assertRaises(ValueError):self.fetch()
        result = demo.publication.read_json(self.out/'result.json')
        self.assertEqual(result['status'], 'invalidated')
        self.assertFalse(result['source_files_exact'])
        self.assertFalse(result['accepted'])
        self.assertTrue(list(self.out.glob('invalidated-result-*')))
        name = 'Hardware/SparkFun_Qwiic_5V_Boost_AP3012K.kicad_prl'
        self.assertEqual((self.out/'project'/name).read_bytes(), self.payloads[name])

    def test_insufficient_cap_cannot_drop_cache_PRL_or_notices(self):
        self.cfg['output_byte_cap'] = 9038095
        with self.assertRaises(ValueError):self.fetch()
        self.assertEqual(self.cfg['output_byte_cap'], 9038095)
        self.assertEqual(demo.verify_project(self.out/'project', profile_id='ap3012k-boost')['file_count'], 8)
        self.assertFalse(any(json.loads(path.read_text()).get('accepted') for path in self.out.glob('*result*.json')))


if __name__=='__main__':unittest.main()
