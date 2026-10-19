"""Owned source-shaped alias controls; synthetic APIs prove no Native support."""
import ast
import copy
import json
from pathlib import Path
import re
import tempfile
from types import SimpleNamespace as NS
import unittest
from unittest.mock import Mock, patch

from autorouter import config as c, default_targets as d, layer_policy as lp
from autorouter import netclass as nc, netclass_native as n, pipeline as p, sexpr as sx
from autorouter.adapter import _parse_dsn, _dump_dsn
from tests.test_default_targets import SOURCE, fixtures, inputs


def identity(labels=('top_copper', 'bottom_copper')):
    return dict(schema=1, policy=n.SOURCE_ALL_LAYER_POLICY, copper_count=2,
        layers=[dict(id=code, canonical=name, standard_name=name, display_name=display,
                     index=i, type='signal', enabled=True,
                     canonical_lookup_id=code, display_lookup_id=code)
                for i, (code, name, display) in enumerate(zip((0, 2), ('F.Cu', 'B.Cu'), labels))])


def alias_fixture(labels=('top_copper', 'bottom_copper'), version='20241229'):
    raw, native, project, task = fixtures(fixed=True)
    sx.one(task, 'version')[1] = version
    table = sx.one(task, 'layers')
    for row, label in zip(table[1:], labels):
        row.append(json.dumps(label, ensure_ascii=False))
    # Source-shaped metadata retained in both exposed projects. This is an
    # owned construction, not a redistributed Sonde/NUS geometry payload.
    table.extend([['5', '"F.SilkS"', 'user', '"F.Silkscreen"'],
                  ['7', '"B.SilkS"', 'user', '"B.Silkscreen"']])
    task.append(['setup', ['stackup', *[['layer', json.dumps(name), ['type', '"copper"']]
                  for name in ('F.Cu', 'B.Cu')]]])
    tree = _parse_dsn(raw.decode())
    mapping = dict(zip(('F.Cu', 'B.Cu'), labels))
    def rename(node):
        for i, value in enumerate(node):
            if type(value) is list: rename(value)
            elif value in mapping:
                label = mapping[value]
                node[i] = label if re.fullmatch(r'[A-Za-z_][A-Za-z0-9_.-]*', label) else json.dumps(label, ensure_ascii=False)
    rename(tree)
    native[n.SOURCE_ALL_LAYER_KEY] = identity(labels)
    return _dump_dsn(tree).encode(), native, project, task


