"""Proposed pure class-intent controls; not Native or routing evidence.

SPDX-License-Identifier: GPL-3.0-or-later
Requires the lead-owned public schematic_class_intent_v1 fixture on integration.
No dependency on a private .runs path or retained Native output.
"""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from autorouter import pipeline as p, sexpr as sx
from experiments.schematic_class_intent_v1 import fixture


class SchematicClassGuardControls(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.board = self.root/(fixture.STEM+'.kicad_pcb')
        self.schematic = self.board.with_suffix('.kicad_sch')
        self.write(fixture.files(with_directive=False))

    def write(self, files):
        for name, raw in files.items():
            target = self.root/name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)

    def flag(self, name='CRITICAL', property_name='Netclass'):
        return ['netclass_flag', '""', ['at', '38.1', '40.64', '0'],
                ['property', json.dumps(property_name, ensure_ascii=False), json.dumps(name)]]

    def add(self, node, path=None):
        path = self.schematic if path is None else path
        tree = sx.parse(path.read_text())
        tree.append(copy.deepcopy(node))
        path.write_text(sx.dump(tree)+'\n')

    def test_actual_owned_critical_packet_was_preflight_admissible_but_is_now_blocked(self):
        self.write(fixture.files(with_directive=True))
        before = {path.name: path.read_bytes() for path in self.root.iterdir()}
        # Isolate the newly added gate to show all prior preflight gates still
        # admit these same counterexample bytes. This is not Native validation.
        with patch.object(p, 'check_schematic_class_support', return_value=None):
            self.assertEqual(p.preflight(self.board)[0], 'kicad_pcb')
        with self.assertRaisesRegex(p.Rejected, 'PCB class membership and inheritance are not independently verified'):
            p.preflight(self.board)
        self.assertEqual(before, {path.name: path.read_bytes() for path in self.root.iterdir()})

    def test_no_directive_project_remains_admissible(self):
        self.assertIsNone(p.check_schematic_class_support(self.board))
        self.assertEqual(p.preflight(self.board)[0], 'kicad_pcb')

    def test_child_directory_directive_is_not_hidden_by_clean_root(self):
        child = self.root/'subcircuits'/'child.kicad_sch'
        child.parent.mkdir()
        child.write_bytes(self.schematic.read_bytes())
        self.add(self.flag(), child)
        with self.assertRaisesRegex(p.Rejected, 'subcircuits/child.kicad_sch'):
            p.preflight(self.board)

    def test_localized_blank_default_and_malformed_structural_flags_all_refuse(self):
        original = self.schematic.read_bytes()
        variants = [self.flag('CRITICAL', 'ネットクラス'), self.flag('', 'ネットクラス'),
                    self.flag('Default'), ['netclass_flag'], ['netclass_flag', '""']]
        for node in variants:
            with self.subTest(node=node):
                self.schematic.write_bytes(original)
                self.add(node)
                with self.assertRaisesRegex(p.Rejected, 'netclass_flag unsupported'):
                    p.check_schematic_class_support(self.board)

    def test_quoted_property_text_and_sexpr_comment_do_not_become_structural_tags(self):
        tree = sx.parse(self.schematic.read_text())
        symbol = sx.children(tree, 'symbol')[0]
        prop = next(row for row in sx.children(symbol, 'property')
                    if sx.unquote(row[1]) == 'Description')
        prop[2] = json.dumps('(netclass_flag "CRITICAL") (sheet "text only")')
        tree.append(['sheet_instances', ['path', '"/"', ['page', '"1"']]])
        self.schematic.write_text('; (netclass_flag "CRITICAL")\n'+sx.dump(tree)+'\n')
        self.assertIsNone(p.check_schematic_class_support(self.board))

    def test_absent_schematic_preserves_board_only_preflight_path(self):
        self.schematic.unlink()
        self.assertIsNone(p.check_schematic_class_support(self.board))
        self.assertEqual(p.preflight(self.board)[0], 'kicad_pcb')

    def test_unknown_root_malformed_version_and_parse_failures_refuse(self):
        variants = ['(unknown_schematic (version 20250114))', '(kicad_sch)',
                    '(kicad_sch (version 20250114) (version 20250114))',
                    '(kicad_sch (version nan))', '(kicad_sch (version 20250114.0))',
                    '(kicad_sch (version "20250114"))', '(kicad_sch (version 00000000))',
                    '(kicad_sch (version 20250114)', b'\xff']
        for raw in variants:
            with self.subTest(raw=raw):
                self.schematic.write_bytes(raw if isinstance(raw, bytes) else raw.encode())
                with self.assertRaises(p.Rejected):
                    p.preflight(self.board)

    def test_older_numeric_schematic_version_is_not_newly_disallowed_by_this_guard(self):
        tree = sx.parse(self.schematic.read_text())
        sx.one(tree, 'version')[1] = '20230121'
        self.schematic.write_text(sx.dump(tree)+'\n')
        self.assertIsNone(p.check_schematic_class_support(self.board))

    def test_external_sheet_cannot_hide_uncaptured_class_intent(self):
        original = self.schematic.read_bytes()
        for reference in ('../uncaptured.kicad_sch', '/unread-uncaptured.kicad_sch',
                          'missing-child.kicad_sch'):
            with self.subTest(reference=reference):
                self.schematic.write_bytes(original)
                self.add(['sheet', ['property', '"Sheetfile"', json.dumps(reference)]])
                with self.assertRaisesRegex(p.Rejected, 'hierarchy dependency closure'):
                    p.preflight(self.board)

    def test_even_captured_sheet_is_not_admitted_without_qualified_closure(self):
        self.write({'child.kicad_sch': self.schematic.read_bytes()})
        self.add(['sheet', ['property', '"Sheetfile"', '"child.kicad_sch"']])
        with self.assertRaisesRegex(p.Rejected, 'hierarchy dependency closure'):
            p.preflight(self.board)

    def test_symlink_child_schematic_fails_closed(self):
        (self.root/'linked.kicad_sch').symlink_to(self.schematic)
        with self.assertRaisesRegex(p.Rejected, 'symlink'):
            p.preflight(self.board)

    def test_project_read_error_is_wrapped_as_preflight_rejection(self):
        with patch('autorouter.placement_clearance.inventory', side_effect=OSError('owned read failure')):
            with self.assertRaisesRegex(p.Rejected, 'schematic class intent not qualified.*owned read failure'):
                p.preflight(self.board)


if __name__ == '__main__':
    unittest.main()
