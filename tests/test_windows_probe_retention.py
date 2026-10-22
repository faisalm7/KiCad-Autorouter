"""AST-only owned-log retention controls; no Windows/security/Native proof."""
import ast
import base64
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[1] / 'scripts/windows_native_slice/appcontainer_canary.py'


class WindowsProbeRetentionControls(unittest.TestCase):
    def functions(self, *names, **extra):
        # Extract the actual implementation without importing Windows modules.
        tree = ast.parse(SOURCE.read_text())
        nodes = [next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
                 for name in names]
        printed = []
        scope = dict(Path=Path, base64=base64, hashlib=hashlib, json=json,
                     print=lambda value, **kwargs: printed.append(json.loads(value)), **extra)
        exec(compile(ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[])),
                     str(SOURCE), 'exec'), scope)
        return scope, printed

    def recovered(self, printed, label):
        rows = [x for x in printed if x['kind'] == 'owned-canary-log-base64-chunk' and x['label'] == label]
        self.assertEqual([x['index'] for x in rows], list(range(len(rows))))
        return b''.join(base64.b64decode(x['data'], validate=True) for x in rows)

    def test_exact_nonutf8_multichunk_bytes_match_waited_process_SHA(self):
        scope, printed = self.functions('retain_owned_log')
        raw = (b'\x00\x80\xff\n\rA' * 9000) + b'last-byte\xfe'
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'actual.log'; path.write_bytes(raw)
            meta = scope['retain_owned_log'](path, 'denial', {'log_sha256': hashlib.sha256(raw).hexdigest()})
            self.assertIs(meta['complete'], True)
            self.assertFalse(meta['truncated'])
            self.assertEqual(meta['bytes'], len(raw))
            self.assertEqual(meta['retained_bytes'], len(raw))
            self.assertEqual(meta['chunks'], 3)
            self.assertEqual(self.recovered(printed, 'denial'), raw)
            self.assertEqual(meta['sha256'], hashlib.sha256(raw).hexdigest())
            self.assertEqual(path.read_bytes(), raw)

    def test_missing_log_or_process_or_hash_never_establishes_complete_material(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'actual.log'
            scope, printed = self.functions('retain_owned_log')
            self.assertIs(scope['retain_owned_log'](path, 'missing', None)['complete'], False)
            raw = b'available failure bytes\xff'; path.write_bytes(raw)
            for process in (None, {}, {'log_sha256': '0' * 64}):
                with self.subTest(process=process):
                    scope, printed = self.functions('retain_owned_log')
                    meta = scope['retain_owned_log'](path, 'failed', process)
                    self.assertIs(meta['complete'], False)
                    self.assertEqual(meta['sha256'], hashlib.sha256(raw).hexdigest())
                    # Absent receipt and wrong digest still retain available raw bytes.
                    self.assertEqual(self.recovered(printed, 'failed'), raw)

    def test_oversized_log_is_incomplete_and_only_exact_prefix_is_emitted(self):
        raw = b'\xff' * (256 * 1024) + b'not-retained'
        scope, printed = self.functions('retain_owned_log')
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'oversized.log'; path.write_bytes(raw)
            meta = scope['retain_owned_log'](path, 'oversized', {'log_sha256': hashlib.sha256(raw).hexdigest()})
            self.assertIs(meta['complete'], False)
            self.assertIs(meta['truncated'], True)
            self.assertEqual(meta['bytes'], len(raw))
            self.assertEqual(meta['retained_bytes'], 256 * 1024)
            self.assertEqual(self.recovered(printed, 'oversized'), raw[:256 * 1024])
            self.assertEqual(path.read_bytes(), raw)

    def execute_case(self, *, persistent, status='success', cleanup=True, runner_error=False):
        raw = b'owned setup\x00\xff\n'
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'compile1.log'
            receipt = dict(status=status, cleanup_complete=cleanup, log_sha256=hashlib.sha256(raw).hexdigest())
            def setup(argv, *, cwd, log, root, seconds):
                self.assertEqual((cwd, root, log, seconds), (path.parent, path.parent, path, 30))
                log.write_bytes(raw)
                if runner_error: raise OSError('constructed runner failure')
                return receipt
            scope, printed = self.functions('retain_owned_log', 'execute', run_owned_setup=setup)
            if runner_error:
                with self.assertRaisesRegex(OSError, 'constructed runner failure'):
                    scope['execute'](['owned-setup'], cwd=path.parent, log=path, retain_raw=persistent)
            elif status != 'success' or not cleanup:
                with self.assertRaisesRegex(RuntimeError, 'Compiler/setup command failed'):
                    scope['execute'](['owned-setup'], cwd=path.parent, log=path, retain_raw=persistent)
            else:
                self.assertIs(scope['execute'](['owned-setup'], cwd=path.parent, log=path, retain_raw=persistent), receipt)
            diagnostic = next(x for x in printed if x['kind'] == 'additional-owned-setup-process')
            return raw, diagnostic, printed

    def test_actual_setup_call_sites_select_raw_retention_only_for_persistent_guard(self):
        tree = ast.parse(SOURCE.read_text())
        main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'main')
        calls = [n for n in ast.walk(main) if isinstance(n, ast.Call)
                 and isinstance(n.func, ast.Name) and n.func.id == 'execute']
        self.assertEqual(len(calls), 2)  # DNS setup plus the two-role compiler call site.
        for call in calls:
            choice = next(k.value for k in call.keywords if k.arg == 'retain_raw')
            expr = compile(ast.fix_missing_locations(ast.Expression(body=choice)), str(SOURCE), 'eval')
            self.assertIs(eval(expr, {'persistent_guard': None}), False)
            self.assertIs(eval(expr, {'persistent_guard': object()}), True)

    def test_persistent_execute_retains_exact_bytes_and_process_binding(self):
        raw, diagnostic, printed = self.execute_case(persistent=True)
        self.assertTrue(diagnostic['log_material']['complete'])
        self.assertNotIn('log_utf8', diagnostic)
        self.assertEqual(self.recovered(printed, 'setup:compile1.log'), raw)

    def test_nonpersistent_execute_keeps_existing_decoded_diagnostic_path(self):
        raw, diagnostic, printed = self.execute_case(persistent=False)
        self.assertEqual(diagnostic['log_utf8'], raw.decode('utf-8', errors='replace'))
        self.assertFalse(diagnostic['log_truncated'])
        self.assertNotIn('log_material', diagnostic)
        self.assertFalse(any(x['kind'].startswith('owned-canary-log-') for x in printed))

    def test_setup_runner_exception_preserves_available_raw_bytes_without_success(self):
        raw, diagnostic, printed = self.execute_case(persistent=True, runner_error=True)
        self.assertIs(diagnostic['process'], None)
        self.assertIs(diagnostic['process_receipt_available'], False)
        self.assertIs(diagnostic['log_material']['complete'], False)
        self.assertIn('log_read_error', diagnostic)
        self.assertEqual(self.recovered(printed, 'setup:compile1.log'), raw)

    def test_setup_nonzero_or_cleanup_failure_is_not_promoted_by_complete_log(self):
        for options in (dict(status='nonzero_exit'), dict(cleanup=False)):
            with self.subTest(options=options):
                _, diagnostic, _ = self.execute_case(persistent=True, **options)
                self.assertIs(diagnostic['log_material']['complete'], True)

    def probe_loop(self, scope):
        # Execute only the actual bounded probe loop, not guard creation or any API.
        tree = ast.parse(SOURCE.read_text())
        main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'main')
        loop = next(n for n in ast.walk(main) if isinstance(n, ast.For)
                    and isinstance(n.target, ast.Tuple)
                    and [x.id for x in n.target.elts] == ['label', 'hold', 'cap', 'cancel'])
        exec(compile(ast.fix_missing_locations(ast.Module(body=[loop], type_ignores=[])),
                     str(SOURCE), 'exec'), scope)

    def test_probe_parse_or_runner_exception_retains_exact_available_failure_log(self):
        for fault in ('parse', 'runner'):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as tmp:
                folder = Path(tmp); raw = b'actual malformed JSON\xff\n'
                def run(argv, *, log, **kwargs):
                    log.write_bytes(raw)
                    if fault == 'runner': raise OSError('constructed probe runner failure')
                    return dict(log_sha256=hashlib.sha256(raw).hexdigest(), status='success', cleanup_complete=True, process_count=2)
                scope, printed = self.functions('retain_owned_log', 'records', run=run)
                result = {'cases': []}
                scope.update(guard=SimpleNamespace(scratch=folder, scope=folder, profile_sid='mock-not-security-proof'),
                    parent='owned-parent', child='owned-child', address='127.0.0.1', port=1,
                    persistent_guard=object(), result=result,
                    check_tokens=lambda *a, **k: self.fail('tokens must not be checked after malformed log'))
                error = UnicodeDecodeError if fault == 'parse' else OSError
                with self.assertRaises(error): self.probe_loop(scope)
                self.assertEqual(result['cases'], [])
                self.assertEqual(len(result['probe_log_material']), 1)
                self.assertIs(result['probe_log_material'][0]['complete'], fault == 'parse')
                self.assertEqual(self.recovered(printed, 'denial'), raw)

    def test_probe_success_path_refuses_incomplete_retention(self):
        # Tokens/processes here are deliberate mocks; only the finally refusal is tested.
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            scope = dict(guard=SimpleNamespace(scratch=folder, scope=folder, profile_sid='mock'),
                parent='owned-parent', child='owned-child', address='127.0.0.1', port=1,
                persistent_guard=object(), result={'cases': []}, records=lambda p: [],
                run=lambda *a, **k: dict(status='success', cleanup_complete=True, process_count=2),
                check_tokens=lambda *a, **k: None, retain_owned_log=lambda *a: {'complete': False})
            with self.assertRaisesRegex(RuntimeError, 'log retention is incomplete'):
                self.probe_loop(scope)


if __name__ == '__main__':
    unittest.main()
