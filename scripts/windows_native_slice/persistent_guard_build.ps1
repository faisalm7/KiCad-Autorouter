# Windows011 readiness only: no profile, guard arming, policy, sockets or Native.
param(
    [string]$Protocol = (Join-Path $PSScriptRoot 'persistent_guard_build_protocol.json'),
    [string]$ProtocolSha256 = $env:GUARD_EXPECTED_PROTOCOL_SHA,
    [string]$ExpectedSourceSha = $env:GUARD_EXPECTED_SOURCE_SHA
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$clock = [Diagnostics.Stopwatch]::StartNew()
if (-not $IsWindows -or $env:GITHUB_ACTIONS -ne 'true' -or
    $env:RUNNER_OS -ne 'Windows' -or $env:RUNNER_ENVIRONMENT -ne 'github-hosted' -or
    $env:GITHUB_REPOSITORY -ne 'faisalm7/KiCad-Autorouter') {
    throw 'This build readiness is restricted to the owned standard hosted Windows repository job.'
}
if ($ExpectedSourceSha -cnotmatch '^[0-9a-f]{40}$' -or $ProtocolSha256 -cnotmatch '^[0-9a-f]{64}$' -or
    $env:GITHUB_SHA -cne $ExpectedSourceSha) { throw 'Exact external source and protocol SHA inputs required.' }
$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$headPath = Join-Path $repoRoot '.git/HEAD'
if ((Get-Content -LiteralPath $headPath -Raw).Trim() -cne $ExpectedSourceSha) {
    throw 'Exact detached checkout HEAD required; no Git command or hooks are run.'
}
$Protocol = (Resolve-Path -LiteralPath $Protocol -ErrorAction Stop).Path
if ((Get-FileHash -LiteralPath $Protocol -Algorithm SHA256).Hash.ToLowerInvariant() -cne $ProtocolSha256) {
    throw 'Frozen protocol hash differs.'
}
$plan = Get-Content -LiteralPath $Protocol -Raw | ConvertFrom-Json
if ($plan.schema -ne 1 -or $plan.kind -cne 'windows011-build-null-ABI-readiness-v1' -or
    $plan.source_base_head -cne '580793ac6087021bf9567f764df5b9f55bfab9db') { throw 'Wrong frozen readiness protocol.' }
$expectedNames = @('persistent_guard_build.py', 'persistent_guard_build.ps1', 'persistent_sid_guard.c',
    'windows_process.py', 'appcontainer_canary.py', 'appcontainer_launch.py',
    'appcontainer_probe.c', 'appcontainer_dns.py', 'appcontainer_diagnostic.ps1') |
    ForEach-Object { 'scripts/windows_native_slice/' + $_ }
$keys = @($plan.source_files_sha256.PSObject.Properties.Name)
if ($keys.Count -ne 9 -or @(Compare-Object $keys $expectedNames).Count -ne 0) { throw 'Exact nine source pins required.' }
foreach ($name in $expectedNames) {
    $pin = $plan.source_files_sha256.PSObject.Properties[$name].Value
    if ($pin -cnotmatch '^[0-9a-f]{64}$' -or
        (Get-FileHash -LiteralPath (Join-Path $repoRoot $name) -Algorithm SHA256).Hash.ToLowerInvariant() -cne $pin) {
        throw ('Frozen source differs: ' + $name)
    }
}
$ownedName = 'kicad-appcontainer007-' + [Guid]::NewGuid().ToString('N')
$scopePath = Join-Path $env:RUNNER_TEMP $ownedName
$reportPath = Join-Path $env:RUNNER_TEMP ($ownedName + '-build-report.json')
foreach ($path in @($scopePath, ($scopePath + '-setup'), $reportPath)) {
    if (Test-Path -LiteralPath $path) { throw 'Fresh exclusive readiness destinations required.' }
}
$pythonExe = (Get-Command python.exe -CommandType Application -ErrorAction Stop).Source
$start = [Diagnostics.ProcessStartInfo]::new()
$start.FileName = $pythonExe
$start.UseShellExecute = $false
$start.RedirectStandardOutput = $true
$start.RedirectStandardError = $true
$start.StandardOutputEncoding = [Text.UTF8Encoding]::new($false)
$start.StandardErrorEncoding = [Text.UTF8Encoding]::new($false)
$start.Environment['PYTHONDONTWRITEBYTECODE'] = '1'
$start.Environment['PYTHONNOUSERSITE'] = '1'
$start.Environment['PYTHONIOENCODING'] = 'utf-8'
foreach ($value in @('-B', (Join-Path $PSScriptRoot 'persistent_guard_build.py'), '--protocol', $Protocol,
    '--protocol-sha256', $ProtocolSha256, '--expected-source-sha', $ExpectedSourceSha,
    '--scope', $scopePath, '--report', $reportPath)) { $start.ArgumentList.Add($value) }
$process = [Diagnostics.Process]::new()
$process.StartInfo = $start
$started = $false
$timedOut = $false
$reaped = $false
$passed = $false
$code = $null
try {
    if (-not $process.Start()) { throw 'Readiness controller did not start.' }
    $started = $true
    $stdout = $process.StandardOutput.ReadToEndAsync()
    $stderr = $process.StandardError.ReadToEndAsync()
    # Keep ten seconds inside the three-minute enclosure for exact-owned tree
    # termination and bounded output retrieval. Never infer compiler cleanup
    # merely because the controller exits or Kill(true) returned.
    $waitMs = [int][Math]::Floor(170000 - $clock.Elapsed.TotalMilliseconds)
    if ($waitMs -le 0 -or -not $process.WaitForExit($waitMs)) {
        $timedOut = $true
        $process.Kill($true)
        $reaped = $process.WaitForExit(8000)
        throw 'Readiness controller exceeded the bounded enclosure; cleanup remains unqualified.'
    }
    $reaped = $true
    $code = $process.ExitCode
    if (-not $stdout.Wait(1000) -or -not $stderr.Wait(1000)) { throw 'Bounded controller output retrieval failed.' }
    if ($stdout.Result.Length -gt 1048576 -or $stderr.Result.Length -gt 65536) { throw 'Readiness output bound exceeded.' }
    Write-Output $stdout.Result
    if ($stderr.Result.Length -gt 0) { Write-Output $stderr.Result }
    if (-not (Test-Path -LiteralPath $reportPath) -or (Get-Item -LiteralPath $reportPath).Length -gt 262144) {
        throw 'Missing or oversized readiness report.'
    }
    $receipt = Get-Content -LiteralPath $reportPath -Raw | ConvertFrom-Json
    if ($code -ne 0 -or $receipt.passed -cne $true -or
        $receipt.actual_policy_operations -cne $false -or $receipt.actual_profile_operations -cne $false -or
        $receipt.Native_admitted -cne $false -or $receipt.Native_executed -cne $false -or
        $receipt.Windows_support -cne $false -or $receipt.NULL_ABI.passed -cne $true) {
        throw 'DLL build/NULL ABI readiness failed; no policy or Windows support claim.'
    }
    $passed = $true
} finally {
    if ($started -and -not $reaped) {
        try { $process.Kill($true); $reaped = $process.WaitForExit(1000) } catch { $reaped = $false }
    }
    $controllerCPU = if ($started -and $reaped) { $process.TotalProcessorTime.TotalSeconds } else { $null }
    $clock.Stop()
    @{ schema = 1; kind = 'Windows011-build-null-ABI-enclosure'; passed = $passed;
       wall_seconds_before_exit = $clock.Elapsed.TotalSeconds; controller_process_CPU_seconds = $controllerCPU;
       whole_external_CPU_seconds = $null; timed_out = $timedOut; controller_reaped = $reaped;
       compiler_cleanup_inferred_from_controller_exit = $false; actual_policy_operations = $false;
       Native_admitted = $false; Windows_support = $false; artifacts_uploaded = 0;
       expected_source_sha = $ExpectedSourceSha; expected_protocol_sha256 = $ProtocolSha256;
       report_path = $reportPath; setup_path = ($scopePath + '-setup');
       scope = 'Fixed SDK DLL/NULL ABI readiness only; setup and compiler Job costs remain separate. No profile, WFP policy, socket, Native or isolation test.' } |
        ConvertTo-Json -Compress | Write-Output
    $process.Dispose()
}
