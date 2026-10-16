# Draft ephemeral Windows CI only; never invoke on the owner's Mac.
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
if(-not $IsWindows -or $env:RUNNER_OS -cne 'Windows'){throw 'Ephemeral Windows runner required'}
& (Join-Path $PSScriptRoot 'test_java25.ps1')
$repo=[IO.Path]::GetFullPath($env:GITHUB_WORKSPACE);$temp=[IO.Path]::GetFullPath($env:RUNNER_TEMP)
$head=(& git -C $repo -c core.fsmonitor=false -c core.hooksPath=/dev/null rev-parse HEAD).Trim()
if($LASTEXITCODE -ne 0 -or $head -cne $env:GITHUB_SHA){throw 'Dispatched checkout mismatch'}
$scratch=Join-Path $temp ('native-slice-'+[Guid]::NewGuid().ToString('N'));New-Item -ItemType Directory $scratch|Out-Null
$installer=Join-Path $scratch 'kicad.exe';$install=Join-Path $scratch 'KiCad';$jar=Join-Path $scratch 'freerouting-2.5.0.jar';$rules=@()
$record=[ordered]@{kind='windows-native-substrate-prototype';source_head=$head;passed=$false;product_windows_support=$false;installer_executed=$false;install_exit=$null;bundled_python_present=$null;native_started=$false;ephemeral_registration_side_effects_expected=$true;artifact_upload=$false;cache_upload=$false}
function Fetch([string]$url,[string]$dest,[long]$size,[string]$sha){
 $client=[Net.Http.HttpClient]::new();$client.Timeout=[TimeSpan]::FromMinutes(3);$input=$null;$output=$null;$cancel=[Threading.CancellationTokenSource]::new([TimeSpan]::FromMinutes(3));$response=$null
 try{$response=$client.GetAsync($url,[Net.Http.HttpCompletionOption]::ResponseHeadersRead,$cancel.Token).GetAwaiter().GetResult();if([int]$response.StatusCode -ne 200 -or $response.Content.Headers.ContentLength -ne $size){throw 'Download status/size mismatch'};$input=$response.Content.ReadAsStream();$output=[IO.File]::Open($dest,'CreateNew','Write','None');$buffer=[byte[]]::new(1MB);$count=[long]0
  while(($n=$input.ReadAsync($buffer,0,$buffer.Length,$cancel.Token).GetAwaiter().GetResult()) -gt 0){$count+=$n;if($count -gt $size){throw 'Download bound'};$output.Write($buffer,0,$n)};$output.Dispose();$output=$null
  if($count -ne $size -or (Get-FileHash $dest -Algorithm SHA256).Hash.ToLowerInvariant() -cne $sha){throw 'Immutable download hash mismatch'}
 }finally{if($output){$output.Dispose()};if($input){$input.Dispose()};if($response){$response.Dispose()};$cancel.Dispose();$client.Dispose()}
}
try{
 if(([IO.DriveInfo]::new([IO.Path]::GetPathRoot($scratch))).AvailableFreeSpace -lt 10GB){throw 'Installation headroom<10GiB'}
 Fetch 'https://kicad-downloads.s3.cern.ch/windows/stable/kicad-10.0.7-x86_64.exe' $installer 968953784 'ce3881b6a9188eb34ac1ebaaec7651149e8a025206410addfb11a1a9656ecf95'
 $signature=Get-AuthenticodeSignature $installer
 $record['installer_sha256']=(Get-FileHash $installer -Algorithm SHA256).Hash.ToLowerInvariant();$record['signature_status']=[string]$signature.Status
 if($signature.Status -ne 'Valid' -or $signature.SignerCertificate.Subject -notmatch '(?:^|,\s*)CN=KICAD SERVICES CORPORATION(?:,|$)' -or $signature.SignerCertificate.Issuer -notmatch '(?:^|,\s*)CN=GlobalSign GCC R45 EV CodeSigning CA 2020(?:,|$)' -or $signature.SignerCertificate.SerialNumber -cne '39DF6B588D969CA15D8D2756'){throw 'KiCad signer differs'}
 # Application files target RunnerTemp; ordinary ephemeral registry/shortcut side effects are expected.
 # Trusted official setup is online-capable dependency installation, not normal offline routing.
 $p=Start-Process -FilePath $installer -ArgumentList @('/currentuser','/S',('/D='+$install)) -PassThru;$record['installer_executed']=$true
 if(-not $p.WaitForExit(300000)){$p.Kill($true);$null=$p.WaitForExit(5000);$record['installer_timeout']=$true;throw 'Installer timeout'};$record['install_exit']=$p.ExitCode;if($p.ExitCode -ne 0){throw 'Installer failed'}
 $python=Join-Path $install 'bin/python.exe';$cli=Join-Path $install 'bin/kicad-cli.exe'
 $record['bundled_python_present']=[bool](Test-Path $python);$record['cli_present']=[bool](Test-Path $cli);$record['bounded_bin_inventory']=@(Get-ChildItem (Join-Path $install 'bin') -File|Where-Object {$_.Name -match '^(python|_pcbnew|pcbnew|kicad-cli)'}|Select-Object -First 100 Name,Length)
 if(-not (Test-Path $python) -or -not (Test-Path $cli)){throw 'Official matching bundled Python/CLI absent; no guessed ABI fallback'}
 if((Get-Service MpsSvc).Status -ne 'Running' -or @(Get-NetFirewallProfile -PolicyStore ActiveStore|Where-Object {$_.Enabled -ne $true}).Count){throw 'Native gate: firewall not enabled; global protections unchanged'}
 . (Join-Path $repo 'scripts/windows_native_slice/java25.ps1')
 $javaPin=Install-OwnedTemurin25 -Scratch $scratch -Fetch ${function:Fetch};$java=$javaPin.java
 $record['java_archive_sha256']=$javaPin.archive_sha256;$record['java_expanded_bytes']=$javaPin.expanded_bytes
 $javaManifest=Join-Path $scratch 'java-manifest.json';$javaPin|ConvertTo-Json -Depth 5|Set-Content -Encoding utf8 $javaManifest
 $powershell=Join-Path $PSHOME 'pwsh.exe';$record['powershell_sha256']=(Get-FileHash $powershell -Algorithm SHA256).Hash.ToLowerInvariant()
 Fetch 'https://github.com/freerouting/freerouting/releases/download/v2.5.0/freerouting-2.5.0.jar' $jar 64599107 'f6f51bb02245e8e717f9359bd260cc9c5c0b1bc0acc8b7cb2cd5b8ffeb5de3c7'
 foreach($program in @($python,$cli,$java)){foreach($direction in @('Inbound','Outbound')){$name='kicad-native-slice-'+[Guid]::NewGuid().ToString('N');New-NetFirewallRule -Name $name -DisplayName $name -Program $program -Direction $direction -Action Block -Enabled True -Profile Any|Out-Null;$rules+=$name;if((Get-NetFirewallRule -Name $name -PolicyStore ActiveStore).Enabled -ne 'True'){throw 'New deny rule not active'}}}
 $env:KICAD_CONFIG_HOME=Join-Path $scratch 'kicad-config';New-Item -ItemType Directory $env:KICAD_CONFIG_HOME|Out-Null
 $output=Join-Path $scratch 'output';$script=Join-Path $repo 'scripts/windows_native_slice/slice.py'
 # Native and Java calls below use suspended-assigned Job Objects. Host Python starts only the controller.
 [ordered]@{rules=@($rules | ForEach-Object { $rule=Get-NetFirewallRule -Name $_ -PolicyStore ActiveStore; $filter=$rule|Get-NetFirewallApplicationFilter; @{name=$rule.Name;program=$filter.Program;direction=[string]$rule.Direction} })} | ConvertTo-Json -Depth 4 | Set-Content -Encoding utf8 (Join-Path $scratch 'firewall.json')
 $record['controller_started']=$true;& $python -B $script --repo $repo --install $install --java $java --jar $jar --output $output --firewall-manifest (Join-Path $scratch 'firewall.json') --powershell $powershell --java-manifest $javaManifest
 $code=$LASTEXITCODE
 Write-Output (@{kind='windows-native-substrate-only';source_head=$head;installer_sha256=(Get-FileHash $installer).Hash;install_path=$install;ephemeral_registration_side_effects_expected=$true;product_windows_support=$false;exit_code=$code}|ConvertTo-Json -Compress)
 $record['slice_exit']=$code;if($code -ne 0){throw 'Native substrate incomplete/refused; retain CI logs'};$record['native_transport_command_completed']=$true
}catch{$record['error']=$_.Exception.Message}finally{foreach($name in $rules){Remove-NetFirewallRule -Name $name -ErrorAction Continue};if(Test-Path $scratch){Remove-Item $scratch -Recurse -Force};$record['scratch_removed']=-not(Test-Path $scratch);Write-Output ($record|ConvertTo-Json -Depth 5 -Compress)}
if(-not $record.Contains('native_transport_command_completed')){exit 2}
