"""Owned constructed transport controls; no Native execution or routing claim."""
import copy
import hashlib
import json
import unittest
from unittest.mock import patch

from autorouter import default_targets as m, netclass as nc, sexpr as sx
from autorouter.adapter import _parse_dsn, _dump_dsn


SOURCE = '/owned/project/board.kicad_pcb'


def fixtures(four=False, fixed=False):
    names = list(nc.FOUR_COPPER_NAMES) if four else ['F.Cu', 'B.Cu']
    ids = list(nc.FOUR_COPPER_IDS) if four else [0, 2]
    cls = {'name': 'Default', 'track_width': .2, 'clearance': .2,
           'via_diameter': .6, 'via_drill': .3}
    project = {'net_settings': {'classes': [cls], 'netclass_patterns': [], 'netclass_assignments': {}},
               'board': {'design_settings': {'rules': {'min_track_width': .3,
                         'min_clearance': .3, 'min_via_diameter': 1.5,
                         'min_through_hole_diameter': .3, 'min_via_annular_width': .3}}}}
    task = ['kicad_pcb', ['version', '20260206'],
            ['layers', *[[str(i), '"' + name + '"', 'signal'] for i, name in zip(ids, names)]]]
    for i, net in enumerate(('DATA', 'RETURN'), 1):
        task.append(['footprint', '"Owned"', ['property', '"Reference"', '"J' + str(i) + '"'],
                     ['pad', '"1"', 'thru_hole', 'circle', ['net', '"' + net + '"']]])
    via = 'Via[0-' + str(len(names) - 1) + ']_600:300_um'
    layers = ' '.join('(layer ' + name + ' (type signal) (property (index ' + str(i) + ')))'
                      for i, name in enumerate(names))
    shapes = ' '.join('(shape (circle ' + name + ' 600))' for name in names)
    wiring = ''
    if fixed:
        wiring = '(wire (path F.Cu 300 0 0 1000 0) (net DATA) (type fix)) ' + \
                 '(via "' + via + '" 1000 0 (net DATA) (type fix))'
        task.append(['via', ['at', '1', '0'], ['size', '.6'], ['drill', '.3'],
                     ['layers', '"F.Cu"', '"B.Cu"'], ['net', '"DATA"'], ['locked', 'yes']])
    raw = f'''(pcb "owned"
      (parser (string_quote ") (host_cad "KiCad's Pcbnew") (host_version "10.0.7"))
      (unit um) (resolution um 10)
      (structure {layers} (boundary (path pcb 0 0 0 10000 0 10000 10000 0 0))
        (keepout "owned" (polygon F.Cu 0 2000 2000 3000 2000 3000 3000))
        (plane DATA (polygon B.Cu 0 4000 4000 5000 4000 5000 5000))
        (via "{via}") (rule (width 200) (clearance 200) (clearance 50 (type smd_smd))))
      (placement (component Owned (place J1 0 0 front 0 (PN Owned)) (place J2 1000 0 front 0 (PN Owned))))
      (library (image Owned (pin Pad 1 0 0))
        (padstack Pad (shape (circle F.Cu 1000)) (attach off))
        (padstack "{via}" {shapes} (attach off)))
      (network (net DATA (pins J1-1)) (net RETURN (pins J2-1))
        (class kicad_default DATA RETURN (circuit (use_via "{via}")) (rule (width 200) (clearance 200))))
      (wiring {wiring}))'''.encode()
    native = {'schema': 1, 'native_version': '10.0.7', 'units': 'integer nanometres',
              'source': SOURCE, 'board_saved': False, 'nets': [],
              'effective_floors_nm': {key: m.floors.millimetres(value, zero=True)
                  for key,value in project['board']['design_settings']['rules'].items()}}
    for i, net in enumerate(('DATA', 'RETURN'), 1):
        row = {'name': net, 'netcode': i, 'class': 'Default', 'copper_pad_count': 1,
               'width_nm': 200000, 'clearance_nm': 200000,
               'via_diameter_nm': 600000, 'via_drill_nm': 300000}
        row['parameter_parents'] = {key: {'name': 'Default', 'value_nm': row[key],
                                        'specified': True, 'priority': 2147483647}
                                    for key in m.floors.DIMENSIONS}
        native['nets'].append(row)
    if four:
        native['copper_layers'] = [{'id': i, 'name': name, 'type': 'signal', 'index': index}
                                  for index, (i, name) in enumerate(zip(ids, names))]
    return raw, native, project, task


