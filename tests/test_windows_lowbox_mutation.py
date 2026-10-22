"""Unexecuted constructed observation controls; no Windows/Native proof."""
import ast
import copy
from pathlib import Path
import unittest

CANARY = Path(__file__).resolve().parents[1] / 'scripts/windows_native_slice/appcontainer_canary.py'


class LowBoxMutationControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        tree = ast.parse(CANARY.read_text())
        functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)
                     and node.name in ('check_tokens', 'check_mutations')]
        if {node.name for node in functions} != {'check_tokens', 'check_mutations'}:
            raise RuntimeError('Actual current observation checkers required')
        namespace = {}
        exec(compile(ast.Module(body=functions, type_ignores=[]), str(CANARY), 'exec'), namespace)
        cls.tokens = staticmethod(namespace['check_tokens'])
        cls.mutations = staticmethod(namespace['check_mutations'])

    def rows(self):
        rows = [dict(kind='self_token', role=role, pid=100 + role,
                     is_appcontainer=1, capabilities=0, sid='S-1-15-2-42') for role in (1, 2)]
        rows += [dict(kind='suspended_child_token', role=1, pid=102,
                      is_appcontainer=1, capabilities=0, sid='S-1-15-2-42')]
        for role in (1, 2):
            for endpoint in ('owned_loopback', 'public_ipv4'):
                rows.append(dict(kind='tcp', role=role, pid=100 + role, endpoint=endpoint,
                                 connected=False, wsa_error=10013, explicit_access_denied=True))
            for target in (0, 1):
                for operation in ('write_dac', 'write_owner'):
                    rows.append(dict(kind='state_mutation', role=role, pid=100 + role,
                                     target=target, operation=operation, opened=False,
                                     winerror=5, explicit_access_denied=True))
                rows.append(dict(kind='policy_mutation', role=role, pid=100 + role,
                                 target=target, operation='reapply_same_protected_dacl',
                                 winerror=5, explicit_access_denied=True))
            for kind in ('mutation_engine_open', 'mutation_engine_close'):
                rows.append(dict(kind=kind, role=role, pid=100 + role, winerror=0))
        return rows

    def test_exact_both_token_and_denial_population(self):
        rows = self.rows()
        self.tokens(rows, 'S-1-15-2-42')
        self.assertEqual(self.mutations(rows)['state_access_denials'], 8)
        self.assertEqual(self.mutations(rows)['policy_same_DACL_denials'], 4)

    def test_unknown_or_success_is_not_explicit_denial(self):
        for kind in ('state_mutation', 'policy_mutation'):
            for error in (0, 2, 13, 32, 1460, True):
                rows = self.rows()
                next(row for row in rows if row['kind'] == kind)['winerror'] = error
                with self.subTest(kind=kind, error=error), self.assertRaises(RuntimeError):
                    self.mutations(rows)
        for field, value in (('opened', True), ('explicit_access_denied', False)):
            rows = self.rows()
            next(row for row in rows if row['kind'] == 'state_mutation')[field] = value
            with self.subTest(field=field), self.assertRaises(RuntimeError):
                self.mutations(rows)

    def test_no_entry_denial_or_missing_close_upgrades_policy_object_proof(self):
        for kind in ('mutation_engine_open', 'mutation_engine_close'):
            rows = self.rows()
            next(row for row in rows if row['kind'] == kind)['winerror'] = 5
            with self.subTest(kind=kind), self.assertRaises(RuntimeError):
                self.mutations(rows)
        rows = self.rows()
        rows = [row for row in rows if not (row['kind'] == 'mutation_engine_close' and row['role'] == 2)]
        with self.assertRaises(RuntimeError): self.mutations(rows)

    def test_missing_duplicate_wrong_identity_or_target_refuses(self):
        for operation in ('missing', 'duplicate', 'pid', 'target', 'role'):
            rows = self.rows()
            index = next(i for i, row in enumerate(rows) if row['kind'] == 'policy_mutation')
            if operation == 'missing': rows.pop(index)
            elif operation == 'duplicate': rows.append(copy.deepcopy(rows[index]))
            elif operation == 'pid': rows[index]['pid'] = 999
            elif operation == 'target': rows[index]['target'] = 3
            else: rows[index]['role'] = True
            with self.subTest(operation=operation), self.assertRaises(RuntimeError): self.mutations(rows)
        rows = self.rows()
        rows[1]['pid'] = rows[0]['pid']
        with self.assertRaises(RuntimeError): self.mutations(rows)

    def test_wrong_capability_or_suspended_child_identity_refuses_before_mutations(self):
        for kind, field, value in (('self_token', 'capabilities', 1),
                                   ('self_token', 'sid', 'S-1-15-2-99'),
                                   ('suspended_child_token', 'pid', 999)):
            rows = self.rows()
            next(row for row in rows if row['kind'] == kind)[field] = value
            with self.subTest(kind=kind, field=field), self.assertRaises(RuntimeError):
                self.tokens(rows, 'S-1-15-2-42')


if __name__ == '__main__':
    unittest.main()
