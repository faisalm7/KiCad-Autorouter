"""Exercise the qualification source guard without importing its proof reader.

The real module deliberately refuses import before both audited files are
committed. Extract only that actual function for small filesystem fault tests;
this does not qualify any Native evidence or open the comparison gate.
"""
import ast
import hashlib
from pathlib import Path
import re
import tempfile
import types
import unittest


class QualificationSourceGuard(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        (self.root/'scripts').mkdir()
        self.helper = self.root/'scripts/freeze_current_comparison.py'
        self.module = self.root/'scripts/qualification_runtime074.py'
        self.helper.write_bytes(b'owned helper\n')
        self.module.write_bytes(b'owned qualification\n')
        self.committed = {p.relative_to(self.root).as_posix(): p.read_bytes()
                          for p in (self.helper, self.module)}
        self.head = 'a'*40
        source = Path(__file__).resolve().parents[1]/'scripts/qualification_runtime074.py'
        node = next(n for n in ast.parse(source.read_text()).body
                    if isinstance(n, ast.FunctionDef) and n.name == '_check_shared_helper_source')
        self.scope = dict(Path=Path, hashlib=hashlib, ROOT=self.root,
                          __file__=str(self.module), SHARED_HELPER_PATH=self.helper,
                          pv=types.SimpleNamespace(_HEAD=re.compile('[0-9a-f]{40}'), _git=self.git))
        exec(compile(ast.Module(body=[node], type_ignores=[]), str(source), 'exec'), self.scope)
        self.guard = self.scope['_check_shared_helper_source']

    def git(self, root, *args):
        self.assertEqual(root, self.root)
        if args == ('rev-parse', 'HEAD'):
            return self.head.encode()+b'\n'
        self.assertEqual(args[0], 'show')
        commit, name = args[1].split(':', 1)
        self.assertEqual(commit, self.head)
        return self.committed[name]

    def test_same_head_exact_bytes_then_mid_replay_change_refused(self):
        identity = self.guard()
        self.assertEqual(identity['files']['scripts/freeze_current_comparison.py'],
                         hashlib.sha256(self.helper.read_bytes()).hexdigest())
        self.assertEqual(identity['head'], self.head)
        self.scope['SOURCE_IDENTITY'] = identity
        self.assertEqual(self.guard(), identity)
        self.helper.write_bytes(b'new audited helper\n')
        self.committed['scripts/freeze_current_comparison.py'] = self.helper.read_bytes()
        with self.assertRaisesRegex(ValueError, 'changed during replay'):
            self.guard()

    def test_committed_module_change_and_new_head_cannot_attest_loaded_code(self):
        identity = self.guard()
        self.scope['SOURCE_IDENTITY'] = identity
        original = self.module.read_bytes()
        self.module.write_bytes(b'new committed module\n')
        self.committed['scripts/qualification_runtime074.py'] = self.module.read_bytes()
        with self.assertRaisesRegex(ValueError, 'changed during replay'):
            self.guard()
        self.module.write_bytes(original)
        self.committed['scripts/qualification_runtime074.py'] = original
        self.head = 'b'*40
        with self.assertRaisesRegex(ValueError, 'changed during replay'):
            self.guard()

    def test_each_uncommitted_file_refused(self):
        for path in (self.helper, self.module):
            with self.subTest(path=path.name):
                original = path.read_bytes()
                path.write_bytes(original+b'changed\n')
                with self.assertRaisesRegex(ValueError, 'differs from committed HEAD'):
                    self.guard()
                path.write_bytes(original)

    def test_symlink_oversize_and_bad_head_refused(self):
        original = self.helper.read_bytes()
        self.helper.unlink()
        self.helper.symlink_to(self.module)
        with self.assertRaisesRegex(ValueError, 'canonical bounded'):
            self.guard()
        self.helper.unlink()
        self.helper.write_bytes(b'x'*(2*1024**2+1))
        with self.assertRaisesRegex(ValueError, 'canonical bounded'):
            self.guard()
        self.helper.write_bytes(original)
        self.head = 'not-a-commit'
        with self.assertRaisesRegex(ValueError, 'source HEAD'):
            self.guard()


if __name__ == '__main__':
    unittest.main()
