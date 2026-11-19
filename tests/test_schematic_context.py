"""Saved hierarchy/display controls. Native electrical validation is separate."""
import json
from pathlib import Path
import tempfile
import unittest

from autorouter import gui, schematic_context, sexpr
from experiments import schematic_hierarchy_fixture as fixture


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
