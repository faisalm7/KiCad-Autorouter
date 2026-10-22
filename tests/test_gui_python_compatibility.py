"""Real selected KiCad Python import smoke; no GUI interaction qualification."""
import json
import subprocess
import unittest

from autorouter import config as c, gui


class GuiPythonCompatibility(unittest.TestCase):
    @unittest.skipUnless(c.PYTHON.is_file(), 'Selected KiCad Python unavailable; GUI startup unqualified')
    def test_actual_GUI_interpreter_imports_entrypoint_and_wx(self):
        # AST parsing accepts a Python3.10 type union even on3.9; only evaluating
        # the real imports catches that demonstrated toolbar-startup blocker.
        program = ('import sys,json; import autorouter.gui,autorouter.pipeline,'
                   'autorouter.strategy,autorouter.review_export; import wx; '
                   'print(json.dumps(dict(python=list(sys.version_info[:3]),'
                   'entrypoint=autorouter.gui.__file__,wx=wx.version())))')
        result = subprocess.run([str(c.PYTHON), '-B', '-c', program], cwd=c.ROOT,
            env=gui.child_environment(), capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr[:4096])
        self.assertLess(len(result.stdout), 4096)
        value = json.loads(result.stdout)
        self.assertEqual(value['entrypoint'], str(c.ROOT / 'autorouter/gui.py'))
        self.assertIsInstance(value['python'], list)
        self.assertIsInstance(value['wx'], str)
        self.assertTrue(value['wx'])


if __name__ == '__main__':
    unittest.main()
