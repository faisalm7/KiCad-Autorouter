"""Authored task-copper command/provenance controls; no Native tools run.

These reuse the existing normal-import and explicit-toolchain factories. Worker
metadata and saved reports are synthetic consistency fixtures, not evidence of
routing, export behavior, or Native correctness.
"""
import copy
from pathlib import Path
import unittest

from autorouter import adapter, floor_route as f, pipeline as p
from autorouter import placement_clearance as pc, task_copper as tc
from tests import test_native_parser_context as parser_fixture
from tests import test_normal_selected_import as import_fixture


def author_current_task_copper(root, data):
    """Setup only: upgrade the existing normal-import authored fixture.

    The caller supplies its current captured pipeline. This authors current
    Native/helper provenance and paired worker metadata before fault injection;
    it does not execute an exporter, importer, or any captured code.
    """
    root = Path(root)
    project = Path(p.__file__).resolve().parent
    for name in ('native.py', 'task_copper.py'):
        path = root / 'code' / name
        path.write_bytes((project / name).read_bytes())
        data['tools']['implementation_sha256']['autorouter/' + name] = p.sha(path)
    data['tools']['normal_task_copper_fixed_policy'] = tc.POLICY
    parse = adapter.native_command_parser(with_task_copper=True)
    for imported in list(data['steps']):
        parsed = parse(imported.get('argv'), 'import')
        if parsed is None:
            continue
        args, fixed = parsed
        if not fixed:
            imported['argv'].append(tc.FLAG)
        output = str(Path(imported['cwd']) / 'task.dsn')
        exports = []
        for step in data['steps']:
            exported = parse(step.get('argv'), 'export')
            if (exported is not None and step.get('cwd') == imported['cwd']
                    and exported[0][3:5] == [args[3], output]):
                exports.append((step, exported[1]))
        if not exports:
            step = {key: copy.deepcopy(value) for key, value in imported.items()
                    if key not in {'name', 'argv'}}
            step.update(name='export', argv=[*f.SANDBOX, *p.native_prefix(),
                        'export', args[3], output, tc.FLAG])
            data['steps'].insert(data['steps'].index(imported), step)
            exports = [(step, True)]
        if len(exports) != 1:
            raise AssertionError('authored fixture must have one normal export')
        for step, fixed in exports:
            if not fixed:
                step['argv'].append(tc.FLAG)
        for step in [imported, exports[0][0]]:
            path = Path(step['cwd']) / (step['name'] + '-process.json')
            worker = f.read_json(path) if path.exists() else {
                key: copy.deepcopy(value) for key, value in step.items() if key != 'phase'}
            worker['argv'] = list(step['argv'])
            p.save_json(path, worker)


