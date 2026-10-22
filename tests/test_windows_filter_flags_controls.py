"""Draft offline controls for the applied014 build helper; no Windows APIs.

This module AST-loads the real function and real ctypes layouts after the014
patch is applied. It does not apply the patch or load a DLL. The fake library
checks Python harness custody/refusal behavior, not C semantics or isolation.
"""
import ast
import copy
import ctypes
from pathlib import Path
from types import SimpleNamespace
import unittest


# Works in this ignored draft directory or after copying into repository tests.
SOURCE = next(parent / 'scripts/windows_native_slice/persistent_guard_build.py'
              for parent in tuple(Path(__file__).resolve().parents)[:5]
              if (parent / 'scripts/windows_native_slice/persistent_guard_build.py').is_file())


def require(value, message):
    if not value:
        raise RuntimeError(message)


def control_before_owner(tree):
    """Require an unconditional sibling control call before the canary branch."""
    main = next(node for node in tree.body
                if isinstance(node, ast.FunctionDef) and node.name == 'main')
    owner_calls = [node for node in ast.walk(main) if isinstance(node, ast.Call)
                   and isinstance(node.func, ast.Name) and node.func.id == 'PersistentGuardState']
    if len(owner_calls) != 1:
        raise AssertionError('one live owner constructor required')
    for block in ast.walk(main):
        body = getattr(block, 'body', None)
        if not isinstance(body, list):
            continue
        for index, statement in enumerate(body):
            if (isinstance(statement, ast.Assign) and isinstance(statement.value, ast.Call)
                    and isinstance(statement.value.func, ast.Name)
                    and statement.value.func.id == 'filter_flags_controls'):
                # This assignment may throw. There must be no local catch that
                # permits continuing to the owner after a failed control.
                later = body[index + 1:]
                if any(isinstance(item, ast.If) and owner_calls[0] in tuple(ast.walk(item))
                       for item in later):
                    return body, index
    raise AssertionError('flags controls must run before live owner construction')