def inputs(raw, native, project, task):
    pro = json.dumps(project).encode()
    board = (sx.dump(task) + '\n').encode()
    native = copy.deepcopy(native)
    native.update(project_sha256=hashlib.sha256(pro).hexdigest(), board_sha256=hashlib.sha256(board).hexdigest())
    return raw, native, pro, board


class DefaultTargetsTests(unittest.TestCase):
    def setUp(self):
        self.raw, self.native, self.project, self.task = fixtures()

    def args(self):
        return inputs(self.raw, self.native, self.project, self.task)

    def transform(self):
        return m.transform(*self.args(), source=SOURCE)

    def reject(self):
        with self.assertRaises((ValueError, KeyError)):
            self.transform()

    def edit(self, callback):
        tree = _parse_dsn(self.raw.decode()); callback(tree)
        self.raw = _dump_dsn(tree).encode()

    def test_below_floor_targets_preserve_every_other_value_and_raw_inputs(self):
        before = copy.deepcopy((self.raw, self.native, self.project, self.task))
        guided, receipt = self.transform()
        self.assertEqual(receipt['derived_nm'], {'width_nm': 300000, 'clearance_nm': 300000,
                         'via_diameter_nm': 1500000, 'via_drill_nm': 300000})
        self.assertEqual(before, (self.raw, self.native, self.project, self.task))
        old = _parse_dsn(self.raw.decode()); new = _parse_dsn(guided.decode())
        # Normalize exactly the expected routing target nodes back to the raw
        # values, then compare the complete trees, including protected objects.
        old_structure, new_structure = sx.one(old, 'structure'), sx.one(new, 'structure')
        new_structure[new_structure.index(sx.one(new_structure, 'rule'))] = copy.deepcopy(sx.one(old_structure, 'rule'))
        sx.one(new_structure, 'via')[:] = copy.deepcopy(sx.one(old_structure, 'via'))
        old_class = sx.children(sx.one(old, 'network'), 'class')[0]
        new_class = sx.children(sx.one(new, 'network'), 'class')[0]
        new_class[new_class.index(sx.one(new_class, 'rule'))] = copy.deepcopy(sx.one(old_class, 'rule'))
        sx.one(new_class, 'circuit')[:] = copy.deepcopy(sx.one(old_class, 'circuit'))
        library = sx.one(new, 'library')
        library.remove(sx.children(library, 'padstack')[-1])
        self.assertEqual(new, old)
        self.assertFalse(receipt['native_execution_proven'])
        self.assertFalse(receipt['routing_accepted'])
        self.assertTrue(receipt['raw_mapping_audit']['raw_default_for_target_derivation_only'])
        self.assertTrue(receipt['original_via_stack_preserved'])
        self.assertTrue(receipt['derived_via_stack_added'])
        self.assertEqual(m.check(self.raw, guided, receipt, self.args()[1], self.args()[2], self.args()[3], source=SOURCE), receipt)

    def test_four_copper_targets(self):
        self.raw, self.native, self.project, self.task = fixtures(four=True)
        guided, rec = self.transform()
        self.assertEqual(rec['copper_layers'], list(nc.FOUR_COPPER_NAMES))
        tree = _parse_dsn(guided.decode())
        stack = sx.children(sx.one(tree, 'library'), 'padstack')[-1]
        self.assertEqual([sx.one(shape, 'circle') for shape in sx.children(stack, 'shape')],
                         [['circle', name, '1500'] for name in nc.FOUR_COPPER_NAMES])

    def test_protected_wiring_and_original_via_stack_survive_changed_target(self):
        for four in (False, True):
            with self.subTest(four=four):
                self.raw, self.native, self.project, self.task = fixtures(four, fixed=True)
                guided, receipt = self.transform()
                old = _parse_dsn(self.raw.decode()); new = _parse_dsn(guided.decode())
                self.assertEqual(sx.one(old, 'wiring'), sx.one(new, 'wiring'))
                self.assertEqual(sx.children(sx.one(old, 'library'), 'padstack'),
                                 sx.children(sx.one(new, 'library'), 'padstack')[:-1])
                self.assertTrue(receipt['protected_via_stack_preserved'])

    def test_image_pin_referencing_original_via_stack_keeps_its_definition(self):
        self.edit(lambda tree: sx.children(sx.children(sx.one(tree, 'library'), 'image')[0], 'pin')[0].__setitem__(1, '"Via[0-1]_600:300_um"'))
        guided, receipt = self.transform()
        self.assertEqual(m.check(self.raw, guided, receipt, *self.args()[1:], source=SOURCE), receipt)
        old = _parse_dsn(self.raw.decode()); new = _parse_dsn(guided.decode())
        declared = {sx.unquote(stack[1]) for stack in sx.children(sx.one(new, 'library'), 'padstack')}
        for image in sx.children(sx.one(new, 'library'), 'image'):
            for pin in sx.children(image, 'pin'):
                self.assertIn(sx.unquote(pin[1]), declared)
        self.assertEqual(sx.one(old, 'wiring'), sx.one(new, 'wiring'))
        self.assertEqual(sx.children(sx.one(old, 'library'), 'image'), sx.children(sx.one(new, 'library'), 'image'))
        self.assertEqual(sx.children(sx.one(old, 'library'), 'padstack'), sx.children(sx.one(new, 'library'), 'padstack')[:-1])

    def test_stronger_defaults_are_retained_but_typed_clearance_is_fixed(self):
        self.project['board']['design_settings']['rules'] = dict.fromkeys(m.floors.FLOORS, 0)
        self.native['effective_floors_nm'] = dict.fromkeys(m.floors.FLOORS, 0)
        guided, rec = self.transform()
        self.assertEqual(rec['raw_nm'], rec['derived_nm'])
        rules = sx.one(sx.one(_parse_dsn(guided.decode()), 'structure'), 'rule')
        self.assertEqual(rules[-1], ['clearance', '200', ['type', 'smd_smd']])
        self.assertEqual(len(sx.children(sx.one(_parse_dsn(guided.decode()), 'library'), 'padstack')), 2)

    def test_annular_floor_can_drive_via_diameter(self):
        self.project['board']['design_settings']['rules'].update(min_via_diameter=.5, min_via_annular_width=.4)
        self.native['effective_floors_nm'].update(min_via_diameter=500000,min_via_annular_width=400000)
        self.assertEqual(self.transform()[1]['derived_nm']['via_diameter_nm'], 1100000)

    def test_legacy_two_copper_task(self):
        sx.one(self.task, 'version')[1] = '20241229'
        self.assertEqual(self.transform()[1]['copper_layers'], ['F.Cu', 'B.Cu'])

    def test_foreign_hidden_or_reordered_source_layer_is_refused(self):
        original = copy.deepcopy(self.task)
        for row in (['31', '"B.Cu"', 'signal'], ['5', '"hidden"', 'signal'],
                    ['2', '"B.Cu"', 'power']):
            with self.subTest(row=row):
                self.task = copy.deepcopy(original)
                if row[1] == '"hidden"': sx.one(self.task, 'layers').append(row)
                else: sx.one(self.task, 'layers')[2] = row
                self.reject()

    def test_strict_existing_audits_still_refuse_below_floor(self):
        _, native, pro, _ = self.args()
        # Hold only the pure version selector fixed, so this control reaches
        # the existing below-floor rejection rather than a version mismatch.
        with patch('autorouter.pipeline.experimental_native_version', return_value='10.0.7'):
            with self.assertRaisesRegex(ValueError, 'below original board floor'):
                nc.audit_native(native, json.loads(pro))
            with self.assertRaisesRegex(ValueError, 'below original board floor'):
                nc.audit_mapping(_parse_dsn(self.raw.decode()), native, json.loads(pro))
        with self.assertRaises(ValueError): nc.audit_native(native, self.project, derive_default_targets=1)
        self.project['net_settings']['classes'].append(dict(self.project['net_settings']['classes'][0], name='Other'))
        self.reject()

    def test_source_map_and_byte_bindings_refuse(self):
        args = list(self.args())
        for key, value in [('source', '/other/board.kicad_pcb'), ('board_saved', True),
                           ('board_sha256', '0' * 64), ('project_sha256', '0' * 64),
                           ('native_version', '10.0.0'), ('schema', True), ('units', 'mm')]:
            with self.subTest(key=key):
                wrong = copy.deepcopy(args); wrong[1][key] = value
                with self.assertRaises(ValueError): m.transform(*wrong, source=SOURCE)
        for source in ('relative.kicad_pcb', '/a/../board.kicad_pcb', '/a/board.txt'):
            with self.assertRaises(ValueError): m.transform(*args, source=source)
        for i in (0, 2, 3):
            wrong = list(args); wrong[i] = bytearray(wrong[i])
            with self.assertRaises(ValueError): m.transform(*wrong, source=SOURCE)

    def test_parent_scalar_priority_and_source_class_refusals(self):
        original = copy.deepcopy(self.native)
        for key, value in [('name', 'Other'), ('value_nm', 200001), ('specified', False), ('priority', True), ('priority', 1)]:
            with self.subTest(key=key, value=value):
                self.native = copy.deepcopy(original)
                self.native['nets'][0]['parameter_parents']['width_nm'][key] = value
                self.reject()
        self.native = copy.deepcopy(original)
        for parent in self.native['nets'][1]['parameter_parents'].values():
            parent['priority'] = 1
        self.reject()
        self.native = copy.deepcopy(original)
        self.project['net_settings']['classes'][0]['priority'] = 1; self.reject()
        self.project['net_settings']['classes'][0]['priority'] = 2147483647
        self.transform()

    def test_sole_Default_omitted_priority_accepts_unanimous_native_constructor_sentinel(self):
        for row in self.native['nets']:
            for parent in row['parameter_parents'].values(): parent['priority'] = -1
        self.assertEqual(self.transform()[1]['derived_nm']['width_nm'],300000)
        for priority in (-1,True,-2):
            self.project['net_settings']['classes'][0]['priority'] = priority
            with self.subTest(explicit_priority=priority):self.reject()
        del self.project['net_settings']['classes'][0]['priority']
        self.native['nets'][0]['parameter_parents']['width_nm']['priority'] = -2
        self.reject()

    def test_numeric_source_floors_and_grid_refusals(self):
        for value in (True, -.1, float('nan'), float('inf'), '0.3', .3001):
            with self.subTest(value=value):
                self.project['board']['design_settings']['rules']['min_track_width'] = value
                self.reject()

    def test_assignments_custom_rules_and_exclusions_refuse(self):
        original = copy.deepcopy(self.project)
        for location, key, value in [('net_settings', 'netclass_assignments', {'DATA': ['Default']}),
                                     ('net_settings', 'netclass_patterns', [{'pattern': '*', 'netclass': 'Default'}]),
                                     ('settings', 'custom_rules', ['unknown']),
                                     ('settings', 'drc_exclusions', ['excluded'])]:
            with self.subTest(key=key):
                self.project = copy.deepcopy(original)
                target = self.project['board']['design_settings'] if location == 'settings' else self.project[location]
                target[key] = value
                self.reject()

    def test_source_dimension_API_matches_transform_and_is_detached(self):
        project_raw = self.args()[2]
        result = m.source_dimensions(project_raw)
        receipt = self.transform()[1]
        self.assertEqual(result, {key: receipt[key] for key in ('raw_nm', 'original_floors_nm', 'derived_nm')})
        result['raw_nm']['width_nm'] = 1
        self.assertEqual(m.source_dimensions(project_raw)['raw_nm']['width_nm'], 200000)
        self.assertEqual(self.args()[2], project_raw)

    def test_implicit_Default_and_floors_use_observed_values_without_source_edits(self):
        self.project = {'meta': {'filename': 'board.kicad_pro', 'version': 1}}
        before = copy.deepcopy(self.project)
        guided, receipt = self.transform()
        self.assertEqual(receipt['derived_nm']['via_diameter_nm'], 1500000)
        self.assertEqual(receipt['dimension_resolution']['implicit_class_fields'], list(m.floors.DIMENSIONS.values()))
        self.assertEqual(receipt['dimension_resolution']['implicit_floor_fields'], list(m.floors.FLOORS))
        self.assertEqual(self.project, before)
        self.assertEqual(m.check(self.raw, guided, receipt, *self.args()[1:], source=SOURCE), receipt)

    def test_individually_absent_fields_are_resolved_but_present_ones_must_match(self):
        del self.project['net_settings']['classes'][0]['via_drill']
        del self.project['board']['design_settings']['rules']['min_via_annular_width']
        receipt = self.transform()[1]
        self.assertEqual(receipt['dimension_resolution']['implicit_class_fields'], ['via_drill'])
        self.assertEqual(receipt['dimension_resolution']['implicit_floor_fields'], ['min_via_annular_width'])
        self.project['net_settings']['classes'][0]['track_width'] = .3
        self.reject()

    def test_observed_floors_cannot_be_missing_partial_malformed_or_disagree(self):
        original = copy.deepcopy(self.native)
        for value in (None, {}, {'min_track_width': 300000}, [],
                      dict(original['effective_floors_nm'], min_track_width=True),
                      dict(original['effective_floors_nm'], min_track_width=-1),
                      dict(original['effective_floors_nm'], min_track_width=2147483648),
                      dict(original['effective_floors_nm'], min_track_width=400000)):
            with self.subTest(value=value):
                self.native = copy.deepcopy(original)
                if value is None: self.native.pop('effective_floors_nm')
                else: self.native['effective_floors_nm'] = value
                self.reject()

    def test_implicit_resolution_does_not_treat_invalid_present_fields_as_absent(self):
        original = copy.deepcopy(self.project)
        for fault in ('null_settings', 'null_classes', 'empty_classes', 'null_board', 'null_rules',
                      'null_dimension', 'zero_dimension', 'wrong_floor', 'nondefault'):
            self.project = copy.deepcopy(original)
            if fault == 'null_settings': self.project['net_settings'] = None
            elif fault == 'null_classes': self.project['net_settings']['classes'] = None
            elif fault == 'empty_classes': self.project['net_settings']['classes'] = []
            elif fault == 'null_board': self.project['board'] = None
            elif fault == 'null_rules': self.project['board']['design_settings']['rules'] = None
            elif fault == 'null_dimension': self.project['net_settings']['classes'][0]['track_width'] = None
            elif fault == 'zero_dimension': self.project['net_settings']['classes'][0]['track_width'] = 0
            elif fault == 'wrong_floor': self.project['board']['design_settings']['rules']['min_track_width'] = .4
            else: self.project['net_settings']['classes'][0]['name'] = 'Power'
            with self.subTest(fault=fault): self.reject()

    def test_implicit_resolution_requires_consistent_Default_and_parents_on_every_net(self):
        self.project = {}
        original = copy.deepcopy(self.native)
        for fault in ('nondefault', 'different_values', 'missing_parent', 'wrong_priority', 'unbounded'):
            self.native = copy.deepcopy(original)
            row = self.native['nets'][1]
            if fault == 'nondefault': row['class'] = 'Other'
            elif fault == 'different_values': row['width_nm'] += 200
            elif fault == 'missing_parent': row['parameter_parents'].pop('width_nm')
            elif fault == 'wrong_priority': row['parameter_parents']['width_nm']['priority'] = -1
            else: row['width_nm'] = 2147483648
            with self.subTest(fault=fault): self.reject()

    def test_source_dimension_API_qualifies_without_Native_or_receipt(self):
        original = copy.deepcopy(self.project)
        for fault in ('extra_class', 'assignment', 'pattern', 'custom', 'exclude', 'invalid_floor', 'invalid_priority'):
            self.project = copy.deepcopy(original)
            if fault == 'extra_class': self.project['net_settings']['classes'].append(dict(self.project['net_settings']['classes'][0], name='Other'))
            elif fault == 'assignment': self.project['net_settings']['netclass_assignments'] = {'DATA': ['Default']}
            elif fault == 'pattern': self.project['net_settings']['netclass_patterns'] = [{'pattern': '*', 'netclass': 'Default'}]
            elif fault == 'custom': self.project['custom_rules'] = ['unknown']
            elif fault == 'exclude': self.project['board']['design_settings']['drc_exclusions'] = ['hidden']
            elif fault == 'invalid_floor': self.project['board']['design_settings']['rules']['min_clearance'] = True
            else: self.project['net_settings']['classes'][0]['priority'] = True
            with self.subTest(fault=fault), self.assertRaises((ValueError, KeyError)):
                m.source_dimensions(json.dumps(self.project).encode())
        raw = json.dumps(original).encode()
        with self.assertRaises(ValueError): m.source_dimensions(raw[:-1] + b',"net_settings":{}}')

    def test_units_global_and_class_rule_overrides_refuse(self):
        original = self.raw
        for change in [lambda t: sx.one(t, 'unit').__setitem__(1, 'mm'),
                       lambda t: sx.one(t, 'resolution').__setitem__(2, '100'),
                       lambda t: sx.one(sx.one(t, 'structure'), 'rule').append(['clearance', '1']),
                       lambda t: sx.one(sx.children(sx.one(t, 'network'), 'class')[0], 'rule').append(['clearance', '1', ['type', 'smd_smd']]),
                       lambda t: sx.one(t, 'structure').append(['layer_rule', 'F.Cu', ['rule', ['width', '1']]]),
                       lambda t: sx.one(t, 'library').append(['control', ['via_at_smd', 'on']])]:
            self.raw = original; self.edit(change); self.reject()

    def test_native_and_DSN_membership_counts_refuse(self):
        native = copy.deepcopy(self.native)
        for change in [lambda n: n['nets'][0].update(copper_pad_count=2),
                       lambda n: n['nets'][0].update(width_nm=200001),
                       lambda n: n['nets'].append(copy.deepcopy(n['nets'][0])),
                       lambda n: n['nets'][0].update(**{'class': 'Other'})]:
            self.native = copy.deepcopy(native); change(self.native); self.reject()
        self.native = native
        self.edit(lambda t: sx.one(sx.children(sx.one(t, 'network'), 'net')[0], 'pins').append('EXTRA-1')); self.reject()

    def test_via_collision_shape_layer_and_ambiguous_choice_refuse(self):
        original = self.raw
        for change in [lambda t: sx.one(t, 'structure').append(['via', 'other']),
                       lambda t: sx.children(sx.one(t, 'library'), 'padstack')[-1].append(['shape', ['circle', 'F.Cu', '600']]),
                       lambda t: sx.one(sx.children(sx.children(sx.one(t, 'library'), 'padstack')[-1], 'shape')[0], 'circle').__setitem__(2, '601'),
                       lambda t: sx.one(t, 'library').append(['padstack', '"Via[0-1]_1500:300_um"'])]:
            self.raw = original; self.edit(change); self.reject()

    def test_nonfixed_or_unknown_wiring_is_not_reinterpreted(self):
        self.raw, self.native, self.project, self.task = fixtures(fixed=True)
        original = self.raw
        for change in [lambda t: sx.one(sx.children(sx.one(t, 'wiring'), 'wire')[0], 'type').__setitem__(1, 'route'),
                       lambda t: sx.children(sx.one(t, 'wiring'), 'via')[0].__setitem__(1, 'other'),
                       lambda t: sx.one(t, 'wiring').append(['arc', 'unknown'])]:
            self.raw = original; self.edit(change); self.reject()

    def test_rehashed_receipt_cannot_authorize_other_edit(self):
        guided, receipt = self.transform(); args = self.args()
        for alter in ('wire', 'class', 'source', 'policy', 'target', 'admission'):
            changed = _parse_dsn(guided.decode()); rec = copy.deepcopy(receipt)
            if alter == 'wire': sx.one(changed, 'wiring').append(['wire', ['path', 'F.Cu', '1', '0', '0', '1', '1'], ['net', 'DATA'], ['type', 'fix']])
            elif alter == 'class': sx.one(sx.children(sx.one(changed, 'network'), 'class')[0], 'rule')[1][1] = '200'
            elif alter == 'source': rec['source'] = '/other/board.kicad_pcb'
            elif alter == 'policy': rec['policy'] = 'unknown'
            elif alter == 'target': rec['derived_nm']['width_nm'] = 200000
            else: rec['routing_accepted'] = True
            encoded = _dump_dsn(changed).encode(); rec['output_sha256'] = hashlib.sha256(encoded).hexdigest()
            with self.subTest(alter=alter), self.assertRaises(ValueError):
                m.check(self.raw, encoded, rec, *args[1:], source=SOURCE)


if __name__ == '__main__':
    unittest.main()
