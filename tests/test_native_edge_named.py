"""Pure named-edge prototype controls; no JVM/Native matrix qualification.

Reuse the strict class-mapping fixtures. These prove AST/input boundaries only;
the pinned full importer must still establish actual matrix/item inheritance.
"""
import copy
import json
import unittest

from autorouter import adapter as a, native_edge as edge, netclass as nc, sexpr as sx
from tests import test_native_edge as original
from tests.test_netclass import fixtures
from tests.test_netclass_parent_policy import example


def inputs(*, parent=False):
    tree, native, project = example() if parent else fixtures()
    project['board']['design_settings']['rules']['min_copper_edge_clearance'] = .3
    structure = sx.one(tree, 'structure')
    baseline = sx.one(a._parse_dsn(original.DSN), 'structure')
    structure.append(copy.deepcopy(sx.one(baseline, 'boundary')))
    structure.append(copy.deepcopy(sx.one(baseline, 'rule')))
    return tree, native, project


def context(project, board=original.BOARD):
    return edge.derive_context(board, json.dumps(project).encode(), experimental_named_classes=True)


def corrected(tree, project):
    raw = a._dump_dsn(tree).encode()
    result, record = edge.correct(raw, context(project))
    return a._parse_dsn(result.decode()), record


class NamedEdgePrototypeTests(unittest.TestCase):
    def test_production_default_and_false_do_not_admit_named_scope(self):
        tree, _, project = inputs(); raw = a._dump_dsn(tree).encode(); project_raw = json.dumps(project).encode()
        for options in ({}, {'experimental_named_classes': False}):
            with self.subTest(options=options):
                source_context = edge.derive_context(original.BOARD, project_raw, **options)
                self.assertFalse(source_context['applicable'])
                self.assertEqual(source_context['reason'], 'outside Default-only unassigned project scope')
                self.assertNotIn('named_class_scope', source_context)
                output, record = edge.correct(raw, source_context)
                self.assertEqual(output, raw); self.assertFalse(record['applied'])
        for value in (None, 0, 1, 'yes', [], {}):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, 'Boolean'):
                edge.derive_context(original.BOARD, project_raw, experimental_named_classes=value)

    def test_literal_class_mapping_and_all_nonedge_ast_remain_exact(self):
        tree, native, project = inputs(); before = copy.deepcopy(tree)
        source_context = context(project); frozen_context = copy.deepcopy(source_context)
        raw, record = edge.correct(a._dump_dsn(tree).encode(), source_context)
        changed = a._parse_dsn(raw.decode()); structure = sx.one(changed, 'structure')
        self.assertEqual(sx.one(structure, 'boundary').pop(), ['clearance_class', edge.CLASS])
        self.assertEqual(structure.pop(), ['rule',
            ['clearance', '300', ['type', 'default_kicadedge']],
            ['clearance', '300', ['type', 'smd_kicadedge']],
            ['clearance', '300', ['type', 'kicadedge_kicadedge']]])
        self.assertEqual(changed, before)
        self.assertEqual(tree, before); self.assertEqual(source_context, frozen_context)
        self.assertTrue(nc.audit_mapping(a._parse_dsn(raw.decode()), native, project)['passed'])
        self.assertEqual(record['dsn_class_identities'], ['Power', 'kicad_default'])
        self.assertTrue(record['native_class_mapping_required'])
        self.assertFalse(record['loaded_named_matrix_qualified']); self.assertFalse(record['routing_accepted'])
        # Creating a Power structure pair would bypass the importer's normal
        # named-row initialization and can weaken nonedge/item-class behavior.
        self.assertNotIn(b'Power_kicadedge', raw)

    def test_parent_composites_preserve_exact_identity_and_native_mapping(self):
        tree, native, project = inputs(parent=True)
        changed, record = corrected(tree, project)
        self.assertEqual(record['named_class_scope']['source_policy'], nc.PARENT_POLICY)
        self.assertTrue(record['named_class_scope']['allow_default_composites'])
        self.assertEqual(record['dsn_class_identities'], ['Power,Default', 'Signal,Default', 'kicad_default'])
        self.assertTrue(nc.audit_mapping(changed, native, project, parent_policy=True)['passed'])
        self.assertEqual(sx.one(changed, 'network'), sx.one(tree, 'network'))

    def test_underscore_names_are_never_interpolated_into_clearance_pairs(self):
        tree, native, project = inputs()
        project['net_settings']['classes'][1]['name'] = 'Power_A'
        for row in project['net_settings']['netclass_patterns']: row['netclass'] = 'Power_A'
        native['nets'][1]['class'] = 'Power_A'
        sx.children(sx.one(tree, 'network'), 'class')[1][1] = 'Power_A'
        changed, record = corrected(tree, project)
        self.assertTrue(nc.audit_mapping(changed, native, project)['passed'])
        self.assertEqual(record['dsn_class_identities'], ['Power_A', 'kicad_default'])
        self.assertEqual(len(sx.children(sx.one(changed, 'structure'), 'rule')[-1]), 4)

    def test_higher_class_clearance_and_unqualified_sources_stay_byte_exact_noops(self):
        tree, _, base = inputs(); raw = a._dump_dsn(tree).encode()
        cases = []
        high = copy.deepcopy(base); high['net_settings']['classes'][1]['clearance'] = .31; cases.append(high)
        implicit = copy.deepcopy(base); implicit['net_settings']['netclass_assignments'] = {'DATA': ['Power']}; cases.append(implicit)
        pattern = copy.deepcopy(base); pattern['net_settings']['netclass_patterns'][0]['pattern'] = 'G*'; cases.append(pattern)
        missing = copy.deepcopy(base); missing['net_settings']['classes'][1].pop('via_drill'); cases.append(missing)
        custom = copy.deepcopy(base); custom['board']['design_settings']['custom_rules'] = ['unqualified']; cases.append(custom)
        for name in ('smd', 'wire', 'via', 'pin', 'area', 'null', 'KicadEdge', 'board_edge'):
            collision = copy.deepcopy(base); collision['net_settings']['classes'][1]['name'] = name
            for row in collision['net_settings']['netclass_patterns']: row['netclass'] = name
            cases.append(collision)
        for project in cases:
            with self.subTest(project=project):
                source_context = context(project)
                self.assertFalse(source_context['applicable'])
                output, record = edge.correct(raw, source_context)
                self.assertEqual(output, raw); self.assertFalse(record['applied'])
        alias = copy.deepcopy(base); alias['net_settings']['classes'][1]['name'] = 'default'
        with self.assertRaisesRegex(ValueError, 'ambiguous source class namespace'): context(alias)

    def test_unobserved_declared_class_is_not_invented_in_the_dsn(self):
        tree, native, project = inputs()
        project['net_settings']['netclass_patterns'] = []
        network = sx.one(tree, 'network'); classes = sx.children(network, 'class')
        classes[0].insert(3, 'GND'); network.remove(classes[1])
        changed, record = corrected(tree, project)
        self.assertEqual(record['dsn_class_identities'], ['kicad_default'])
        self.assertEqual(sx.children(sx.one(changed, 'network'), 'class'), sx.children(network, 'class'))

    def test_unknown_duplicate_reversed_or_unqualified_class_identities_refuse(self):
        for parent, name in ((False, 'Unknown'), (False, 'Power,Default'), (True, 'Default,Power'),
                             (True, 'Power,Power'), (True, 'Power,Signal,Default'),
                             (True, 'Power,Unknown'), (True, 'Default')):
            tree, _, project = inputs(parent=parent)
            sx.children(sx.one(tree, 'network'), 'class')[1][1] = name
            with self.subTest(parent=parent, name=name), self.assertRaises(ValueError): corrected(tree, project)
        tree, _, project = inputs()
        network = sx.one(tree, 'network'); network.append(copy.deepcopy(sx.children(network, 'class')[1]))
        with self.assertRaisesRegex(ValueError, 'duplicate'): corrected(tree, project)

    def test_class_rule_and_namespace_overrides_refuse_without_editing_inputs(self):
        for mutation in ('width', 'clearance', 'typed', 'rule_duplicate', 'layer_rule', 'circuit', 'class_class', 'clearance_class'):
            tree, _, project = inputs(); network = sx.one(tree, 'network')
            cls = sx.children(network, 'class')[1]; rule = sx.one(cls, 'rule')
            if mutation in ('width', 'clearance'): sx.one(rule, mutation)[1] = '249'
            elif mutation == 'typed': sx.one(rule, 'clearance').append(['type', 'smd_smd'])
            elif mutation == 'rule_duplicate': cls.append(copy.deepcopy(rule))
            elif mutation == 'layer_rule': cls.append(['layer_rule', 'F.Cu', ['clearance', '1']])
            elif mutation == 'circuit': sx.one(cls, 'circuit').append(['use_layer', 'F.Cu'])
            elif mutation == 'class_class': network.append(['class_class', 'Power', 'kicad_default', ['rule', ['clearance', '1']]])
            else: cls.append(['clearance_class', 'Power'])
            before = copy.deepcopy(tree)
            with self.subTest(mutation=mutation), self.assertRaises(ValueError): corrected(tree, project)
            self.assertEqual(tree, before)

    def test_named_context_missing_or_tampered_fields_refuse(self):
        tree, _, project = inputs(); source_context = context(project); raw = a._dump_dsn(tree).encode()
        for change in ('none', 'policy', 'source_policy', 'default', 'parameter', 'unknown', 'high', 'bool'):
            bad = copy.deepcopy(source_context); scope = bad['named_class_scope']
            if change == 'none': bad['named_class_scope'] = None
            elif change == 'policy': scope['policy'] = 'unqualified'
            elif change == 'source_policy': scope['source_policy'] = 'generic'
            elif change == 'default': scope['source_classes'].pop('Default')
            elif change == 'parameter': scope['source_classes']['Power']['width_um'] = None
            elif change == 'unknown': scope['extra'] = 'unqualified'
            elif change == 'high': scope['source_classes']['Power']['clearance_um'] = '301'
            else: scope['allow_default_composites'] = 1
            with self.subTest(change=change), self.assertRaises(ValueError): edge.correct(raw, bad)

    def test_existing_default_context_and_output_have_no_named_scope(self):
        source_context = edge.derive_context(original.BOARD, json.dumps(original.PROJECT).encode())
        output, record = edge.correct(original.DSN.encode(), source_context)
        self.assertNotIn('named_class_scope', source_context)
        self.assertNotIn('named_class_scope', record)
        self.assertNotIn('loaded_named_matrix_qualified', record)
        self.assertTrue(record['applied'])
        self.assertEqual(sx.one(a._parse_dsn(output.decode()), 'network'), sx.one(a._parse_dsn(original.DSN), 'network'))


if __name__ == '__main__': unittest.main()
