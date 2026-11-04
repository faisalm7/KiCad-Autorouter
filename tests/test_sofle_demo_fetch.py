"""Nested original-packet custody, using authored bytes; no Native proof."""
import copy
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from scripts import fetch_led_demo as demo
from tests.test_uv_demo_fetch import UVFetchControls


class SoflePacketControls(unittest.TestCase):
    transport = UVFetchControls.transport

    def test_plan_is_offline_and_does_not_claim_library_or_native_support(self):
        cfg = demo.fixed_profile('sofle-v2-soldered')
        with tempfile.TemporaryDirectory(dir=demo.ROOT / 'tests') as temp:
            root = Path(temp)
            plan = demo.fetch_demo(cfg['default_output'], root=root,
                profile_id='sofle-v2-soldered',
                transport=lambda *args: self.fail('offline plan transported'))
            self.assertEqual(list(root.iterdir()), [])
        self.assertEqual(plan['network_requests'], 0)
        self.assertEqual(plan['planned_bytes'], 4209277)
        self.assertEqual(plan['planned_network_requests'], 15)
        self.assertFalse(plan['native_accepted'])
        self.assertFalse(cfg['independent_ancestry_established'])
        self.assertFalse(cfg['raw_assets_public'])
        self.assertIn('absent variant/footprints', ' '.join(cfg['warnings']))
        self.assertEqual(demo.OUTPUT_BYTES, 2 * 1024**2)
        self.assertEqual(demo.shared.CAP, 10 * 1024**2)

    def test_nested_source_tables_and_prl_are_preserved_without_path_resolution(self):
        cfg = copy.deepcopy(demo.fixed_profile('sofle-v2-soldered'))
        self.calls, self.payloads = [], {}
        for row in cfg['rows']:
            raw = ('authored fixture: ' + row['source_path']).encode()
            if row['source_path'].endswith('/fp-lib-table'):
                raw = b'(fp_lib_table (lib (uri "${KIPRJMOD}/../footprints/absent.pretty")))\n'
            self.payloads[row['source_path']] = raw
            row.update(bytes=len(raw), sha256=demo.shared.sha(raw),
                git_blob_sha1=hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest())
        cfg['bytes'] = sum(map(len, self.payloads.values()))
        cfg['network_byte_cap'] = cfg['bytes'] + len(cfg['rows'])
        cfg['native_packet_bytes'] = cfg['bytes'] + sum(
            len(self.payloads[n]) for n in cfg['native_packet_notice_copies'].values())
        with tempfile.TemporaryDirectory(dir=demo.ROOT / 'tests') as temp:
            self.root = Path(temp)
            for name in (*demo.MATERIAL, *demo.ARC_MATERIAL):
                target = self.root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((demo.ROOT / name).read_bytes())
            with mock.patch.object(demo, 'SOFLE_PROFILE', cfg):
                result = demo.fetch_demo(cfg['default_output'], root=self.root,
                    profile_id='sofle-v2-soldered', fetch=True, transport=self.transport)
                out = self.root / cfg['default_output']
                for name, raw in self.payloads.items():
                    self.assertEqual((out / 'project' / name).read_bytes(), raw)
                    self.assertEqual((out / 'native-project' / name).read_bytes(), raw)
                self.assertEqual(demo.verify_project(out / 'native-project',
                    profile_id='sofle-v2-soldered', native_packet=True)['file_count'], 19)
                self.assertFalse((out / 'native-project/Sofle_v2_soldered/footprints').exists())
                self.assertTrue(result['source_files_exact'])
                self.assertFalse(result['accepted'])
                self.assertFalse(result['native_accepted'])
                self.assertEqual((result['native_jobs'], result['engine_jobs']), (0, 0))
