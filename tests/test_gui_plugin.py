"""Owned plugin preparation; actual KiCad registration remains a Native gate."""
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
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
            self.assertIn('--from-toolbar',launcher.read_text())
            self.assertIn('unset PYTHONPATH PYTHONHOME',launcher.read_text())
            self.assertEqual(subprocess.run(['/bin/sh','-n',str(launcher)],capture_output=True,timeout=5).returncode,0)
            with self.assertRaises(ValueError):g.prepare(root/'documents')
    def test_missing_controller_or_linked_destination_refuses(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve()
            with patch.object(g.c,'ROOT',root):
                with self.assertRaisesRegex(ValueError,'controller'):g.prepare(root/'documents')
            (root/'alias').symlink_to(root,target_is_directory=True)
            with self.assertRaises(Exception):g.prepare(root/'alias/new')

    def test_toolbar_uses_only_its_local_socket_and_the_exact_document(self):
        with tempfile.TemporaryDirectory() as tmp, socket.socket(socket.AF_UNIX) as listener:
            root = Path(tmp).resolve()
            endpoint = root/'editor.sock'; listener.bind(str(endpoint))
            board = root/'Saved board.kicad_pcb'
            for suffix in ('.kicad_pcb', '.kicad_pro', '.kicad_sch'):
                board.with_suffix(suffix).write_text('fixture')
            document = SimpleNamespace(type=1, board_filename=board.name,
                                       project=SimpleNamespace(path=str(root), name=board.stem))
            client = Mock(return_value=Mock(get_open_documents=Mock(return_value=[document])))
            modules = {'kipy':SimpleNamespace(KiCad=client),
                       'kipy.proto.common.types':SimpleNamespace(DocumentType=SimpleNamespace(DOCTYPE_PCB=1))}
            with patch.dict(sys.modules, modules):
                self.assertEqual(g.toolbar_board('ipc://' + str(endpoint), 'local-session'), board)
                client.assert_called_once_with(socket_path='ipc://' + str(endpoint), kicad_token='local-session', timeout_ms=1500)
                client.return_value.get_open_documents.assert_called_once_with(1)
                client.return_value.get_open_documents.return_value = [document, document]
                with self.assertRaisesRegex(ValueError, 'one PCB'):
                    g.toolbar_board(str(endpoint), 'local-session')
                client.return_value.get_open_documents.return_value = [document]
                document.project.name = 'Different project'
                with self.assertRaisesRegex(ValueError, 'identities differ'):
                    g.toolbar_board(str(endpoint), 'local-session')
                client.reset_mock()
                for uri, token in (('tcp://localhost:1234', 'test'), (str(endpoint), ''), (str(board), 'test')):
                    with self.subTest(uri=uri), self.assertRaises(ValueError):
                        g.toolbar_board(uri, token)
                client.assert_not_called()

    def test_toolbar_fallback_and_handoff_never_pass_editor_session_to_gui(self):
        board = Path('/owned/source/board.kicad_pcb')
        for success in (True, False):
            read = Mock(return_value=board, side_effect=None if success else ValueError('private failure'))
            with self.subTest(success=success), patch.object(g, 'toolbar_board', read), \
                 patch.dict(os.environ, KICAD_API_SOCKET='editor', KICAD_API_TOKEN='private'), \
                 patch.object(g.os, 'chdir'), patch.object(g.os, 'execve') as execute:
                g.launch_toolbar()
            read.assert_called_once_with('editor', 'private')
            _, args, environment = execute.call_args.args
            self.assertEqual(args[4:], ['--toolbar-project', str(board.with_suffix('.kicad_pro'))]
                             if success else ['--toolbar-unavailable'])
            self.assertNotIn('KICAD_API_SOCKET', environment)
            self.assertNotIn('KICAD_API_TOKEN', environment)
if __name__=='__main__':unittest.main()
