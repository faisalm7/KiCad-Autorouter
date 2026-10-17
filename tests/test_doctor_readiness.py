"""Authored doctor readiness controls; no executable, permission or Native work."""
import subprocess
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from autorouter import __main__ as cli, pipeline as p


class DoctorReadinessTests(unittest.TestCase):
    JAVA_BANNER = 'openjdk version "25.0.2"\nOpenJDK Runtime Environment'

    def probe(self, *, java=None, native_failure=None):
        """All identities, file reads, platform checks and processes are mocked."""
        identity = {'kind': 'owned-doctor-test', 'git_head': 'a' * 40}
        paths = {cli.c.CLI, cli.c.PYTHON, cli.c.JAVA, cli.c.JAR}
        hashes = {path: 'b' * 64 for path in paths}
        hashes[cli.c.JAR] = cli.c.JAR_SHA256
        argv = {
            'kicad_version': (str(cli.c.CLI), 'version'),
            'pcbnew_version': (str(cli.c.PYTHON), '-c',
                               'import pcbnew; print(pcbnew.GetBuildVersion())'),
            'java_version': (str(cli.c.JAVA), '-version'),
        }
        outputs = {
            argv['kicad_version']: SimpleNamespace(returncode=0, stdout='10.0.0', stderr=''),
            argv['pcbnew_version']: SimpleNamespace(returncode=0, stdout='10.0.0', stderr=''),
            argv['java_version']: (java if java is not None else
                                  SimpleNamespace(returncode=0, stdout='', stderr=self.JAVA_BANNER)),
        }
        if native_failure is not None:
            self.assertIn(native_failure, ('kicad_version', 'pcbnew_version'))
            outputs[argv[native_failure]] = SimpleNamespace(
                returncode=1, stdout='10.0.0', stderr='')

        def run(actual, **kwargs):
            self.assertEqual(kwargs, {'capture_output': True, 'text': True, 'timeout': 15})
            key = tuple(actual)
            self.assertIn(key, outputs, 'Unexpected tool invocation in pure doctor control')
            value = outputs[key]
            if isinstance(value, BaseException):
                raise value
            return value

        def which(name):
            self.assertEqual(name, 'sandbox-exec')
            return '/usr/bin/sandbox-exec'

        with mock.patch.object(p, 'tool_manifest', return_value={'source_provenance': identity}), \
                mock.patch.object(Path, 'is_file', autospec=True,
                                  side_effect=lambda path: path in paths), \
                mock.patch.object(cli, 'sha', side_effect=lambda path: hashes[path]), \
                mock.patch.object(cli.platform, 'system', return_value='Darwin'), \
                mock.patch.object(cli.platform, 'platform', return_value='owned-test-host'), \
                mock.patch.object(cli.shutil, 'which', side_effect=which), \
                mock.patch.object(cli.subprocess, 'run', side_effect=run) as execute:
            result = cli.doctor()

        self.assertEqual(execute.call_args_list, [
            mock.call(list(argv[name]), capture_output=True, text=True, timeout=15)
            for name in ('kicad_version', 'pcbnew_version', 'java_version')
        ])
        self.assertTrue(result['checks']['runtime_provenance']['verified'])
        return result

    def test_healthy_pinned_tools_accept_stderr_openjdk_version(self):
        result = self.probe()
        self.assertIs(result['ready'], True)
        self.assertEqual(result['checks']['java_version'],
                         {'exit': 0, 'output': self.JAVA_BANNER})

    def test_java_permission_error_is_not_ready(self):
        result = self.probe(java=PermissionError('owned mock: Java is not executable'))
        self.assertIs(result['ready'], False)
        self.assertIn('Java is not executable', result['checks']['java_version']['error'])

    def test_java_timeout_is_not_ready(self):
        result = self.probe(java=subprocess.TimeoutExpired(
            [str(cli.c.JAVA), '-version'], timeout=15))
        self.assertIs(result['ready'], False)
        self.assertIn('error', result['checks']['java_version'])

    def test_java_nonzero_with_valid_banner_is_not_ready(self):
        result = self.probe(java=SimpleNamespace(
            returncode=1, stdout='', stderr=self.JAVA_BANNER))
        self.assertIs(result['ready'], False)
        self.assertEqual(result['checks']['java_version']['exit'], 1)

    def test_java_empty_success_is_not_ready(self):
        result = self.probe(java=SimpleNamespace(returncode=0, stdout='', stderr=''))
        self.assertIs(result['ready'], False)
        self.assertEqual(result['checks']['java_version']['output'], '')

    def test_java_unrecognized_success_banner_is_not_ready(self):
        result = self.probe(java=SimpleNamespace(
            returncode=0, stdout='Java platform available', stderr=''))
        self.assertIs(result['ready'], False)
        self.assertEqual(result['checks']['java_version']['output'], 'Java platform available')

    def test_kicad_nonzero_with_expected_version_is_not_ready(self):
        result = self.probe(native_failure='kicad_version')
        self.assertIs(result['ready'], False)
        self.assertEqual(result['checks']['kicad_version'], {'exit': 1, 'output': '10.0.0'})

    def test_pcbnew_nonzero_with_expected_version_is_not_ready(self):
        result = self.probe(native_failure='pcbnew_version')
        self.assertIs(result['ready'], False)
        self.assertEqual(result['checks']['pcbnew_version'], {'exit': 1, 'output': '10.0.0'})


if __name__ == '__main__':
    unittest.main()