class SourceAllAliasControls(unittest.TestCase):
    def setUp(self):
        self.raw, self.native, self.project, self.task = alias_fixture()

    def args(self):
        return inputs(self.raw, self.native, self.project, self.task)

    def transform(self):
        return d.transform(*self.args(), source=SOURCE)

    def edit(self, callback):
        tree = _parse_dsn(self.raw.decode()); callback(tree)
        self.raw = _dump_dsn(tree).encode()

    def test_source_shaped_aliases_preserve_all_raw_names_geometry_and_protected_wiring(self):
        for labels in (('top_copper', 'bottom_copper'), ('upper_trace', 'lower_trace'),
                       ('Front copper', 'Back copper'), ('上面', '下面')):
            for version in ('20241229', '20260206'):
                with self.subTest(labels=labels, version=version):
                    self.raw, self.native, self.project, self.task = alias_fixture(labels, version)
                    before = copy.deepcopy((self.raw, self.native, self.project, self.task))
                    guided, record = self.transform()
                    self.assertEqual(before, (self.raw, self.native, self.project, self.task))
                    self.assertEqual(record['copper_layers'], list(labels))
                    self.assertEqual(record[n.SOURCE_ALL_LAYER_KEY], identity(labels))
                    old, new = (_parse_dsn(raw.decode()) for raw in (self.raw, guided))
                    self.assertEqual(sx.children(sx.one(old, 'structure'), 'layer'), sx.children(sx.one(new, 'structure'), 'layer'))
                    self.assertEqual(sx.one(old, 'wiring'), sx.one(new, 'wiring'))
                    self.assertEqual(sx.children(sx.one(old, 'library'), 'padstack'), sx.children(sx.one(new, 'library'), 'padstack')[:-1])
                    self.assertEqual(d.check(self.raw, guided, record, *self.args()[1:], source=SOURCE), record)

    def test_duplicate_colliding_or_malformed_display_names_refuse(self):
        original = copy.deepcopy(self.task)
        for alias in ('bottom_copper', 'BOTTOM_COPPER', 'B.Cu', 'f.cu', 'In1.Cu',
                      'F.SilkS', 'F.Silkscreen', 'signal', 'pcb', '', ' leading', 'trailing ',
                      'bad\nname', 'x' * 257, 'μ' * 129):
            self.task = copy.deepcopy(original)
            sx.one(self.task, 'layers')[1][3] = json.dumps(alias, ensure_ascii=False)
            with self.subTest(alias=alias), self.assertRaises(ValueError): self.transform()
        for atom in ('unquoted', '"unterminated', '"bad\\q"', ['display', '"upper"']):
            self.task = copy.deepcopy(original); sx.one(self.task, 'layers')[1][3] = atom
            with self.subTest(atom=atom), self.assertRaises(ValueError): self.transform()

    def test_source_physical_ids_types_order_stackup_and_hidden_copper_stay_closed(self):
        original = copy.deepcopy(self.task)
        for fault in ('wrong_id', 'duplicate_id', 'noncanonical_id', 'wrong_name',
                      'power', 'mixed', 'order', 'hidden', 'stackup', 'extra_atom', 'version'):
            self.task = copy.deepcopy(original); table = sx.one(self.task, 'layers')
            if fault == 'wrong_id': table[1][0] = '4'
            elif fault == 'duplicate_id': table[2][0] = '0'
            elif fault == 'noncanonical_id': table[1][0] = '00'
            elif fault == 'wrong_name': table[1][1] = '"Top"'
            elif fault in ('power', 'mixed'): table[1][2] = fault
            elif fault == 'order': table[1:3] = table[1:3][::-1]
            elif fault == 'hidden': table.append(['4', '"Hidden"', 'user'])
            elif fault == 'stackup': sx.one(sx.one(self.task, 'setup'), 'stackup')[1:3] = sx.one(sx.one(self.task, 'setup'), 'stackup')[1:3][::-1]
            elif fault == 'extra_atom': table[1].append('"extra"')
            else: sx.one(self.task, 'version')[1] = '20221018'
            with self.subTest(fault=fault), self.assertRaises(ValueError): self.transform()

    def test_nus_shaped_mixed_power_is_a_distinct_unqualified_type_not_an_alias(self):
        self.raw, self.native, self.project, self.task = fixtures()
        sx.one(self.task, 'version')[1] = '20241229'
        sx.one(self.task, 'layers')[1][2] = 'mixed'
        sx.one(self.task, 'layers')[2][2] = 'power'
        self.assertIsNone(n.observe_source_all_layers(object(), (sx.dump(self.task)+'\n').encode(), object()))
        with self.assertRaisesRegex(ValueError, 'type or alias'): self.transform()

    def test_dsn_label_order_index_type_count_and_duplicate_refuse(self):
        original = self.raw
        for fault in ('swap_names', 'swap_rows', 'index', 'type', 'missing', 'duplicate', 'canonical'):
            self.raw = original
            def change(tree):
                structure = sx.one(tree, 'structure'); rows = sx.children(structure, 'layer')
                if fault == 'swap_names': rows[0][1], rows[1][1] = rows[1][1], rows[0][1]
                elif fault == 'swap_rows':
                    first, second = structure.index(rows[0]), structure.index(rows[1])
                    structure[first], structure[second] = rows[1], rows[0]
                elif fault == 'index': sx.one(rows[1], 'property')[1][1] = '0'
                elif fault == 'type': sx.one(rows[0], 'type')[1] = 'power'
                elif fault == 'missing': structure.remove(rows[1])
                elif fault == 'duplicate': rows[1][1] = rows[0][1]
                else: rows[0][1] = 'F.Cu'
            self.edit(change)
            with self.subTest(fault=fault), self.assertRaises(ValueError): self.transform()

    def test_native_proof_deletion_schema_types_lookups_and_source_mismatch_refuse(self):
        original = copy.deepcopy(self.native)
        for fault in ('missing', 'schema_bool', 'unknown', 'count', 'policy', 'duplicate',
                      'id', 'standard', 'display', 'enabled', 'enabled_int', 'type', 'canonical_lookup',
                      'display_lookup', 'lookup_bool', 'index', 'four_marker'):
            self.native = copy.deepcopy(original); record = self.native[n.SOURCE_ALL_LAYER_KEY]
            row = record['layers'][0]
            if fault == 'missing': del self.native[n.SOURCE_ALL_LAYER_KEY]
            elif fault == 'schema_bool': record['schema'] = True
            elif fault == 'unknown': record['extra'] = False
            elif fault == 'count': record['copper_count'] = True
            elif fault == 'policy': record['policy'] = 'unqualified'
            elif fault == 'duplicate': record['layers'][1] = copy.deepcopy(row)
            elif fault == 'id': row['id'] = 2
            elif fault == 'standard': row['standard_name'] = 'Top'
            elif fault == 'display': row['display_name'] = 'different_display'
            elif fault == 'enabled': row['enabled'] = False
            elif fault == 'enabled_int': row['enabled'] = 1
            elif fault == 'type': row['type'] = 'mixed'
            elif fault == 'canonical_lookup': row['canonical_lookup_id'] = 2
            elif fault == 'display_lookup': row['display_lookup_id'] = 2
            elif fault == 'lookup_bool': row['display_lookup_id'] = False
            elif fault == 'index': row['index'] = 1
            else: self.native['copper_layers'] = []
            with self.subTest(fault=fault), self.assertRaises(ValueError): self.transform()

    def test_stale_source_hash_and_final_candidate_alias_change_or_proof_removal_refuse(self):
        raw, native, pro, board = self.args()
        stale = copy.deepcopy(native); stale['board_sha256'] = '0' * 64
        with self.assertRaises(ValueError): d.transform(raw, stale, pro, board, source=SOURCE)
        with tempfile.TemporaryDirectory() as tmp, patch.object(c, 'NATIVE_VERSION', '10.0.7'):
            candidate = Path(tmp).resolve() / 'board.kicad_pcb'
            candidate.write_bytes(board); candidate.with_suffix('.kicad_pro').write_bytes(pro)
            mapping = copy.deepcopy(native); mapping['source'] = str(candidate)
            protected = p.routes(self.task)
            self.assertTrue(p.audit_candidate_netclasses(candidate, protected, mapping, default_target_policy=True)['native']['passed'])
            missing = copy.deepcopy(mapping); del missing[n.SOURCE_ALL_LAYER_KEY]
            with self.assertRaisesRegex(ValueError, 'needs its Native'): p.audit_candidate_netclasses(candidate, protected, missing, default_target_policy=True)
            changed = copy.deepcopy(self.task); sx.one(changed, 'layers')[1][3] = '"changed_front"'
            sx.write(candidate, changed); mapping['board_sha256'] = p.sha(candidate)
            with self.assertRaisesRegex(ValueError, 'source/Native'): p.audit_candidate_netclasses(candidate, protected, mapping, default_target_policy=True)
            self.assertNotEqual(p.immutable(changed), p.immutable(self.task))
            # Exercise the real immutable fence before any Native normalization.
            # Unrelated preflight prerequisites are outside this synthetic unit.
            job = NS(out=Path(tmp)/'never-created', drc=Mock(side_effect=AssertionError('Native must not run')))
            with patch.object(p, 'check_schematic_class_support', return_value=None), \
                 patch.object(p, 'check_rule_area_support'), patch.object(p, 'check_hole_machining_support'):
                with self.assertRaisesRegex(p.Rejected, 'immutable geometry changed'):
                    p.validate_candidate(job, self.task, candidate, {}, protected, default_target_policy=True)
            job.drc.assert_not_called()

    def test_canonical_two_four_and_explicit_mask_contracts_are_unchanged(self):
        for four in (False, True):
            raw, native, project, task = fixtures(four=four)
            guided, record = d.transform(*inputs(raw, native, project, task), source=SOURCE)
            self.assertNotIn(n.SOURCE_ALL_LAYER_KEY, record)
            self.assertEqual(record['copper_layers'], list(nc.FOUR_COPPER_NAMES) if four else ['F.Cu', 'B.Cu'])
        for version in ('20241229', '20260206'):
            self.raw, self.native, self.project, self.task = alias_fixture(version=version)
            with self.assertRaises(ValueError):
                lp.bind(self.args()[3], self.raw, self.raw, ['F.Cu'], scope='whole_board_unlocked_routing', engine_profile='completion-only', guidance_policy='native')

    def test_proof_cannot_be_added_to_canonical_source_or_experimental_toolchain(self):
        raw, native, project, task = fixtures()
        native[n.SOURCE_ALL_LAYER_KEY] = identity(('F.Cu', 'B.Cu'))
        with self.assertRaisesRegex(ValueError, 'needs its Native'):
            d.transform(*inputs(raw, native, project, task), source=SOURCE)
        with patch.object(p, 'experimental_native_version', return_value='10.0.7'):
            with self.assertRaisesRegex(ValueError, 'requires Native7 two-copper'):
                nc.audit_native(self.native, self.project, native_toolchain=object())


