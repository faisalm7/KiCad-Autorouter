# Actual PowerShell regression controls; no download, extraction or Java run.
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'java25.ps1')
foreach($pair in @(@(0,0L),@(32,32L),@(-2147483648,2147483648L),@(-2114453504,2180513792L))){
 $actual=ConvertTo-OwnedZipAttributes -Value $pair[0]
 if($actual -isnot [uint32] -or [long]$actual -ne $pair[1]){throw 'ZIP signed regular attribute regression'}
}
# Unix symlink mode and DOS FILE_ATTRIBUTE_REPARSE_POINT must still refuse.
foreach($value in @(-1577123840,1024,-2114452480,-1)){
 $refused=$false
 try{$null=ConvertTo-OwnedZipAttributes -Value $value}catch{
  if($_.Exception.Message -cne 'Archive symlink/reparse member refused'){throw}
  $refused=$true
 }
 if(-not $refused){throw 'ZIP symlink/reparse regression'}
}
Write-Output 'Owned ZIP signed-attribute controls passed (4 regular, 4 invalid).'
