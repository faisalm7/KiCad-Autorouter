"""Bounded Improve log display controls, not wx/Native/GUI qualification."""
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
from tests import test_gui as gui_fixture
from autorouter import strategy


class ImproveProgressTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(); self.addCleanup(temporary.cleanup)
        self.workspace = Path(temporary.name).resolve()
        self.root = self.workspace / 'route'; self.root.mkdir()
        self.flow = SimpleNamespace(workspace=self.workspace, method='improve')
        self.window = SimpleNamespace(busy=True, flow=self.flow, log=Mock())

    def log(self, relative, text, timestamp):
        path = self.root / relative; path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text); os.utime(path, ns=(timestamp, timestamp))
        return path

    def tick(self):
        gui_fixture.window_method('tick')(self.window, None)

    def test_incumbent_progress_updates_without_parent_logs(self):
        self.log('incumbent/source-drc.log', 'source validated', 100)
        self.log('incumbent/engine.log', 'routing incumbent', 200)
        self.tick()
        self.window.log.SetValue.assert_called_once_with('incumbent/engine.log\nrouting incumbent')
        self.assertIs(self.window.flow, self.flow); self.assertTrue(self.window.busy)

    def test_latest_canonical_trial_then_parent_finalization_is_visible(self):
        self.log('incumbent/final-drc.log', 'old incumbent', 100)
        self.log('trials/trial-0031/refill-drc.log', 'trial refill', 200)
        self.tick()
        self.window.log.SetValue.assert_called_once_with('trials/trial-0031/refill-drc.log\ntrial refill')
        self.window.log.reset_mock()
        self.log('final-drc.log', 'parent final validation', 300)
        self.tick()
        self.window.log.SetValue.assert_called_once_with('final-drc.log\nparent final validation')

    def test_out_of_range_and_noncanonical_directories_are_not_scanned(self):
        self.assertEqual(strategy.MAX_TRIALS, 32)  # Deliberately bounded GUI namespace must track the producer.
        self.log('trials/trial-0000/refill-drc.log', 'allowed trial', 100)
        for relative in ('trials/trial-0032/engine.log', 'trials/trial-0/engine.log',
                         'arbitrary/engine.log', 'recovery/engine.log'):
            self.log(relative, 'not this method namespace', 900)
        self.tick()
        self.window.log.SetValue.assert_called_once_with('trials/trial-0000/refill-drc.log\nallowed trial')

    def test_tail_is_bounded_and_leaf_symlink_log_is_ignored(self):
        text = 'x' * 4096 + 'latest bytes'
        self.log('incumbent/engine.log', text, 100)
        target = self.log('arbitrary/private.log', 'not followed', 900)
        alias = self.root / 'trials/trial-0000/final-drc.log'
        alias.parent.mkdir(parents=True); alias.symlink_to(target)
        self.tick()
        self.window.log.SetValue.assert_called_once_with('incumbent/engine.log\n' + text[-2048:])

    def test_completed_or_cancelled_window_keeps_its_terminal_message(self):
        self.log('incumbent/engine.log', 'old progress', 100)
        self.window.busy = False
        self.tick()
        self.window.log.SetValue.assert_not_called()

    def test_disappearing_nested_log_does_not_change_flow_or_raise(self):
        phase = self.log('incumbent/engine.log', 'temporary progress', 100)
        original_stat = type(phase).stat
        def disappearing(path, *args, **kwargs):
            result = original_stat(path, *args, **kwargs)
            if path == phase and kwargs.get('follow_symlinks', True):
                phase.unlink()
            return result
        with patch.object(type(phase), 'stat', autospec=True, side_effect=disappearing):
            self.tick()
        self.window.log.SetValue.assert_not_called()
        self.assertIs(self.window.flow, self.flow); self.assertTrue(self.window.busy)


if __name__ == '__main__': unittest.main()