class TaskCopperContractControls(unittest.TestCase):
    make_import = import_fixture.NormalSelectedImportControls.make

    def make(self, *, protected=False, nested=False, selected=False):
        root, data, original, candidate, check = self.make_import(
            # The shared whole-board fixture already uses protection=[];
            # its setup expects source routes even for that empty protection.
            protected=protected if selected else True, nested=nested, selected=selected)
        project = Path(p.__file__).resolve().parent
        for name in ('pipeline.py',):
            path = root / 'code' / name
            path.write_bytes((project / name).read_bytes())
            data['tools']['implementation_sha256']['autorouter/' + name] = p.sha(path)
        data['tools']['normal_protected_via_import_policy'] = p.PROTECTED_VIA_IMPORT_POLICY
        author_current_task_copper(root, data)

        def contract():
            imports = adapter.check_fixed_placement_import(root, data, pc.inventory(root))
            return tc.check_contract(root, data, imports, declaration=tc.POLICY)

        return root, data, original, candidate, check, contract

    @staticmethod
    def save_workers(data):
        for step in data['steps']:
            if step['name'] not in {'export', 'import'}:
                continue
            path = Path(step['cwd']) / (step['name'] + '-process.json')
            worker = f.read_json(path) if path.exists() else copy.deepcopy(step)
            worker['argv'] = list(step['argv'])
            p.save_json(path, worker)

    @staticmethod
    def rewrite(root, data, name, transform):
        path = root / 'code' / name
        path.write_text(transform(path.read_text()))
        data['tools']['implementation_sha256']['autorouter/' + name] = p.sha(path)

    def remove_flags(self, data, actions=('export', 'import')):
        for step in data['steps']:
            if step['name'] in actions:
                step['argv'] = [value for value in step['argv'] if value != tc.FLAG]
        self.save_workers(data)

    def test_current_whole_zero_and_selected_protection_read_back_without_writes(self):
        for selected, protected in ((False, False), (True, False), (True, True)):
            with self.subTest(selected=selected, protected=protected):
                root, data, _, _, check, contract = self.make(
                    selected=selected, protected=protected)
                before = pc.inventory(root)
                self.assertIsNone(contract())
                expected = ({'expected_policy': p.SELECTED_PROPOSAL_IMPORT_POLICY,
                             'selected_names': ['LED']} if selected else {})
                self.assertEqual(check(), expected)
                self.assertEqual(pc.inventory(root), before)

    def test_either_or_both_flags_missing_refuse_even_with_zero_protection(self):
        for actions in (('export',), ('import',), ('export', 'import')):
            with self.subTest(actions=actions):
                _, data, _, _, check, _ = self.make()
                self.remove_flags(data, actions)
                with self.assertRaisesRegex(p.Rejected, 'paired exact'):
                    check()

    def test_current_declarations_markers_and_source_pins_are_required(self):
        for fault in ('marker_missing', 'marker_unknown', 'pipeline_missing',
                      'pipeline_unknown', 'native_missing', 'native_unknown',
                      'native_unpinned', 'helper_unpinned', 'helper_missing',
                      'helper_pin_missing'):
            with self.subTest(fault=fault):
                root, data, _, _, check, _ = self.make()
                if fault.startswith('marker'):
                    data['tools'].pop('normal_task_copper_fixed_policy')
                    if fault == 'marker_unknown':
                        data['tools']['normal_task_copper_fixed_policy'] = 'unknown'
                elif fault.startswith('pipeline') or fault in {'native_missing', 'native_unknown'}:
                    name = 'pipeline.py' if fault.startswith('pipeline') else 'native.py'
                    identifier = ('NORMAL_TASK_COPPER_FIXED_POLICY' if name == 'pipeline.py'
                                  else 'TASK_COPPER_FIXED_POLICY')
                    replacement = ('# removed declaration' if fault.endswith('missing')
                                   else identifier + "='unknown'")
                    self.rewrite(root, data, name, lambda raw: raw.replace(
                        identifier + "='" + tc.POLICY + "'", replacement))
                elif fault in {'native_unpinned', 'helper_unpinned'}:
                    name = 'native.py' if fault == 'native_unpinned' else 'task_copper.py'
                    path = root / 'code' / name
                    path.write_text(path.read_text() + '\n# unpinned drift\n')
                elif fault == 'helper_missing':
                    (root / 'code/task_copper.py').unlink()
                else:
                    data['tools']['implementation_sha256'].pop('autorouter/task_copper.py')
                with self.assertRaises((p.Rejected, ValueError, OSError)):
                    check()

    def test_current_code_cannot_downgrade_by_deleting_both_declarations_and_flags(self):
        root, data, _, _, check, _ = self.make()
        for name, identifier in (('pipeline.py', 'NORMAL_TASK_COPPER_FIXED_POLICY'),
                                 ('native.py', 'TASK_COPPER_FIXED_POLICY')):
            self.rewrite(root, data, name, lambda raw, identifier=identifier:
                raw.replace(identifier + "='" + tc.POLICY + "'", '# removed declaration'))
        data['tools'].pop('normal_task_copper_fixed_policy')
        self.remove_flags(data)
        with self.assertRaisesRegex(p.Rejected, 'task copper'):
            check()

    def test_task_deletion_with_earlier_policy_and_proof_deletion_still_refuses(self):
        for remove_native in (False, True):
            with self.subTest(remove_native=remove_native):
                root, data, _, _, check, _ = self.make()
                self.rewrite(root, data, 'pipeline.py', lambda raw: raw.replace(
                    "NORMAL_TASK_COPPER_FIXED_POLICY='" + tc.POLICY + "'",
                    '# removed task declaration').replace(
                    "NORMAL_SELECTED_PROPOSAL_IMPORT_POLICY='selected-proposals-exact-source-v1'",
                    '# removed older declaration'))
                if remove_native:
                    self.rewrite(root, data, 'native.py', lambda raw: raw.replace(
                        "TASK_COPPER_FIXED_POLICY='" + tc.POLICY + "'", '# removed task declaration'))
                data['tools'].pop('normal_task_copper_fixed_policy')
                data['tools'].pop('normal_selected_proposal_import_policy')
                data.pop('protected_route_import')
                self.remove_flags(data)
                with self.assertRaises(p.Rejected):
                    check()

    def test_genuine_older_authored_source_keeps_existing_contract(self):
        root, data, _, _, check = self.make_import(selected=False)
        before = pc.inventory(root)
        self.assertEqual(check(), {})
        self.assertEqual(pc.inventory(root), before)

    def test_zero_protection_cannot_omit_qualified_import_census(self):
        root, data, _, _, _, _ = self.make()
        with self.assertRaisesRegex(p.Rejected, 'qualified Native import census'):
            tc.check_contract(root, data, None, declaration=tc.POLICY)

    def test_nested_parent_checks_child_pair_and_preserves_phase_annotation(self):
        for fault in (None, 'export_flag', 'import_flag', 'both_flags', 'export_cwd',
                      'export_candidate', 'export_output'):
            with self.subTest(fault=fault):
                root, data, _, _, _, contract = self.make(nested=True)
                exported, imported = data['steps'][:2]
                exported['phase'] = imported['phase'] = 'incumbent'
                if fault in {'export_flag', 'import_flag', 'both_flags'}:
                    actions = (('export', 'import') if fault == 'both_flags' else
                               ('export',) if fault == 'export_flag' else ('import',))
                    self.remove_flags(data, actions)
                elif fault == 'export_cwd':
                    exported['cwd'] = str(root)
                elif fault in {'export_candidate', 'export_output'}:
                    index = len(f.SANDBOX) + 3 + (fault == 'export_output')
                    exported['argv'][index] = str(root / 'wrong')
                if fault is None:
                    self.assertIsNone(contract())
                else:
                    with self.assertRaisesRegex(p.Rejected, 'paired exact'):
                        contract()

    def test_orphan_flagged_export_and_duplicate_pair_refuse(self):
        for duplicate in (False, True):
            with self.subTest(duplicate=duplicate):
                _, data, _, candidate, _, contract = self.make()
                extra = copy.deepcopy(data['steps'][0])
                extra['name'] = 'another-export'
                if not duplicate:
                    extra['argv'][-2] = str(candidate.parent.parent / 'other.dsn')
                data['steps'].append(extra)
                with self.assertRaisesRegex(p.Rejected, 'unpaired|paired exact'):
                    contract()


