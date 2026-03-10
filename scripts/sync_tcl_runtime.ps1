param(
  [Parameter(Mandatory = $true)]
  [string]$PythonExe,

  [Parameter(Mandatory = $true)]
  [string]$BundleInternalDir
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path $PythonExe)) {
  Write-Output "python not found: $PythonExe"
  exit 2
}

if (-not (Test-Path $BundleInternalDir)) {
  Write-Output "bundle directory not found: $BundleInternalDir"
  exit 3
}

$pythonDir = Split-Path -Parent $PythonExe
$envRoot = $pythonDir
$libraryBin = Join-Path $envRoot 'Library\bin'
$tclDllSource = Join-Path $libraryBin 'tcl86t.dll'
$tkDllSource = Join-Path $libraryBin 'tk86t.dll'
$tclDllTarget = Join-Path $BundleInternalDir 'tcl86t.dll'
$tkDllTarget = Join-Path $BundleInternalDir 'tk86t.dll'
$tclDataDir = Join-Path $BundleInternalDir '_tcl_data'
$tkDataDir = Join-Path $BundleInternalDir '_tk_data'
$initTcl = Join-Path $tclDataDir 'init.tcl'

foreach ($path in @($tclDllSource, $tkDllSource, $tclDataDir, $tkDataDir, $initTcl)) {
  if (-not (Test-Path $path)) {
    Write-Output "required path missing: $path"
    exit 4
  }
}

$tempPy = [System.IO.Path]::GetTempFileName() + '.py'
$tempOut = [System.IO.Path]::GetTempFileName()
$tempErr = [System.IO.Path]::GetTempFileName()

@"
import tkinter
print(tkinter.Tcl().eval('info patchlevel'))
"@ | Set-Content -Path $tempPy -Encoding UTF8

try {
  $proc = Start-Process -FilePath $PythonExe -ArgumentList @($tempPy) -NoNewWindow -Wait -PassThru -RedirectStandardOutput $tempOut -RedirectStandardError $tempErr
  if ($proc.ExitCode -ne 0) {
    $err = ''
    if (Test-Path $tempErr) {
      $err = (Get-Content -Raw -Encoding UTF8 $tempErr).Trim()
    }
    if ($err) {
      Write-Output $err
    }
    Write-Output 'failed to read Tcl patchlevel.'
    exit 5
  }

  $expectedPatchlevel = ''
  if (Test-Path $tempOut) {
    $expectedPatchlevel = (Get-Content -Raw -Encoding UTF8 $tempOut).Trim()
  }
  if ([string]::IsNullOrWhiteSpace($expectedPatchlevel)) {
    Write-Output 'empty Tcl patchlevel.'
    exit 6
  }
}
finally {
  if (Test-Path $tempPy) { Remove-Item -Force $tempPy }
  if (Test-Path $tempOut) { Remove-Item -Force $tempOut }
  if (Test-Path $tempErr) { Remove-Item -Force $tempErr }
}

Copy-Item -Force $tclDllSource $tclDllTarget
Copy-Item -Force $tkDllSource $tkDllTarget

$initContent = Get-Content -Raw -Encoding UTF8 $initTcl
$expectedRequire = "package require -exact Tcl $expectedPatchlevel"
if ($initContent -notmatch [Regex]::Escape($expectedRequire)) {
  Write-Output "init.tcl requirement mismatch, expected: $expectedRequire"
  exit 7
}

$tclVersion = [string](Get-Item $tclDllTarget).VersionInfo.FileVersion
$tkVersion = [string](Get-Item $tkDllTarget).VersionInfo.FileVersion

Write-Output "expected Tcl patchlevel: $expectedPatchlevel"
Write-Output "bundled tcl86t.dll: $tclVersion"
Write-Output "bundled tk86t.dll: $tkVersion"

if ($tclVersion -ne $expectedPatchlevel) {
  Write-Output "bundled tcl86t.dll mismatch: $tclVersion"
  exit 8
}

if ($tkVersion -ne $expectedPatchlevel) {
  Write-Output "bundled tk86t.dll mismatch: $tkVersion"
  exit 9
}

Write-Output 'Tcl/Tk runtime sync done.'
exit 0
