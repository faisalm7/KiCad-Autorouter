"""Authored selected20241229/readback controls; not Native qualification."""
import copy
import json
import unittest
from unittest.mock import patch

from autorouter import config as c, default_targets as d, pipeline as p
from autorouter import routing_scope as rs, sexpr as sx
from tests import test_default_target_integration as integration
from tests import test_native7_selected_default as selected
from tests import test_selected_proposal_import as proposals
from tests import test_legacy_via_import as via_import


class Native7SelectedLegacyTests(unittest.TestCase):
    write = integration.DefaultTargetIntegrationTests.write
    check = integration.DefaultTargetIntegrationTests.check

    def setUp(self):
        integration.DefaultTargetIntegrationTests.setUp(self)
        tree = copy.deepcopy(self.original)
        sx.one(tree, 'version')[1] = '20241229'
        tree.extend([['net', '0', '""'], ['net', '1', '"DATA"'],
                     ['net', '2', '"RETURN"']])
        for index, fp in enumerate(sx.children(tree, 'footprint'), 1):
            pad_net = sx.one(sx.one(fp, 'pad'), 'net')
            pad_net[:] = ['net', str(index), pad_net[1]]
        self.refresh(tree)

    def refresh(self, tree):
        self.original = copy.deepcopy(tree)
        task = p.routing_task(self.original, 'selected_nets', ['DATA'])
        self.raw_task = (sx.dump(task) + '\n').encode()
        sx.write(self.snapshot, self.original)
        self.candidate.write_bytes(self.raw_task)
        self.native['board_sha256'] = p.sha(self.candidate)
        self.write('export-netclasses.json', self.native)
        guided, self.record = d.transform(self.original_raw, self.native,
            self.candidate.with_suffix('.kicad_pro').read_bytes(), self.raw_task,
            source=str(self.candidate))
        (self.root/'default-targets.dsn').write_bytes(guided)
        self.write('default-targets.json', self.record)
        self.data.update(task_sha256=p.sha(self.candidate),
            default_target_transport=dict(policy=d.POLICY, file='default-targets.json',
                                          sha256=p.sha(self.root/'default-targets.json')))
        selected.Native7SelectedDefaultTests.selected(self)

    def guard(self, tree=None):
        if tree is not None:
            sx.write(self.snapshot, tree)
        return p.check_native7_selected_source(self.snapshot, ['DATA'])

    def producer(self, text, *, rehash=True):
        self.code.write_text(text)
        if rehash:
            self.data['tools']['implementation_sha256']['autorouter/pipeline.py'] = p.sha(self.code)

    def test_legacy_source_and_transport_are_rederived_without_source_normalization(self):
        before = {path: path.read_bytes() for path in
                  (self.snapshot, self.candidate, self.snapshot.with_suffix('.kicad_pro'))}
        self.assertIsNone(self.guard())
        self.assertEqual(self.check(), self.record)
        self.assertEqual(rs._net_mapping(self.original)[0], 'legacy_table')
        self.assertEqual(sx.one(sx.one(sx.children(self.original, 'footprint')[0], 'pad'), 'net'),
                         ['net', '1', '"DATA"'])
        self.assertEqual({path: path.read_bytes() for path in before}, before)
        self.assertFalse(self.record['routing_accepted'])
        self.assertFalse(self.record['native_execution_proven'])

    def test_partition_keeps_all_pins_classes_and_rules_with_legacy_identity(self):
        raw = (self.root/'default-targets.dsn').read_bytes()
        emitted, binding = rs.partition_dsn(raw, ['DATA'])
        self.assertEqual(emitted, (self.root/'task.dsn').read_bytes())
        self.assertEqual(binding, self.data['selected_dsn_binding'])
        self.assertTrue(binding['all_nets_and_pins_retained'])
        self.assertTrue(binding['class_rules_copied_exactly'])
        self.assertFalse(binding['native_classes_changed'])
        self.assertEqual(self.record['derived_nm'], dict(width_nm=300000, clearance_nm=300000,
            via_diameter_nm=1500000, via_drill_nm=300000))

    def test_selected_task_and_import_preserve_exact_nonselected_copper_and_geometry(self):
        tree = copy.deepcopy(self.original)
        unlocked = proposals.segment('legacy-data', '1')
        protected = proposals.segment('legacy-return', '2', end='2.0005')
        protected.append(['locked', 'yes'])
        tree.extend([unlocked, protected])
        self.assertIsNone(self.guard(tree))
        task = p.routing_task(tree, 'selected_nets', ['DATA'])
        self.assertEqual(p.routes(task), [protected])
        self.assertEqual(p.immutable(task), p.immutable(tree))
        imported = copy.deepcopy(task)
        sx.one(p.routes(imported)[0], 'end')[1] = '2'
        imported.append(proposals.segment('legacy-new-data', '1', end='4'))
        audit = {}
        result = p.transplant_routes(tree, imported, protected=[protected], audit=audit,
            policy=p.SELECTED_PROPOSAL_IMPORT_POLICY, selected_names=['DATA'])
        self.assertEqual(p.routes(result)[0], protected)
        self.assertEqual(p.immutable(result), p.immutable(tree))
        self.assertTrue(rs.audit(tree, result, ['DATA'])['scope_passed'])
        self.assertEqual(audit['ignored_nonselected_proposals'][0]['net_name'], 'RETURN')
        self.assertEqual(sx.one(p.routes(result)[1], 'net'), ['net', '1'])

    def test_mixed_malformed_and_unknown_legacy_identities_refuse(self):
        for mode in ('no_table', 'duplicate_code', 'duplicate_name', 'empty_nonzero',
                     'named_zero', 'noncanonical_code', 'pad_alias', 'modern_pad',
                     'unknown_pad', 'modern_route', 'unknown_route', 'conflicting_zone',
                     'zone_name_alias', 'modern_zone', 'unknown_zone', 'undeclared_zero'):
            tree = copy.deepcopy(self.original)
            table = sx.children(tree, 'net')
            pad_net = sx.one(sx.one(sx.children(tree, 'footprint')[0], 'pad'), 'net')
            if mode == 'no_table':
                tree[:] = [row for row in tree if row not in table]
                for fp in sx.children(tree, 'footprint'):
                    row = sx.one(sx.one(fp, 'pad'), 'net'); row[:] = ['net', row[2]]
            elif mode == 'duplicate_code': tree.append(['net', '1', '"OTHER"'])
            elif mode == 'duplicate_name': tree.append(['net', '3', '"DATA"'])
            elif mode == 'empty_nonzero': table[1][2] = '""'
            elif mode == 'named_zero': table[0][2] = '"OTHER"'
            elif mode == 'noncanonical_code': table[1][1] = '01'
            elif mode == 'pad_alias': pad_net[2] = '"RETURN"'
            elif mode == 'modern_pad': pad_net[:] = ['net', '"DATA"']
            elif mode == 'unknown_pad': pad_net[1] = '3'
            elif mode == 'modern_route': tree.append(proposals.segment('mixed', '"DATA"'))
            elif mode == 'unknown_route': tree.append(proposals.segment('unknown', '3'))
            elif mode == 'conflicting_zone': tree.append(['zone', ['net', '1', '"RETURN"']])
            elif mode == 'zone_name_alias': tree.append(['zone', ['net', '1'], ['net_name', '"RETURN"']])
            elif mode == 'modern_zone': tree.append(['zone', ['net', '"DATA"']])
            elif mode == 'unknown_zone': tree.append(['zone', ['net', '3']])
            else:
                tree.remove(table[0]); tree.append(proposals.segment('undeclared-zero', '0'))
            with self.subTest(mode=mode), self.assertRaises(p.Rejected): self.guard(tree)

    def test_declared_zero_is_protected_and_consistent_zone_names_are_retained(self):
        tree = copy.deepcopy(self.original)
        tree.append(proposals.segment('unconnected', '0'))
        zone = ['zone', ['net', '1'], ['net_name', '"DATA"']]
        tree.append(zone)
        self.assertIsNone(self.guard(tree))
        task = rs.task(tree, ['DATA'])
        self.assertEqual(p.routes(task), p.routes(tree))
        self.assertEqual(sx.one(task, 'zone'), zone)
        self.assertEqual(rs.protected_routes(tree, ['DATA']), p.routes(tree))

    def test_import_code_permutation_uses_names_and_restores_omitted_mode_via(self):
        tree = copy.deepcopy(self.original)
        via = copy.deepcopy(p.routes(via_import.board())[0])
        sx.one(via, 'net')[1] = '2'
        tree.append(via)
        self.assertIsNone(self.guard(tree))
        imported = copy.deepcopy(tree)
        table = sx.children(imported, 'net')
        for row in table:
            if row[1] == '1': row[1] = '22'
            elif row[1] == '2': row[1] = '11'
        for fp in sx.children(imported, 'footprint'):
            row = sx.one(sx.one(fp, 'pad'), 'net'); row[1] = '22' if row[2] == '"DATA"' else '11'
        sx.one(p.routes(imported)[0], 'net')[1] = '11'
        p.routes(imported)[0].extend(copy.deepcopy(via_import.FEATURES))
        imported.append(proposals.segment('permuted-data', '22'))
        result = p.transplant_routes(tree, imported, protected=[via],
            policy=p.SELECTED_PROPOSAL_IMPORT_POLICY, selected_names=['DATA'])
        self.assertEqual(p.routes(result)[0], via)
        self.assertTrue(p.legacy_via_omitted(p.routes(result)[0]))
        self.assertEqual(sx.one(p.routes(result)[1], 'net'), ['net', '1'])
        self.assertEqual(p.immutable(result), p.immutable(tree))

    def test_legacy_transport_does_not_waive_class_or_floor_observations(self):
        for mode in ('width', 'floor', 'class'):
            wrong = copy.deepcopy(self.native)
            if mode == 'width': wrong['nets'][0]['width_nm'] += 1000
            elif mode == 'floor': wrong['effective_floors_nm']['min_clearance'] += 1000
            else: wrong['nets'][0]['class'] = 'OTHER'
            self.write('export-netclasses.json', wrong)
            with self.subTest(mode=mode), self.assertRaises((p.Rejected, ValueError)): self.check()

    def test_unknown_formats_native_versions_and_duplicate_versions_refuse(self):
        for version in ('20241228', '20241230', '20260101', '20260207'):
            tree = copy.deepcopy(self.original); sx.one(tree, 'version')[1] = version
            with self.subTest(version=version), self.assertRaises(p.Rejected): self.guard(tree)
        tree = copy.deepcopy(self.original); tree.append(['version', '20241229'])
        with self.assertRaises(p.Rejected): self.guard(tree)
        tree = copy.deepcopy(self.original); tree[0] = 'other'
        with self.assertRaises(p.Rejected): self.guard(tree)
        for version in ('10.0.0', '10.0.8'):
            with self.subTest(native=version), patch.object(c, 'NATIVE_VERSION', version):
                with self.assertRaises(p.Rejected): self.guard(self.original)

    def test_existing_Default_layer_selected_lock_and_schematic_fences_remain(self):
        raw_pro = self.snapshot.with_suffix('.kicad_pro').read_bytes()
        sch = self.snapshot.with_suffix('.kicad_sch')
        raw_sch = sch.read_bytes()
        for mode in ('nondefault', 'patterns', 'assignments', 'four_copper', 'selected_lock', 'missing_SCH'):
            tree = copy.deepcopy(self.original); project = json.loads(raw_pro)
            self.snapshot.with_suffix('.kicad_pro').write_bytes(raw_pro); sch.write_bytes(raw_sch)
            if mode == 'nondefault': project['net_settings']['classes'].append({'name': 'OTHER'})
            elif mode == 'patterns': project['net_settings']['netclass_patterns'] = [{'pattern': '*', 'netclass': 'Default'}]
            elif mode == 'assignments': project['net_settings']['netclass_assignments'] = {'DATA': 'Default'}
            elif mode == 'four_copper': sx.one(tree, 'layers').insert(2, ['4', '"In1.Cu"', 'signal'])
            elif mode == 'selected_lock':
                route = proposals.segment('locked-data', '1'); route.append(['locked', 'yes']); tree.append(route)
            else: sch.unlink()
            self.snapshot.with_suffix('.kicad_pro').write_text(json.dumps(project))
            with self.subTest(mode=mode), self.assertRaises(p.Rejected): self.guard(tree)

    def test_legacy_capability_cannot_be_removed_rehashed_or_dynamically_declared(self):
        self.assertEqual(self.check(), self.record)
        before = self.code.read_text()
        literal = "NATIVE7_SELECTED_LEGACY_POLICY='native7-selected-legacy-table-v1'"
        self.assertIn(literal, before)
        for mode in ('missing', 'unknown', 'nested', 'dynamic', 'duplicate', 'old_Default_only',
                     'unhashed_change', 'missing_transport_deleted'):
            if mode == 'unknown': replacement = "NATIVE7_SELECTED_LEGACY_POLICY='unknown'"
            elif mode == 'nested': replacement = 'if True:\n    ' + literal
            elif mode == 'dynamic': replacement = "NATIVE7_SELECTED_LEGACY_POLICY=str('native7-selected-legacy-table-v1')"
            elif mode == 'duplicate': replacement = literal + '\n' + literal
            else: replacement = '# no legacy population capability'
            code = before.replace(literal, replacement)
            if mode == 'old_Default_only':
                code = "DEFAULT_TARGET_ADMISSION_POLICY='single-default-global-floor-targets-v2'\n" + \
                       "NATIVE7_SELECTED_DEFAULT_POLICY='native7-selected-sole-default-v1'\n"
            self.producer(code, rehash=mode != 'unhashed_change')
            if mode == 'missing_transport_deleted':
                self.data.pop('default_target_transport')
                (self.root/'default-targets.json').unlink(); (self.root/'default-targets.dsn').unlink()
            with self.subTest(mode=mode), self.assertRaises(p.Rejected): self.check()

    def test_legacy_capability_requirement_uses_actual_snapshot_not_supplied_original(self):
        before = self.code.read_text()
        self.producer(before.replace("NATIVE7_SELECTED_LEGACY_POLICY='native7-selected-legacy-table-v1'", '# old producer'))
        supplied = copy.deepcopy(self.original); sx.one(supplied, 'version')[1] = '20260206'
        with self.assertRaisesRegex(p.Rejected, 'captured legacy producer capability'):
            p.check_default_target_transport(self.root, self.data, supplied, self.candidate)

    def test_old_modern_selected_producer_remains_readable_without_legacy_capability(self):
        modern = copy.deepcopy(self.original)
        sx.one(modern, 'version')[1] = '20260206'
        modern[:] = [row for row in modern if row not in sx.children(modern, 'net')]
        for fp in sx.children(modern, 'footprint'):
            row = sx.one(sx.one(fp, 'pad'), 'net'); row[:] = ['net', row[2]]
        self.refresh(modern)
        self.producer(self.code.read_text().replace(
            "NATIVE7_SELECTED_LEGACY_POLICY='native7-selected-legacy-table-v1'", '# old modern producer'))
        self.assertIsNone(self.guard())
        self.assertEqual(self.check(), self.record)


if __name__ == '__main__': unittest.main()