class TaskCopperParserControls(unittest.TestCase):
    setUp = parser_fixture.ExplicitParserContextControls.setUp

    def test_flag_presence_is_returned_without_changing_argv_or_legacy_normalization(self):
        for action, arguments in (('export', ['source', 'output']),
                                  ('export', ['source', 'output', 'classmap']),
                                  ('import', ['source', 'output', 'session'])):
            for fixed in (False, True):
                with self.subTest(action=action, arguments=arguments, fixed=fixed):
                    raw = [*f.SANDBOX, *p.native_prefix(), action, *arguments]
                    if fixed:
                        raw.append(tc.FLAG)
                    before = copy.deepcopy(raw)
                    normalized = [*p.native_prefix(), action, *arguments]
                    self.assertEqual(adapter.native_command_parser(
                        with_task_copper=True)(raw, action), (normalized, fixed))
                    self.assertEqual(adapter.native_command_parser()(raw, action), normalized)
                    self.assertEqual(raw, before)

    def test_malformed_flags_refuse_before_action_specific_census_filtering(self):
        prefix = p.native_prefix()
        tails = [
            ['export', 'source', 'output', tc.FLAG, tc.FLAG],
            ['export', tc.FLAG, 'source', 'output'],
            [tc.FLAG, 'export', 'source', 'output'],
            ['metrics', 'source', 'output', tc.FLAG],
            ['roundtrip', 'source', 'output', tc.FLAG],
            ['export', 'source', 'output', '--unknown'],
            ['export', 'source', 'output', '--unknown', tc.FLAG],
        ]
        for tail in tails:
            with self.subTest(tail=tail), self.assertRaises(p.Rejected):
                adapter.native_command_parser(data={'steps': [
                    {'argv': [*prefix, *tail]}]})
        with self.assertRaises(p.Rejected):
            adapter.native_command_parser(with_task_copper=1)

    def test_explicit_1007_refuses_task_flag_but_keeps_unflagged_prefix(self):
        raw = [*p.native_prefix(self.nt), 'import', 'source', 'output', 'session']
        parse = adapter.native_command_parser(self.nt, with_task_copper=True)
        normalized, fixed = parse(raw, 'import')
        self.assertFalse(fixed)
        self.assertEqual(normalized, [str(self.nt.python), str(p.c.ROOT / 'autorouter/native.py'),
                                      'import', 'source', 'output', 'session'])
        with self.assertRaisesRegex(p.Rejected, 'task copper'):
            parse([*raw, tc.FLAG], 'export')
        class FakeVersion:
            @staticmethod
            def GetBuildVersion():
                return '10.0.7'
        with self.assertRaisesRegex(ValueError, 'qualified Native10.0.0'):
            tc.invoke(None, self.root / 'never-opened', FakeVersion, lambda: None)


if __name__ == '__main__':
    unittest.main()
