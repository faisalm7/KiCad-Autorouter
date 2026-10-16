# Read-only gate for the exact two Any-scope deny rules owned by this CI probe.
param([Parameter(Mandatory=$true)][string]$Manifest,[Parameter(Mandatory=$true)][string]$Program,[Parameter(Mandatory=$true)][string]$Sha256)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
if((Get-Service MpsSvc).Status -ne 'Running' -or @(Get-NetFirewallProfile -PolicyStore ActiveStore|Where-Object {$_.Enabled -ne $true}).Count){throw 'Enabled live firewall profiles required'}
if((Get-FileHash -LiteralPath $Program -Algorithm SHA256).Hash.ToLowerInvariant() -cne $Sha256){throw 'Program bytes changed'}
$owned=Get-Content -LiteralPath $Manifest -Raw|ConvertFrom-Json
$rules=@($owned.rules|Where-Object {$_.program -ceq $Program})
if($rules.Count -ne 2 -or @($rules.direction|Sort-Object -Unique).Count -ne 2){throw 'Exactly two owned inbound/outbound rules required'}
$observations=@()
foreach($entry in $rules){
 if($entry.name -notmatch '^kicad-native-slice-[0-9a-f]{32}$' -or $entry.direction -notin @('Inbound','Outbound')){throw 'Owned rule identity malformed'}
 $r=Get-NetFirewallRule -Name $entry.name -PolicyStore ActiveStore
 if(@($r).Count -ne 1 -or [string]$r.Enabled -ne 'True' -or [string]$r.Action -ne 'Block' -or [string]$r.Direction -cne $entry.direction -or [string]$r.Profile -ne 'Any' -or [string]$r.PrimaryStatus -ne 'OK' -or [string]$r.EnforcementStatus -ne 'Full'){
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
 if($app.Program -cne $Program -or $app.Package -ne 'Any' -or $address.LocalAddress -ne 'Any' -or $address.RemoteAddress -ne 'Any' -or $port.Protocol -ne 'Any' -or $port.LocalPort -ne 'Any' -or $port.RemotePort -ne 'Any' -or $service.Service -ne 'Any' -or $interface.InterfaceAlias -ne 'Any' -or $type.InterfaceType -ne 'Any'){throw 'Deny rule has narrowed or changed applicability'}
 $observations+=@{name=$entry.name;direction=$entry.direction;profile='Any';enforcement='Full';program=$Program}
}
@{verified_active_outbound_block=$true;verified_active_inbound_block=$true;program=$Program;sha256=$Sha256;rules=$observations}|ConvertTo-Json -Depth 4 -Compress
