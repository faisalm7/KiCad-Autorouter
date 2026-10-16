"""Portable preparation/launch seams; no real KiCad/GUI is launched here."""
import json
import os
from pathlib import Path
import shlex
import tempfile
import subprocess
import sys
import unittest
from unittest.mock import patch

from scripts import install_gui as g


class GuiInstallerTests(unittest.TestCase):
    def test_actual_cli_refusal_is_a_nonzero_exit(self):
        result = subprocess.run([sys.executable, '-B', str(Path(g.__file__)), '--launch', 'not-install.json'],
                                capture_output=True, timeout=5)
        self.assertEqual(result.returncode, 2)
        self.assertIn(b'Launcher refused:', result.stderr)

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.checkout = self.root / "checkout with spaces ' $(literal)"; self.checkout.mkdir()
        for relative in ('autorouter/gui.py', 'scripts/install_gui.py', 'scripts/prepare_gui_plugin.py', '.venv/bin/python'):
            path = self.checkout / relative; path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('# owned test input\n'); path.chmod(0o700)
        self.apps = self.root / 'Existing KiCad'; self.apps.mkdir()
        self.manager = self.apps / 'kicad'; self.manager.write_bytes(b'owned manager fixture'); self.manager.chmod(0o700)
        for change in (patch.object(g.c, 'ROOT', self.checkout), patch.object(g.c, 'PYTHON', Path('/bin/sh')),
                       patch.object(g.c, 'CLI', self.apps / 'kicad-cli'),
                       patch.object(g.p, 'tool_manifest', return_value={'git_head': 'owned', 'files': {}}),
                       patch.object(g, 'require_closed_kicad')):
            change.start(); self.addCleanup(change.stop)
        self.output = self.root / 'local launcher'

    def prepare(self):
        return g.prepare(self.output)

    def rewrite(self, mutate):
        path = self.output / 'install.json'; record = json.loads(path.read_text()); mutate(record)
        path.write_text(json.dumps(record))

    def test_fresh_owned_layout_quoted_command_and_isolated_initial_config(self):
        record = self.prepare()
        self.assertFalse(record['installed_globally']); self.assertFalse(record['standalone'])
        self.assertEqual(set(record['immutable_files']), g.IMMUTABLE_FILES)
        launcher = self.output / 'Launch Autorouter.command'
        self.assertTrue(os.access(launcher, os.X_OK))
        command = shlex.split(launcher.read_text().splitlines()[-1])
        self.assertEqual(command, ['exec', str(self.checkout / '.venv/bin/python'), '-B',
            str(self.checkout / 'scripts/install_gui.py'), '--launch', str(self.output / 'install.json')])
        common = json.loads((self.output / 'config/10.0/kicad_common.json').read_text())
        self.assertTrue(common['api']['enable_server']); self.assertFalse(common['system']['enable_sentry_reporting'])
        manager = json.loads((self.output / 'config/10.0/kicad.json').read_text())
        self.assertFalse(manager['system']['check_for_kicad_updates']); self.assertFalse(manager['pcm']['check_for_updates'])
        self.assertTrue((self.output / g.PLUGIN / 'plugin.json').is_file())

    def test_existing_or_symlink_destination_never_overwrites(self):
        self.prepare(); initial = (self.output / 'install.json').read_bytes()
        with self.assertRaises(ValueError): self.prepare()
        self.assertEqual((self.output / 'install.json').read_bytes(), initial)
        alias = self.root / 'alias'; alias.symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(Exception): g.prepare(alias / 'new')
        self.assertFalse((self.root / 'new').exists())

    def test_launch_checks_and_passes_exact_scoped_environment_without_child(self):
        self.prepare()
        # Config is intentionally user-editable after first launch, not restored.
        (self.output / 'config/10.0/kicad.json').write_text('{"owned_user_change":true}')
        with patch.dict(os.environ, dict(KICAD_API_TOKEN='private', KICAD_API_SOCKET='private',
                PYTHONPATH='bad', PYTHONHOME='bad')), patch.object(g.os, 'chdir') as cwd, patch.object(g.os, 'execve') as execute:
            g.launch(self.output / 'install.json')
        cwd.assert_called_once_with(self.checkout)
        executable, argv, env = execute.call_args.args
        self.assertEqual(executable, self.manager); self.assertEqual(argv, [str(self.manager)])
        for key, folder in [('KICAD_CONFIG_HOME','config'), ('KICAD_DOCUMENTS_HOME','documents'), ('KICAD_CACHE_HOME','cache')]:
            self.assertEqual(env[key], str(self.output / folder))
        for key in ('KICAD_API_TOKEN', 'KICAD_API_SOCKET', 'PYTHONPATH', 'PYTHONHOME'): self.assertNotIn(key, env)

    def test_changed_manager_plugin_or_dropped_population_refuses_before_exec(self):
        self.prepare()
        targets = [self.manager, self.output / g.PLUGIN / 'launch-autorouter']
        for target in targets:
            with self.subTest(target=target), patch.object(g.os, 'execve') as execute:
                before = target.read_bytes(); target.write_bytes(b'changed')
                with self.assertRaises(ValueError): g.launch(self.output / 'install.json')
                execute.assert_not_called(); target.write_bytes(before)
        self.rewrite(lambda record: record['immutable_files'].pop(g.PLUGIN + 'launch-autorouter'))
        with patch.object(g.os, 'execve') as execute:
            with self.assertRaises(ValueError): g.launch(self.output / 'install.json')
            execute.assert_not_called()

    def test_source_or_home_escape_refuses_before_exec(self):
        self.prepare()
        for key in ('checkout', 'config_home', 'documents_home', 'cache_home'):
            with self.subTest(key=key), patch.object(g.os, 'execve') as execute:
                path = self.output / 'install.json'; before = path.read_bytes()
                self.rewrite(lambda record: record.update({key: str(self.root)}))
                with self.assertRaises(ValueError): g.launch(path)
                execute.assert_not_called(); path.write_bytes(before)
        with patch.object(g.p, 'tool_manifest', return_value={'git_head':'changed'}), patch.object(g.os, 'execve') as execute:
            with self.assertRaises(ValueError): g.launch(self.output / 'install.json')
            execute.assert_not_called()


    def test_preexisting_live_config_file_directory_and_hardlink_aliases_refuse(self):
        self.prepare()
        outside = self.root / 'outside'; outside.mkdir()
        external = outside / 'global.json'; external.write_bytes(b'owned outside fixture')
        folder = self.output / 'config/10.0'
        backup = folder.with_name('10.0-retained'); folder.rename(backup)
        folder.symlink_to(outside, target_is_directory=True)
        with patch.object(g.os, 'execve') as execute:
            with self.assertRaises(Exception): g.launch(self.output / 'install.json')
            execute.assert_not_called()
        folder.unlink(); backup.rename(folder)
        target = folder / 'kicad_common.json'; original = target.read_bytes(); target.unlink()
        for alias in ('symlink','hardlink'):
            with self.subTest(alias=alias), patch.object(g.os, 'execve') as execute:
                if alias == 'symlink': target.symlink_to(external)
                else: os.link(external,target)
                with self.assertRaises(Exception): g.launch(self.output / 'install.json')
                execute.assert_not_called(); target.unlink()
        target.write_bytes(original)
        self.assertEqual(external.read_bytes(),b'owned outside fixture')


class InstancePreconditionTests(unittest.TestCase):
    def test_closed_existing_error_and_malformed_results(self):
        from types import SimpleNamespace
        for code, data, allowed in [(1,b'',True),(0,b'123\n456\n',False),(2,b'',False),(0,b'not-a-pid',False),(1,b'123',False)]:
            with self.subTest(code=code,data=data), patch.object(g.subprocess,'run',return_value=SimpleNamespace(returncode=code,stdout=data,stderr=b'')) as run:
                if allowed: g.require_closed_kicad()
                else:
                    with self.assertRaises(ValueError): g.require_closed_kicad()
                self.assertEqual(run.call_args.kwargs['timeout'],3)
                self.assertFalse(run.call_args.kwargs['check'])
        with patch.object(g.subprocess,'run',side_effect=g.subprocess.TimeoutExpired('owned',3)):
            with self.assertRaises(ValueError): g.require_closed_kicad()


if __name__ == '__main__': unittest.main()
