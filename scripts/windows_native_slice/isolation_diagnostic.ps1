# Finite hosted diagnostic only: no installation, Native/JVM, routing or admission.
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
if(-not $IsWindows -or $env:RUNNER_OS -cne 'Windows' -or $env:GITHUB_ACTIONS -cne 'true' -or $env:RUNNER_ENVIRONMENT -cne 'github-hosted' -or -not [Environment]::Is64BitProcess){throw 'Ephemeral GitHub-hosted x64 Windows runner required'}
$started=[Diagnostics.Stopwatch]::StartNew();$owned=@();$scratch=$null;$scratchCreated=$false;$exitCode=2
$record=[ordered]@{kind='windows-isolation-diagnostic';product_windows_support=$false;admission=$false;native_executed=$false;JVM_executed=$false;system_executable_executed=$false;artifact_upload=$false;cache_upload=$false;diagnostic_completed=$false;cleanup_complete=$false;whole_CPU_seconds=$null;limits=@{gate_seconds=12;mock_seconds=20;CIM_query_seconds=5;stream_bytes=16384;script_admission_seconds=110;workflow_minutes=3;log_enforcement='Polling plus bounded readback, not an OS disk quota'}}
function Assert-Budget {if($started.Elapsed.TotalSeconds -gt 110){throw 'Diagnostic admission wall budget exceeded'}}
function Invoke-BoundedQuery([scriptblock]$Start){
 $job=$null
 try{$job=& $Start;if(@($job).Count -ne 1 -or $job -isnot [Management.Automation.Job]){throw 'One owned CIM query job required'};if($null -eq (Wait-Job -Job $job -Timeout 5)){throw 'Owned CIM query timeout'};Receive-Job -Job $job -ErrorAction Stop}
 finally{if($null -ne $job){Stop-Job -Job $job -ErrorAction SilentlyContinue;Remove-Job -Job $job -Force -ErrorAction SilentlyContinue}}
}
function Read-OwnedRule([string]$Name,[string]$Store='ActiveStore'){
 try{Invoke-BoundedQuery {Get-NetFirewallRule -Name $Name -PolicyStore $Store -AsJob}}
 catch{if($_.CategoryInfo.Category -ne [Management.Automation.ErrorCategory]::ObjectNotFound){throw}}
}
function Read-BoundedLog([string]$Path){
 $length=(Get-Item -LiteralPath $Path).Length;$stream=[IO.File]::OpenRead($Path)
 try{$bytes=[byte[]]::new([Math]::Min(16384,$length));$count=0;while($count -lt $bytes.Length){$read=$stream.Read($bytes,$count,$bytes.Length-$count);if($read -eq 0){break};$count+=$read};if($count -ne $bytes.Length){throw 'Owned log readback incomplete'}}finally{$stream.Dispose()}
 return @{bytes=$length;retained_bytes=$bytes.Length;truncated=$length -gt 16384;sha256=([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes))).ToLowerInvariant();base64=[Convert]::ToBase64String($bytes)}
}
function Invoke-OwnedPowerShell([string]$Script,[string[]]$Extra,[string]$Label,[int]$Seconds){
 Assert-Budget
 $stdout=Join-Path $scratch ($Label+'.stdout.log');$stderr=Join-Path $scratch ($Label+'.stderr.log');$arguments=@('-NoProfile','-NonInteractive','-File',$Script)+$Extra
 if(@($arguments|Where-Object {$_ -match '["\r\n]' -or $_.EndsWith('\')}).Count){throw 'Owned argument cannot be quoted safely'}
 $quoted=($arguments|ForEach-Object {'"'+$_+'"'}) -join ' ';$child=$null;$watch=[Diagnostics.Stopwatch]::StartNew();$reason='exited'
 try{
  $child=Start-Process -FilePath $powershell -ArgumentList $quoted -WorkingDirectory $scratch -RedirectStandardOutput $stdout -RedirectStandardError $stderr -PassThru
  while(-not $child.WaitForExit(25)){
   if($watch.Elapsed.TotalSeconds -ge $Seconds){$reason='timeout';break}
   if(@(@($stdout,$stderr)|Where-Object {(Test-Path -LiteralPath $_) -and (Get-Item -LiteralPath $_).Length -gt 16384}).Count){$reason='log_limit';break}
  }
  if(-not $child.HasExited){$child.Kill($true)}
  if(-not $child.WaitForExit(3000)){throw 'Owned PowerShell child did not exit'}
  $out=Read-BoundedLog $stdout;$err=Read-BoundedLog $stderr
  if($out.truncated -or $err.truncated){$reason='log_limit'}
  return @{reason=$reason;exit_code=$child.ExitCode;cleanup_complete=$true;wall_seconds=$watch.Elapsed.TotalSeconds;stdout=$out;stderr=$err}
 }finally{if($null -ne $child){if(-not $child.HasExited){$child.Kill($true);$null=$child.WaitForExit(3000)};$child.Dispose()}}
}
try{
 $repo=[IO.Path]::GetFullPath($env:GITHUB_WORKSPACE);$temp=[IO.Path]::GetFullPath($env:RUNNER_TEMP)
 if([IO.Path]::GetFullPath($PSScriptRoot) -cne [IO.Path]::GetFullPath((Join-Path $repo 'scripts/windows_native_slice'))){throw 'Diagnostic source outside dispatched checkout'}
 $head=(& git -C $repo -c core.fsmonitor=false -c core.hooksPath=/dev/null rev-parse HEAD).Trim()
 if($LASTEXITCODE -ne 0 -or $head -cne $env:GITHUB_SHA){throw 'Dispatched checkout mismatch'}
 $record['source_head']=$head;$record['source_sha256']=[ordered]@{}
 foreach($relative in @('.github/workflows/manual-python-controls.yml','scripts/windows_native_slice/isolation_diagnostic.ps1','scripts/windows_native_slice/firewall_gate.ps1','scripts/windows_native_slice/test_firewall_gate.ps1')){$record.source_sha256[$relative]=(Get-FileHash -LiteralPath (Join-Path $repo $relative) -Algorithm SHA256).Hash.ToLowerInvariant()}
 $scratch=Join-Path $temp ('isolation-diagnostic-'+[Guid]::NewGuid().ToString('N'));New-Item -ItemType Directory -Path $scratch|Out-Null;$scratchCreated=$true
 $powershell=Join-Path $PSHOME 'pwsh.exe';$record['powershell_sha256']=(Get-FileHash -LiteralPath $powershell -Algorithm SHA256).Hash.ToLowerInvariant()
 $record['mocked_controls']=Invoke-OwnedPowerShell (Join-Path $PSScriptRoot 'test_firewall_gate.ps1') @() 'mocked-controls' 20
 if($record.mocked_controls.reason -cne 'exited' -or $record.mocked_controls.exit_code -ne 0){throw 'Mocked structure/refusal controls failed; no live rules created'}
 $program=[IO.Path]::GetFullPath((Join-Path $env:SystemRoot 'System32/cmd.exe'));$item=Get-Item -LiteralPath $program
 if($item.Attributes -band [IO.FileAttributes]::ReparsePoint -or $item.VersionInfo.CompanyName -cne 'Microsoft Corporation'){throw 'Ordinary official System32 executable required'}
 $signature=Get-AuthenticodeSignature -LiteralPath $program
 if($signature.Status -ne 'Valid' -or $signature.SignerCertificate.Subject -notmatch '(?:^|,\s*)O=Microsoft Corporation(?:,|$)'){throw 'System executable Microsoft signature not verified'}
 $programPin=(Get-FileHash -LiteralPath $program -Algorithm SHA256).Hash.ToLowerInvariant();$record['system_executable']=@{path=$program;sha256=$programPin;signature_status=[string]$signature.Status;signer_subject=$signature.SignerCertificate.Subject;executed=$false}
 $manifestRules=@()
 foreach($direction in @('Inbound','Outbound')){
  Assert-Budget
  $name='kicad-native-slice-'+[Guid]::NewGuid().ToString('N')
  if(@(Read-OwnedRule $name).Count -ne 0 -or @(Read-OwnedRule $name 'PersistentStore').Count -ne 0){throw 'New owned rule name already present'}
  # Track the verified-absent owned name before creation, including partial failure.
  $owned+=$name
  $null=Invoke-BoundedQuery {New-NetFirewallRule -Name $name -DisplayName $name -Program $program -Direction $direction -Action Block -Enabled True -Profile Any -AsJob}
  $manifestRules+=@{name=$name;program=$program;direction=$direction}
 }
 $record['owned_rules']=$manifestRules;$manifest=Join-Path $scratch 'firewall.json';@{rules=$manifestRules}|ConvertTo-Json -Depth 4|Set-Content -LiteralPath $manifest -Encoding utf8
 $record['gate']=Invoke-OwnedPowerShell (Join-Path $PSScriptRoot 'firewall_gate.ps1') @('-Manifest',$manifest,'-Program',$program,'-Sha256',$programPin) 'gate' 12
 $packets=@();$raw=[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($record.gate.stderr.base64))
 foreach($line in @($raw -split '\r?\n')){try{$packet=$line.TrimStart([char]0xfeff)|ConvertFrom-Json -ErrorAction Stop;if($packet.PSObject.Properties['kind']){$packets+=$packet}}catch{}}
 $snapshots=@($packets|Where-Object {$_.kind -ceq 'owned-live-firewall-diagnostic'})
 $record['original_rule_refusal_packets']=@($packets|Where-Object {$_.kind -ceq 'owned-live-rule-rejected'}).Count
 $record['non_admitting_snapshot_packets']=$snapshots.Count
 if($record.gate.reason -cne 'exited' -or $record.gate.exit_code -ne 1 -or $snapshots.Count -ne 1 -or $snapshots[0].non_admitting -ne $true -or @($snapshots[0].rules).Count -ne 2){throw 'Complete expected refusal/dual-rule snapshot unavailable; no admission'}
 foreach($entry in $manifestRules){
  $view=@($snapshots[0].rules|Where-Object {$_.name -ceq $entry.name -and $_.expected_direction -ceq $entry.direction})
  if($view.Count -ne 1 -or @($view[0].rule.rows).Count -ne 1 -or @($view[0].rule.rows[0].EnforcementStatus.items).Count -eq 0){throw 'Diagnostic exact owned rule/status projection unavailable'}
  foreach($kind in @('application','address','port','service','interface','interface_type')){if(@($view[0].filters.PSObject.Properties[$kind].Value.rows).Count -ne 1){throw 'Diagnostic filter projection unavailable'}}
 }
 if(@($snapshots[0].profiles.rows).Count -ne 3 -or @($snapshots[0].active_interfaces.rows).Count -eq 0){throw 'Diagnostic profile/interface census unavailable'}
 foreach($relative in $record.source_sha256.Keys){if((Get-FileHash -LiteralPath (Join-Path $repo $relative) -Algorithm SHA256).Hash.ToLowerInvariant() -cne $record.source_sha256[$relative]){throw 'Diagnostic source changed'}}
 if((Get-FileHash -LiteralPath $program -Algorithm SHA256).Hash.ToLowerInvariant() -cne $programPin){throw 'System executable bytes changed'}
 $record['diagnostic_completed']=$true;$exitCode=0
}catch{$message=$_.Exception.Message;$record['error']=$message.Substring(0,[Math]::Min(512,$message.Length))}finally{
 $cleanup=@()
 foreach($name in $owned){
  $removed=$true;$absent=$false;$persistentAbsent=$false;$cleanupError=$null
  try{$null=Invoke-BoundedQuery {Remove-NetFirewallRule -Name $name -AsJob}}catch{if($_.CategoryInfo.Category -ne [Management.Automation.ErrorCategory]::ObjectNotFound){$removed=$false;$cleanupError=$_.Exception.GetType().FullName}}
  try{$absent=@(Read-OwnedRule $name).Count -eq 0}catch{$cleanupError=$_.Exception.GetType().FullName}
  try{$persistentAbsent=@(Read-OwnedRule $name 'PersistentStore').Count -eq 0}catch{$cleanupError=$_.Exception.GetType().FullName}
  $cleanup+=@{name=$name;remove_completed=$removed;active_store_absence_observed=$absent;persistent_store_absence_observed=$persistentAbsent;query_error_type=$cleanupError}
 }
 $record['cleanup']=$cleanup;$record['cleanup_complete']=@($cleanup|Where-Object {-not $_.remove_completed -or -not $_.active_store_absence_observed -or -not $_.persistent_store_absence_observed}).Count -eq 0
 if(-not $record.cleanup_complete){$exitCode=2}
 if($scratchCreated){try{Remove-Item -LiteralPath $scratch -Recurse -Force;$record['scratch_removed']=-not(Test-Path -LiteralPath $scratch)}catch{$record['scratch_removed']=$false;$exitCode=2}}
 $record['wall_seconds']=$started.Elapsed.TotalSeconds;Write-Output ($record|ConvertTo-Json -Depth 16 -Compress)
}
exit $exitCode
