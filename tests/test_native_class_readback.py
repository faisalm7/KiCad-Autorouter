"""Class-map presence controls; native routing proof is recorded separately."""
from pathlib import Path
import tempfile
import unittest
from unittest import mock
from autorouter import pipeline as p
from experiments.native_paired_v1.readback import native_class_readback


class NativeClassReadback(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.folder = Path(self.tmp.name)
        self.board = Path(__file__).resolve().parents[1]/'fixtures/smoke/smoke.kicad_pcb'

    def test_actual_default_project_needs_no_explicit_class_map(self):
        self.assertIsNone(p.netclass_policy(self.board))
        self.assertEqual(native_class_readback(self.folder, {}, self.board, []), (None, False))

    def test_default_project_cannot_silently_ignore_unexpected_class_map(self):
        (self.folder/'final-netclasses.json').write_text('{}')
        with self.assertRaisesRegex(p.Rejected, 'unexpected class map'):
            native_class_readback(self.folder, {}, self.board, [])

    def test_required_policy_without_map_cannot_use_default_fallback(self):
        with mock.patch.object(p, 'netclass_policy', return_value={'policy':'explicit-required-control'}):
            with self.assertRaises(FileNotFoundError):
                native_class_readback(self.folder, {}, self.board, [])
