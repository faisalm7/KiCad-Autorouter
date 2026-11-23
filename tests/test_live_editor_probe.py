"""Exact readback controls for the owned live-editor qualification."""
from pathlib import Path
from types import SimpleNamespace
import sys
import unittest
from unittest.mock import Mock, patch

from autorouter import live_move, sexpr
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

    def test_local_request_clarifies_scope_and_uses_exact_nanometres(self):
        self.assertEqual(probe.requested_offset('Move J1 right by 0.500001 mm', 'J1'), (500_001, 0))
        self.assertEqual(probe.requested_offset('Move selected part up by 0.25 mm.', 'J1'), (0, -250_000))
        with self.assertRaisesRegex(ValueError, 'J1 is selected'):
            probe.requested_offset('Move J2 right by 0.75 mm', 'J1')
        with self.assertRaisesRegex(ValueError, 'no more than 1 mm'):
            probe.requested_offset('Move J1 right by 1.000001 mm', 'J1')
        with self.assertRaisesRegex(ValueError, 'Choose a direction'):
            probe.requested_offset('Move it a little', 'J1')

    def test_revised_draft_replaces_approval_identity_and_checks_live_state(self):
        session = probe.Session.__new__(probe.Session)
        session.initial = dict(raw=self.snapshot, sha256='fixture', disk={'original': 'exact'})
        session.apply_disabled = False
        session.index = 0
        session.snapshot = Mock(return_value=session.initial)
        session.write = Mock()
        observed = contract.inspect_board(probe.board_file(self.snapshot), scope=contract.THT_BASELINE_SCOPE)
        row, = [part for part in observed['footprints'] if part['reference'] == 'J1']
        x, y = row['position_nm']
        part = SimpleNamespace(id=SimpleNamespace(value=row['uuid']), position=SimpleNamespace(x=x, y=y),
            reference_field=SimpleNamespace(text=SimpleNamespace(value='J1')))
        session.selected = Mock(return_value=[part])
        self.assertEqual(session.inspect(board_view=True)['selection'], ['J1'])
        first = session.preview('Move J1 right by 0.5 mm', board_view=True)
        self.assertEqual(first['to_nm'], [x + 500_000, y])
        self.assertIn('Proposed move · J1', first['scene']['svg'])
        revised = session.preview('Move J1 right by 0.75 mm')
        with self.assertRaisesRegex(ValueError, 'Preview a new move'):
            session.fresh(first['id'])
        self.assertEqual(session.fresh(revised['id'])['to_nm'], [x + 750_000, y])
        session.snapshot.return_value = dict(session.initial, disk={'changed': True})
        with self.assertRaisesRegex(ValueError, 'KiCad changed after preview'):
            session.fresh(revised['id'])
        with self.assertRaisesRegex(ValueError, 'Saved project files changed'):
            session.preview('Move J1 right by 0.5 mm')
        self.assertIsNone(session.plan)
        session.snapshot.return_value = session.initial
        other = next(part for part in observed['footprints'] if part['reference'] == 'J2')
        session.selected.return_value = [SimpleNamespace(id=SimpleNamespace(value=other['uuid']),
            reference_field=SimpleNamespace(text=SimpleNamespace(value='J2')))]
        with self.assertRaisesRegex(probe.EditorContextChanged, 'Read selection'):
            session.preview('Move selected part right by 0.5 mm')
        self.assertIsNone(session.plan)

    def test_uncertain_transaction_retires_the_plan_and_blocks_another_move(self):
        geometry = SimpleNamespace(Vector2=SimpleNamespace(from_xy=lambda *position: position))
        for stage in ('begin', 'drop', 'exact drop'):
            with self.subTest(stage=stage), patch.dict(sys.modules, {'kipy.geometry': geometry}):
                session = probe.Session.__new__(probe.Session)
                session.direct_trial = True
                session.direct_attempted = session.apply_disabled = False
                session.applied = None
                session.plan = {'snapshot': {'raw': self.snapshot}, 'native': {}}
                session.snapshot = Mock(return_value=session.plan['snapshot'])
                session.fresh = Mock(return_value={'uid': 'owned', 'to_nm': [15_000_000, 10_000_000]})
                session.selected = Mock(return_value=[SimpleNamespace()])
                session.write = Mock()
                session.pcb = Mock()
                session.pcb.update_items.side_effect = ValueError('Deliberate stage refusal')
                if stage == 'begin':
                    session.pcb.begin_commit.side_effect = OSError('Unconfirmed opening')
                if stage == 'drop':
                    session.pcb.drop_commit.side_effect = OSError('Unconfirmed drop')
                reason = {'begin': 'did not confirm', 'drop': 'could not verify', 'exact drop': 'Deliberate stage refusal'}
                with self.assertRaisesRegex(ValueError, reason[stage]):
                    session.apply_direct_trial(1)
                self.assertEqual(session.apply_disabled, stage != 'exact drop')
                self.assertIsNone(session.plan)
                self.assertIsNone(session.applied)
                session.pcb.push_commit.assert_not_called()

    def test_owned_workspace_passes_the_bound_saved_project_to_its_panel(self):
        session = Mock(path=Path('/owned/inspection/checked.kicad_pcb'))
        panel = Mock()
        panel.stdout.readline.return_value = ''
        with patch.object(live_move.subprocess, 'Popen', return_value=panel) as start:
            live_move.workspace(session)
        self.assertEqual(start.call_args.args[0][-2:], ['--saved-project', '/owned/inspection/checked.kicad_pro'])
        panel.stdin.close.assert_called_once()
        panel.stdout.close.assert_called_once()


if __name__ == '__main__':
    unittest.main()
