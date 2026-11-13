"""Fresh bounded activity queries; no project backup or historical retirement."""
import os
from pathlib import Path
import selectors
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from scripts import verification_scratch as scratch


class BatchActivity(unittest.TestCase):
    def setUp(self):
        base = Path(__file__).resolve().parents[1] / '.cache/activity-tests'
        base.mkdir(parents=True, exist_ok=True)
        temporary = tempfile.TemporaryDirectory(dir=base)
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()

    def result(self, text='', **kwargs):
        return SimpleNamespace(returncode=kwargs.get('returncode', 0),
                               stderr=kwargs.get('stderr', ''), stdout=text)

    def query(self, targets, result):
        with patch.object(scratch.sys, 'platform', 'darwin'), \
             patch.object(scratch.subprocess, 'run', return_value=result) as call:
            answer = scratch.active_users_many(targets)
        return answer, call

    def test_85_paths_share_one_query_and_match_exact_descendants_only(self):
        targets = [self.root / ('scope' + str(index)) for index in range(85)]
        child = targets[0] / 'sub'; targets.append(child)
        text = 'p71\nn' + str(child / 'open') + '\nn' + str(targets[1]) + '\n'
        text += 'p72\nn' + str(self.root / 'scope2-sibling/open') + '\n'
        answer, call = self.query(targets, self.result(text))
        self.assertEqual(answer[str(targets[0])], ['71'])
        self.assertEqual(answer[str(child)], ['71'])
        self.assertEqual(answer[str(targets[1])], ['71'])
        self.assertEqual(answer[str(targets[2])], [])
        self.assertEqual(len(answer), 86)
        self.assertEqual(call.call_count, 1)
        self.assertEqual(call.call_args.kwargs['timeout'], 30)
        self.assertEqual(call.call_args.args[0][-1], '-Fpn')
        self.assertNotIn(str(self.root / 'scope2-sibling/open'), answer)

    def test_each_boundary_and_legacy_api_queries_freshly(self):
        target = self.root / 'target'
        outputs = [self.result('p11\nn/unrelated\n'),
                   self.result('p12\nn' + str(target / 'open') + '\n'),
                   self.result('p13\nn' + str(target) + '\n')]
        with patch.object(scratch.sys, 'platform', 'darwin'), \
             patch.object(scratch.subprocess, 'run', side_effect=outputs) as call:
            self.assertEqual(scratch.active_users_many([target]), {str(target): []})
            self.assertEqual(scratch.active_users_many([target]), {str(target): ['12']})
            self.assertEqual(scratch.active_users(target), ['13'])
        self.assertEqual(call.call_count, 3)

    def test_query_failure_refuses_whole_batch_without_partial_answer(self):
        class Oversized(str):
            def __len__(self): return 16 * 1024**2 + 1
        target = self.root / 'target'
        failures = [self.result('p1\n', returncode=1),
                    self.result('p1\n', stderr='inspection incomplete'),
                    self.result(Oversized('p1\n')),
                    self.result('n' + str(target) + '\n'),
                    self.result('pbad\nn' + str(target) + '\n'),
                    self.result('p0\n'), self.result('p\n'), self.result('p-1\n'),
                    self.result('p１\n'), self.result(''), self.result('unrecognized\n')]
        for result in failures:
            with self.subTest(result=result), self.assertRaises(scratch.ScratchError):
                self.query([target], result)
        for error in (PermissionError('denied'), subprocess.TimeoutExpired('lsof', 30),
                      UnicodeError('unreadable output')):
            with self.subTest(error=type(error).__name__), \
                 patch.object(scratch.sys, 'platform', 'darwin'), \
                 patch.object(scratch.subprocess, 'run', side_effect=error), \
                 self.assertRaises(scratch.ScratchError):
                scratch.active_users_many([target])

    def test_scope_refusals_precede_process_query(self):
        alias = self.root / 'alias'; alias.symlink_to(self.root, target_is_directory=True)
        batches = [[], str(self.root), self.root, [alias], [self.root / 'bad\nname'],
                   [self.root / 'bad\rname'], [self.root / '..' / 'outside'],
                   [self.root / 'x'] * 4097]
        with patch.object(scratch.subprocess, 'run') as call:
            for targets in batches:
                with self.subTest(targets_type=type(targets).__name__), \
                     self.assertRaises(scratch.ScratchError):
                    scratch.active_users_many(targets)
        call.assert_not_called()

    def test_unsupported_platform_refuses(self):
        with patch.object(scratch.sys, 'platform', 'win32'), \
             self.assertRaisesRegex(scratch.ScratchError, 'not qualified'):
            scratch.active_users_many([self.root])

    def test_duplicate_paths_and_file_records_do_not_duplicate_pids(self):
        answer, call = self.query([self.root, self.root],
            self.result('p5\nn' + str(self.root) + '\nn' + str(self.root / 'file') + '\n'))
        self.assertEqual(answer, {str(self.root): ['5']})
        self.assertEqual(call.call_count, 1)

    @unittest.skipUnless(sys.platform == 'darwin', 'actual macOS owned-file activity')
    def test_actual_owned_open_file_detects_child_and_fresh_exit(self):
        selected, sibling = self.root / 'selected', self.root / 'sibling'
        selected.mkdir(); sibling.mkdir()
        payload = selected / 'payload'; payload.write_bytes(b'owned activity fixture')
        child = subprocess.Popen([sys.executable, '-B', '-c',
            'import sys; f=open(sys.argv[1],"rb"); print("ready",flush=True); sys.stdin.buffer.read()',
            str(payload)], cwd=self.root, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True)
        try:
            with selectors.DefaultSelector() as selector:
                selector.register(child.stdout, selectors.EVENT_READ)
                self.assertTrue(selector.select(timeout=5), 'Owned fixture did not become ready')
            self.assertEqual(child.stdout.readline().strip(), 'ready')
            observed = scratch.active_users_many([selected, payload, sibling])
            self.assertIn(str(child.pid), observed[str(selected)])
            self.assertIn(str(child.pid), observed[str(payload)])
            self.assertNotIn(str(child.pid), observed[str(sibling)])
            self.assertEqual(set(observed), {str(selected), str(payload), str(sibling)})
        finally:
            child.terminate(); child.communicate(timeout=5)
        fresh = scratch.active_users_many([selected, sibling])
        self.assertNotIn(str(child.pid), fresh[str(selected)])
        self.assertEqual(payload.read_bytes(), b'owned activity fixture')


if __name__ == '__main__': unittest.main()
