"""Observed open-review recovery; source/candidate authority remains in CLI."""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
import tempfile
import unittest
from autorouter import gui, handoff as h
from tests.test_gui import window_method


class ReviewCloseTests(unittest.TestCase):
    def test_actual_accept_callback_retains_route_and_review_on_observed_lock(self):
        flow = SimpleNamespace(workspace=Path('/owned/job'), ready={'preview','route','review'},
                               records={'route':{'accepted':True}}, choice=None)
        window = SimpleNamespace(flow=flow, chooser=None, busy=False, inspected=Mock(),
            status=Mock(), log=Mock(), refresh=Mock(), refused=Mock())
        window.inspected.GetValue.return_value=True
        hint=Mock(side_effect=h.ReviewProjectOpen('Use File > Close Project'))
        callback=window_method('act',review_close_hint=hint)
        callback(window,'accept')
        self.assertIs(window.flow,flow);self.assertEqual(flow.ready,{'preview','route','review'})
        self.assertEqual(flow.records,{'route':{'accepted':True}});self.assertIsNone(flow.choice)
        window.inspected.SetValue.assert_called_once_with(False);window.refused.assert_not_called()
        self.assertFalse(window.busy);self.assertIn('no acceptance',window.log.SetValue.call_args.args[0])

    def test_hint_uses_real_bounded_inventory_without_ignoring_locks_or_backups(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();project=root/'review/project';project.mkdir(parents=True)
            (project/'board.kicad_pcb').write_text('owned unchanged control')
            lock=project/'~board.kicad_pro.lck';lock.write_text('owned lock')
            with self.assertRaises(h.ReviewProjectOpen):gui.review_close_hint(root)
            lock.unlink();(project/'board-backups').mkdir();(project/'board-backups/owned.zip').write_bytes(b'owned')
            gui.review_close_hint(root)
            (project/'alias').symlink_to(project/'board.kicad_pcb')
            with self.assertRaises(h.Rejected):gui.review_close_hint(root)

    def test_missing_acknowledgement_never_discards_recoverable_review_or_starts_work(self):
        flow=object();window=SimpleNamespace(flow=flow,chooser=None,busy=False,
            inspected=Mock(),status=Mock(),log=Mock(),refresh=Mock(),refused=Mock())
        window.inspected.GetValue.return_value=False;hint=Mock()
        window_method('act',review_close_hint=hint)(window,'accept')
        self.assertIs(window.flow,flow);self.assertFalse(window.busy)
        hint.assert_not_called();window.refused.assert_not_called()
        self.assertIn('no acceptance',window.log.SetValue.call_args.args[0])

    def test_uppercase_nested_marker_is_also_a_refusal(self):
        with self.assertRaises(h.ReviewProjectOpen):h.require_closed_review({'nested/~board.kicad_sch.LCK':'owned'})


if __name__=='__main__':unittest.main()
