"""Small source-policy and retained-provenance regressions; no Native claims."""
import hashlib
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from . import driver, multipad_fixture as fixture


class SourceScope(unittest.TestCase):
    def test_named_multipad_task_preserves_all_source_bytes_and_locked_copper(self):
        raw = fixture.files()[fixture.STEM+'.kicad_pcb']
        task, record = driver.task_bytes(raw,'multipad-preserve-v1')
        self.assertEqual(task,raw)
        self.assertEqual(record['removed_routes'],[])
        self.assertFalse(record['original_mutated'])
        self.assertEqual(record['derived_board_sha256'],hashlib.sha256(raw).hexdigest())

    def test_unknown_scope_never_falls_back_to_unrouted_task(self):
        with self.assertRaises(ValueError):
            driver.task_bytes(fixture.files()[fixture.STEM+'.kicad_pcb'],'other')
        with self.assertRaises(AssertionError):
            driver.source_paths('other')

    def test_actual_changed_source_manifest_refuses_late_readback(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);path=root/'source.json';path.write_bytes(b'{"source":"original"}\n')
            module=SimpleNamespace(sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest())
            spec={'seed_manifest':path.name,'seed_manifest_sha256':module.sha(path)}
            with patch.object(driver,'ROOT',root):
                self.assertTrue(driver.source_manifest_unchanged(spec,module))
                path.write_bytes(b'{"source":"changed"}\n')
                self.assertFalse(driver.source_manifest_unchanged(spec,module))


if __name__=='__main__':
    unittest.main()
