"""Owned pure hierarchy join controls; no Native, routing or admission proof.

SPDX-License-Identifier: GPL-3.0-or-later
Constructed Native-shaped rows exercise semantic boundaries after their hashes
are rebound, so a stale-byte rejection alone cannot satisfy these controls.
"""
import copy
import json
import unittest
from unittest.mock import patch

from autorouter import schematic_hierarchy as q, sexpr as sx
from experiments import schematic_hierarchy_fixture as f


def text(node, key):
    return sx.unquote(sx.one(node, key)[1])


def properties(node):
    return {sx.unquote(row[1]): sx.unquote(row[2]) for row in sx.children(node, 'property')}


class HierarchyBindingControls(unittest.TestCase):
    def setUp(self):
        self.case = f.case()

    def derive(self, **overrides):
        arguments = f.arguments(self.case)
        arguments.update(overrides)
        return q.derive(**arguments)

    def refused(self, **overrides):
        with self.assertRaises(ValueError):
            self.derive(**overrides)

    def root(self):
        return self.case['schematics'][f.ROOT_SCH]

    def child(self):
        return self.case['schematics'][f.CHILD_SCH]

    def symbol(self, name):
        return next(row for row in sx.children(self.child(), 'symbol') if text(row, 'uuid') == f.uid(name))

    def component(self, reference):
        return next(row for row in sx.children(sx.one(self.case['netlist'], 'components'), 'comp')
                    if text(row, 'ref') == reference)

    def footprint(self, reference):
        return next(row for row in sx.children(self.case['board'], 'footprint')
                    if properties(row)['Reference'] == reference)

    def net(self, name):
        return next(row for row in sx.children(sx.one(self.case['netlist'], 'nets'), 'net')
                    if text(row, 'name') == name)

    def library(self, name):
        return next(row for row in sx.children(sx.one(self.child(), 'lib_symbols'), 'symbol')
                    if sx.unquote(row[1]) == name)

    def test_repeated_multiunit_shared_pins_alias_power_and_original_no_net_census(self):
        before = copy.deepcopy(self.case)
        proof = self.derive()
        self.assertIs(proof['class_parity_qualified'], True)
        self.assertEqual((proof['components'], proof['terminals'], proof['nets'], proof['instances']),
                         (5, 11, 5, 3))
        for name in ('accepted', 'routing_accepted', 'production_qualified'):
            self.assertIs(proof[name], False)
        serialized = json.dumps(proof, sort_keys=True)
        for reference in ('J1', 'J2'):
            pads = [pad for pad in sx.children(self.footprint(reference), 'pad')
                    if sx.unquote(pad[1]) == 'MP']
            self.assertEqual(len(pads), 2)
            for pad in pads:
                self.assertIn(text(pad, 'uuid'), serialized)
        self.assertEqual(proof, self.derive())
        self.assertEqual(before, self.case)

    def test_repeated_instance_alias_cannot_hide_behind_same_child_bytes(self):
        sx.one(self.footprint('U2'), 'path')[1] = sx.one(self.footprint('U1'), 'path')[1]
        self.refused()

    def test_reused_pin_uuid_is_scoped_by_document_and_full_instance_identity(self):
        root_symbols = sx.children(self.root(), 'symbol')
        original = sx.one(sx.children(root_symbols[0], 'pin')[0], 'uuid')[1]
        sx.one(sx.children(self.symbol('child/J'), 'pin')[0], 'uuid')[1] = original
        proof = self.derive()
        self.assertEqual((proof['components'], proof['terminals'], proof['nets'], proof['instances']),
                         (5, 11, 5, 3))
        self.assertIs(proof['class_parity_qualified'], True)
        self.assertIs(proof['accepted'], False)
        # This is a document-scoped pin UUID only, not permission to merge
        # either physical component or the two repeated child instances.
        self.assertEqual(proof, self.derive())

    def test_expanded_unit_power_and_pin_censuses_have_independent_ceilings(self):
        # This fixture has3 power instances,10 placed unit instances and20
        # expanded placed pins, while each embedded unit has at most3pins and
        # the joined physical census has only11 terminals. Exercise expanded
        # limits without tripping the smaller per-library/member checks first.
        for owner, name, ceiling in ((q, 'MAX_POWER', 2), (q, 'MAX_UNITS', 9),
                                     (q.flat, 'MAX_TERMINALS', 12)):
            with self.subTest(census=name), patch.object(owner, name, ceiling):
                self.refused()

    def test_caller_mapping_replacement_cannot_rebind_parsed_schematic_hashes(self):
        args = f.arguments(self.case)
        original = args['schematics']
        before = dict(original)
        actual_closure = q._closure

        def replace_caller_entry(passed, root_name):
            # Deterministic caller mutation at the pure parser boundary; no
            # Native API or filesystem is mocked. The actual parser still runs.
            original[root_name] = before[root_name] + b'\n'
            return actual_closure(passed, root_name)

        with patch.object(q, '_closure', side_effect=replace_caller_entry):
            proof = q.derive(**args)
        self.assertNotEqual(original[f.ROOT_SCH], before[f.ROOT_SCH])
        self.assertEqual(proof['sha256']['schematics'],
                         {name: f.digest(raw) for name, raw in before.items()})
        self.assertEqual(proof['components'], 5)
        self.assertIs(proof['accepted'], False)

    def test_pin_uuid_collision_within_one_document_still_refuses(self):
        root_symbols = sx.children(self.root(), 'symbol')
        a = sx.one(sx.children(root_symbols[0], 'pin')[0], 'uuid')
        b = sx.one(sx.children(root_symbols[1], 'pin')[0], 'uuid')
        b[1] = a[1]
        self.refused()

    def test_common_unit_zero_only_means_one_placed_unit_and_native_A(self):
        libs = sx.one(self.root(), 'lib_symbols')
        old = next(row for row in libs[1:] if sx.unquote(row[1]) == 'Owned:RootTerm')
        libs[libs.index(old)] = f.library('Owned:RootTerm', {0: ['1']})
        proof = self.derive()
        self.assertEqual((proof['components'], proof['terminals']), (5, 11))
        self.assertIs(proof['class_parity_qualified'], True)
        for fault in ('placed_two', 'native_B'):
            with self.subTest(fault=fault):
                modified = copy.deepcopy(self.case)
                if fault == 'placed_two':
                    symbol = next(row for row in sx.children(modified['schematics'][f.ROOT_SCH], 'symbol')
                                  if text(row, 'uuid') == f.uid('root/X'))
                    sx.one(symbol, 'unit')[1] = '2'
                    project = sx.one(sx.one(symbol, 'instances'), 'project')
                    sx.one(sx.children(project, 'path')[0], 'unit')[1] = '2'
                else:
                    comp = next(row for row in sx.children(sx.one(modified['netlist'], 'components'), 'comp')
                                if text(row, 'ref') == 'X1')
                    sx.one(sx.children(sx.one(comp, 'units'), 'unit')[0], 'name')[1] = '"B"'
                with self.assertRaises(ValueError): q.derive(**f.arguments(modified))

    def test_owned_20241229_numeric_table_keeps_absent_unconnected_pad_nets(self):
        self.case = f.numeric_20241229(f.case())
        before = copy.deepcopy(self.case)
        proof = self.derive()
        self.assertEqual((proof['components'], proof['terminals'], proof['nets'], proof['instances']),
                         (5, 11, 5, 3))
        self.assertIs(proof['class_parity_qualified'], True)
        self.assertIs(proof['accepted'], False)
        self.assertEqual(before, self.case)
        self.assertEqual(proof, self.derive())

    def test_numeric_declared_code_and_name_are_bijective_and_canonical(self):
        for fault in ('identical_duplicate', 'duplicate_code', 'duplicate_name', 'missing_code',
                      'zero_named', 'empty_positive', 'leading_zero', 'negative', 'fraction'):
            with self.subTest(fault=fault):
                self.case = f.numeric_20241229(f.case())
                table = sx.children(self.case['board'], 'net')
                if fault == 'identical_duplicate': self.case['board'].append(copy.deepcopy(table[1]))
                elif fault == 'duplicate_code': self.case['board'].append(['net', table[1][1], '"OTHER"'])
                elif fault == 'duplicate_name': self.case['board'].append(['net', '99', table[1][2]])
                elif fault == 'missing_code': self.case['board'].remove(table[1])
                elif fault == 'zero_named': table[0][2] = '"ZERO"'
                elif fault == 'empty_positive': table[1][2] = '""'
                elif fault == 'leading_zero': table[1][1] = '01'
                elif fault == 'negative': table[1][1] = '-1'
                else: table[1][1] = '1.0'
                self.refused()

    def test_numeric_pad_code_name_and_zero_identity_cannot_be_normalized_away(self):
        for fault in ('name_mismatch', 'unknown_code', 'zero_library_terminal', 'zero_named_extra', 'zero_empty_extra',
                      'named_only', 'modern_numeric'):
            with self.subTest(fault=fault):
                self.case = f.numeric_20241229(f.case())
                pads = sx.children(self.footprint('J1'), 'pad'); net = sx.one(pads[0], 'net')
                if fault == 'name_mismatch': net[2] = '"GND"'
                elif fault == 'unknown_code': net[1] = '999'
                elif fault == 'zero_library_terminal':
                    net[:] = ['net', '0', '""']
                    next(n for n in self.case['native']['nets'] if n['name'] == '/A/SIG_A')['copper_pad_count'] -= 1
                elif fault in ('zero_named_extra', 'zero_empty_extra'):
                    extra = next(p for p in pads if sx.unquote(p[1]) == 'MP')
                    extra.append(['net', '0', '"GND"' if fault == 'zero_named_extra' else '""'])
                elif fault == 'named_only': net[:] = ['net', net[2]]
                else: sx.one(self.case['board'], 'version')[1] = '20260206'
                self.refused()

    def test_source_all_literal_User5_through9_do_not_widen_explicit_layer_policy(self):
        from autorouter import layer_policy
        self.assertEqual(layer_policy._source_layers(self.case['board']), [['0', 'F.Cu'], ['2', 'B.Cu']])
        additions = [[str(code), f.quote('User.' + str(number)), 'user']
                     for code, number in zip((47, 49, 51, 53, 55), range(5, 10))]
        sx.one(self.case['board'], 'layers').extend(additions)
        proof = self.derive()
        self.assertIs(proof['class_parity_qualified'], True)
        self.assertIs(proof['accepted'], False)
        # Modern syntax isolates the explicit route-layer table guard from its
        # independent older-version rejection. It must still reject User.5.
        with self.assertRaises(ValueError): layer_policy._source_layers(self.case['board'])
        f.numeric_20241229(self.case)
        self.assertIs(self.derive()['class_parity_qualified'], True)

    def test_source_all_extended_user_layer_id_name_and_type_remain_exact(self):
        for fault in ('foreign_id', 'foreign_name', 'type', 'duplicate_id', 'hidden_copper'):
            with self.subTest(fault=fault):
                self.case = f.case(); layers = sx.one(self.case['board'], 'layers')
                row = ['47', '"User.5"', 'user']; layers.append(row)
                if fault == 'foreign_id': row[0] = '48'
                elif fault == 'foreign_name': row[1] = '"User.10"'
                elif fault == 'type': row[2] = 'signal'
                elif fault == 'duplicate_id': layers.append(['47', '"User.6"', 'user'])
                else: row[1:] = ['"In1.Cu"', 'signal']
                self.refused()

    def test_board_root_prefix_primary_unit_and_instance_path_refuse(self):
        for fault in ('root_prefix', 'other_unit', 'other_instance', 'traversal', 'relative'):
            with self.subTest(fault=fault):
                self.case = f.case(); row = sx.one(self.footprint('U1'), 'path')
                if fault == 'root_prefix': row[1] = f.quote('/' + f.uid('root') + sx.unquote(row[1]))
                elif fault == 'other_unit': row[1] = f.quote('/' + f.uid('sheet/A') + '/' + f.uid('child/U/2'))
                elif fault == 'other_instance': row[1] = f.quote('/' + f.uid('sheet/B') + '/' + f.uid('child/U/1'))
                elif fault == 'traversal': row[1] = '"/../symbol"'
                else: row[1] = '"relative/symbol"'
                self.refused()

    def test_source_root_and_instance_reference_unit_identity_refuse(self):
        for fault in ('root_uuid', 'path', 'duplicate_path', 'project', 'reference', 'unit'):
            with self.subTest(fault=fault):
                self.case = f.case()
                symbol = self.symbol('child/U/1')
                project = sx.one(sx.one(symbol, 'instances'), 'project')
                paths = sx.children(project, 'path')
                if fault == 'root_uuid': sx.one(self.root(), 'uuid')[1] = f.quote(f.uid('wrong/root'))
                elif fault == 'path': paths[0][1] = f.quote('/' + f.uid('wrong/root') + '/' + f.uid('sheet/A'))
                elif fault == 'duplicate_path': project.append(copy.deepcopy(paths[0]))
                elif fault == 'project': project[1] = '"foreign_project"'
                elif fault == 'reference': sx.one(paths[1], 'reference')[1] = '"U1"'
                else: sx.one(paths[0], 'unit')[1] = '2'
                self.refused()

    def test_native_design_sheet_paths_and_project_source_are_bound(self):
        for fault in ('source', 'tool', 'sheet_path', 'sheet_name', 'duplicate_sheet', 'missing_sheet'):
            with self.subTest(fault=fault):
                self.case = f.case(); design = sx.one(self.case['netlist'], 'design')
                sheets = sx.children(design, 'sheet')
                if fault == 'source': sx.one(design, 'source')[1] = '"/wrong/source.kicad_sch"'
                elif fault == 'tool': sx.one(design, 'tool')[1] = '"Eeschema 10.0.0"'
                elif fault == 'sheet_path': sx.one(sheets[1], 'tstamps')[1] = sx.one(sheets[2], 'tstamps')[1]
                elif fault == 'sheet_name': sx.one(sheets[1], 'name')[1] = '"/B/"'
                elif fault == 'duplicate_sheet': design.append(copy.deepcopy(sheets[1]))
                else: design.remove(sheets[1])
                self.refused()

    def test_native_unit_stamp_sequence_is_complete_and_ordered(self):
        for fault in ('missing', 'reverse', 'duplicate', 'foreign', 'extra'):
            with self.subTest(fault=fault):
                self.case = f.case(); row = sx.one(self.component('U1'), 'tstamps')
                if fault == 'missing': row.pop()
                elif fault == 'reverse': row[1:] = list(reversed(row[1:]))
                elif fault == 'duplicate': row[2] = row[1]
                elif fault == 'foreign': row[2] = f.quote(f.uid('foreign/unit'))
                else: row.append(f.quote(f.uid('extra/unit')))
                self.refused()

    def test_native_multiunit_membership_and_common_pins_refuse(self):
        for fault in ('missing_unit', 'duplicate_unit', 'name', 'wrong_pin', 'missing_common', 'duplicate_pin'):
            with self.subTest(fault=fault):
                self.case = f.case(); units = sx.one(self.component('U1'), 'units')
                a, b = sx.children(units, 'unit')
                pins = sx.one(b, 'pins')
                if fault == 'missing_unit': units.remove(b)
                elif fault == 'duplicate_unit': units.append(copy.deepcopy(a))
                elif fault == 'name': sx.one(b, 'name')[1] = '"A"'
                elif fault == 'wrong_pin': sx.one(pins[1], 'num')[1] = '"1"'
                elif fault == 'missing_common': pins.remove(next(p for p in pins[1:] if text(p, 'num') == '3'))
                else: pins.append(copy.deepcopy(pins[1]))
                self.refused()

    def test_source_unit_and_embedded_pin_membership_refuse_after_hash_rebinding(self):
        for fault in ('placed_unit', 'duplicate_unit', 'missing_pin', 'common_moved', 'unequal_style', 'duplicate_library'):
            with self.subTest(fault=fault):
                self.case = f.case(); lib = self.library('Owned:Dual')
                unit = next(x for x in sx.children(lib, 'symbol') if sx.unquote(x[1]) == 'Dual_1_1')
                if fault == 'placed_unit': sx.one(self.symbol('child/U/2'), 'unit')[1] = '1'
                elif fault == 'duplicate_unit': self.child().append(copy.deepcopy(self.symbol('child/U/1')))
                elif fault == 'missing_pin': unit.remove(sx.children(unit, 'pin')[0])
                elif fault == 'common_moved':
                    common = next(x for x in sx.children(lib, 'symbol') if sx.unquote(x[1]) == 'Dual_0_1')
                    unit.append(copy.deepcopy(sx.children(common, 'pin')[0])); common.remove(sx.children(common, 'pin')[0])
                elif fault == 'unequal_style':
                    style = next(x for x in sx.children(lib, 'symbol') if sx.unquote(x[1]) == 'Dual_1_2')
                    sx.one(sx.children(style, 'pin')[0], 'number')[1] = '"99"'
                else: sx.one(self.child(), 'lib_symbols').append(copy.deepcopy(lib))
                self.refused()

    def test_explicit_library_alias_cannot_be_omitted_or_reinterpreted(self):
        for fault in ('missing', 'wrong', 'duplicate', 'native_part', 'native_lib', 'direct_id'):
            with self.subTest(fault=fault):
                self.case = f.case(); symbol = self.symbol('child/J')
                alias = sx.one(symbol, 'lib_name'); native = sx.one(self.component('J1'), 'libsource')
                if fault == 'missing': symbol.remove(alias)
                elif fault == 'wrong': alias[1] = '"Owned:Dual"'
                elif fault == 'duplicate': symbol.append(copy.deepcopy(alias))
                elif fault == 'native_part': sx.one(native, 'part')[1] = '"Jack"'
                elif fault == 'native_lib': sx.one(native, 'lib')[1] = '"Owned"'
                else: sx.one(self.symbol('child/U/1'), 'lib_id')[1] = '"Other:Dual"'
                self.refused()

    def test_power_exemption_requires_explicit_library_and_no_physical_component(self):
        for fault in ('no_marker', 'footprint', 'physical_missing', 'exported_power'):
            with self.subTest(fault=fault):
                self.case = f.case(); power = self.symbol('child/P')
                if fault == 'no_marker':
                    lib = self.library('Owned:Power'); lib.remove(sx.one(lib, 'power'))
                elif fault == 'footprint':
                    next(x for x in sx.children(power, 'property') if sx.unquote(x[1]) == 'Footprint')[2] = '"Owned:Power"'
                elif fault == 'physical_missing':
                    comp = self.component('J1'); sx.one(self.case['netlist'], 'components').remove(comp)
                    board = self.footprint('J1'); self.case['board'].remove(board)
                    # Remove its entire apparently consistent physical/export
                    # view; only the source symbol still proves it is missing.
                    for net in sx.children(sx.one(self.case['netlist'], 'nets'), 'net'):
                        removed = [n for n in sx.children(net, 'node') if text(n, 'ref') == 'J1']
                        for node in removed:
                            net.remove(node)
                        native = next(n for n in self.case['native']['nets'] if n['name'] == text(net, 'name'))
                        native['copper_pad_count'] -= len(removed)
                else:
                    sx.one(self.case['netlist'], 'components').append(f.component('#PWR02', [f.uid('child/P')],
                        '/A/', '/' + f.uid('sheet/A') + '/', 'Owned', 'Power', [('A', ['1'])]))
                self.refused()

    def test_equal_net_names_counts_and_classes_do_not_hide_partition_swap(self):
        a = sx.children(self.net('/A/SIG_A'), 'node')[0]
        b = sx.children(self.net('/B/SIG_A'), 'node')[0]
        sx.one(a, 'ref')[1], sx.one(b, 'ref')[1] = sx.one(b, 'ref')[1], sx.one(a, 'ref')[1]
        self.refused()

    def test_native_terminal_duplicates_missing_and_unknown_pins_refuse(self):
        for fault in ('duplicate', 'missing', 'unknown_ref', 'wrong_pin', 'case_pin', 'empty_pin'):
            with self.subTest(fault=fault):
                self.case = f.case(); net = self.net('/A/SIG_A'); node = sx.children(net, 'node')[-1]
                if fault == 'duplicate': net.append(copy.deepcopy(node))
                elif fault == 'missing': net.remove(node)
                elif fault == 'unknown_ref': sx.one(node, 'ref')[1] = '"J99"'
                elif fault == 'wrong_pin': sx.one(node, 'pin')[1] = '"MP"'
                elif fault == 'case_pin': sx.one(node, 'pin')[1] = '"r"'
                else: sx.one(node, 'pin')[1] = '""'
                self.refused()

    def test_connected_board_pad_duplicates_and_uuid_aliases_refuse(self):
        for fault in ('duplicate_connected', 'pad_uuid', 'footprint_uuid', 'wrong_net', 'missing_connected', 'case_reference'):
            with self.subTest(fault=fault):
                self.case = f.case(); fp = self.footprint('J1'); pad = sx.children(fp, 'pad')[0]
                if fault == 'duplicate_connected':
                    extra = copy.deepcopy(pad); sx.one(extra, 'uuid')[1] = f.quote(f.uid('another/connected/pad')); fp.append(extra)
                    next(n for n in self.case['native']['nets'] if n['name'] == '/A/SIG_A')['copper_pad_count'] += 1
                elif fault == 'pad_uuid': sx.one(sx.children(fp, 'pad')[1], 'uuid')[1] = sx.one(pad, 'uuid')[1]
                elif fault == 'footprint_uuid': sx.one(fp, 'uuid')[1] = sx.one(self.footprint('J2'), 'uuid')[1]
                elif fault == 'wrong_net': sx.one(pad, 'net')[1] = '"/B/SIG_A"'
                elif fault == 'missing_connected': fp.remove(pad)
                else: next(x for x in sx.children(fp, 'property') if sx.unquote(x[1]) == 'Reference')[2] = '"j1"'
                self.refused()

    def test_connected_extra_pad_and_forged_no_net_exemption_refuse(self):
        for fault in ('connected_extra', 'missing_connected_net', 'extra_alias'):
            with self.subTest(fault=fault):
                self.case = f.case(); pads = sx.children(self.footprint('J1'), 'pad')
                extra = next(x for x in pads if sx.unquote(x[1]) == 'MP')
                if fault == 'connected_extra':
                    extra.append(['net', '"GND"'])
                    next(n for n in self.case['native']['nets'] if n['name'] == 'GND')['copper_pad_count'] += 1
                elif fault == 'missing_connected_net':
                    pads[0].remove(sx.one(pads[0], 'net'))
                    next(n for n in self.case['native']['nets'] if n['name'] == '/A/SIG_A')['copper_pad_count'] -= 1
                else: sx.one(extra, 'uuid')[1] = sx.one(pads[0], 'uuid')[1]
                self.refused()

    def test_class_identity_is_not_derived_from_equal_dimensions(self):
        for fault in ('schematic_class', 'native_class', 'parent_name', 'priority', 'specified', 'scalar', 'parent_scalar'):
            with self.subTest(fault=fault):
                self.case = f.case(); row = self.case['native']['nets'][0]
                if fault == 'schematic_class': sx.one(self.net('GND'), 'class')[1] = '"Signal"'
                elif fault == 'native_class': row['class'] = 'Default,Default'
                elif fault == 'parent_name': row['parameter_parents']['width_nm']['name'] = 'Signal'
                elif fault == 'priority': row['parameter_parents']['width_nm']['priority'] -= 1
                elif fault == 'specified': row['parameter_parents']['width_nm']['specified'] = False
                elif fault == 'scalar': row['width_nm'] += 1
                else: row['parameter_parents']['width_nm']['value_nm'] += 1
                self.refused()

    def test_nondefault_class_directive_and_assignment_never_hidden_in_child(self):
        for fault in ('flag', 'unused_flag', 'class', 'assignment', 'pattern'):
            with self.subTest(fault=fault):
                self.case = f.case(); settings = self.case['project']['net_settings']
                if fault == 'flag': self.child().append(['netclass_flag', '""', ['property', '"Netclass"', '"Default"']])
                elif fault == 'unused_flag':
                    extra = copy.deepcopy(self.child()); extra.append(['netclass_flag', '""', ['property', '"Netclass"', '"Default"']])
                    self.case['schematics']['unused.kicad_sch'] = extra
                elif fault == 'class': settings['classes'].append(dict(settings['classes'][0], name='Signal'))
                elif fault == 'assignment': settings['netclass_assignments'] = {'GND': 'Default'}
                else: settings['netclass_patterns'] = [{'pattern': 'GND', 'netclass': 'Default'}]
                self.refused()

    def test_captured_closure_names_and_sheet_references_must_be_canonical(self):
        for fault in ('missing', 'absolute', 'parent', 'variable', 'case_alias', 'duplicate_sheet_uuid', 'cycle'):
            with self.subTest(fault=fault):
                self.case = f.case(); sheet = sx.children(self.root(), 'sheet')[0]
                prop = next(x for x in sx.children(sheet, 'property') if sx.unquote(x[1]) == 'Sheetfile')
                if fault == 'missing': del self.case['schematics'][f.CHILD_SCH]
                elif fault == 'absolute': prop[2] = '"/external/child.kicad_sch"'
                elif fault == 'parent': prop[2] = '"../child.kicad_sch"'
                elif fault == 'variable': prop[2] = '"${KIPRJMOD}/child.kicad_sch"'
                elif fault == 'case_alias': self.case['schematics']['CHILD.kicad_sch'] = copy.deepcopy(self.child())
                elif fault == 'duplicate_sheet_uuid': sx.one(sx.children(self.root(), 'sheet')[1], 'uuid')[1] = sx.one(sheet, 'uuid')[1]
                else:
                    repeated = copy.deepcopy(sheet)
                    next(x for x in sx.children(repeated, 'property') if sx.unquote(x[1]) == 'Sheetfile')[2] = f.quote(f.ROOT_SCH)
                    self.child().append(repeated)
                self.refused()

    def test_raw_source_map_version_hash_and_type_refuse(self):
        for fault in ('native_version', 'version_argument', 'board_hash', 'project_hash', 'saved', 'source', 'relative', 'stem', 'mapping', 'raw_type'):
            with self.subTest(fault=fault):
                self.case = f.case(); args = f.arguments(self.case)
                native = json.loads(args['native_raw'])
                if fault == 'native_version': native['native_version'] = '10.0.0'
                elif fault == 'version_argument': args['native_version'] = '10.0.0'
                elif fault == 'board_hash': native['board_sha256'] = '0' * 64
                elif fault == 'project_hash': native['project_sha256'] = '0' * 64
                elif fault == 'saved': native['board_saved'] = True
                elif fault == 'source': native['source'] = '/other/' + f.STEM + '.kicad_pcb'
                elif fault == 'relative': args['source'] = f.STEM + '.kicad_pcb'
                elif fault == 'stem': args['schematic_source'] = '/owned/class-input/other.kicad_sch'
                elif fault == 'mapping': args['schematics'] = {f.ROOT_SCH: args['schematics'][f.ROOT_SCH].decode()}
                else: args['board_raw'] = args['board_raw'].decode()
                args['native_raw'] = f.json_bytes(native)
                with self.assertRaises(ValueError): q.derive(**args)


if __name__ == '__main__':
    unittest.main()
