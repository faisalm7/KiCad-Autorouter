"""Owned plugin preparation; actual KiCad registration remains a Native gate."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from scripts import prepare_gui_plugin as g

class PluginPreparationTests(unittest.TestCase):
    def test_exec_plugin_is_project_scoped_and_shell_quotes_checkout(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();checkout=root/"checkout with spaces and ' quote $(literal)";checkout.mkdir()
            (checkout/'autorouter').mkdir();(checkout/'autorouter/gui.py').write_text('# authored')
            with patch.object(g.c,'ROOT',checkout),patch.object(g.c,'PYTHON',Path('/bin/sh')):
                result=g.prepare(root/'documents')
            plugin=Path(result['plugin']);self.assertEqual(plugin.parent,root/'documents/KiCad/10.0/plugins');manifest=json.loads((plugin/'plugin.json').read_bytes())
            self.assertEqual(manifest['runtime'],{'type':'exec'})
            self.assertEqual(manifest['actions'][0]['scopes'],['pcb'])
            self.assertFalse(result['installed_globally'])
            for theme in ('icons-light','icons-dark'):
                for name in manifest['actions'][0][theme]:
                    self.assertTrue((plugin/name).read_bytes().startswith(b'\x89PNG\r\n\x1a\n'))
            launcher=plugin/'launch-autorouter';self.assertTrue(os.access(launcher,os.X_OK))
            self.assertIn('unset KICAD_API_SOCKET KICAD_API_TOKEN',launcher.read_text())
            self.assertEqual(subprocess.run(['/bin/sh','-n',str(launcher)],capture_output=True,timeout=5).returncode,0)
            with self.assertRaises(ValueError):g.prepare(root/'documents')
    def test_missing_controller_or_linked_destination_refuses(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve()
            with patch.object(g.c,'ROOT',root):
                with self.assertRaisesRegex(ValueError,'controller'):g.prepare(root/'documents')
            (root/'alias').symlink_to(root,target_is_directory=True)
            with self.assertRaises(Exception):g.prepare(root/'alias/new')
if __name__=='__main__':unittest.main()
