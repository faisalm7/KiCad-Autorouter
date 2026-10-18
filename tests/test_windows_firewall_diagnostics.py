"""Source/refusal preservation and optional mocked PowerShell controls, not Windows proof."""
import hashlib
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1] / 'scripts/windows_native_slice'


class WindowsFirewallDiagnostics(unittest.TestCase):
    def test_original_gate_bytes_are_preserved_apart_from_diagnostic_insertions(self):
        source = (ROOT / 'firewall_gate.ps1').read_text()
        before, diagnostic_and_after = source.split('# Diagnostics never supply an admission decision.', 1)
        _, after = diagnostic_and_after.split('$observations=@()', 1)
        original = before + '$observations=@()' + after
        original = original.replace('  [Console]::Error.WriteLine((Get-FirewallDiagnostic))\n', '')
        original = original.replace('{[Console]::Error.WriteLine((Get-FirewallDiagnostic));throw', '{throw')
        # actual005's retained source pin: all prechecks, rule predicates, universal
        # filters, unconditional throws and original success payload remain exact.
        self.assertEqual(hashlib.sha256(original.encode()).hexdigest(),
                         'beb4e9479af0138ea9c1772cfdbaaaf51a90b18188d094dcf60281f51b9cf88f')
        self.assertNotIn('verified_active_', diagnostic_and_after.split('$observations=@()', 1)[0])
        self.assertEqual(source.count('Get-FirewallDiagnostic'), 3)  # Definition and two refusal-only calls.

    @unittest.skipUnless(shutil.which('pwsh'), 'PowerShell absent; mocked script execution remains unrun')
    def test_mocked_powershell_refusal_and_snapshot_structure(self):
        result = subprocess.run([shutil.which('pwsh'), '-NoProfile', '-NonInteractive',
                                 '-File', str(ROOT / 'test_firewall_gate.ps1')],
                                capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('no Windows network-denial qualification', result.stdout)


if __name__ == '__main__':
    unittest.main()