class FilterFlagsControls(unittest.TestCase):
    def setUp(self):
        self.tree = ast.parse(SOURCE.read_text())
        nodes = [node for node in self.tree.body if
                 (isinstance(node, ast.ClassDef) and node.name in ('GUID', 'Info', 'Diagnostic'))
                 or (isinstance(node, ast.FunctionDef) and node.name == 'filter_flags_controls')]
        self.assertEqual({node.name for node in nodes},
                         {'GUID', 'Info', 'Diagnostic', 'filter_flags_controls'},
                         'apply the reviewed014 source patch before running these draft controls')
        self.calls, self.binds = [], []
        self.return_override, self.mutate = None, None
        scope = {'C': ctypes, 'require': require,
                 'bind_library': lambda path: self.bind(path)}
        exec(compile(ast.Module(body=nodes, type_ignores=[]), str(SOURCE), 'exec'), scope)
        self.Diagnostic = scope['Diagnostic']
        self.controls = scope['filter_flags_controls']
        self.library = SimpleNamespace(PG_TestFilterFlags=self.fake_flags)

    def bind(self, path):
        self.binds.append(path)
        return self.library, {}, {}

    def fake_flags(self, flags, pointer, size):
        self.calls.append((flags, pointer is None, size))
        if pointer is None:
            code = 24
        else:
            row = ctypes.cast(pointer, ctypes.POINTER(self.Diagnostic)).contents
            row.abi, row.bytes = 1, 136
            code = 0 if flags == 65 else 13
            if code:
                row.recorded, row.error = 1, 13
                row.stage, row.predicate = b'filter_fields', b'flags'
                row.object_index, row.expected_low, row.actual_low = 1, 65, flags
            if self.mutate is not None:
                self.mutate(flags, row)
        if self.return_override is not None:
            code = self.return_override(flags, pointer is None, code)
        return code

    def test_exact_complete_population_and_null_output_precede_all_scalar_calls(self):
        marker = object()
        result = self.controls(marker)
        expected_flags = [65] + [65 ^ (1 << bit) for bit in range(32)] + [0, 0xffffffff]
        self.assertEqual(self.binds, [marker])
        self.assertEqual(self.calls, [(65, True, 136)] +
                         [(flags, False, 136) for flags in expected_flags])
        rows = result['outcomes']
        self.assertEqual(len(rows), 35)
        self.assertEqual([row['flags'] for row in rows], expected_flags)
        self.assertEqual([row['actual'] for row in rows], [0] + [13] * 34)
        self.assertEqual([row['case'] for row in rows[1:33]],
                         ['toggle_bit_' + str(bit) for bit in range(32)])
        self.assertTrue(all(row['passed'] for row in rows))
        self.assertTrue(result['passed'])
        self.assertEqual(result['predicate_cases'], 35)
        self.assertEqual(result['null_output_refusal'], 24)
        self.assertEqual(result['exact_returned_flags'], 65)
        self.assertEqual(result['unchanged_requested_flags'], 1)
        for name in ('actual_policy_operations', 'valid_owner_created', 'Native_admitted'):
            self.assertIs(result[name], False)

    def test_bad_null_refusal_stops_before_any_scalar_case(self):
        self.return_override = lambda flags, null, code: 0 if null else code
        with self.assertRaisesRegex(RuntimeError, 'NULL output refusal'):
            self.controls('unused-DLL-path')
        self.assertEqual(self.calls, [(65, True, 136)])

    def test_wrong_C_outcomes_never_become_successful_control_report(self):
        # Both false refusal and false acceptance matter, including accepting
        # unindexed persistence or a filter carrying the DISABLED bit.
        for target, code in ((65, 13), (1, 0), (65 | 32, 0), (64, 87)):
            with self.subTest(flags=target, code=code):
                self.calls.clear()
                self.return_override = lambda flags, null, original: code if not null and flags == target else original
                with self.assertRaisesRegex(RuntimeError, 'exact C flags predicate differs'):
                    self.controls('unused-DLL-path')
                self.assertEqual(self.calls[-1], (target, False, 136))

    def test_malformed_failure_diagnostics_refuse_even_with_expected_C_error(self):
        faults = {'abi': 2, 'bytes': 135, 'recorded': 0, 'error': 0,
                  'stage': b'wrong', 'predicate': b'wrong', 'object_index': 2,
                  'element_index': 1, 'expected_low': 1, 'expected_high': 1,
                  'actual_low': 65, 'actual_high': 1}
        #64 is the first scalar negative (missing PERSISTENT); each corrupt
        #field is applied only there, leaving the successful65 case intact.
        for field, value in faults.items():
            with self.subTest(field=field):
                self.calls.clear()
                self.mutate = lambda flags, row: setattr(row, field, value) if flags == 64 else None
                with self.assertRaisesRegex(RuntimeError, 'exact C flags'):
                    self.controls('unused-DLL-path')
                self.assertEqual(self.calls[-1], (64, False, 136))

    def test_success_diagnostic_cannot_smuggle_recorded_failure_or_residue(self):
        faults = {'recorded': 1, 'error': 13, 'stage': b'filter_fields',
                  'predicate': b'flags', 'object_index': 1, 'element_index': 1,
                  'expected_low': 65, 'expected_high': 1,
                  'actual_low': 65, 'actual_high': 1}
        for field, value in faults.items():
            with self.subTest(field=field):
                self.calls.clear()
                self.mutate = lambda flags, row: setattr(row, field, value) if flags == 65 else None
                with self.assertRaisesRegex(RuntimeError, 'invented failure evidence'):
                    self.controls('unused-DLL-path')
                self.assertEqual(self.calls[-1], (65, False, 136))

    def test_source_requires_controls_before_any_live_owner(self):
        body, index = control_before_owner(self.tree)
        self.assertIsInstance(body[index].value.args[0], ast.Name)
        self.assertEqual(body[index].value.args[0].id, 'dll')
        # Falsify the sequencing assertion by moving that exact statement after
        # the canary branch; no import or main/Windows execution is involved.
        changed = copy.deepcopy(self.tree)
        changed_body, changed_index = control_before_owner(changed)
        late = changed_body.pop(changed_index)
        changed_body.append(late)
        with self.assertRaisesRegex(AssertionError, 'before live owner'):
            control_before_owner(changed)


if __name__ == '__main__':
    unittest.main()
