"""Saved hierarchy/display controls. Native electrical validation is separate."""
import json
from pathlib import Path
import tempfile
import unittest

from autorouter import gui, schematic_context, schematic_hierarchy, sexpr
from experiments import schematic_hierarchy_fixture as fixture
from experiments.placement_native_proposal_v1 import ordinary_fixture


class SavedSchematicContextTests(unittest.TestCase):
    def setUp(self):
        self.workspace = tempfile.TemporaryDirectory()
        self.addCleanup(self.workspace.cleanup)
        self.root = Path(self.workspace.name).resolve()
        self.board = self.root / (fixture.STEM + '.kicad_pcb')
        self.case = fixture.case()
        self.board.write_text(sexpr.dump(self.case['board']))
        self.board.with_suffix('.kicad_pro').write_text(json.dumps(self.case['project']))
        for name, tree in self.case['schematics'].items():
            (self.root / name).write_text(sexpr.dump(tree))
        self.hashes = gui.source_inventory(self.board)

    def test_repeated_sheet_refs_bind_to_distinct_instances_and_pad_nets(self):
        context = schematic_context.capture(self.board, self.hashes)
        first, second = (context['components'][name] for name in ('J1', 'J2'))
        self.assertEqual(len(context['sheets']), 3)
        self.assertEqual(first['file'], second['file'])
        self.assertNotEqual(first['sheet'], second['sheet'])
        self.assertNotEqual(first['units'][0]['path'], second['units'][0]['path'])
        self.assertNotEqual(first['pin_nets'], second['pin_nets'])
        description = schematic_context.describe(context, ['J1', 'J2'])
        self.assertIn(first['sheet'][0], description)
        self.assertTrue(all(name in description for name in first['pin_nets'].values()))
        self.assertIn('saved PCB pad assignments', description)
        self.assertFalse(context['electrical_validation_performed'])

    def test_conversation_context_names_only_the_verified_selected_parts_and_nets(self):
        context = schematic_context.capture(self.board, self.hashes)
        first = context['components']['J1']
        summary = schematic_context.selection_summary(context, ['J1'])
        self.assertIn('Selected J1', summary)
        self.assertIn(first['sheet'][0], summary)
        self.assertTrue(all(net in summary for net in first['pin_nets'].values()))
        self.assertNotIn('J2', summary)
        self.assertIn('Suggested J1, J2', schematic_context.selection_summary(context, ['J1', 'J2'], proposed=True))
        self.assertEqual(schematic_context.selection_summary(context, []), '')
        self.assertIn('no verified schematic link', schematic_context.selection_summary(context, ['UNKNOWN']))

    def test_changed_or_missing_child_cannot_reuse_earlier_context(self):
        context = schematic_context.capture(self.board, self.hashes)
        child = self.root / fixture.CHILD_SCH
        with child.open('ab') as stream:
            stream.write(b'\n')
        with self.assertRaisesRegex(ValueError, 'Saved project changed'):
            schematic_context.current(context, self.board)
        with self.assertRaisesRegex(ValueError, 'changed during'):
            schematic_context.capture(self.board, self.hashes)
        child.unlink()  # Test-owned copy, outside all user inputs.
        result, reason = schematic_context.observe(self.board, gui.source_inventory(self.board))
        self.assertIsNone(result)
        self.assertIn('hierarchy child absent', reason)

    def test_current_flat_save_supplies_read_only_context_with_unchanged_proof_scope(self):
        board = ordinary_fixture.write_project(self.root / 'flat')
        schematic = board.with_suffix('.kicad_sch')
        tree = sexpr.parse(schematic.read_text())
        sexpr.one(tree, 'version')[1] = '20260306'
        schematic.write_text(sexpr.dump(tree))
        original = gui.source_inventory(board)

        self.assertEqual(schematic_context.assigned_footprint_count(board, original), 6)
        context = schematic_context.capture(board, original)
        self.assertEqual(set(context['components']), {'J1', 'J2', 'J3', 'J4', 'J5', 'J6'})
        self.assertFalse(context['electrical_validation_performed'])
        with self.assertRaisesRegex(ValueError, 'schematic version unqualified'):
            schematic_hierarchy._closure({schematic.name: schematic.read_bytes()}, schematic.name)
        self.assertEqual(gui.source_inventory(board), original)

        sexpr.one(tree, 'generator_version')[1] = '"11.0"'
        schematic.write_text(sexpr.dump(tree))
        with self.assertRaisesRegex(ValueError, 'changed during schematic inspection'):
            schematic_context.assigned_footprint_count(board, original)
        with self.assertRaisesRegex(ValueError, 'schematic version unqualified'):
            schematic_context.assigned_footprint_count(board, gui.source_inventory(board))

    def test_swapped_hierarchical_reference_path_is_never_inferred_by_name(self):
        board = self.case['board']
        footprints = [fp for fp in sexpr.children(board, 'footprint')
                      if any(sexpr.unquote(p[1]) == 'Reference' and sexpr.unquote(p[2]) in ('J1', 'J2')
                             for p in sexpr.children(fp, 'property'))]
        a, b = [sexpr.one(item, 'path') for item in footprints]
        a[1], b[1] = b[1], a[1]
        self.board.write_text(sexpr.dump(board))
        result, reason = schematic_context.observe(self.board, gui.source_inventory(self.board))
        self.assertIsNone(result)
        self.assertIn('instance/group path differs', reason)


if __name__ == '__main__':
    unittest.main()
