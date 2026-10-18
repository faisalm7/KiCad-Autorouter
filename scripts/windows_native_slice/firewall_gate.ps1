# Read-only gate for the exact two Any-scope deny rules owned by this CI probe.
param([Parameter(Mandatory=$true)][string]$Manifest,[Parameter(Mandatory=$true)][string]$Program,[Parameter(Mandatory=$true)][string]$Sha256)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
if((Get-Service MpsSvc).Status -ne 'Running' -or @(Get-NetFirewallProfile -PolicyStore ActiveStore|Where-Object {$_.Enabled -ne $true}).Count){throw 'Enabled live firewall profiles required'}
if((Get-FileHash -LiteralPath $Program -Algorithm SHA256).Hash.ToLowerInvariant() -cne $Sha256){throw 'Program bytes changed'}
$owned=Get-Content -LiteralPath $Manifest -Raw|ConvertFrom-Json
$rules=@($owned.rules|Where-Object {$_.program -ceq $Program})
if($rules.Count -ne 2 -or @($rules.direction|Sort-Object -Unique).Count -ne 2){throw 'Exactly two owned inbound/outbound rules required'}
# Diagnostics never supply an admission decision. Only refusal branches collect
# both directions before their original throw; success performs no extra queries.
function Get-DiagnosticValue($Value){
 $items=@($Value|Select-Object -First 9);$projected=@()
 foreach($item in @($items|Select-Object -First 8)){
  $text=[string]$item;$itemProjection=[ordered]@{type=if($null -eq $item){$null}else{$item.GetType().FullName};text=$text.Substring(0,[Math]::Min(128,$text.Length));text_truncated=$text.Length -gt 128}
  if($item -is [Enum]){$itemProjection['enum_numeric']=[string]$item.value__}
  elseif($item -is [byte] -or $item -is [sbyte] -or $item -is [int16] -or $item -is [uint16] -or $item -is [int32] -or $item -is [uint32] -or $item -is [int64] -or $item -is [uint64]){$itemProjection['integer_numeric']=[string]$item}
  $projected+=$itemProjection
 }
 return @{type=if($null -eq $Value){$null}else{$Value.GetType().FullName};items=$projected;items_truncated=$items.Count -gt 8}
}
function Get-DiagnosticRows([scriptblock]$Read,[string[]]$Fields){
 try{
  $rows=@(& $Read|Select-Object -First 9);$projected=@()
  foreach($row in @($rows|Select-Object -First 8)){
   $values=[ordered]@{}
   foreach($field in $Fields){$property=$row.PSObject.Properties[$field];$values[$field]=if($null -eq $property){@{missing=$true}}else{Get-DiagnosticValue $property.Value}}
   $projected+=$values
  }
  return @{observed_count_at_least=$rows.Count;rows=$projected;rows_truncated=$rows.Count -gt 8}
 }catch{return @{unavailable=$true;error_type=$_.Exception.GetType().FullName}}
}
function Get-FirewallDiagnostic {
try{
 $diagnosticRules=@()
 foreach($entry in $rules){
  if($entry.name -notmatch '^kicad-native-slice-[0-9a-f]{32}$' -or $entry.direction -notin @('Inbound','Outbound')){continue}
  $diagnosticRule=@{name=$entry.name;expected_direction=$entry.direction}
  $diagnosticRule['rule']=Get-DiagnosticRows {Get-NetFirewallRule -Name $entry.name -PolicyStore ActiveStore} @('Enabled','Action','Direction','Profile','PrimaryStatus','EnforcementStatus')
  $diagnosticRule['filters']=[ordered]@{}
  foreach($filter in @(
   @{kind='application';command='Get-NetFirewallApplicationFilter';fields=@('Program','Package')},
   @{kind='address';command='Get-NetFirewallAddressFilter';fields=@('LocalAddress','RemoteAddress')},
   @{kind='port';command='Get-NetFirewallPortFilter';fields=@('Protocol','LocalPort','RemotePort')},
   @{kind='service';command='Get-NetFirewallServiceFilter';fields=@('Service')},
   @{kind='interface';command='Get-NetFirewallInterfaceFilter';fields=@('InterfaceAlias')},
   @{kind='interface_type';command='Get-NetFirewallInterfaceTypeFilter';fields=@('InterfaceType')}
  )){$diagnosticRule.filters[$filter.kind]=Get-DiagnosticRows {Get-NetFirewallRule -Name $entry.name -PolicyStore ActiveStore | & $filter.command} $filter.fields}
  $diagnosticRules+=$diagnosticRule
 }
 $snapshot=[ordered]@{kind='owned-live-firewall-diagnostic';non_admitting=$true;expected_profile_names=@('Domain','Private','Public');profiles=(Get-DiagnosticRows {Get-NetFirewallProfile -PolicyStore ActiveStore} @('Name','Enabled'));active_interfaces=(Get-DiagnosticRows {Get-NetConnectionProfile} @('InterfaceIndex','InterfaceAlias','NetworkCategory','IPv4Connectivity','IPv6Connectivity'));rules=$diagnosticRules}
 $diagnostic=$snapshot|ConvertTo-Json -Depth 12 -Compress
 if([Text.Encoding]::UTF8.GetByteCount($diagnostic) -gt 12000){$diagnostic='{"kind":"owned-live-firewall-diagnostic","non_admitting":true,"unavailable":true,"reason":"snapshot exceeds 12000 UTF-8 bytes"}'}
}catch{$diagnostic='{"kind":"owned-live-firewall-diagnostic","non_admitting":true,"unavailable":true,"reason":"snapshot unavailable"}'}
return $diagnostic
}
$observations=@()
foreach($entry in $rules){
 if($entry.name -notmatch '^kicad-native-slice-[0-9a-f]{32}$' -or $entry.direction -notin @('Inbound','Outbound')){throw 'Owned rule identity malformed'}
 $r=Get-NetFirewallRule -Name $entry.name -PolicyStore ActiveStore
 if(@($r).Count -ne 1 -or [string]$r.Enabled -ne 'True' -or [string]$r.Action -ne 'Block' -or [string]$r.Direction -cne $entry.direction -or [string]$r.Profile -ne 'Any' -or [string]$r.PrimaryStatus -ne 'OK' -or [string]$r.EnforcementStatus -ne 'Full'){
  [Console]::Error.WriteLine((Get-FirewallDiagnostic))
  try{
   $properties=[ordered]@{}
   if(@($r).Count -eq 1){
    foreach($property in @('Enabled','Action','Direction','Profile','PrimaryStatus','EnforcementStatus')){
     $value=$r.PSObject.Properties[$property].Value
     $properties[$property]=@{type=if($null -eq $value){$null}else{$value.GetType().FullName};text=[string]$value;items=@($value|ForEach-Object{[string]$_})}
    }
   }
   [Console]::Error.WriteLine((@{kind='owned-live-rule-rejected';name=$entry.name;expected_direction=$entry.direction;count=@($r).Count;properties=$properties}|ConvertTo-Json -Depth 5 -Compress))
  }catch{
   [Console]::Error.WriteLine('Owned live rule property projection unavailable')
  }
  throw 'Owned live rule is not fully enforced for every profile'
 }
 $app=$r|Get-NetFirewallApplicationFilter;$address=$r|Get-NetFirewallAddressFilter;$port=$r|Get-NetFirewallPortFilter;$service=$r|Get-NetFirewallServiceFilter;$interface=$r|Get-NetFirewallInterfaceFilter;$type=$r|Get-NetFirewallInterfaceTypeFilter
 if($app.Program -cne $Program -or $app.Package -ne 'Any' -or $address.LocalAddress -ne 'Any' -or $address.RemoteAddress -ne 'Any' -or $port.Protocol -ne 'Any' -or $port.LocalPort -ne 'Any' -or $port.RemotePort -ne 'Any' -or $service.Service -ne 'Any' -or $interface.InterfaceAlias -ne 'Any' -or $type.InterfaceType -ne 'Any'){[Console]::Error.WriteLine((Get-FirewallDiagnostic));throw 'Deny rule has narrowed or changed applicability'}
 $observations+=@{name=$entry.name;direction=$entry.direction;profile='Any';enforcement='Full';program=$Program}
}
@{verified_active_outbound_block=$true;verified_active_inbound_block=$true;program=$Program;sha256=$Sha256;rules=$observations}|ConvertTo-Json -Depth 4 -Compress
