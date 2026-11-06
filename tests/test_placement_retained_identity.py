"""Read-only retained replay controls; no Native or GUI execution."""
import ast
from contextlib import contextmanager
import copy
import inspect
import os
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

from experiments import placement_choice as choice
from experiments import placement_native_evidence as reader


class RetainedIdentity(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.output = self.root / '.runs' / 'retained'
        self.work = self.output / 'work'
        self.work.mkdir(parents=True)
        self.payload = self.work / 'proof.json'
        self.payload.write_text('{"native":"retained"}')

    def identity(self):
        return reader.retained_tree_identity(self.output, self.root)

    def requests(self):
        info = self.work.stat()
        current = dict(schema=1, board=str(self.work / 'source.kicad_pcb'),
                       job_identity=[info.st_dev, info.st_ino], moves_nm={'part': [1, 2]})
        historical = copy.deepcopy(current)
        historical['job_identity'][0] += 1
        return current, historical

    def test_remounted_retained_request_passes_without_mutating_either_record(self):
        current, historical = self.requests(); before = copy.deepcopy((current, historical))
        self.assertEqual(choice.check_native_request(historical, current, retained=True), historical['job_identity'])
        self.assertEqual((current, historical), before)

    def test_same_request_still_refused_for_live_execution(self):
        current, historical = self.requests()
        self.assertIsNone(choice.check_native_request(current, current))
        with self.assertRaisesRegex(ValueError, 'Native request differs'):
            choice.check_native_request(historical, current)
        with self.assertRaises(ValueError):
            choice.check_native_request(historical, current, retained=1)

    def test_replay_does_not_relax_other_fields(self):
        current, historical = self.requests()
        for key, value in [('schema', True), ('board', 'another-board'), ('moves_nm', {'part': [2, 2]}),
                           ('extra', 'unrecognized')]:
            changed = copy.deepcopy(historical); changed[key] = value
            with self.subTest(field=key), self.assertRaises(ValueError):
                choice.check_native_request(changed, current, retained=True)

    def test_invalid_historical_identity_or_changed_inode_refuses(self):
        current, historical = self.requests()
        inode = current['job_identity'][1]
        for identity in (None, [], [1], [1, inode, 1], [True, inode], [1, True], [0, inode],
                         [-1, inode], [1.0, inode], [1, inode + 1], (1, inode)):
            changed = dict(historical, job_identity=identity)
            with self.subTest(identity=identity), self.assertRaises(ValueError):
                choice.check_native_request(changed, current, retained=True)

    def test_cross_stage_historical_identity_must_be_consistent(self):
        current, historical = self.requests()
        previous = choice.check_native_request(historical, current, retained=True)
        self.assertEqual(choice.check_native_request(historical, current, retained=True, previous=previous), previous)
        changed = copy.deepcopy(historical); changed['job_identity'][0] += 1
        with self.assertRaisesRegex(ValueError, 'inconsistent retained'):
            choice.check_native_request(changed, current, retained=True, previous=previous)

    def test_complete_current_tree_is_stable_and_contains_descendants(self):
        identity = self.identity()
        self.assertEqual(set(identity), {'.', 'work', 'work/proof.json'})
        self.assertEqual(identity, self.identity())

    def test_same_content_directory_replacement_changes_current_fence(self):
        before = self.identity()
        self.work.rename(self.output / 'old-work')
        self.work.mkdir(); self.payload.write_text('{"native":"retained"}')
        self.assertNotEqual(before['work'], self.identity()['work'])

    def test_same_content_file_replacement_and_permission_change_are_visible(self):
        before = self.identity()
        self.payload.rename(self.work / 'original')
        self.payload.write_text('{"native":"retained"}')
        self.assertNotEqual(before['work/proof.json'], self.identity()['work/proof.json'])
        before = self.identity()
        self.payload.chmod(0o400)
        self.assertNotEqual(before, self.identity())

    def test_symlink_file_directory_or_ancestor_refuses(self):
        link = self.work / 'linked'; link.symlink_to(self.payload)
        with self.assertRaises(ValueError): self.identity()
        link.unlink(); link.symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(ValueError): self.identity()
        ancestor = self.root / 'alias'; ancestor.symlink_to(self.output, target_is_directory=True)
        with self.assertRaises(ValueError): reader.retained_tree_identity(ancestor / 'work', self.root)

    @unittest.skipUnless(hasattr(os, 'mkfifo'), 'POSIX fixture')
    def test_special_file_refuses_without_opening_it(self):
        os.mkfifo(self.work / 'fifo')
        with self.assertRaisesRegex(ValueError, 'special file'): self.identity()

    def test_unexpected_descendant_mount_refuses_before_descent(self):
        real_scandir = os.scandir
        @contextmanager
        def different_mount(fd):
            with real_scandir(fd) as iterator:
                rows = []
                for entry in iterator:
                    info = entry.stat(follow_symlinks=False)
                    value = SimpleNamespace(st_dev=info.st_dev + 1, st_ino=info.st_ino,
                        st_mode=info.st_mode, st_uid=info.st_uid, st_gid=info.st_gid,
                        st_flags=getattr(info, 'st_flags', 0))
                    rows.append(SimpleNamespace(name=entry.name, stat=lambda *, follow_symlinks, value=value: value))
                yield iter(rows)
        with patch.object(reader.os, 'scandir', different_mount), self.assertRaisesRegex(ValueError, 'unexpected mount'):
            self.identity()

    def test_outside_project_and_unbounded_entry_tree_refuse(self):
        with self.assertRaises(ValueError): reader.retained_tree_identity(self.root, self.output)
        real_scandir = os.scandir
        @contextmanager
        def repeated(fd):
            with real_scandir(fd) as iterator:
                entry = next(iterator)
                yield iter([entry] * 4001)
        with patch.object(reader.os, 'scandir', repeated), self.assertRaisesRegex(ValueError, 'entry ceiling'):
            self.identity()

    def test_only_completed_reader_opts_into_historical_request_replay(self):
        tree = ast.parse(inspect.getsource(choice))
        calls = []
        for function in tree.body:
            if isinstance(function, ast.FunctionDef):
                for node in ast.walk(function):
                    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'proof':
                        calls.append((function.name, {item.arg: ast.literal_eval(item.value) for item in node.keywords}))
        self.assertEqual([name for name, values in calls if values.get('retained') is True], ['check'])
        self.assertTrue(all(not values for name, values in calls if name != 'check'))
        self.assertIs(inspect.signature(choice.proof).parameters['retained'].default, False)


if __name__ == '__main__': unittest.main()
