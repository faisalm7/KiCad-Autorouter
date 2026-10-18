"""Cheap source-boundary controls only; this does not execute or qualify Windows."""
from pathlib import Path
import re
import unittest

REPO = Path(__file__).resolve().parents[1]
SOURCE = REPO / 'scripts/windows_native_slice/isolation_diagnostic.ps1'


class WindowsIsolationDiagnosticSource(unittest.TestCase):
    def test_mode_is_manual_bounded_and_separate_from_native(self):
        workflow = (REPO / '.github/workflows/manual-python-controls.yml').read_text()
        self.assertIn('          - windows-isolation\n', workflow)
        job = workflow.split('  windows-isolation:\n', 1)[1]
        self.assertIn("github.event.inputs.probe == 'windows-isolation'", job)
        self.assertIn('runs-on: windows-2022', job)
        self.assertIn('timeout-minutes: 3', job)
        self.assertIn('actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1', job)
        self.assertIn('ref: ${{ github.sha }}', job)
        self.assertIn('persist-credentials: false', job)
        self.assertIn('contents: read', workflow)
        self.assertNotRegex(job, r'(?i)upload-artifact|actions/cache|bootstrap\.ps1|windows_toolchain_probe')
        self.assertEqual(re.findall(r'^on:$', workflow, flags=re.M), ['on:'])
        self.assertNotRegex(workflow, re.compile(r'^  (push|pull_request|schedule):', re.M))

    def test_only_owned_powershell_is_launched_and_no_acquisition_path_exists(self):
        source = SOURCE.read_text()
        self.assertEqual(re.findall(r'Start-Process -FilePath (\$\w+)', source), ['$powershell'])
        self.assertNotRegex(source, r'(?i)Invoke-WebRequest|Invoke-RestMethod|HttpClient|\bFetch\b|Set-NetFirewall|Disable-NetFirewall|Enable-NetFirewall')
        self.assertIn("Join-Path $env:SystemRoot 'System32/cmd.exe'", source)
        self.assertIn("$signature.Status -ne 'Valid'", source)
        self.assertIn('O=Microsoft Corporation', source)
        self.assertIn('system_executable_executed=$false', source)
        self.assertIn('product_windows_support=$false;admission=$false', source)

    def test_exact_two_owned_deny_rules_and_independent_cleanup_queries(self):
        source = SOURCE.read_text()
        self.assertIn("foreach($direction in @('Inbound','Outbound'))", source)
        self.assertEqual(source.count('New-NetFirewallRule '), 1)
        self.assertIn('-Action Block -Enabled True -Profile Any -AsJob', source)
        self.assertIn('foreach($name in $owned)', source)
        self.assertIn('Remove-NetFirewallRule -Name $name -AsJob', source)
        self.assertIn('@(Read-OwnedRule $name).Count -eq 0', source)
        self.assertIn("@(Read-OwnedRule $name 'PersistentStore').Count -eq 0", source)
        self.assertIn('persistent_store_absence_observed=$persistentAbsent', source)
        self.assertIn("@(Read-OwnedRule $name 'PersistentStore').Count -ne 0", source)
        self.assertIn('if($scratchCreated){try{Remove-Item', source)

    def test_external_limits_and_bound_log_readback_remain_explicit(self):
        source = SOURCE.read_text()
        self.assertIn("'test_firewall_gate.ps1') @() 'mocked-controls' 20", source)
        self.assertIn("'gate' 12", source)
        self.assertIn('Wait-Job -Job $job -Timeout 5', source)
        self.assertIn('[Math]::Min(16384,$length)', source)
        self.assertIn('log_enforcement=\'Polling plus bounded readback, not an OS disk quota\'', source)
        self.assertIn('$child.Kill($true)', source)
        self.assertIn('$child.WaitForExit(3000)', source)

    def test_mock_controls_precede_live_rules_and_dispatch_identity_is_checked(self):
        source = SOURCE.read_text()
        self.assertLess(source.index("'mocked-controls' 20"), source.index("foreach($direction in @('Inbound','Outbound'))"))
        self.assertIn("$env:RUNNER_ENVIRONMENT -cne 'github-hosted'", source)
        self.assertIn('$head -cne $env:GITHUB_SHA', source)
        self.assertIn('Diagnostic source changed', source)
        self.assertIn('$record.gate.exit_code -ne 1', source)
        self.assertIn('Complete expected refusal/dual-rule snapshot unavailable; no admission', source)


if __name__ == '__main__':
    unittest.main()
