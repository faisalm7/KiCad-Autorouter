"""Small-file controls; mocked transport never opens a socket or executes data."""
import copy
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import signal
import tempfile
import time
import unittest
from unittest import mock

HERE = Path(__file__).absolute().parent
spec = importlib.util.spec_from_file_location('acquisition', HERE / 'fetch.py')
f = importlib.util.module_from_spec(spec)
spec.loader.exec_module(f)


class Controls(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=HERE, prefix='test-scratch-')
        self.root = Path(self.tmp.name)
        (self.root / '.data').mkdir()
        (self.root / '.data/original').mkdir()
        (self.root / '.data/original/board.kicad_pcb').write_bytes(b'original')
        (self.root / '.runs').mkdir()
        self.baseline = f.inventory(self.root / '.data')
        self.plan, self.original, self.rows = f.load(HERE)
        (self.root / '.git').mkdir()
        (self.root / '.git/HEAD').write_text('0' * 40)
        self.runtime = {'head': '0' * 40, 'files': {name:f.sha(f.bounded(HERE/name)) for name in f.MATERIAL}, 'git_identity':f.git_identity(self.root)}
        self.row = {'destination': 'one/project.kicad_pcb', 'bytes': 4,
                    'git_blob_sha1': hashlib.sha1(b'blob 4\0data').hexdigest(), 'sha256': None}

    def tearDown(self):
        self.tmp.cleanup()

    def transport(self, row, rec, path, allowance, remaining):
        remaining()
        rec.update(status='response_received', received_bytes=4, url='mock://no-network', response_sha256=f.sha(b'data'))
        path.write_bytes(b'data')
        return b'data'

    def run_small(self, transport=None):
        with mock.patch.object(f, 'committed', return_value=self.runtime):
            return f.acquire(self.root, HERE, self.root / '.runs/output', self.plan, self.baseline,
                             [self.row], self.runtime, time.monotonic(), transport or self.transport)

    def test_exact_plan_and_census(self):
        self.assertEqual((len(self.rows), sum(r['bytes'] for r in self.rows)), (33, 5016162))
        self.assertEqual((self.original['file_count'], self.original['bytes']), (312, 32392408))
        self.assertEqual(self.original['bytes'] + self.plan['planned_bytes'], 37408570)

    def test_legacy_default_and_explicit_destination(self):
        self.assertEqual(f.profile()['directory'], 'experiments/licensed_acquisition_v1')
        self.assertIn('expansion004', f.extend(self.baseline, {})['directories'])
        changed = f.extend(self.baseline, {'one': {'bytes': 1, 'sha256': 'a' * 64}},
                           destination_root='expansion005')
        self.assertIn('expansion005/one', changed['files'])
        self.assertNotIn('expansion004', changed['directories'])
        with self.assertRaisesRegex(ValueError, 'destination root'):
            f.extend(self.baseline, {}, destination_root='../elsewhere')

    def test_cross_profile_and_unknown_profile_refused(self):
        with self.assertRaisesRegex(ValueError, 'scope'):
            f.validate_protocol(self.plan, self.original, 'v2')
        with self.assertRaisesRegex(ValueError, 'protocol pin'):
            f.load(HERE, 'v2')
        for profile_id in ('v5', '../v1', True, None):
            with self.subTest(profile_id=profile_id), self.assertRaisesRegex(ValueError, 'unreviewed'):
                f.profile(profile_id)

    def test_unsafe_paths(self):
        for path in ('/absolute', '../escape', 'a//b', 'a/./b', 'a\\b', 'a\x00b', ''):
            with self.subTest(path=path), self.assertRaises(ValueError):
                f.safe(path)

    def test_protocol_identity_mode_boolean_and_url(self):
        for key, value in (('mode', '100755'), ('bytes', True), ('commit', '0' * 40),
                           ('repository', 'other/repo'), ('raw_url', 'https://other.invalid/source')):
            plan = copy.deepcopy(self.plan)
            plan['projects'][0]['files'][0][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                f.validate_protocol(plan, self.original)

    def test_no_budget_or_order_downgrade(self):
        plan = copy.deepcopy(self.plan)
        plan['caps']['aggregate_all_data_bytes'] *= 2
        with self.assertRaises(ValueError):
            f.validate_protocol(plan, self.original)
        plan = copy.deepcopy(self.plan)
        plan['projects'].reverse()
        with self.assertRaises(ValueError):
            f.validate_protocol(plan, self.original)

    def test_casefold_plan_collision(self):
        plan = copy.deepcopy(self.plan)
        row = copy.deepcopy(plan['projects'][0]['files'][0])
        row['destination'] = row['destination'].upper()
        plan['projects'][0]['files'].append(row)
        with self.assertRaises(ValueError):
            f.validate_protocol(plan, self.original)

    def test_baseline_changed(self):
        (self.root / '.data/original/board.kicad_pcb').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'inventory changed'):
            f.inventory(self.root / '.data', self.baseline)

    def test_unexpected_member_rejected_before_read(self):
        (self.root / '.data/new').write_bytes(b'x')
        real = f.bounded
        def read(path, *args):
            if path.name == 'new':
                self.fail('unknown file read before rejected')
            return real(path, *args)
        with mock.patch.object(f, 'bounded', side_effect=read), self.assertRaisesRegex(ValueError, 'unexpected file'):
            f.inventory(self.root / '.data', self.baseline)

    def test_inventory_entry_and_bytes_limits(self):
        with mock.patch.object(f, 'MAX_ENTRIES', 1), self.assertRaisesRegex(ValueError, 'entry cap'):
            f.inventory(self.root / '.data')
        with self.assertRaisesRegex(ValueError, 'aggregate byte cap'):
            f.inventory(self.root / '.data', cap=2)

    def test_symlinks_rejected(self):
        (self.root / '.data/link').symlink_to(self.root / '.data/original/board.kicad_pcb')
        with self.assertRaisesRegex(ValueError, 'symlink'):
            f.inventory(self.root / '.data')
        with self.assertRaisesRegex(ValueError, 'symlink'):
            f.contained(self.root, self.root / '.data/link')

    def test_bounded_concurrent_growth(self):
        p = self.root / 'small'
        p.write_bytes(b'x')
        with mock.patch.object(Path, 'open', return_value=io.BytesIO(b'abcd')):
            with self.assertRaisesRegex(ValueError, 'grew'):
                f.bounded(p, cap=2)

    def test_payload_checks(self):
        self.assertEqual(f.payload(self.row, b'data')['sha256'], f.sha(b'data'))
        for raw in (b'bad', b'evil'):
            with self.assertRaises(ValueError):
                f.payload(self.row, raw)
        row = dict(self.row, bytes=46)
        raw = b'version https://git-lfs.github.com/spec/'
        row['bytes'] = len(raw)
        with self.assertRaisesRegex(ValueError, 'LFS'):
            f.payload(row, raw)

    def test_ignored_directory_cannot_fetch(self):
        # Exercise the path gate independently of this test's installation path.
        draft = self.root / '.runs/draft'
        draft.mkdir(parents=True)
        with mock.patch.object(f, 'git') as metadata:
            with self.assertRaisesRegex(ValueError, 'promoted'):
                f.committed(self.root, draft)
            metadata.assert_not_called()

    def test_committed_byte_guard(self):
        here = self.root / 'experiments/licensed_acquisition_v1'
        here.mkdir(parents=True)
        for name in f.MATERIAL:
            (here / name).write_bytes(b'committed')
        (self.root / '.git/HEAD').write_text('1' * 40)
        def git(root, args):
            return ('1' * 40).encode() if args[0] == 'rev-parse' else b'committed'
        with mock.patch.object(f, 'git', side_effect=git):
            self.assertEqual(f.committed(self.root, here)['head'], '1' * 40)
            (here / 'fetch.py').write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError, 'committed bytes'):
                f.committed(self.root, here)

    def test_helper_mutated_during_last_git_show_rejected(self):
        here = self.root / 'experiments/licensed_acquisition_v1'
        here.mkdir(parents=True)
        for name in f.MATERIAL:
            (here / name).write_bytes(b'committed')
        def git(root, args):
            if args[0] == 'rev-parse':
                return b'0' * 40
            if args[1].endswith('/STATIC_AUDIT.md'):
                (here / 'fetch.py').write_bytes(b'changed')
            return b'committed'
        with mock.patch.object(f, 'git', side_effect=git), self.assertRaisesRegex(ValueError, 'after metadata'):
            f.committed(self.root, here)

    def test_head_mutated_during_last_git_show_rejected(self):
        here = self.root / 'experiments/licensed_acquisition_v1'
        here.mkdir(parents=True)
        for name in f.MATERIAL:
            (here / name).write_bytes(b'committed')
        def git(root, args):
            if args[0] == 'rev-parse':
                return b'0' * 40
            if args[1].endswith('/STATIC_AUDIT.md'):
                (self.root / '.git/HEAD').write_text('1' * 40)
            return b'committed'
        with mock.patch.object(f, 'git', side_effect=git), self.assertRaisesRegex(ValueError, 'after metadata'):
            f.committed(self.root, here)

    def test_symbolic_loose_and_packed_identity(self):
        (self.root / '.git/HEAD').write_text('ref: refs/heads/rebuild/local-test\n')
        folder = self.root / '.git/refs/heads/rebuild'
        folder.mkdir(parents=True)
        (folder / 'local-test').write_text('2' * 40 + '\n')
        self.assertEqual(f.git_identity(self.root)['resolved_head'], '2' * 40)
        (folder / 'local-test').unlink()
        (self.root / '.git/packed-refs').write_text('3' * 40 + ' refs/heads/rebuild/local-test\n')
        self.assertEqual(f.git_identity(self.root)['resolved_head'], '3' * 40)
        with (self.root / '.git/packed-refs').open('a') as stream:
            stream.write('4' * 40 + ' refs/heads/rebuild/local-test\n')
        with self.assertRaisesRegex(ValueError, 'ambiguous'):
            f.git_identity(self.root)

    def test_final_output_scan_response_and_source_mutations(self):
        for variant in ('response', 'source'):
            with self.subTest(variant=variant):
                # Fresh miniature invocation for each mutation; actual .data untouched.
                with tempfile.TemporaryDirectory(dir=HERE, prefix='scan-scratch-') as td:
                    root = Path(td)
                    (root / '.data').mkdir()
                    (root / '.data/original').write_bytes(b'original')
                    (root / '.runs').mkdir()
                    (root / '.git').mkdir()
                    (root / '.git/HEAD').write_text('0' * 40)
                    baseline = f.inventory(root / '.data')
                    batch = root / '.runs/output'
                    actual = f.inventory
                    mutated = False
                    def scan(path, *args, **kwargs):
                        nonlocal mutated
                        if path == batch and not mutated:
                            target = batch / 'response-000.bin' if variant == 'response' else root / '.data/original'
                            target.write_bytes(b'evil')
                            mutated = True
                        return actual(path, *args, **kwargs)
                    with mock.patch.object(f, 'inventory', side_effect=scan), mock.patch.object(f, 'committed', return_value=self.runtime), self.assertRaises(ValueError):
                        f.acquire(root, HERE, batch, self.plan, baseline, [self.row], self.runtime, time.monotonic(), self.transport)
                    self.assertTrue(mutated)
                    self.assertEqual(json.loads((batch / 'receipt.json').read_text())['status'], 'failed')

    def test_small_flow_and_freshness(self):
        result = self.run_small()
        self.assertEqual(result['status'], 'acquired_unqualified')
        self.assertFalse(result['dependency_closure_verified'])
        self.assertEqual(result['aggregate_data_bytes'], 12)
        self.assertEqual((self.root / '.data/original/board.kicad_pcb').read_bytes(), b'original')
        with self.assertRaisesRegex(ValueError, 'fresh output'):
            self.run_small()

    def test_partial_failure_preserved(self):
        def failure(row, rec, path, allowance, remaining):
            rec.update(received_bytes=3, status='failed')
            path.write_bytes(b'bad')
            raise ValueError('injected network failure')
        with self.assertRaisesRegex(ValueError, 'network failure'):
            self.run_small(failure)
        record = json.loads((self.root / '.runs/output/receipt.json').read_text())
        self.assertEqual(record['status'], 'failed')
        self.assertTrue(record['preexisting_files_unchanged'])
        self.assertEqual((self.root / '.runs/output/response-000.bin').read_bytes(), b'bad')
        self.assertTrue((self.root / '.data/expansion004').is_dir())

    def test_source_change_during_metadata_rejected(self):
        count = 0
        def metadata(*args):
            nonlocal count
            count += 1
            if count == 3:
                (self.root / '.data/original/board.kicad_pcb').write_bytes(b'changed')
            return self.runtime
        with mock.patch.object(f, 'committed', side_effect=metadata), self.assertRaisesRegex(ValueError, 'inventory changed'):
            f.acquire(self.root, HERE, self.root / '.runs/output', self.plan, self.baseline,
                      [self.row], self.runtime, time.monotonic(), self.transport)
        self.assertNotEqual(json.loads((self.root / '.runs/output/receipt.json').read_text())['status'], 'acquired_unqualified')

    def test_transport_response_artifact_must_equal_returned_bytes(self):
        def altered(row, rec, path, allowance, remaining):
            raw = self.transport(row, rec, path, allowance, remaining)
            path.write_bytes(b'evil')
            return raw
        with self.assertRaisesRegex(ValueError, 'artifact/returned'):
            self.run_small(altered)
        record = json.loads((self.root / '.runs/output/receipt.json').read_text())
        self.assertEqual(record['status'], 'failed')
        self.assertEqual(record['files'], [])

    def test_transport_receipt_sha_must_equal_returned_bytes(self):
        def altered(row, rec, path, allowance, remaining):
            raw = self.transport(row, rec, path, allowance, remaining)
            rec['response_sha256'] = '0' * 64
            return raw
        with self.assertRaisesRegex(ValueError, 'artifact/returned'):
            self.run_small(altered)

    def test_self_signals_invalidate_and_restore_handlers(self):
        for signum in (signal.SIGINT, signal.SIGTERM):
            with self.subTest(signal=signum):
                out = self.root / '.runs' / ('signal-' + str(signum))
                out.mkdir()
                previous = {s: signal.getsignal(s) for s in (signal.SIGINT, signal.SIGTERM)}
                calls = 0
                def stable():
                    nonlocal calls
                    calls += 1
                    if calls == 2:
                        os.kill(os.getpid(), signum)
                with self.assertRaises(KeyboardInterrupt), f.cancellation():
                    f.publish(out, {'status': 'acquired_unqualified'}, stable, lambda: 299)
                self.assertEqual(json.loads((out / 'receipt.json').read_text())['status'], 'cancelled')
                self.assertEqual({s: signal.getsignal(s) for s in previous}, previous)

    def test_original_failure_survives_final_audit_error(self):
        def failure(row, rec, path, allowance, remaining):
            (self.root / '.data/unexpected-link').symlink_to(self.root / '.data/original')
            raise ValueError('first network failure')
        with self.assertRaisesRegex(ValueError, 'first network failure'):
            self.run_small(failure)
        record = json.loads((self.root / '.runs/output/receipt.json').read_text())
        self.assertIn('first network failure', record['error'])
        self.assertIn('symlink', record['failure_audit_error'])
        self.assertFalse(record['preexisting_files_unchanged'])

    def test_completed_response_not_rebased(self):
        calls = 0
        def metadata(*args):
            nonlocal calls
            calls += 1
            if calls == 3:
                (self.root / '.runs/output/response-000.bin').write_bytes(b'evil')
            return self.runtime
        with mock.patch.object(f, 'committed', side_effect=metadata), self.assertRaisesRegex(ValueError, 'evidence changed'):
            f.acquire(self.root, HERE, self.root / '.runs/output', self.plan, self.baseline,
                      [self.row], self.runtime, time.monotonic(), self.transport)

    def test_publication_final_scan_mutation(self):
        out = self.root / '.runs/pub'
        out.mkdir()
        record = {'status': 'acquired_unqualified'}
        def scan(*args, **kwargs):
            (out / 'receipt.json').write_text('{}')
            return {}
        with mock.patch.object(f, 'inventory', side_effect=scan), self.assertRaisesRegex(ValueError, 'receipt changed'):
            f.publish(out, record, lambda: None, lambda: 299)
        self.assertEqual(json.loads((out / 'receipt.json').read_text())['status'], 'failed')
        self.assertTrue((out / 'receipt.invalidated.json').exists())

    def test_publication_final_scan_timeout(self):
        out = self.root / '.runs/pub'
        out.mkdir()
        expired = False
        def scan(*args, **kwargs):
            nonlocal expired
            expired = True
            return {}
        def remaining():
            if expired:
                raise TimeoutError('deadline')
            return 299
        with mock.patch.object(f, 'inventory', side_effect=scan), self.assertRaises(TimeoutError):
            f.publish(out, {'status': 'acquired_unqualified'}, lambda: None, remaining)
        self.assertEqual(json.loads((out / 'receipt.json').read_text())['status'], 'failed')

    def test_cancel_post_positive_and_failed_corrective_write(self):
        out = self.root / '.runs/pub'
        out.mkdir()
        calls = 0
        actual = f.write_json
        def write(path, record):
            nonlocal calls
            calls += 1
            if calls > 1:
                raise OSError('corrective write unavailable')
            return actual(path, record)
        stable_calls = 0
        def stable():
            nonlocal stable_calls
            stable_calls += 1
            if stable_calls == 2:
                raise KeyboardInterrupt('postpositive cancellation')
        with mock.patch.object(f, 'write_json', side_effect=write), self.assertRaises(KeyboardInterrupt):
            f.publish(out, {'status': 'acquired_unqualified'}, stable, lambda: 299)
        self.assertFalse((out / 'receipt.json').exists())
        self.assertTrue((out / 'receipt.invalidated.json').exists())

    def test_no_redirect(self):
        with self.assertRaisesRegex(ValueError, 'redirect'):
            f.NoRedirect().redirect_request(None, None, 302, '', {}, 'https://other.invalid')

    def test_http_failure_and_oversize_retained(self):
        class Response(io.BytesIO):
            code = 200
            headers = {}
            url = 'https://raw.githubusercontent.com/fixed'
        row = dict(self.row, raw_url=Response.url)
        for index, (code, raw) in enumerate(((200, b'123456789'), (404, b'fail'))):
            response = Response(raw)
            response.code = code
            opener = mock.Mock()
            opener.open.return_value = response
            rec = {}
            path = self.root / f'http-{index}.bin'
            with mock.patch.object(f.urllib.request, 'build_opener', return_value=opener):
                if code == 200:
                    result = f.fetch_one(row, rec, path, 100, lambda: 299)
                    self.assertEqual(len(result), 5)
                    with self.assertRaisesRegex(ValueError, 'size'):
                        f.payload(row, result)
                else:
                    with self.assertRaisesRegex(ValueError, 'HTTP status'):
                        f.fetch_one(row, rec, path, 100, lambda: 299)
                self.assertLessEqual(path.stat().st_size, 5)
                self.assertEqual(rec['http_status'], code)

    def test_strict_json(self):
        for raw in (b'{"a":1,"a":2}', b'{"a":NaN}'):
            with self.assertRaises(ValueError):
                f.decode(raw)


if __name__ == '__main__':
    unittest.main(verbosity=2)
