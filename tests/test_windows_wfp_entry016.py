"""Constructed observation regressions; only actual Windows can qualify016."""
import ast
import copy
from pathlib import Path
import unittest

CANARY = Path(__file__).resolve().parents[1] / 'scripts/windows_native_slice/appcontainer_canary.py'


class Entry016Controls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        functions = [node for node in ast.parse(CANARY.read_text()).body
                     if isinstance(node, ast.FunctionDef) and node.name == 'check_entry016']
        namespace = {}
        assert len(functions) == 1
        exec(compile(ast.Module(body=functions, type_ignores=[]), str(CANARY), 'exec'), namespace)
        cls.check = staticmethod(namespace['check_entry016'])

    def rows(self):
        rows = []
        for role in (1, 2):
            rows.append(dict(kind='self_token', role=role, pid=100+role,
                             is_appcontainer=1, capabilities=0))
            rows.append(dict(kind='wfp_entry_denial016', role=role, pid=100+role,
                             server_null=True, authn_WINNT=True, identity_null=True,
                             session_null=True, no_thread_token=True, thread_token_error=1008,
                             winerror=5, handle_present=False, close_called=False,
                             close_error=0, setter_calls=0))
        return rows

    def test_two_exact_entries_do_not_claim_setter_equivalence(self):
        result = self.check(self.rows())
        self.assertEqual(result['entry_denials'], 2)
        self.assertEqual(result['object_setters_reached'], 0)
        self.assertFalse(result['inherited_handle_or_broker_equivalence'])

    def test_missing_duplicate_wrong_pid_or_role_refuses(self):
        for change in ('missing', 'duplicate', 'pid', 'role'):
            rows = self.rows()
            if change == 'missing': rows.pop()
            elif change == 'duplicate': rows.append(copy.deepcopy(rows[-1]))
            elif change == 'pid': rows[-1]['pid'] = 999
            else: rows[-1]['role'] = True
            with self.subTest(change=change), self.assertRaises(RuntimeError): self.check(rows)

    def test_success_unknown_error_opened_handle_or_impersonation_refuses(self):
        for key, value in [('winerror', 0), ('winerror', 2), ('winerror', True),
                           ('handle_present', True), ('no_thread_token', False),
                           ('thread_token_error', 5), ('close_error', 5),
                           ('setter_calls', 1), ('session_null', False)]:
            rows = self.rows(); rows[-1][key] = value
            with self.subTest(key=key, value=value), self.assertRaises(RuntimeError): self.check(rows)

    def test_wrong_capability_or_same_process_refuses(self):
        for key, value in [('capabilities', 1), ('is_appcontainer', 0), ('pid', 101)]:
            rows = self.rows(); rows[2][key] = value
            with self.subTest(key=key), self.assertRaises(RuntimeError): self.check(rows)

    def test_object_probe_rows_cannot_be_relabelled_as_entry_only(self):
        for kind in ('state_mutation', 'policy_mutation', 'mutation_engine_open', 'mutation_engine_close'):
            with self.subTest(kind=kind), self.assertRaises(RuntimeError):
                self.check(self.rows() + [dict(kind=kind)])


if __name__ == '__main__':
    unittest.main()
