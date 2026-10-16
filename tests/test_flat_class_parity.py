"""Pure class-parity regressions, not Native execution or routing evidence.

SPDX-License-Identifier: GPL-3.0-or-later

The small native-shaped positive below is constructed test data. The mismatch
test embeds the exact literal class witness from the retained runtime006 public
record; fresh actual positive Native observation remains the lead's experiment.
"""
import copy
import hashlib
import json
from pathlib import Path
import unittest

from autorouter import sexpr as sx
from experiments.flat_class_parity_v1 import compare as q
from experiments.schematic_class_intent_v1 import fixture


def encoded(tree):
    return (sx.dump(tree) + '\n').encode()


def json_bytes(value):
    return (json.dumps(value, sort_keys=True, indent=2) + '\n').encode()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


class FlatClassParityControls(unittest.TestCase):
    def setUp(self):
        files = fixture.files()
        self.board_raw = files[fixture.STEM + '.kicad_pcb']
        self.project_raw = files[fixture.STEM + '.kicad_pro']
        self.sch = sx.parse(files[fixture.STEM + '.kicad_sch'].decode())
        flag = sx.one(self.sch, 'netclass_flag')
        sx.one(flag, 'property')[2] = '"POWER"'
        self.source = '/owned/candidate/' + fixture.STEM + '.kicad_pcb'
        self.sch_source = '/owned/final-drc-input/' + fixture.STEM + '.kicad_sch'
        self.netlist = ['export', ['version', '"E"'],
            ['design', ['source', json.dumps(self.sch_source)],
                ['date', '"2026-10-16T09:41:30"'], ['tool', '"Eeschema 10.0.0"'],
                ['sheet', ['number', '"1"'], ['name', '"/"'], ['tstamps', '"/"']]],
            ['components'], ['groups'], ['variants'], ['libparts'], ['libraries'], ['nets']]
        comp_section = sx.one(self.netlist, 'components')
        for symbol in sx.children(self.sch, 'symbol'):
            ref = next(sx.unquote(p[2]) for p in sx.children(symbol, 'property')
                       if p[1] == '"Reference"')
            uid = sx.one(symbol, 'uuid')[1]
            comp_section.append(['comp', ['ref', json.dumps(ref)],
                ['tstamps', uid], ['sheetpath', ['names', '"/"'], ['tstamps', '"/"']],
                ['units', ['unit', ['name', '"A"'], ['pins', ['pin', ['num', '"1"']]]]]])
        nets = sx.one(self.netlist, 'nets')
        definitions = [('GND', 'SIGNAL,Default', ('J5', 'J6')),
                       ('KEEP', 'Default', ('J3', 'J4')),
                       ('ROUTE', 'POWER,Default', ('J1', 'J2'))]
        for code, (name, cls, refs) in enumerate(definitions, 1):
            nets.append(['net', ['code', json.dumps(str(code))], ['name', json.dumps(name)],
                ['class', json.dumps(cls)], *[['node', ['ref', json.dumps(ref)],
                    ['pin', '"1"'], ['pinfunction', '"1_1"'], ['pintype', '"passive"']]
                    for ref in refs]])
        project = json.loads(self.project_raw)
        classes = {c['name']: c for c in project['net_settings']['classes']}
        dimension_keys = [('width_nm', 'track_width'), ('clearance_nm', 'clearance'),
                          ('via_diameter_nm', 'via_diameter'), ('via_drill_nm', 'via_drill')]
        rows = []
        for name, identity, _ in definitions:
            cls = classes[{'GND': 'SIGNAL', 'KEEP': 'Default', 'ROUTE': 'POWER'}[name]]
            dimensions = {key: round(cls[pro] * 1000000) for key, pro in dimension_keys}
            rows.append({'name': name, 'netcode': {'GND': 3, 'KEEP': 2, 'ROUTE': 1}[name], 'copper_pad_count': 2,
                'class': identity, **dimensions,
                'parameter_parents': {key: {'name': cls['name'], 'value_nm': value,
                    'specified': True, 'priority': cls['priority']}
                    for key, value in dimensions.items()}})
        self.native = {'schema': 1, 'native_version': '10.0.0', 'units': 'integer nanometres',
            'resolution': 'BOARD.SynchronizeNetsAndNetClasses(False); NETINFO_ITEM.GetNetClassSlow()',
            'source': self.source, 'board_sha256': digest(self.board_raw),
            'project_sha256': digest(self.project_raw), 'board_saved': False, 'nets': rows,
            'copper_layers': [{'id': i, 'name': name, 'type': 'signal', 'index': index}
                for index, (i, name) in enumerate(zip((0, 4, 6, 2), ('F.Cu', 'In1.Cu', 'In2.Cu', 'B.Cu')))]}

    def derive(self, **overrides):
        values = dict(raw_netlist=encoded(self.netlist), board_raw=self.board_raw,
            project_raw=self.project_raw, native_raw=json_bytes(self.native),
            source=self.source, schematic_source=self.sch_source, schematic_raw=encoded(self.sch))
        values.update(overrides)
        return q.derive(**values)

    def net(self, name):
        return next(n for n in sx.children(sx.one(self.netlist, 'nets'), 'net')
                    if sx.one(n, 'name')[1] == json.dumps(name))

    def refuse(self, **overrides):
        with self.assertRaises(ValueError) as caught:
            self.derive(**overrides)
        return caught.exception

    def test_structurally_matching_positive_compares_all_partitions_without_acceptance(self):
        before = copy.deepcopy((self.netlist, self.sch, self.native, self.board_raw, self.project_raw))
        result = self.derive()
        self.assertTrue(result['class_parity_qualified'])
        self.assertEqual((result['components'], result['terminals'], result['nets']), (6, 6, 3))
        self.assertEqual([r['class'] for r in result['partitions']],
                         ['SIGNAL,Default', 'Default', 'POWER,Default'])
        self.assertEqual(result['class_flags'], ['POWER'])
        for key in ('accepted', 'routing_accepted', 'production_qualified',
                    'native_execution_performed_by_comparator'):
            self.assertIs(result[key], False)
        self.assertEqual(before, (self.netlist, self.sch, self.native, self.board_raw, self.project_raw))
        self.assertEqual(result['sha256']['native_map'], digest(json_bytes(self.native)))

    def test_recorded_runtime006_negative_class_witness_has_specific_mismatch(self):
        path = Path(__file__).resolve().parents[1]/'evidence/schematic-class-false-accept-runtime006-001.json'
        record = json.loads(path.read_bytes())
        witness = record['actual_final_route_and_export'][0]
        self.assertEqual(witness['schematic_class_ast'], ['class', '"CRITICAL,POWER,Default"'])
        self.assertEqual(witness['PCB_native']['class'], 'POWER,Default')
        sx.one(self.net('ROUTE'), 'class')[:] = witness['schematic_class_ast']
        sx.one(sx.one(self.sch, 'netclass_flag'), 'property')[2] = '"CRITICAL"'
        # These other two rows are constructed unit data. ROUTE's entire class
        # scalar row is the actual retained public observation, not a guess.
        self.native['nets'][2] = copy.deepcopy(witness['PCB_native'])
        with self.assertRaises(q.ClassIdentityMismatch) as caught:
            self.derive()
        error = caught.exception
        self.assertEqual(error.code, 'class_identity_mismatch')
        self.assertEqual(error.net, 'ROUTE')
        self.assertEqual(error.terminals, (('J1', '1'), ('J2', '1')))
        self.assertEqual(error.partition_count, 3)
        self.assertIs(error.schematic_identity_in_scope, False)
        self.assertEqual(error.schematic_class, 'CRITICAL,POWER,Default')
        self.assertEqual(error.pcb_class, 'POWER,Default')

    def test_same_names_and_counts_do_not_hide_changed_terminal_partition(self):
        # Swap two terminals between complete two-pin nets; labels, terminal
        # population, classes and per-net counts still match the original.
        a = sx.children(self.net('ROUTE'), 'node')[0]
        b = sx.children(self.net('KEEP'), 'node')[0]
        sx.one(a, 'ref')[1], sx.one(b, 'ref')[1] = sx.one(b, 'ref')[1], sx.one(a, 'ref')[1]
        error = self.refuse()
        self.assertNotIsInstance(error, q.ClassIdentityMismatch)
        self.assertIn('terminal partition differs', str(error))

    def test_missing_duplicate_changed_and_alias_native_terminals_refuse(self):
        original = copy.deepcopy(self.netlist)
        for kind in ('missing', 'duplicate', 'unknown', 'case_alias', 'zero_alias'):
            with self.subTest(kind=kind):
                self.netlist = copy.deepcopy(original)
                net = self.net('ROUTE'); node = sx.children(net, 'node')[0]
                if kind == 'missing': net.remove(node)
                elif kind == 'duplicate': net.append(copy.deepcopy(node))
                elif kind == 'unknown': sx.one(node, 'ref')[1] = '"J999"'
                elif kind == 'case_alias': sx.one(node, 'ref')[1] = '"j1"'
                else: sx.one(node, 'pin')[1] = '"01"'
                self.refuse()

    def test_board_pad_census_alias_and_uuid_failures_survive_rebinding_hash(self):
        original = sx.parse(self.board_raw.decode())
        for kind in ('missing', 'duplicate', 'unnumbered', 'zero_alias', 'netless',
                     'case_ref', 'shared_uuid', 'wrong_path'):
            with self.subTest(kind=kind):
                tree = copy.deepcopy(original); fps = sx.children(tree, 'footprint')
                fp = fps[0]; pad = sx.one(fp, 'pad')
                if kind == 'missing': fp.remove(pad)
                elif kind == 'duplicate': fp.append(copy.deepcopy(pad))
                elif kind == 'unnumbered': pad[1] = '""'
                elif kind == 'zero_alias': pad[1] = '"01"'
                elif kind == 'netless': pad.remove(sx.one(pad, 'net'))
                elif kind == 'case_ref':
                    next(p for p in sx.children(fp, 'property') if p[1] == '"Reference"')[2] = '"j1"'
                elif kind == 'shared_uuid': sx.one(sx.one(fps[1], 'pad'), 'uuid')[1] = sx.one(pad, 'uuid')[1]
                else: sx.one(fp, 'path')[1] = sx.one(fps[1], 'path')[1]
                raw = encoded(tree); native = copy.deepcopy(self.native); native['board_sha256'] = digest(raw)
                self.refuse(board_raw=raw, native_raw=json_bytes(native))

    def test_exact_class_identity_order_default_alias_and_unknown_fields_refuse(self):
        original = copy.deepcopy(self.netlist)
        for value in ('POWER', 'Default,POWER', 'POWER, Default', 'power,Default',
                      'POWER,Default,Default', 'CRITICAL,POWER,Default', 'POWER\\,Default'):
            with self.subTest(value=value):
                self.netlist = copy.deepcopy(original)
                sx.one(self.net('ROUTE'), 'class')[1] = json.dumps(value)
                with self.assertRaises(q.ClassIdentityMismatch): self.derive()
        self.netlist = copy.deepcopy(original)
        for kind in ('missing', 'duplicate', 'unknown'):
            with self.subTest(kind=kind):
                self.netlist = copy.deepcopy(original); net = self.net('ROUTE')
                if kind == 'missing': net.remove(sx.one(net, 'class'))
                elif kind == 'duplicate': net.append(copy.deepcopy(sx.one(net, 'class')))
                else: net.append(['class_parent', '"POWER"'])
                error = self.refuse(); self.assertNotIsInstance(error, q.ClassIdentityMismatch)

    def test_native_parent_priority_value_presence_and_specified_flags_are_mandatory(self):
        for field in q._DIMS:
            for kind in ('missing', 'wrong_name', 'value', 'unspecified', 'priority', 'bool_priority', 'extra'):
                with self.subTest(field=field, kind=kind):
                    native = copy.deepcopy(self.native); parents = native['nets'][2]['parameter_parents']
                    if kind == 'missing': del parents[field]
                    elif kind == 'wrong_name': parents[field]['name'] = 'Default'
                    elif kind == 'value': parents[field]['value_nm'] += 1
                    elif kind == 'unspecified': parents[field]['specified'] = False
                    elif kind == 'priority': parents[field]['priority'] += 1
                    elif kind == 'bool_priority': parents[field]['priority'] = True
                    else: parents[field]['unknown'] = True
                    error = self.refuse(native_raw=json_bytes(native))
                    self.assertNotIsInstance(error, q.ClassIdentityMismatch)

    def test_default_parent_is_checked_and_equal_dimensions_do_not_prove_identity(self):
        native = copy.deepcopy(self.native)
        native['nets'][1]['parameter_parents']['width_nm']['name'] = 'SIGNAL'
        self.refuse(native_raw=json_bytes(native))
        # Keep every scalar equal. Changing only the SCH class must still fail.
        sx.one(self.net('KEEP'), 'class')[1] = '"POWER,Default"'
        with self.assertRaises(q.ClassIdentityMismatch): self.derive()

    def test_missing_duplicate_extra_alias_and_unknown_native_rows_refuse(self):
        for kind in ('missing', 'duplicate', 'extra', 'alias', 'unknown_class', 'reordered_class', 'extra_field', 'zero_pads'):
            with self.subTest(kind=kind):
                native = copy.deepcopy(self.native)
                if kind == 'missing': native['nets'].pop()
                elif kind == 'duplicate': native['nets'].append(copy.deepcopy(native['nets'][0]))
                elif kind == 'extra':
                    row = copy.deepcopy(native['nets'][0]); row.update(name='EXTRA', netcode=9); native['nets'].append(row)
                elif kind == 'alias': native['nets'][2]['name'] = 'route'
                elif kind == 'unknown_class': native['nets'][2]['class'] = 'CRITICAL,POWER,Default'
                elif kind == 'reordered_class': native['nets'][2]['class'] = 'Default,POWER'
                elif kind == 'extra_field': native['nets'][2]['unknown'] = True
                else: native['nets'][2]['copper_pad_count'] = 0
                self.refuse(native_raw=json_bytes(native))

    def test_source_project_class_namespace_parameters_schema_and_tuning_refuse(self):
        for kind in ('comma_name', 'case_alias', 'unknown_field', 'tuning', 'missing_parent_value',
                     'bool_priority', 'assignments', 'new_settings', 'meta_version'):
            with self.subTest(kind=kind):
                project = json.loads(self.project_raw); settings = project['net_settings']; cls = settings['classes'][1]
                if kind == 'comma_name': cls['name'] = 'POWER,Default'
                elif kind == 'case_alias': settings['classes'][-1]['name'] = 'power'
                elif kind == 'unknown_field': cls['unknown'] = 0
                elif kind == 'tuning': cls['tuning_profile'] = 'critical timing'
                elif kind == 'missing_parent_value': del cls['via_drill']
                elif kind == 'bool_priority': cls['priority'] = True
                elif kind == 'assignments': settings['netclass_assignments'] = {'ROUTE': 'POWER'}
                elif kind == 'new_settings': settings['unknown'] = []
                else: settings['meta']['version'] = 6
                raw = json_bytes(project); native = copy.deepcopy(self.native); native['project_sha256'] = digest(raw)
                self.refuse(project_raw=raw, native_raw=json_bytes(native))

    def test_duplicate_json_keys_nonfinite_invalid_utf8_and_size_refuse(self):
        bad = (b'{"net_settings":{},"net_settings":{}}', b'{"x":NaN}', b'\xff',
               b'', b'x' * (q.MAX_BYTES + 1))
        for raw in bad:
            for key in ('project_raw', 'native_raw'):
                with self.subTest(key=key, raw_size=len(raw)):
                    self.refuse(**{key: raw})

    def test_unknown_export_schema_missing_components_and_hierarchy_refuse(self):
        original = copy.deepcopy(self.netlist)
        for kind in ('version', 'tool', 'extra_root', 'extra_net', 'missing_comp',
                     'duplicate_comp', 'missing_pin', 'duplicate_pin', 'unit', 'sheet'):
            with self.subTest(kind=kind):
                self.netlist = copy.deepcopy(original)
                design = sx.one(self.netlist, 'design'); comps = sx.one(self.netlist, 'components')
                if kind == 'version': sx.one(self.netlist, 'version')[1] = '"F"'
                elif kind == 'tool': sx.one(design, 'tool')[1] = '"Eeschema 10.0.7"'
                elif kind == 'extra_root': self.netlist.append(['unknown'])
                elif kind == 'extra_net': self.net('ROUTE').append(['unknown'])
                elif kind == 'missing_comp': comps.pop()
                elif kind == 'duplicate_comp': comps.append(copy.deepcopy(comps[1]))
                elif kind == 'sheet': design.append(copy.deepcopy(sx.one(design, 'sheet')))
                else:
                    unit = sx.one(comps[1], 'units')[1]; pins = sx.one(unit, 'pins')
                    if kind == 'missing_pin': pins.pop()
                    elif kind == 'duplicate_pin': pins.append(copy.deepcopy(pins[1]))
                    else: sx.one(unit, 'name')[1] = '"B"'
                self.refuse()
        self.netlist = original
        self.sch.append(['sheet', ['property', '"Sheetfile"', '"child.kicad_sch"']])
        self.assertIn('hierarchy remains unsupported', str(self.refuse()))

    def test_missing_changed_and_alias_source_symbol_pin_refuse(self):
        original = copy.deepcopy(self.sch)
        for kind in ('missing_pin', 'duplicate_pin', 'wrong_pin', 'shared_uuid', 'case_ref', 'unknown_flag'):
            with self.subTest(kind=kind):
                self.sch = copy.deepcopy(original); symbols = sx.children(self.sch, 'symbol'); symbol = symbols[0]
                if kind == 'missing_pin': symbol.remove(sx.one(symbol, 'pin'))
                elif kind == 'duplicate_pin': symbol.append(copy.deepcopy(sx.one(symbol, 'pin')))
                elif kind == 'wrong_pin': sx.one(symbol, 'pin')[1] = '"2"'
                elif kind == 'shared_uuid':
                    sx.one(sx.one(symbols[1], 'pin'), 'uuid')[1] = sx.one(sx.one(symbol, 'pin'), 'uuid')[1]
                elif kind == 'case_ref':
                    next(p for p in sx.children(symbol, 'property') if p[1] == '"Reference"')[2] = '"j1"'
                else: sx.one(sx.one(self.sch, 'netclass_flag'), 'property')[2] = '"Unknown"'
                self.refuse()

    def test_source_path_hash_version_and_native_schema_binding_refuse(self):
        for key, value in (('schema', True), ('schema', 2), ('native_version', '10.0.7'),
                           ('board_saved', True), ('source', self.source + '.other'),
                           ('board_sha256', '0' * 64), ('project_sha256', '0' * 64),
                           ('resolution', 'unverified'), ('unknown', False)):
            with self.subTest(key=key, value=value):
                native = copy.deepcopy(self.native); native[key] = value
                self.refuse(native_raw=json_bytes(native))
        for key, value in (('source', '/owned/../candidate/' + fixture.STEM + '.kicad_pcb'),
                           ('schematic_source', '/owned/other.kicad_sch'),
                           ('schematic_source', self.sch_source.replace('final-drc-input', 'wrong'))):
            with self.subTest(key=key, value=value): self.refuse(**{key: value})

    def test_four_copper_layer_identity_cannot_be_removed_or_changed(self):
        native = copy.deepcopy(self.native); del native['copper_layers']
        self.refuse(native_raw=json_bytes(native))
        native = copy.deepcopy(self.native); native['copper_layers'][1]['id'] = 1
        self.refuse(native_raw=json_bytes(native))


if __name__ == '__main__':
    unittest.main()
