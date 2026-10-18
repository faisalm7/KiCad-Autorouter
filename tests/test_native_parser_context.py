"""Portable authored parser controls; never Native/tool/routing qualification.

Fake tool files and worker metadata are explicit software fixtures. This module
does not run any executable. Existing fixture setup is reused without inheriting
or rerunning its original test population.
"""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from autorouter import adapter, config as c, floor_route as f, local_settings as ls
from autorouter import netclass, padless_alias, pipeline as p, placement_clearance as pc
from tests import test_fixed_placement_session as fixed_fixture
from tests import test_netclass as class_fixture
from tests import test_normal_local_settings_policy as normal_fixture
from tests import test_padless_alias_policy as alias_fixture


class ExplicitParserContextControls(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='owned-native-context-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        args = {'expected_version': '10.0.7'}
        for name in ('cli', 'python', 'pcbnew'):
            path = self.root / name
            path.write_bytes(('Authored fake ' + name + '; never executed.').encode())
            args[name] = path
            args[name + '_sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
        self.nt = p.ExperimentalNativeToolchain(**args)

    def fixture(self, cls, method):
        owned = cls(methodName=method)
        owned.setUp()
        self.addCleanup(owned.doCleanups)
        return owned

    def author_context(self, root, data):
        """Setup only: declare new fake metadata before introducing any fault."""
        data['experimental_native_toolchain'] = self.nt.record()
        for step in data['steps']:
            argv = step.get('argv', [])
            sandbox = f.SANDBOX if argv[:len(f.SANDBOX)] == f.SANDBOX else []
            args = argv[len(sandbox):]
            if args[:2] == [str(c.PYTHON), str(c.ROOT / 'autorouter/native.py')]:
                # Author the separately qualified explicit Native path. Its
                # worker never enables the production10.0.0 task-copper flag.
                from autorouter.task_copper import FLAG
                step['argv'] = [*sandbox, *p.native_prefix(self.nt),
                                *(value for value in args[2:] if value != FLAG)]
            elif args[:3] == [str(c.CLI), 'pcb', 'drc']:
                step['argv'] = [*sandbox, str(self.nt.cli), *args[1:]]
                path = Path(step['cwd']) / (step['name'] + '-binding.json')
                binding = f.read_json(path)
                binding['experimental_native_toolchain'] = self.nt.record()
                p.save_json(path, binding)
            else:
                continue
            process = Path(step['cwd']) / (step['name'] + '-process.json')
            if process.exists():
                worker = f.read_json(process)
                worker['argv'] = list(step['argv'])
                p.save_json(process, worker)
        for path in root.rglob('*.alias-export.json'):
            proof = f.read_json(path)
            proof['native_version'] = '10.0.7'
            p.save_json(path, proof)

    def test_exact_default_and_explicit_prefixes_are_read_only(self):
        for nt in (None, self.nt):
            parse = adapter.native_command_parser(nt)
            raw = [*f.SANDBOX, *p.native_prefix(nt), 'import', '/owned/board',
                   '/owned/imported', '/owned/routes.ses']
            before = copy.deepcopy(raw)
            expected_python = c.PYTHON if nt is None else nt.python
            self.assertEqual(parse(raw, 'import'), [str(expected_python),
                str(c.ROOT / 'autorouter/native.py'), 'import', *raw[-3:]])
            self.assertEqual(raw, before)
            self.assertIsNone(parse(raw, 'export'))

    def test_default_refuses_experimental_prefix_even_with_default_python(self):
        # This would be skipped if the parser looked only for action at index2.
        parse = adapter.native_command_parser()
        for python in (str(c.PYTHON), str(self.nt.python)):
            raw = [python, str(c.ROOT / 'autorouter/native.py'),
                   '--experimental-native', json.dumps(self.nt.record(), sort_keys=True),
                   'import', 'source', 'output', 'session']
            with self.subTest(python=python), self.assertRaises(p.Rejected):
                parse(raw, 'export')  # Reject before action-specific census filtering.
        with self.assertRaises(p.Rejected):
            adapter.native_command_parser(data={'experimental_native_toolchain': self.nt.record()})
        with self.assertRaises(p.Rejected):
            adapter.native_command_parser(data={'steps': [{'argv': raw}]})

    def test_other_prefix_record_and_extra_flag_cannot_escape_census(self):
        parse = adapter.native_command_parser(self.nt)
        good = [*p.native_prefix(self.nt), 'export', 'source', 'output']
        cases = []
        bad = list(good); bad[0] = str(c.PYTHON); cases.append(bad)
        bad = list(good); bad[1] = str(self.root / 'other/native.py'); cases.append(bad)
        bad = list(good); bad[3] = json.dumps(self.nt.record(), indent=2); cases.append(bad)
        bad = list(good); record = self.nt.record(); record['schema'] = True
        bad[3] = json.dumps(record, sort_keys=True); cases.append(bad)
        bad = list(good); bad.insert(1, '-B'); cases.append(bad)
        bad = [*good[:2], *good[4:]]; cases.append(bad)  # Deleted explicit context.
        for raw in cases:
            with self.subTest(raw=raw), self.assertRaises(p.Rejected):
                parse(raw, 'import')
        with self.assertRaises(p.Rejected):
            adapter.native_command_parser(self.nt.record())  # Dict is not typed authority.

    def test_class_mapping_explicit_version_preserves_all_metrics_and_default(self):
        tree, native, project = class_fixture.fixtures(True)
        self.assertTrue(netclass.audit_mapping(tree, native, project)['passed'])
        native['native_version'] = '10.0.7'
        before = copy.deepcopy((tree, native, project))
        self.assertTrue(netclass.audit_mapping(tree, native, project,
            native_toolchain=self.nt)['passed'])
        self.assertEqual((tree, native, project), before)
        with self.assertRaises(ValueError): netclass.audit_mapping(tree, native, project)
        native['native_version'] = '10.0.0'
        with self.assertRaises(ValueError):
            netclass.audit_native(native, project, native_toolchain=self.nt)
        with self.assertRaises(p.Rejected):
            netclass.audit_native(native, project, native_toolchain=self.nt.record())

    def test_dsn_audit_threads_context_and_still_rejects_terminal_loss(self):
        tree, native, project = class_fixture.fixtures(True)
        native['native_version'] = '10.0.7'
        path = self.root / 'owned.dsn'
        path.write_text(adapter._dump_dsn(tree))
        self.assertTrue(netclass.audit_dsn(path, native, project,
            native_toolchain=self.nt)['passed'])
        from autorouter import sexpr as sx
        sx.one(sx.children(sx.one(tree, 'network'), 'net')[0], 'pins').pop()
        path.write_text(adapter._dump_dsn(tree))
        with self.assertRaises(ValueError):
            netclass.audit_dsn(path, native, project, native_toolchain=self.nt)

    def test_explicit_import_replays_and_missing_step_remains_in_census(self):
        owned = self.fixture(fixed_fixture.FixedPlacementImportReadbackControls,
                             'test_nested_authored_import_proof_replays_exactly')
        self.author_context(owned.root, owned.data)
        retained = pc.inventory(owned.root)
        self.assertEqual(len(adapter.check_fixed_placement_import(owned.root,
            owned.data, retained, native_toolchain=self.nt)), 1)
        with self.assertRaises(p.Rejected):
            adapter.check_fixed_placement_import(owned.root, owned.data, retained)
        owned.data.pop('experimental_native_toolchain')
        with self.assertRaises(p.Rejected):
            adapter.check_fixed_placement_import(owned.root, owned.data, retained)
        owned.data['steps'] = []
        with self.assertRaisesRegex(p.Rejected, 'population'):
            adapter.check_fixed_placement_import(owned.root, owned.data, retained,
                                                 native_toolchain=self.nt)

    def test_zero_alias_export_requires_explicit_version_and_complete_census(self):
        owned = self.fixture(alias_fixture.ExportPolicy,
                             'test_zero_alias_complete_source_project_dsn_proof_is_read_only')
        self.author_context(owned.out, owned.data)
        retained = pc.inventory(owned.out)
        self.assertEqual(padless_alias.check_exports(owned.out, owned.data,
            retained, native_toolchain=self.nt)[0]['alias_count'], 0)
        with self.assertRaises(p.Rejected):
            padless_alias.check_exports(owned.out, owned.data, retained)
        proof = f.read_json(owned.paths['proof']); proof['native_version'] = '10.0.0'
        p.save_json(owned.paths['proof'], proof)
        with self.assertRaises(p.Rejected):
            padless_alias.check_exports(owned.out, owned.data, pc.inventory(owned.out),
                                       native_toolchain=self.nt)
        proof['native_version'] = '10.0.7'; p.save_json(owned.paths['proof'], proof)
        owned.data['steps'] = [s for s in owned.data['steps'] if s['name'] != 'export']
        with self.assertRaises(p.Rejected):
            padless_alias.check_exports(owned.out, owned.data, pc.inventory(owned.out),
                                       native_toolchain=self.nt)

    def test_nonzero_aliases_stay_unqualified_with_explicit_context(self):
        owned = self.fixture(alias_fixture.ExportPolicy,
                             'test_zero_alias_complete_source_project_dsn_proof_is_read_only')
        owned.build(aliases=True)
        self.author_context(owned.out, owned.data)
        with self.assertRaisesRegex(p.Rejected, 'nonzero aliases'):
            padless_alias.check_exports(owned.out, owned.data, pc.inventory(owned.out),
                                       native_toolchain=self.nt)

    def test_normal_policy_explicit_drc_cli_binding_and_omission_checks(self):
        owned = self.fixture(normal_fixture.NormalPolicyReceiptControls,
                             'test_current_source_and_tools_policy_must_agree')
        self.author_context(owned.run, owned.data)
        ls.check_normal_policy(owned.run, owned.data, native_toolchain=self.nt)
        with self.assertRaises(p.Rejected):ls.check_normal_policy(owned.run, owned.data)
        row = next(s for s in owned.data['steps'] if s['name'] == 'final-drc')
        path = owned.run / 'final-drc-binding.json'
        binding = f.read_json(path); original = copy.deepcopy(binding)
        binding.pop('experimental_native_toolchain'); p.save_json(path, binding)
        with self.assertRaisesRegex(p.Rejected, 'toolchain binding'):
            ls.check_normal_policy(owned.run, owned.data, native_toolchain=self.nt)
        p.save_json(path, original)
        owned.data['steps'] = [s for s in owned.data['steps'] if s is not row]
        with self.assertRaisesRegex(p.Rejected, 'population'):
            ls.check_normal_policy(owned.run, owned.data, native_toolchain=self.nt)

    def test_normal_policy_other_drc_cli_is_rejected_before_census_filtering(self):
        owned = self.fixture(normal_fixture.NormalPolicyReceiptControls,
                             'test_current_source_and_tools_policy_must_agree')
        self.author_context(owned.run, owned.data)
        row = next(s for s in owned.data['steps'] if s['name'] == 'final-drc')
        argv = list(row['argv']); offset = len(f.SANDBOX) if argv[:len(f.SANDBOX)] == f.SANDBOX else 0
        argv[offset] = str(c.CLI)
        row['argv'] = argv
        path = owned.run / 'final-drc-process.json'
        process = f.read_json(path); process['argv'] = argv; p.save_json(path, process)
        with self.assertRaisesRegex(p.Rejected, 'DRC prefix'):
            ls.check_normal_policy(owned.run, owned.data, native_toolchain=self.nt)


if __name__ == '__main__':
    unittest.main()