class SourceAllScalarObservation(unittest.TestCase):
    def api(self, labels=('top_copper', 'bottom_copper')):
        displays = dict(zip((0, 2), labels)); codes = {'F.Cu': 0, 'B.Cu': 2, **dict(zip(labels, (0, 2)))}
        board = NS(GetLayerName=lambda code: displays[code], GetLayerID=lambda name: codes[name],
                   IsLayerEnabled=lambda code: True, GetLayerType=lambda code: 0, GetCopperLayerCount=lambda: 2)
        api = NS(F_Cu=0, B_Cu=2, LT_SIGNAL=0, LayerName=lambda code: {0: 'F.Cu', 2: 'B.Cu'}[code], GetBuildVersion=lambda: '10.0.7')
        return board, api

    def test_same_loaded_board_observation_and_legacy_no_alias_shape(self):
        raw, native, project, task = alias_fixture(); board, api = self.api()
        before = copy.deepcopy(task)
        self.assertEqual(n.observe_source_all_layers(board, (sx.dump(task)+'\n').encode(), api), identity())
        self.assertEqual(task, before)
        _, _, _, canonical = fixtures()
        self.assertIsNone(n.observe_source_all_layers(object(), (sx.dump(canonical)+'\n').encode(), object()))

    def test_unknown_disabled_alias_lookup_type_count_and_wrong_version_refuse(self):
        _, _, _, task = alias_fixture(); raw = (sx.dump(task)+'\n').encode()
        for fault in ('display', 'display_none', 'lookup', 'lookup_bool', 'disabled', 'enabled_int', 'type', 'type_bool', 'count', 'standard', 'version'):
            board, api = self.api()
            if fault == 'display': board.GetLayerName = lambda _: 'changed'
            elif fault == 'display_none': board.GetLayerName = lambda _: None
            elif fault == 'lookup': board.GetLayerID = lambda _: 2
            elif fault == 'lookup_bool': board.GetLayerID = lambda _: False
            elif fault == 'disabled': board.IsLayerEnabled = lambda _: False
            elif fault == 'enabled_int': board.IsLayerEnabled = lambda _: 1
            elif fault == 'type': board.GetLayerType = lambda _: 1
            elif fault == 'type_bool': board.GetLayerType = lambda _: False
            elif fault == 'count': board.GetCopperLayerCount = lambda: True
            elif fault == 'standard': api.LayerName = lambda _: 'alias'
            else: api.GetBuildVersion = lambda: '10.0.0'
            with self.subTest(fault=fault), self.assertRaises((ValueError, KeyError)):
                n.observe_source_all_layers(board, raw, api)

    def test_normal_worker_only_enables_observation_for_selected_native7(self):
        tree = ast.parse(Path(p.__file__).with_name('native.py').read_text())
        main = next(row for row in tree.body if isinstance(row, ast.FunctionDef) and row.name == 'main')
        calls = [row for row in ast.walk(main) if isinstance(row, ast.Call) and isinstance(row.func, ast.Name) and row.func.id == 'netclasses']
        self.assertEqual(len(calls), 2)
        for call in calls:
            selected = next(kw.value for kw in call.keywords if kw.arg == 'source_all_layers')
            self.assertEqual(ast.dump(selected), ast.dump(ast.parse("not experimental and c.NATIVE_VERSION=='10.0.7'", mode='eval').body))

    def test_new_scalar_helpers_are_in_existing_readback_module_identity(self):
        with p.validation_readback_session():
            state = p._readback_session.get()
            self.assertIn(n, state['modules'])
        # Closed class-map consumers still reject extra alias fields. Canonical
        # sources emit no such field, so their old exact headers remain valid.
        from tests import test_schematic_hierarchy as hierarchy_fixture
        case = hierarchy_fixture.HierarchyBindingControls(); case.setUp()
        args = hierarchy_fixture.f.arguments(case.case)
        source = json.loads(args['native_raw']); source[n.SOURCE_ALL_LAYER_KEY] = identity()
        args['native_raw'] = json.dumps(source).encode()
        with self.assertRaisesRegex(ValueError, 'native class map source/schema'): hierarchy_fixture.q.derive(**args)
        from tests import test_flat_class_parity as flat_fixture
        from autorouter import schematic_classes as flat
        case = flat_fixture.FlatClassParityControls(); case.setUp()
        native = copy.deepcopy(case.native); native[n.SOURCE_ALL_LAYER_KEY] = identity()
        with self.assertRaisesRegex(ValueError, 'map schema/source/hash'):
            flat.derive(flat_fixture.encoded(case.netlist), case.board_raw, case.project_raw,
                flat_fixture.json_bytes(native), source=case.source, schematic_source=case.sch_source,
                schematic_raw=flat_fixture.encoded(case.sch))


if __name__ == '__main__': unittest.main()
