# Mocked read/serialization controls only; no Windows firewall or network proof.
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
enum DiagnosticEnforcement { Enforced=1; ProfileInactive=5 }
$global:FirewallDiagnosticFixture=@{status=@([DiagnosticEnforcement]::ProfileInactive,[DiagnosticEnforcement]::Enforced);fail_filter='';fail_connections=$false;narrow_address=$false;filter_reads=@();profile_reads=0;connection_reads=0;rule_reads=0}
function Assert-Condition($Condition,[string]$Message){if(-not $Condition){throw $Message}}
function Get-Service {param($Name);[pscustomobject]@{Status='Running'}}
function Get-FileHash {param($LiteralPath,$Algorithm);[pscustomobject]@{Hash=('a'*64)}}
function Get-NetFirewallProfile {param($PolicyStore);$global:FirewallDiagnosticFixture.profile_reads++;foreach($name in @('Domain','Private','Public')){[pscustomobject]@{Name=$name;Enabled=$true}}}
function Get-NetConnectionProfile {
 $global:FirewallDiagnosticFixture.connection_reads++
 if($global:FirewallDiagnosticFixture.fail_connections){throw 'mock connection census unavailable'}
 [pscustomobject]@{InterfaceIndex=7;InterfaceAlias='owned-test-interface';NetworkCategory='Public';IPv4Connectivity='Internet';IPv6Connectivity='NoTraffic'}
}
function Get-NetFirewallRule {
 param($Name,$PolicyStore)
 $global:FirewallDiagnosticFixture.rule_reads++
 [pscustomobject]@{Name=$Name;Enabled='True';Action='Block';Direction=if($Name -ceq ('kicad-native-slice-'+('a'*32))){'Inbound'}else{'Outbound'};Profile='Any';PrimaryStatus='OK';EnforcementStatus=$global:FirewallDiagnosticFixture.status}
}
function Get-MockFilter($Kind,$Rule){
 $global:FirewallDiagnosticFixture.filter_reads+=($Rule.Name+':'+$Kind)
 if($global:FirewallDiagnosticFixture.fail_filter -ceq $Kind){throw 'mock filter unavailable'}
 switch($Kind){
  'application' {[pscustomobject]@{Program='owned-tool.exe';Package='Any'}}
  'address' {[pscustomobject]@{LocalAddress='Any';RemoteAddress=if($global:FirewallDiagnosticFixture.narrow_address){'127.0.0.1'}else{'Any'}}}
  'port' {[pscustomobject]@{Protocol='Any';LocalPort='Any';RemotePort='Any'}}
  'service' {[pscustomobject]@{Service='Any'}}
  'interface' {[pscustomobject]@{InterfaceAlias='Any'}}
  'interface_type' {[pscustomobject]@{InterfaceType='Any'}}
 }
}
function Get-NetFirewallApplicationFilter {param([Parameter(ValueFromPipeline=$true)]$Rule);process{Get-MockFilter 'application' $Rule}}
function Get-NetFirewallAddressFilter {param([Parameter(ValueFromPipeline=$true)]$Rule);process{Get-MockFilter 'address' $Rule}}
function Get-NetFirewallPortFilter {param([Parameter(ValueFromPipeline=$true)]$Rule);process{Get-MockFilter 'port' $Rule}}
function Get-NetFirewallServiceFilter {param([Parameter(ValueFromPipeline=$true)]$Rule);process{Get-MockFilter 'service' $Rule}}
function Get-NetFirewallInterfaceFilter {param([Parameter(ValueFromPipeline=$true)]$Rule);process{Get-MockFilter 'interface' $Rule}}
function Get-NetFirewallInterfaceTypeFilter {param([Parameter(ValueFromPipeline=$true)]$Rule);process{Get-MockFilter 'interface_type' $Rule}}
function Invoke-MockGate($Manifest){
 $writer=[IO.StringWriter]::new();$previous=[Console]::Error;$failure=$null;$output=@()
 $global:FirewallDiagnosticFixture.filter_reads=@()
 $global:FirewallDiagnosticFixture.profile_reads=0;$global:FirewallDiagnosticFixture.connection_reads=0;$global:FirewallDiagnosticFixture.rule_reads=0
 try{
  [Console]::SetError($writer)
  try{$output=@(& (Join-Path $PSScriptRoot 'firewall_gate.ps1') -Manifest $Manifest -Program 'owned-tool.exe' -Sha256 ('a'*64))}catch{$failure=$_.Exception.Message}
 }finally{[Console]::SetError($previous)}
 $stderr=$writer.ToString();$writer.Dispose()
 $snapshot=if($stderr){($stderr.Trim() -split '\r?\n')[0]|ConvertFrom-Json}else{$null}
 return @{failure=$failure;output=$output;stderr=$stderr;snapshot=$snapshot}
}
$manifest=[IO.Path]::GetTempFileName()
try{
 @{rules=@(@{name=('kicad-native-slice-'+('a'*32));program='owned-tool.exe';direction='Inbound'},@{name=('kicad-native-slice-'+('b'*32));program='owned-tool.exe';direction='Outbound'})}|ConvertTo-Json -Depth 4|Set-Content -LiteralPath $manifest -Encoding utf8
 $result=Invoke-MockGate $manifest
 Assert-Condition ($result.failure -ceq 'Owned live rule is not fully enforced for every profile') 'Mixed status must retain original refusal'
 Assert-Condition ($result.output.Count -eq 0 -and $result.snapshot.non_admitting -eq $true) 'Diagnostic must not admit'
 Assert-Condition ($result.snapshot.kind -ceq 'owned-live-firewall-diagnostic' -and $result.snapshot.rules.Count -eq 2) 'Both exact owned directions must be projected'
 Assert-Condition ($result.snapshot.rules[0].expected_direction -ceq 'Inbound' -and $result.snapshot.rules[1].expected_direction -ceq 'Outbound') 'Direction identities changed'
 Assert-Condition ($global:FirewallDiagnosticFixture.filter_reads.Count -eq 12) 'All six filters in both directions must be read before first refusal'
 Assert-Condition ($result.snapshot.profiles.observed_count_at_least -eq 3 -and $result.snapshot.active_interfaces.rows[0].InterfaceIndex.items[0].integer_numeric -ceq '7') 'Profile/interface census missing'
 $status=$result.snapshot.rules[0].rule.rows[0].EnforcementStatus
 Assert-Condition ($status.type -ceq 'System.Object[]' -and $status.items[0].type -ceq 'DiagnosticEnforcement' -and $status.items[0].enum_numeric -ceq '5' -and $status.items[1].enum_numeric -ceq '1') 'Typed mixed status projection missing'
 Assert-Condition ([Text.Encoding]::UTF8.GetByteCount(($result.snapshot|ConvertTo-Json -Depth 12 -Compress)) -le 12000) 'Normal diagnostic exceeds byte cap'
 Assert-Condition (-not $result.snapshot.PSObject.Properties['verified_active_inbound_block'] -and -not $result.snapshot.PSObject.Properties['verified_active_outbound_block']) 'Snapshot cannot carry verified flags'

 $global:FirewallDiagnosticFixture.status=@('Enforced')
 $result=Invoke-MockGate $manifest
 $item=$result.snapshot.rules[0].rule.rows[0].EnforcementStatus.items[0]
 Assert-Condition ($result.failure -ceq 'Owned live rule is not fully enforced for every profile' -and $item.type -ceq 'System.String' -and -not $item.PSObject.Properties['enum_numeric']) 'String status must not become enum admission'

 $global:FirewallDiagnosticFixture.fail_filter='address';$global:FirewallDiagnosticFixture.fail_connections=$true
 $result=Invoke-MockGate $manifest
 Assert-Condition ($result.failure -ceq 'Owned live rule is not fully enforced for every profile' -and $result.snapshot.rules[1].filters.address.unavailable -eq $true -and $result.snapshot.active_interfaces.unavailable -eq $true) 'Unavailable diagnostics must preserve original refusal and other direction'
 Assert-Condition ($global:FirewallDiagnosticFixture.filter_reads.Count -eq 12) 'Unavailable filter must not stop remaining diagnostic reads'

 $global:FirewallDiagnosticFixture.fail_filter='';$global:FirewallDiagnosticFixture.fail_connections=$false;$global:FirewallDiagnosticFixture.status='Full';$global:FirewallDiagnosticFixture.narrow_address=$true
 $result=Invoke-MockGate $manifest
 Assert-Condition ($result.failure -ceq 'Deny rule has narrowed or changed applicability' -and $result.output.Count -eq 0 -and $result.snapshot.non_admitting -eq $true) 'Narrowed filter must retain original refusal'

 $global:FirewallDiagnosticFixture.narrow_address=$false
 $result=Invoke-MockGate $manifest
 Assert-Condition ($null -eq $result.failure -and $result.stderr -ceq '' -and $result.output.Count -eq 1) 'Existing scalar-Full path changed'
 Assert-Condition (($result.output[0]|ConvertFrom-Json).verified_active_inbound_block -eq $true) 'Original admission result changed'
 Assert-Condition ($global:FirewallDiagnosticFixture.filter_reads.Count -eq 12 -and $global:FirewallDiagnosticFixture.connection_reads -eq 0) 'Success must perform only original filter reads and no connection-profile diagnostic query'
 Assert-Condition ($global:FirewallDiagnosticFixture.profile_reads -eq 1 -and $global:FirewallDiagnosticFixture.rule_reads -eq 2) 'Success must retain original profile/rule query counts'
 Write-Output 'Mocked firewall diagnostic structure/refusal controls passed; no Windows network-denial qualification.'
}finally{Remove-Item -LiteralPath $manifest -Force;Remove-Variable -Name FirewallDiagnosticFixture -Scope Global}
