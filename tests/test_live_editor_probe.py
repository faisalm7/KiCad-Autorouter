"""Exact readback controls for the owned live-editor qualification."""
from pathlib import Path
import unittest
from unittest.mock import Mock

from autorouter import sexpr
from experiments.live_editor_v1 import probe
from experiments.placement_native_proposal_v1 import contract


class EditorReadback(unittest.TestCase):
    def setUp(self):
        path = Path(probe.FIXTURE) / (probe.NAME + '.kicad_pcb')
        self.before = contract.read_board(path.read_bytes())
        self.headers = [sexpr.one(self.before, key) for key in ('version', 'generator', 'generator_version')]
        for footprint in sexpr.children(self.before, 'footprint'):
            footprint[2:2] = self.headers
        self.snapshot = self.dump(self.before)

    @staticmethod
    def dump(tree):
        return (sexpr.dump(tree) + '\n').encode()

    def test_exact_clipboard_headers_are_the_only_projection(self):
        board = contract.read_board(probe.board_file(self.snapshot))
        self.assertEqual([sexpr.one(board, n[0]) for n in self.headers], self.headers)
        for footprint in sexpr.children(board, 'footprint'):
            self.assertTrue(sexpr.children(footprint, 'units'))
            self.assertFalse(sexpr.children(footprint, 'generator_version'))
        sexpr.children(self.before, 'footprint')[0][2] = ['version', 'unrecognized']
        with self.assertRaisesRegex(ValueError, 'headers'):
            probe.board_file(self.dump(self.before))

    def test_readback_rejects_metadata_loss_and_changes_to_saved_inputs(self):
        # The exact parser stays authoritative for footprint unit and field IDs.
        expected = contract.read_board(probe.board_file(self.snapshot))
        disk = {'pcb': 'unchanged'}
        plan = dict(snapshot=dict(disk=disk), expected=expected)
        self.assertTrue(probe.unchanged_outside_move(plan, dict(raw=self.snapshot, disk=disk)))
        self.assertFalse(probe.unchanged_outside_move(plan, dict(raw=self.snapshot, disk={})))
        item = sexpr.children(self.before, 'footprint')[0]
        item.remove(sexpr.one(item, 'units'))
        self.assertFalse(probe.unchanged_outside_move(plan, dict(raw=self.dump(self.before), disk=disk)))
        item.append(sexpr.one(sexpr.children(expected, 'footprint')[0], 'units'))
        sexpr.one(sexpr.children(item, 'property')[0], 'uuid')[1] = '"different"'
        self.assertFalse(probe.unchanged_outside_move(plan, dict(raw=self.dump(self.before), disk=disk)))

    def test_workspace_selection_read_retires_checked_move(self):
        session = probe.Session.__new__(probe.Session)
        session.plan = {'info': {'id': 1}, 'native': {'blocking': 0}}
        session.initial = {'raw': self.snapshot, 'sha256': 'fixture', 'disk': {}}
        session.snapshot = Mock(return_value=session.initial)
        session.selected = Mock(return_value=[])
        session.write = Mock()
        self.assertIn('svg', session.inspect(board_view=True)['scene'])
        with self.assertRaisesRegex(ValueError, 'Preview a new move'):
            session.fresh(1)


if __name__ == '__main__':
    unittest.main()
