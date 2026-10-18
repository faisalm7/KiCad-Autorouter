# Non-admitting, finite hosted-runner experiment. No installer or Native worker.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if (-not $IsWindows -or $env:GITHUB_ACTIONS -ne 'true' -or
    $env:RUNNER_ENVIRONMENT -ne 'github-hosted' -or
    $env:GITHUB_REPOSITORY -ne 'faisalm7/KiCad-Autorouter') {
    throw 'This diagnostic is restricted to the authorized standard hosted repository job.'
}
$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$ownedName = 'kicad-appcontainer007-' + [Guid]::NewGuid().ToString('N')
$scopePath = Join-Path $env:RUNNER_TEMP $ownedName
$reportPath = Join-Path $env:RUNNER_TEMP ($ownedName + '-report.json')
if ((Test-Path -LiteralPath $scopePath) -or (Test-Path -LiteralPath $reportPath)) {
    throw 'Fresh diagnostic destinations required.'
}
$pythonExe = (Get-Command python.exe -CommandType Application -ErrorAction Stop).Source
$clock = [Diagnostics.Stopwatch]::StartNew()
try {
    & $pythonExe -B (Join-Path $PSScriptRoot 'appcontainer_canary.py') --scope $scopePath --report $reportPath
    $code = $LASTEXITCODE
    if (-not (Test-Path -LiteralPath $reportPath)) { throw 'No canary receipt; no isolation or cleanup claim.' }
    $receipt = Get-Content -LiteralPath $reportPath -Raw | ConvertFrom-Json
    if ($code -ne 0 -or $receipt.passed -cne $true -or
        $receipt.Native_admitted -cne $false -or $receipt.Native_executed -cne $false -or
        $receipt.owned_server_thread_reaped -cne $true) {
        throw 'Non-admitting canary failed or cleanup is unknown; inspect retained job log.'
    }
} finally {
    $clock.Stop()
    @{ schema = 1; kind = 'Windows-AppContainer007-diagnostic-enclosure';
       wall_seconds_before_exit = $clock.Elapsed.TotalSeconds;
       whole_CPU_seconds = $null; Native_admitted = $false; artifacts_uploaded = 0;
       repo_source = $env:GITHUB_SHA; report_path = $reportPath;
       scope = 'Bounded canary only; SDK/compile, API/token/TCP/job costs are separate. No Windows routing support.' } |
        ConvertTo-Json -Compress | Write-Output
}
