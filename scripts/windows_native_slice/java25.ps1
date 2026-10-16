# Source-only draft. Dot-source after review; invoke only on the ephemeral Windows runner.
function Install-OwnedTemurin25 {
 param([Parameter(Mandatory)][string]$Scratch,[Parameter(Mandatory)][scriptblock]$Fetch)
 if(-not $IsWindows -or $env:RUNNER_OS -cne 'Windows'){throw 'Ephemeral Windows runner only'}
 $temp=[IO.Path]::GetFullPath($env:RUNNER_TEMP).TrimEnd('\')+'\';$scratchPath=[IO.Path]::GetFullPath($Scratch)
 if(-not $scratchPath.StartsWith($temp,[StringComparison]::OrdinalIgnoreCase)){throw 'Scratch escaped RunnerTemp'}
 function NoReparse([string]$path){
  $item=[IO.DirectoryInfo]::new($path)
  while($item){if($item.Exists -and ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)){throw 'Reparse directory refused'};$item=$item.Parent}
 }
 NoReparse $scratchPath
 $destination=Join-Path $scratchPath 'temurin25-owned';$archive=Join-Path $scratchPath 'temurin25-jre.zip'
 if((Test-Path $destination) -or (Test-Path $archive)){throw 'Fresh exclusive Java paths required'}
 $url='https://github.com/adoptium/temurin25-binaries/releases/download/jdk-25.0.2%2B10/OpenJDK25U-jre_x64_windows_hotspot_25.0.2_10.zip'
 $size=[long]58426848;$sha='1919e7e1603bc5937187139db2d65824f8d95ef42d0423ae9f9f1d9eb97842f6'
 & $Fetch $url $archive $size $sha
 if((Get-Item $archive).Length -ne $size -or (Get-FileHash $archive -Algorithm SHA256).Hash.ToLowerInvariant() -cne $sha){throw 'Official immutable JRE archive mismatch'}
 $archiveStream=$null;$zip=$null;$made=$false
 try{
  $archiveStream=[IO.File]::Open($archive,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read)
  if((Get-FileHash $archive -Algorithm SHA256).Hash.ToLowerInvariant() -cne $sha){throw 'Archive changed before lock'}
  $zip=[IO.Compression.ZipArchive]::new($archiveStream,[IO.Compression.ZipArchiveMode]::Read,$true)
  if($zip.Entries.Count -lt 2 -or $zip.Entries.Count -gt 4096){throw 'Archive entry count bound'}
  $seen=[Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase);$members=[Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase);$tops=[Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal);$declared=[long]0
  foreach($entry in $zip.Entries){
   $name=$entry.FullName.Replace('\','/');$parts=$name.TrimEnd('/').Split('/')
   if([IO.Path]::IsPathRooted($name) -or $name.Contains(':') -or $name.Contains([char]0) -or $parts.Count -lt 1){throw 'Rooted/device/archive path refused'}
   foreach($part in $parts){if(-not $part -or $part -in @('.','..') -or $part -match '[. ]$|[<>"|?*\x00-\x1f]' -or $part -match '^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(\..*)?$'){throw 'Ambiguous/reserved archive path'}}
   if(-not $seen.Add($name.TrimEnd('/'))){throw 'Case-folded duplicate archive member'};$null=$tops.Add($parts[0])
   if(-not $name.EndsWith('/')){$null=$members.Add($name)}
   $attributes=[uint32]([long]$entry.ExternalAttributes -band 0xffffffff)
   if((($attributes -shr 16) -band 0xf000) -eq 0xa000 -or ($attributes -band 0x400)){throw 'Archive symlink/reparse member refused'}
   if($entry.Length -lt 0 -or $entry.Length -gt 128MB){throw 'Archive member size bound'};$declared+=$entry.Length
   if($declared -gt 256MB){throw 'Archive expanded-byte bound'}
  }
  if($tops.Count -ne 1){throw 'One owned JRE root required'}
  New-Item -ItemType Directory -Path $destination|Out-Null;$made=$true;$prefix=[IO.Path]::GetFullPath($destination).TrimEnd('\')+'\';$actual=[long]0
  foreach($entry in $zip.Entries){
   $path=[IO.Path]::GetFullPath((Join-Path $destination $entry.FullName.Replace('/','\')))
   if(-not $path.StartsWith($prefix,[StringComparison]::OrdinalIgnoreCase)){throw 'Extraction escaped owned root'}
   if($entry.FullName.EndsWith('/') -or $entry.FullName.EndsWith('\')){New-Item -ItemType Directory -Path $path -Force|Out-Null;continue}
   $parent=[IO.Path]::GetDirectoryName($path);New-Item -ItemType Directory -Path $parent -Force|Out-Null;NoReparse $parent
   $reader=$entry.Open();$writer=$null;$count=[long]0
   try{$writer=[IO.File]::Open($path,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None);$buffer=[byte[]]::new(1MB)
    while(($n=$reader.Read($buffer,0,$buffer.Length)) -gt 0){$count+=$n;$actual+=$n;if($count -gt $entry.Length -or $actual -gt 256MB){throw 'Inflated stream exceeded declarations'};$writer.Write($buffer,0,$n)}
    if($count -ne $entry.Length){throw 'Truncated extracted member'}
   }finally{if($writer){$writer.Dispose()};$reader.Dispose()}
  }
  if($actual -ne $declared){throw 'Expanded archive population differs'}
  $jre=Join-Path $destination (@($tops)[0]);$java=Join-Path $jre 'bin/java.exe';$release=Join-Path $jre 'release'
  if(-not(Test-Path $java -PathType Leaf) -or -not(Test-Path $release -PathType Leaf) -or (Get-Item $release).Length -gt 16KB){throw 'JRE executable/release absent or unbounded'}
  $properties=@{};foreach($line in [IO.File]::ReadAllLines($release)){if($line -match '^([A-Z0-9_]+)="([^"]*)"$'){if($properties.ContainsKey($Matches[1])){throw 'Duplicate JRE property'};$properties[$Matches[1]]=$Matches[2]}}
  foreach($pair in @{JAVA_VERSION='25.0.2';JAVA_RUNTIME_VERSION='25.0.2+10-LTS';IMPLEMENTOR='Eclipse Adoptium';OS_NAME='Windows';OS_ARCH='x86_64'}.GetEnumerator()){if($properties[$pair.Key] -cne $pair.Value){throw ('Exact official JRE property mismatch: '+$pair.Key)}}
  $files=@{};foreach($file in Get-ChildItem $destination -Recurse -File){if($file.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Post-extraction reparse refused'};$files[$file.FullName.Substring($prefix.Length)]=(Get-FileHash $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()}
  if(-not $members.SetEquals([string[]]@($files.Keys|ForEach-Object {$_.Replace('\','/')}))){throw 'Extracted file population differs from immutable archive'}
  if((Get-FileHash $archive -Algorithm SHA256).Hash.ToLowerInvariant() -cne $sha){throw 'Locked archive changed'}
  return @{java=$java;java_sha256=(Get-FileHash $java -Algorithm SHA256).Hash.ToLowerInvariant();jre_root=$destination;files_sha256=$files;archive_url=$url;archive_bytes=$size;archive_sha256=$sha;expanded_bytes=$actual;entries=$zip.Entries.Count;expected_java_version='25.0.2';expected_vendor='Eclipse Adoptium';executed=$false}
 }catch{if($made -and (Test-Path $destination)){Remove-Item $destination -Recurse -Force};throw}finally{if($zip){$zip.Dispose()};if($archiveStream){$archiveStream.Dispose()}}
}
