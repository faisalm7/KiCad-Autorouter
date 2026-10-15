"""Owned cancellation observer routing only; no Native or process is launched."""
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from scripts import native_cancellation as control
from scripts import native_cancellation as runner

class CancellationMetadataControls(unittest.TestCase):
    def test_mac_routes_only_owned_selector_to_shared_reader_without_ps(self):
        row={'pid':42,'ppid':41,'pgid':42}
        with patch.object(control.sys,'platform','darwin'),patch.object(runner,'owned_process_metadata',return_value=[row]) as read,patch.object(control.subprocess,'run',side_effect=AssertionError('no ps launch')):
            self.assertEqual(control.process_metadata(parent_pid=41),[row]);read.assert_called_with(parent_pid=41,pgid=None)
            self.assertEqual(control.process_metadata(pgid=42),[row]);read.assert_called_with(parent_pid=None,pgid=42)

    def test_missing_mixed_boolean_and_nonpositive_selectors_refuse(self):
        for args in ({},{'parent_pid':True},{'pgid':0},{'pgid':-1},{'parent_pid':41,'pgid':42}):
            with self.subTest(args=args),patch.object(control.subprocess,'run',side_effect=AssertionError('no subprocess')):
                with self.assertRaises(ValueError):control.process_metadata(**args)

    def test_existing_other_posix_observer_filters_its_selector(self):
        fake=SimpleNamespace(stdout='42 41 42\n77 76 77\n')
        with patch.object(control.sys,'platform','linux'),patch.object(control.subprocess,'run',return_value=fake):
            self.assertEqual(control.process_metadata(parent_pid=41),[{'pid':42,'ppid':41,'pgid':42}])
            self.assertEqual(control.process_metadata(pgid=77),[{'pid':77,'ppid':76,'pgid':77}])
