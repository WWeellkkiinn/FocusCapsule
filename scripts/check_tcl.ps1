param(
  [string]$PythonExe
)

$ErrorActionPreference = 'Stop'

if (-not $PythonExe) {
  $cmd = Get-Command python -ErrorAction SilentlyContinue
  if ($null -ne $cmd) {
    $python = $cmd.Source
  } else {
    $python = 'python'
  }
} else {
  $python = $PythonExe
}

if ([System.IO.Path]::IsPathRooted($python) -and -not (Test-Path $python)) {
  Write-Output "python not found: $python"
  exit 2
}

$tempOut = [System.IO.Path]::GetTempFileName()
$tempErr = [System.IO.Path]::GetTempFileName()
$tempPy = [System.IO.Path]::GetTempFileName() + '.py'

@"
import json
import tkinter
import _tkinter

print(json.dumps({
    'patchlevel': tkinter.Tcl().eval('info patchlevel'),
    'tk': _tkinter.TK_VERSION,
    'tcl': _tkinter.TCL_VERSION,
}))
"@ | Set-Content -Path $tempPy -Encoding UTF8

try {
  $proc = Start-Process -FilePath $python -ArgumentList @($tempPy) -NoNewWindow -Wait -PassThru -RedirectStandardOutput $tempOut -RedirectStandardError $tempErr

  $json = ''
  $err = ''
  if (Test-Path $tempOut) {
    $jsonRaw = Get-Content -Raw -Encoding UTF8 $tempOut
    if ($null -ne $jsonRaw) {
      $json = ([string]$jsonRaw).Trim()
    }
  }
  if (Test-Path $tempErr) {
    $errRaw = Get-Content -Raw -Encoding UTF8 $tempErr
    if ($null -ne $errRaw) {
      $err = ([string]$errRaw).Trim()
    }
  }

  if ($proc.ExitCode -ne 0) {
    if ($err) { Write-Output $err }
    Write-Output 'failed to query Tcl/Tk versions.'
    exit 3
  }

  if ([string]::IsNullOrWhiteSpace($json)) {
    Write-Output 'empty version output.'
    exit 4
  }

  $data = $json | ConvertFrom-Json
  $patchlevel = [string]$data.patchlevel
  $tkVersion = [string]$data.tk
  $tclVersion = [string]$data.tcl
  $expectedPatchlevel = [string]$env:EXPECTED_TCL_PATCHLEVEL

  Write-Output "Tcl patchlevel: $patchlevel"
  Write-Output "_tkinter TK_VERSION: $tkVersion"
  Write-Output "_tkinter TCL_VERSION: $tclVersion"
  if (-not [string]::IsNullOrWhiteSpace($expectedPatchlevel)) {
    Write-Output "Expected Tcl patchlevel: $expectedPatchlevel"
  }

  if (($tkVersion -ne $tclVersion) -or (-not $patchlevel.StartsWith($tkVersion))) {
    Write-Output 'Tcl/Tk mismatch.'
    exit 1
  }

  if (-not [string]::IsNullOrWhiteSpace($expectedPatchlevel) -and ($patchlevel -ne $expectedPatchlevel)) {
    Write-Output "Tcl patchlevel mismatch: have $patchlevel, expected $expectedPatchlevel."
    exit 1
  }

  Write-Output 'Tcl/Tk version match.'
  exit 0
}
finally {
  if (Test-Path $tempOut) { Remove-Item -Force $tempOut }
  if (Test-Path $tempErr) { Remove-Item -Force $tempErr }
  if (Test-Path $tempPy) { Remove-Item -Force $tempPy }
}
