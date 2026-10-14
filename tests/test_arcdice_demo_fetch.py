"""Fixed ArcDice fetch lifecycle controls; authored bytes, no cache/network/native."""
import copy
import hashlib
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import fetch_led_demo as demo
from experiments.placement_handoff_native_v1 import driver


class ArcDiceFetchControls(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=demo.ROOT / 'tests', prefix='arc-fetch-test-')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for name in (*demo.MATERIAL, *demo.ARC_MATERIAL):
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes((demo.ROOT / name).read_bytes())
        self.public = copy.deepcopy(demo.ARC_PROFILE)
        self.cfg = copy.deepcopy(self.public)
        self.payloads = {}
        for row in self.cfg['rows']:
            prefix = ('authored synthetic fixture ' + row['source_path'] + '\n').encode()
            raw = prefix + b'x' * (row['bytes'] - len(prefix))
            self.payloads[row['source_path']] = raw
            row['sha256'] = hashlib.sha256(raw).hexdigest()
            row['git_blob_sha1'] = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
        patch = mock.patch.object(demo, 'ARC_PROFILE', self.cfg)
        patch.start()
        self.addCleanup(patch.stop)
        self.calls = []

    def transport(self, row, record, path, allowance, remaining):
        remaining()
        self.calls.append(row['source_path'])
        raw = self.payloads[row['source_path']]
        with path.open('xb') as stream:
            stream.write(raw)
        record.update(received_bytes=len(raw), response_sha256=demo.shared.sha(raw),
                      status='response_received', http_status=200, wall_seconds=0.0)
        return raw

    def fetch(self, name='.data/arcdice-demo-test'):
        return demo.fetch_demo(name, profile_id='arcdice', fetch=True,
                               root=self.root, transport=self.transport)

    def test_fixed_identity_and_fresh_plan_without_cache_network_or_creation(self):
        from experiments.arcdice_native_class_v1 import source
        self.assertEqual([{k: row[k] for k in source.ROWS[0]} for row in self.public['rows']],
                         list(source.ROWS))
        result = demo.fetch_demo('.data/arcdice-demo-test', profile_id='arcdice', root=self.root,
                                 transport=lambda *args: self.fail('plan attempted network'))
        self.assertEqual((result['planned_bytes'], result['network_requests']), (595341, 0))
        self.assertFalse((self.root / '.data').exists())
        self.assertFalse((self.root / '.runs').exists())
        self.assertFalse((self.root / '.git').exists())
        with self.assertRaisesRegex(ValueError, 'unknown'):
            demo.fetch_demo('.data/arcdice-demo-test', profile_id='unknown', root=self.root)

    def test_exact_five_originals_and_seven_file_native_notice_packet(self):
        result = self.fetch()
        out = self.root / '.data/arcdice-demo-test'
        project, native = out / 'project', out / 'native-project'
        self.assertEqual((result['status'], result['new_network_requests'], result['received_bytes']),
                         ('acquired_unqualified', 5, 595341))
        self.assertTrue(result['source_files_exact'])
        self.assertTrue(result['native_packet_prepared'])
        self.assertTrue(result['within_budget'])
        self.assertFalse(result['accepted'])
        self.assertFalse(result['native_accepted'])
        self.assertEqual(result['engine_jobs'], 0)
        self.assertEqual(result['native_jobs'], 0)
        self.assertEqual(demo.verify_project(project, profile_id='arcdice')['file_count'], 5)
        self.assertEqual(demo.verify_project(native, profile_id='arcdice', native_packet=True)['file_count'], 7)
        for name, content in self.payloads.items():
            self.assertEqual((project / name).read_bytes(), content)
            self.assertEqual((native / name).read_bytes(), content)
        for name, origin in self.cfg['native_packet_notice_copies'].items():
            self.assertEqual((native / name).read_bytes(), self.payloads[origin])
        expected = ({'responses/' + str(i + 1).zfill(2) + '.payload' for i in range(5)}
                    | {'project/' + n for n in self.payloads}
                    | {'native-project/' + n for n in self.payloads}
                    | {'native-project/' + n for n in self.cfg['native_packet_notice_copies']}
                    | {'result.json'})
        self.assertEqual(set(demo.shared.inventory(out)['files']), expected)
        self.assertEqual(demo.publication.read_json(out / 'result.json'), result)

    def test_descriptor_anchor_refuses_replacement_between_guard_and_open(self):
        original_open = demo.os.open
        injected = []
        out = self.root / '.data/arcdice-demo-test'
        moved = self.root / 'preserved-responses'

        def replace(name, flags, *args, **kwargs):
            if name == '01.payload' and flags & os.O_CREAT and not injected:
                injected.append(True)
                (out / 'responses').rename(moved)
                (out / 'responses').mkdir()
                (out / 'responses/owner').write_bytes(b'other owner')
            return original_open(name, flags, *args, **kwargs)

        with mock.patch.object(demo.os, 'open', side_effect=replace), self.assertRaises(demo.h.Rejected):
            self.fetch()
        self.assertEqual(list((out / 'responses').iterdir()), [out / 'responses/owner'])
        self.assertEqual((out / 'responses/owner').read_bytes(), b'other owner')
        # Exclusive creation stays on the original descriptor; the following
        # ownership check rejects before any response bytes are written.
        self.assertEqual((moved / '01.payload').read_bytes(), b'')
        self.assertFalse((out / 'result.json').exists())

    def test_legitimate_partial_copy_retains_failed_receipt_and_first_cause(self):
        def fail(files, target, *, expected_parent_owner=None):
            demo.h.owned_destination(expected_parent_owner)
            target.mkdir()
            (target / 'LICENSE').write_bytes(files['LICENSE'])
            raise OSError('deliberate owned partial copy')

        with mock.patch.object(driver, 'copy_bytes', side_effect=fail):
            result = self.fetch()
        out = self.root / '.data/arcdice-demo-test'
        self.assertEqual(result['status'], 'failed')
        self.assertFalse(result['source_files_exact'])
        self.assertFalse(result['native_packet_prepared'])
        self.assertFalse(result['accepted'])
        self.assertIn('deliberate owned partial copy', result['first_failure'])
        self.assertEqual(len(self.calls), 5)
        self.assertEqual((out / 'project/LICENSE').read_bytes(), self.payloads['LICENSE'])
        self.assertFalse((out / 'native-project').exists())
        self.assertEqual(demo.publication.read_json(out / 'result.json'), result)

    def test_readonly_verifier_rejects_stale_notice_extra_directory_and_missing_source(self):
        self.fetch()
        out = self.root / '.data/arcdice-demo-test'
        native, project = out / 'native-project', out / 'project'
        before = demo.shared.inventory(native)
        demo.verify_project(native, profile_id='arcdice', native_packet=True)
        self.assertEqual(demo.shared.inventory(native), before)
        (native / 'hardware/_licenses/creator/LICENSE').write_bytes(b'changed')
        with self.assertRaises(ValueError):
            demo.verify_project(native, profile_id='arcdice', native_packet=True)
        (project / 'unexpected').mkdir()
        with self.assertRaises(ValueError):
            demo.verify_project(project, profile_id='arcdice')
        # A separately complete original packet also rejects a missing payload.
        missing = self.root / 'missing-source'
        driver.copy_bytes(self.payloads, missing)
        (missing / 'hardware/ArcDice.kicad_sch').rename(self.root / 'preserved-schematic')
        with self.assertRaises(ValueError):
            demo.verify_project(missing, profile_id='arcdice')

    def test_preexisting_destination_and_wrong_profile_prefix_preserve_owner(self):
        out = self.root / '.data/arcdice-demo-test'
        out.mkdir(parents=True)
        (out / 'owner').write_bytes(b'keep')
        with self.assertRaisesRegex(ValueError, 'exists'):
            self.fetch()
        self.assertEqual((out / 'owner').read_bytes(), b'keep')
        self.assertEqual(self.calls, [])
        with self.assertRaises(ValueError):
            demo.fetch_demo('.data/led-demo-test', profile_id='arcdice', root=self.root)

    def test_after_return_byte_identical_replacement_is_not_adopted(self):
        real_copy = driver.copy_bytes
        for stage in ('project', 'native-project'):
            with self.subTest(stage=stage):
                out = self.root / ('.data/arcdice-demo-replace-' + stage)
                moved = self.root / ('retained-' + stage)
                replaced = []
                foreign = {}

                def replace(files, target, *, expected_parent_owner=None):
                    lifecycle = real_copy(files, target, expected_parent_owner=expected_parent_owner)
                    if target.name == stage and not replaced:
                        replaced.append(True)
                        target.rename(moved)
                        # These are a different owner's byte-identical files.
                        # Hash verification alone deliberately succeeds.
                        real_copy(files, target, expected_parent_owner=expected_parent_owner)
                        demo.verify_project(target, profile_id='arcdice', native_packet=stage == 'native-project')
                        foreign.update(demo.shared.inventory(target))
                        foreign['identity'] = (target.stat().st_dev, target.stat().st_ino)
                    return lifecycle

                with mock.patch.object(driver, 'copy_bytes', side_effect=replace), \
                        self.assertRaisesRegex(demo.h.Rejected, 'directory was replaced'):
                    self.fetch(str(out.relative_to(self.root)))
                self.assertEqual(replaced, [True])
                target = out / stage
                self.assertEqual(demo.shared.inventory(target),
                                 {k: v for k, v in foreign.items() if k != 'identity'})
                self.assertEqual((target.stat().st_dev, target.stat().st_ino), foreign['identity'])
                self.assertEqual(demo.shared.inventory(moved), demo.shared.inventory(target))
                self.assertFalse((out / 'result.json').exists())
                self.assertFalse(list(out.glob('invalidated-result-*')))

    def test_before_copy_outer_parent_replacement_cannot_create_foreign_project(self):
        real_copy = driver.copy_bytes
        out = self.root / '.data/arcdice-demo-test'
        moved = self.root / 'retained-output'
        injected = []
        foreign = {}

        def replace(files, target, *, expected_parent_owner=None):
            injected.append(True)
            self.assertEqual(target, out / 'project')
            self.assertEqual(expected_parent_owner['directory_identity'],
                             (out.stat().st_dev, out.stat().st_ino))
            out.rename(moved)
            out.mkdir()
            (out / 'other-owner.kicad_pcb').write_bytes(b'foreign original board')
            (out / 'owner').write_bytes(b'other owner')
            foreign.update(demo.shared.inventory(out))
            return real_copy(files, target, expected_parent_owner=expected_parent_owner)

        with mock.patch.object(driver, 'copy_bytes', side_effect=replace), \
                self.assertRaisesRegex(demo.h.Rejected, 'directory was replaced'):
            self.fetch()
        self.assertEqual(injected, [True])
        self.assertEqual(demo.shared.inventory(out), foreign)
        self.assertEqual((out / 'other-owner.kicad_pcb').read_bytes(), b'foreign original board')
        self.assertFalse((out / 'project').exists())
        self.assertFalse((out / 'native-project').exists())
        self.assertFalse((out / 'result.json').exists())
        self.assertEqual(set(demo.shared.inventory(moved)['files']),
                         {'responses/' + str(i + 1).zfill(2) + '.payload' for i in range(5)})
        self.assertFalse((moved / 'project').exists())

    def test_portable_selector_reads_native_hardware_without_cache_or_staging(self):
        from scripts import experiment_quality as q
        from experiments.arcdice_native_class_v1 import source
        self.fetch()
        default = self.root / '.data/arcdice-demo-001'
        (self.root / '.data/arcdice-demo-test').rename(default)
        before = demo.shared.inventory(self.root)
        with mock.patch.object(q.c, 'ROOT', self.root), \
                mock.patch.object(source, 'capture', side_effect=AssertionError('legacy cache access')) as capture, \
                mock.patch.object(driver, 'copy_bytes', side_effect=AssertionError('selector staging')) as staging:
            board, family = q.selected_source('arcdice')
        self.assertEqual(board, default / 'native-project/hardware/ArcDice.kicad_pcb')
        self.assertEqual(family, 'VorosEgyes-ArcDice-development-exposed')
        self.assertEqual(board.read_bytes(), self.payloads['hardware/ArcDice.kicad_pcb'])
        self.assertEqual(demo.shared.inventory(self.root), before)
        capture.assert_not_called()
        staging.assert_not_called()
        self.assertFalse((self.root / '.runs').exists())

    def test_portable_selector_stale_raw_or_notice_rejects_without_fallback_or_writes(self):
        from scripts import experiment_quality as q
        from experiments.arcdice_native_class_v1 import source
        self.fetch()
        default = self.root / '.data/arcdice-demo-001'
        (self.root / '.data/arcdice-demo-test').rename(default)
        for relative in ('project/hardware/ArcDice.kicad_pro',
                         'native-project/hardware/_licenses/creator/LICENSE'):
            with self.subTest(relative=relative):
                path = default / relative
                original = path.read_bytes()
                path.write_bytes(b'deliberate stale authored fixture')
                before = demo.shared.inventory(self.root)
                with mock.patch.object(q.c, 'ROOT', self.root), \
                        mock.patch.object(source, 'capture', side_effect=AssertionError('legacy fallback')) as capture, \
                        mock.patch.object(driver, 'copy_bytes', side_effect=AssertionError('selector staging')) as staging, \
                        self.assertRaises(ValueError):
                    q.selected_source('arcdice')
                self.assertEqual(demo.shared.inventory(self.root), before)
                capture.assert_not_called()
                staging.assert_not_called()
                self.assertFalse((self.root / '.runs').exists())
                # Restore only this authored test fixture for the next case.
                path.write_bytes(original)


if __name__ == '__main__':
    unittest.main()
