"""One fixed STCC4 recipe and authored custody controls; no HTTP or Native."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from scripts import fetch_led_demo as demo
from tests import test_uv_demo_fetch as uv_controls


class STCC4FetchControls(unittest.TestCase):
    transport = uv_controls.UVFetchControls.transport

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(dir=demo.ROOT/'tests')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.public = demo.fixed_profile('co2-stcc4')
        self.cfg = copy.deepcopy(self.public)
        self.calls, self.payloads = [], {}
        for name in (*demo.MATERIAL, *demo.ARC_MATERIAL):
            path = self.root/name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes((demo.ROOT/name).read_bytes())
        for row in self.cfg['rows']:
            prefix = ('authored STCC4 fixture '+row['source_path']+'\n').encode()
            raw = prefix+b'x'*(row['bytes']-len(prefix))
            self.payloads[row['source_path']] = raw
            row.update(sha256=demo.shared.sha(raw),
                git_blob_sha1=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest())
        patch = mock.patch.object(demo, 'STCC4_PROFILE', self.cfg)
        patch.start();self.addCleanup(patch.stop)
        self.out = self.root/self.cfg['default_output']

    def fetch(self):
        return demo.fetch_demo(self.cfg['default_output'], profile_id='co2-stcc4',
            root=self.root, fetch=True, transport=self.transport)

    def test_exact_registration_and_plan_are_bounded_and_offline(self):
        cfg = self.public
        expected = {
            'LICENSE.md': (2887, '376246815f80747d16439159abde523668ee6490'),
            'README.md': (2252, 'c9fcf5292724f481d496909d063a79827f36d2e5'),
            'Hardware/SparkFun_Qwiic_CO2_Sensor_STCC4.kicad_pcb': (472335, 'b47b4d518af3bd3053839bb9434369b048763cf3'),
            'Hardware/SparkFun_Qwiic_CO2_Sensor_STCC4.kicad_pro': (18259, 'b1cd493716b4f02e8474f62e1c2417063d155f83'),
            'Hardware/SparkFun_Qwiic_CO2_Sensor_STCC4.kicad_sch': (208492, '705b0b313f926308b92ba03230d6bcae80217937')}
        self.assertEqual((cfg['commit'], cfg['file_count'], cfg['bytes'], cfg['native_packet_bytes']),
            ('836b63c8f684d57779cf0e699144ac056e0808ba', 5, 704225, 709364))
        self.assertEqual({row['source_path']: (row['bytes'], row['git_blob_sha1']) for row in cfg['rows']}, expected)
        self.assertEqual((cfg['max_requests'], cfg['network_byte_cap'], cfg['max_single_response_bytes']),
            (5, 704230, 472336))
        self.assertLessEqual(cfg['native_packet_bytes'], 1024**2)
        self.assertLessEqual(cfg['network_byte_cap'], 2*1024**2)
        self.assertEqual(cfg['output_byte_cap'], 2*1024**2)
        self.assertEqual(cfg['directories'], ['Hardware'])
        self.assertFalse(cfg['native_validation_performed_by_fetch'])
        self.assertFalse(cfg['independent_ancestry_established'])
        self.assertFalse(cfg['raw_assets_public'])
        registration = json.loads((demo.ROOT/'data/development-stcc4-001.json').read_text())
        self.assertEqual({row['source_path']: (row['bytes'], row['git_blob_sha1'])
            for row in registration['source_rows']}, expected)
        for row in cfg['rows']:
            self.assertEqual(row['mode'], '100644')
            self.assertEqual(row['raw_url'], 'https://raw.githubusercontent.com/'+cfg['repository']+'/'+cfg['commit']+'/'+row['source_path'])
        cfg['rows'][0]['bytes'] = 0
        self.assertEqual(demo.fixed_profile('co2-stcc4')['rows'][0]['bytes'], 2887)
        plan = demo.fetch_demo(self.cfg['default_output'], profile_id='co2-stcc4', root=self.root,
            transport=lambda *args: self.fail('offline plan attempted transport'))
        self.assertEqual((plan['action'], plan['network_requests'], plan['planned_network_requests'], plan['planned_bytes']),
            ('plan_only', 0, 5, 704225))
        self.assertFalse((self.root/'.data').exists())
        self.assertFalse((self.root/'.runs').exists())
        for bad in ('../outside', '.data/led-demo-other', '.data/co2-stcc4-demo-name/child'):
            with self.assertRaises(ValueError):
                demo.fetch_demo(bad, profile_id='co2-stcc4', root=self.root, transport=self.transport)
        self.assertFalse(self.calls)

    def test_authored_originals_notice_copies_and_readonly_capture_keep_exact_custody(self):
        result = self.fetch()
        self.assertEqual(result['status'], 'acquired_unqualified')
        self.assertTrue(result['source_files_exact'])
        self.assertEqual((len(self.calls), result['received_bytes']), (5, 704225))
        self.assertEqual((result['native_jobs'], result['engine_jobs'], result['models_downloaded']), (0, 0, 0))
        self.assertFalse(result['accepted'])
        self.assertFalse((self.out/'responses').exists())
        packet = demo.verify_project(self.out/'native-project', profile_id='co2-stcc4', native_packet=True)
        self.assertEqual((packet['file_count'], packet['bytes']), (7, 709364))
        before = demo.shared.inventory(self.out)
        base, files = demo.capture_native_source('co2-stcc4', root=self.root)
        self.assertEqual(base, self.out/'native-project')
        self.assertEqual(files, {**self.payloads,
            **{name: self.payloads[origin] for name, origin in self.cfg['native_packet_notice_copies'].items()}})
        self.assertEqual(demo.shared.inventory(self.out), before)
        for name in ('Hardware/SparkFun_Qwiic_CO2_Sensor_STCC4.kicad_pro', 'Hardware/_licenses/creator/LICENSE.md'):
            path = base/name;raw = path.read_bytes()
            for fault in ('missing', 'changed', 'symlink'):
                with self.subTest(name=name, fault=fault):
                    path.unlink()
                    if fault == 'changed': path.write_bytes(b'z'+raw[1:])
                    elif fault == 'symlink': path.symlink_to(base/'README.md')
                    with self.assertRaises(ValueError): demo.capture_native_source('co2-stcc4', root=self.root)
                    if fault != 'missing': path.unlink()
                    path.write_bytes(raw)
        extra = base/'Hardware/foreign.kicad_prl';extra.write_bytes(b'unexpected fixture')
        with self.assertRaises(ValueError): demo.capture_native_source('co2-stcc4', root=self.root)

    def test_wrong_first_acquisition_blob_retains_failed_bytes_without_packet_or_retry(self):
        name = 'Hardware/SparkFun_Qwiic_CO2_Sensor_STCC4.kicad_pcb'
        next(row for row in self.cfg['rows'] if row['source_path']==name).pop('sha256')
        self.payloads[name] = b'z'+self.payloads[name][1:]
        result = self.fetch()
        self.assertEqual(result['status'], 'failed')
        self.assertFalse(result['source_files_exact'])
        self.assertFalse(result['accepted'])
        self.assertIn('payload hash', result['first_failure'])
        self.assertEqual(self.calls, ['LICENSE.md', 'README.md', name])
        self.assertEqual((self.out/'project'/name).read_bytes(), self.payloads[name])
        self.assertFalse((self.out/'native-project').exists())
        with self.assertRaises(ValueError): self.fetch()
        self.assertEqual(len(self.calls), 3)


if __name__ == '__main__': unittest.main()
