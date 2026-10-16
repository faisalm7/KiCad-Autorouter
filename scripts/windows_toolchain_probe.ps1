# First-stage identity acquisition only. Never install or execute downloaded code.
# Source: https://www.kicad.org/download/windows/ (retrieved 2026-10-16 UTC).
# Official signature fields: KICAD SERVICES CORPORATION;
# GlobalSign GCC R45 EV CodeSigning CA 2020; serial39df6b588d969ca15d8d2756.
# No artifacts/cache, credentials, native routing, support or timing gain claim.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if (-not $IsWindows) { throw 'This metadata-only probe requires Windows PowerShell 7.' }
$started = [System.Diagnostics.Stopwatch]::StartNew()
$url = 'https://kicad-downloads.s3.cern.ch/windows/stable/kicad-10.0.7-x86_64.exe'
$expectedBytes = [long]968953784
$maxBytes = [long]1000000000
$expectedSigner = 'KICAD SERVICES CORPORATION'
$expectedIssuer = 'GlobalSign GCC R45 EV CodeSigning CA 2020'
$expectedSerial = '39DF6B588D969CA15D8D2756'
$tempRoot = [IO.Path]::GetFullPath($env:RUNNER_TEMP)
$scratch = Join-Path $tempRoot ('kicad-metadata-' + [Guid]::NewGuid().ToString('N'))
$installer = Join-Path $scratch 'kicad-10.0.7-x86_64.exe'
$handler = $null; $client = $null; $response = $null; $incoming = $null; $outgoing = $null; $cancel = $null
$record = [ordered]@{
    schema = 1; kind = 'windows-official-installer-metadata-only'; passed = $false
    source_head = $env:GITHUB_SHA; script_sha256 = (Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash.ToLowerInvariant()
    expected_version_label = '10.0.7'; url = $url; expected_bytes = $expectedBytes
    expected_signer_common_name = $expectedSigner; expected_issuer_common_name = $expectedIssuer; expected_serial = $expectedSerial
    downloaded_bytes = [long]0; installer_executed = $false; installed = $false
    native_executed = $false; runtime_version_observed = $false; product_support_qualified = $false
    prospective_sha256_only = $true; artifact_upload = $false; cache_upload = $false
    scope = 'Metadata acquisition only. A separate reviewed SHA-pinned install/native probe is still required.'
}
try {
    $actualHead = (& git -C $env:GITHUB_WORKSPACE -c core.fsmonitor=false -c core.hooksPath=/dev/null rev-parse HEAD).Trim()
    if ($LASTEXITCODE -ne 0 -or $actualHead -cne $env:GITHUB_SHA -or $actualHead -notmatch '^[0-9a-f]{40}$') { throw 'Actual checkout does not match dispatched source SHA.' }
    $record['workflow_sha256'] = (Get-FileHash -LiteralPath (Join-Path $env:GITHUB_WORKSPACE '.github/workflows/manual-python-controls.yml') -Algorithm SHA256).Hash.ToLowerInvariant()
    if (-not (Test-Path -LiteralPath $tempRoot -PathType Container)) { throw 'Owned runner temp root missing.' }
    if (Test-Path -LiteralPath $scratch) { throw 'Fresh exclusive metadata scratch required.' }
    $disk = [IO.DriveInfo]::new([IO.Path]::GetPathRoot($tempRoot))
    $record['disk_free_before_bytes'] = $disk.AvailableFreeSpace
    if ($disk.AvailableFreeSpace -lt 3GB) { throw 'Insufficient space for bounded metadata download.' }
    $null = New-Item -ItemType Directory -Path $scratch
    $cancel = [Threading.CancellationTokenSource]::new([TimeSpan]::FromMinutes(8))
    $handler = [Net.Http.HttpClientHandler]::new(); $handler.AllowAutoRedirect = $false
    $client = [Net.Http.HttpClient]::new($handler); $client.Timeout = [TimeSpan]::FromMinutes(8)
    $response = $client.GetAsync($url, [Net.Http.HttpCompletionOption]::ResponseHeadersRead, $cancel.Token).GetAwaiter().GetResult()
    if ([int]$response.StatusCode -ne 200 -or $response.RequestMessage.RequestUri.AbsoluteUri -cne $url) { throw 'Official direct TLS URL did not return exact HTTP200.' }
    if ($response.Content.Headers.ContentLength -ne $expectedBytes) { throw 'Official installer size changed; refuse new bytes.' }
    $record['content_length_bytes'] = $response.Content.Headers.ContentLength
    $record['content_type'] = [string]$response.Content.Headers.ContentType
    $incoming = $response.Content.ReadAsStreamAsync($cancel.Token).GetAwaiter().GetResult()
    $outgoing = [IO.File]::Open($installer, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None)
    $buffer = [byte[]]::new(1MB); $count = [long]0
    while (($read = $incoming.ReadAsync($buffer, 0, $buffer.Length, $cancel.Token).GetAwaiter().GetResult()) -gt 0) {
        $count += $read
        $record['downloaded_bytes'] = $count
        if ($count -gt $expectedBytes -or $count -gt $maxBytes -or $started.Elapsed.TotalSeconds -gt 480) { throw 'Download size/time bound exceeded.' }
        $outgoing.Write($buffer, 0, $read)
    }
    $outgoing.Flush(); $outgoing.Dispose(); $outgoing = $null
    $record['downloaded_bytes'] = $count
    if ($count -ne $expectedBytes -or (Get-Item -LiteralPath $installer).Length -ne $expectedBytes) { throw 'Incomplete or oversized installer.' }
    $firstHash = (Get-FileHash -LiteralPath $installer -Algorithm SHA256).Hash.ToLowerInvariant()
    $record['sha256'] = $firstHash
    $signature = Get-AuthenticodeSignature -LiteralPath $installer
    $record['signature_status'] = [string]$signature.Status
    if ($null -eq $signature.SignerCertificate) { throw 'Installer has no signer certificate.' }
    $certificate = $signature.SignerCertificate
    $record['certificate'] = [ordered]@{ subject = $certificate.Subject; issuer = $certificate.Issuer
        serial_number = $certificate.SerialNumber; thumbprint = $certificate.Thumbprint
        not_before_utc = $certificate.NotBefore.ToUniversalTime().ToString('o'); not_after_utc = $certificate.NotAfter.ToUniversalTime().ToString('o') }
    $subjectPattern = '(?:^|,\s*)CN=' + [regex]::Escape($expectedSigner) + '(?:,|$)'
    $issuerPattern = '(?:^|,\s*)CN=' + [regex]::Escape($expectedIssuer) + '(?:,|$)'
    if ($signature.Status -ne [System.Management.Automation.SignatureStatus]::Valid -or
        -not [regex]::IsMatch($certificate.Subject, $subjectPattern) -or
        -not [regex]::IsMatch($certificate.Issuer, $issuerPattern) -or
        $certificate.SerialNumber.ToUpperInvariant() -cne $expectedSerial) { throw 'Authenticode trust/name/issuer/serial differs from official pin.' }
    $version = [Diagnostics.FileVersionInfo]::GetVersionInfo($installer)
    $record['file_version_metadata'] = $version.FileVersion
    $record['product_version_metadata'] = $version.ProductVersion
    $record['file_description_metadata'] = $version.FileDescription
    if ((Get-FileHash -LiteralPath $installer -Algorithm SHA256).Hash.ToLowerInvariant() -cne $firstHash -or
        (Get-Item -LiteralPath $installer).Length -ne $expectedBytes) { throw 'Installer changed during metadata observation.' }
    $record['passed'] = $true
} catch {
    $record['passed'] = $false; $record['error'] = $_.Exception.Message
} finally {
    foreach ($item in @($outgoing, $incoming, $response, $client, $handler, $cancel)) { if ($null -ne $item) { $item.Dispose() } }
    if (Test-Path -LiteralPath $installer) { Remove-Item -LiteralPath $installer -Force }
    if (Test-Path -LiteralPath $scratch) { Remove-Item -LiteralPath $scratch -Force }
    $record['installer_removed'] = -not (Test-Path -LiteralPath $installer)
    $record['disk_free_after_bytes'] = ([IO.DriveInfo]::new([IO.Path]::GetPathRoot($tempRoot))).AvailableFreeSpace
    $record['wall_seconds_before_log_publication'] = $started.Elapsed.TotalSeconds
    if (-not $record['installer_removed'] -or $started.Elapsed.TotalSeconds -gt 540) { $record['passed'] = $false }
    $json = $record | ConvertTo-Json -Depth 8
    Write-Output $json
    if ($env:GITHUB_STEP_SUMMARY) { Add-Content -LiteralPath $env:GITHUB_STEP_SUMMARY -Value ("## Windows metadata only`n``````json`n" + $json + "`n```````n") }
}
if (-not $record['passed']) { exit 2 }
