"""Synthetic fixed-profile/capture controls; no HTTP, native, models or cache."""
import copy
import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import fetch_led_demo as demo
from experiments.placement_handoff_native_v1 import driver


class AnalogFilterDemoControls(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=demo.ROOT / 'tests', prefix='analog-demo-test-')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for name in (*demo.MATERIAL, *demo.ARC_MATERIAL):
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes((demo.ROOT / name).read_bytes())
        self.public = copy.deepcopy(demo.ANALOG_PROFILE)
        self.cfg = copy.deepcopy(self.public)
        self.payloads = {}
        for row in self.cfg['rows']:
            prefix = ('authored synthetic analog fixture ' + row['source_path'] + '\n').encode()
            raw = prefix + b'x' * (row['bytes'] - len(prefix))
            self.payloads[row['source_path']] = raw
            row['sha256'] = hashlib.sha256(raw).hexdigest()
            row['git_blob_sha1'] = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
        patch = mock.patch.object(demo, 'ANALOG_PROFILE', self.cfg)
        patch.start()
        self.addCleanup(patch.stop)
        self.requests = []
        self.out = self.root / '.data/analog-filter-demo-001'

    def transport(self, row, record, path, allowance, remaining):
        remaining()
        self.requests.append(row['source_path'])
        raw = self.payloads[row['source_path']]
        with path.open('xb') as stream:
            stream.write(raw)
        record.update(received_bytes=len(raw), response_sha256=demo.shared.sha(raw),
                      status='response_received', http_status=200, wall_seconds=0.0)
        return raw

    def fetch(self):
        return demo.fetch_demo('.data/analog-filter-demo-001', profile_id='analog-filter',
                               fetch=True, root=self.root, transport=self.transport)

    def test_fixed_original_profile_and_plan_without_cache_or_output_creation(self):
        commit = '6a34b221758fe32f33eca20d735e88028346753a'
        paths = {'LICENSE', 'README.md', 'kicad/analog_filter_module.kicad_pcb',
                 'kicad/analog_filter_module.kicad_pro', 'kicad/analog_filter_module.kicad_sch'}
        self.assertEqual(self.public['repository'], 'Myrto-Angeliki/analog-filter')
        self.assertEqual(self.public['commit'], commit)
        self.assertEqual({row['source_path'] for row in self.public['rows']}, paths)
        self.assertEqual(sum(row['bytes'] for row in self.public['rows']), 189336)
        self.assertEqual(self.public['native_packet_notice_copies'],
                         {'kicad/_licenses/creator/LICENSE': 'LICENSE',
                          'kicad/_licenses/creator/README.md': 'README.md'})
        for row in self.public['rows']:
            self.assertEqual(row['commit'], commit)
            self.assertEqual(row['raw_url'], 'https://raw.githubusercontent.com/'
                             + self.public['repository'] + '/' + commit + '/' + row['source_path'])
        independent = demo.fixed_profile('analog-filter')
        independent['rows'][0]['sha256'] = 'mutated caller copy'
        self.assertEqual(demo.fixed_profile('analog-filter'), self.cfg)
        plan = demo.fetch_demo('.data/analog-filter-demo-001', profile_id='analog-filter',
                               root=self.root, transport=lambda *args: self.fail('plan fetched'))
        self.assertEqual((plan['planned_files'], plan['planned_bytes'], plan['network_requests']),
                         (5, 189336, 0))
        self.assertFalse((self.root / '.data').exists())
        self.assertFalse((self.root / '.runs').exists())

    def test_five_authored_responses_preserve_raw_and_seven_file_notice_packet(self):
        result = self.fetch()
        self.assertEqual(result['kind'], 'fixed_public_analog_filter_source_acquisition')
        self.assertEqual(result['source_profile'], 'fixed five-file public analog-filter selection')
        self.assertEqual(self.requests, [row['source_path'] for row in self.cfg['rows']])
        self.assertEqual((result['status'], result['new_network_requests'], result['received_bytes']),
                         ('acquired_unqualified', 5, 189336))
        self.assertTrue(result['source_files_exact'])
        self.assertTrue(result['native_packet_prepared'])
        self.assertTrue(result['within_budget'])
        self.assertFalse(result['accepted'])
        self.assertFalse(result['native_accepted'])
        self.assertEqual((result['engine_jobs'], result['native_jobs'], result['models_downloaded']), (0, 0, 0))
        original = demo.verify_project(self.out / 'project', profile_id='analog-filter')
        packet = demo.verify_project(self.out / 'native-project', profile_id='analog-filter', native_packet=True)
        self.assertEqual((original['file_count'], original['bytes']), (5, 189336))
        self.assertEqual((packet['file_count'], packet['bytes']), (7, 198305))
        for name, raw in self.payloads.items():
            self.assertEqual((self.out / 'project' / name).read_bytes(), raw)
            self.assertEqual((self.out / 'native-project' / name).read_bytes(), raw)
        for name, origin in self.cfg['native_packet_notice_copies'].items():
            self.assertEqual((self.out / 'native-project' / name).read_bytes(), self.payloads[origin])
        self.assertEqual(demo.publication.read_json(self.out / 'result.json'), result)

    def test_capture_native_source_preserves_all_bytes_without_staging_or_fetch(self):
        self.fetch()
        before = demo.shared.inventory(self.root)
        with mock.patch.object(demo, 'fetch_demo', side_effect=AssertionError('capture fetched')) as fetch, \
                mock.patch.object(driver, 'copy_bytes', side_effect=AssertionError('capture staged')) as stage:
            base, files = demo.capture_native_source('analog-filter', root=self.root)
        expected = dict(self.payloads)
        expected.update({name: self.payloads[origin] for name, origin
                         in self.cfg['native_packet_notice_copies'].items()})
        self.assertEqual(base, self.out / 'native-project')
        self.assertEqual(files, expected)
        self.assertEqual(demo.shared.inventory(self.root), before)
        fetch.assert_not_called()
        stage.assert_not_called()
        self.assertFalse((self.root / '.runs').exists())

    def test_stale_original_or_creator_notice_refuses_capture_without_fallback(self):
        self.fetch()
        for name in ('project/kicad/analog_filter_module.kicad_pcb',
                     'native-project/kicad/_licenses/creator/LICENSE'):
            with self.subTest(name=name):
                path = self.out / name
                original = path.read_bytes()
                path.write_bytes(b'deliberately stale authored source')
                before = demo.shared.inventory(self.root)
                with mock.patch.object(demo, 'fetch_demo', side_effect=AssertionError('stale fallback fetched')) as fetch, \
                        mock.patch.object(driver, 'copy_bytes', side_effect=AssertionError('stale fallback staged')) as stage, \
                        self.assertRaises(ValueError):
                    demo.capture_native_source('analog-filter', root=self.root)
                self.assertEqual(demo.shared.inventory(self.root), before)
                fetch.assert_not_called()
                stage.assert_not_called()
                path.write_bytes(original)  # Only this authored fixture, for the next case.

    def test_capture_rechecks_native_source_changed_after_initial_verification(self):
        self.fetch()
        native = self.out / 'native-project'
        board = native / 'kicad/analog_filter_module.kicad_pcb'
        real_verify, real_bounded = demo.verify_project, demo.shared.bounded
        ready, changed = [], []

        def verified(path, *args, **kwargs):
            value = real_verify(path, *args, **kwargs)
            if path == native:
                ready.append(True)
            return value

        def change(path, *args, **kwargs):
            raw = real_bounded(path, *args, **kwargs)
            if ready and path == board and not changed:
                changed.append(True)
                board.write_bytes(b'z' + raw[1:])
            return raw

        with mock.patch.object(demo, 'verify_project', side_effect=verified), \
                mock.patch.object(demo.shared, 'bounded', side_effect=change), \
                self.assertRaises(ValueError):
            demo.capture_native_source('analog-filter', root=self.root)
        self.assertEqual(changed, [True])
        self.assertEqual(board.read_bytes(), b'z' + self.payloads['kicad/analog_filter_module.kicad_pcb'][1:])
        self.assertEqual((self.out / 'project/kicad/analog_filter_module.kicad_pcb').read_bytes(),
                         self.payloads['kicad/analog_filter_module.kicad_pcb'])


if __name__ == '__main__':
    unittest.main()
