#!/usr/bin/env pwsh
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

<#
Build a self-contained Windows app (PyInstaller onedir) for Sofa Jobs Navigator.

Usage:
  pwsh -File packaging/windows/build.ps1               # windowed .exe in dist/
  pwsh -File packaging/windows/build.ps1 -Mode console # console variant

Outputs:
  dist/Sofa Jobs Navigator/           # onedir folder with the executable and libs
  dist/README-FIRST.txt               # quickstart
  dist/Sofa_Jobs_Navigator.zip        # zipped folder for sharing
#>

param(
  [ValidateSet('app','console')]
  [string]$Mode = 'app'
)

function Resolve-RepoRoot {
  $scriptDir = Split-Path -Parent $PSCommandPath
  return Resolve-Path (Join-Path $scriptDir '..' '..')
}

$ROOT = (Resolve-RepoRoot)
Set-Location $ROOT

$AppName   = 'Sofa Jobs Navigator'
$IconIco   = Join-Path $ROOT 'sofa_icon.ico'
$HelpDir   = Join-Path $ROOT 'src/sofa_jobs_navigator/ui/assets/help'
$VersionPy = Join-Path $ROOT 'src/sofa_jobs_navigator/version.py'

Write-Host "[mode] $Mode"

Write-Host "[0/6] Cleaning previous build artifacts..."
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue (Join-Path $ROOT 'build') | Out-Null
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue (Join-Path $ROOT 'dist')  | Out-Null
Remove-Item -Force -ErrorAction SilentlyContinue (Join-Path $ROOT "$AppName.spec") | Out-Null

Write-Host "[1/6] Ensuring PyInstaller and project deps are installed..."
python -m pip install --upgrade pip wheel setuptools | Out-Null
python -m pip install --upgrade pyinstaller | Out-Null
python -m pip install --upgrade -e . | Out-Null

Write-Host "[2/6] Preparing version resource..."
$Version = '0.0.0'
if (Test-Path $VersionPy) {
  $text = Get-Content $VersionPy -Raw -Encoding UTF8
  $m = [Regex]::Match($text, '^VERSION\s*(:\s*[^=]+)?\s*=\s*[\"\']([^\"\']+)[\"\']', 'Multiline')
  if ($m.Success) { $Version = $m.Groups[2].Value }
}
$verParts = ($Version -split '\.') + '0','0','0'
$verTuple = "{0, 0, 0, 0}" -f $verParts[0],$verParts[1],$verParts[2],0
$versionFile = Join-Path $ROOT 'packaging\windows\_version_info.txt'
$versionText = @"
VSVersionInfo(
  ffi=FixedFileInfo(filevers=($verTuple), prodvers=($verTuple), mask=0x3f, flags=0x0, OS=0x40004, fileType=0x1, subtype=0x0, date=(0, 0)),
  StringFileInfo([
    StringTable('040904B0', [
      StringStruct('CompanyName', 'Sofa Ops'),
      StringStruct('FileDescription', '$AppName'),
      StringStruct('FileVersion', '$Version'),
      StringStruct('InternalName', '$AppName'),
      StringStruct('LegalCopyright', 'Copyright (c) $(Get-Date -Format yyyy) Sofa Ops'),
      StringStruct('OriginalFilename', '$AppName.exe'),
      StringStruct('ProductName', '$AppName'),
      StringStruct('ProductVersion', '$Version')
    ])
  ]),
  VarFileInfo([VarStruct('Translation', [1033, 1200])])
)
"@
$versionText = $versionText.Replace('$verTuple', $verTuple)
Set-Content -Path $versionFile -Value $versionText -Encoding UTF8

Write-Host "[3/6] Running PyInstaller (onedir, $Mode)..."
$uiArgs = @()
if ($Mode -eq 'app') { $uiArgs += '--windowed' } else { $uiArgs += '--console' }

$helpPng = "$HelpDir\*.png;sofa_jobs_navigator/ui/assets/help"
$helpReadme = "$HelpDir\README.md;sofa_jobs_navigator/ui/assets/help"

pyinstaller `
  --noconfirm `
  --clean `
  --onedir `
  @uiArgs `
  --name "$AppName" `
  --version-file "$versionFile" `
  $(if (Test-Path $IconIco) { "--icon `"$IconIco`"" }) `
  --add-data "$helpPng" `
  --add-data "$helpReadme" `
  --collect-all googleapiclient `
  --collect-all google_auth_oauthlib `
  "run.py"

$DistDir = Join-Path $ROOT "dist\$AppName"
if (-not (Test-Path (Join-Path $DistDir "$AppName.exe"))) {
  throw "Build failed: missing $AppName.exe"
}

Write-Host "[4/6] Writing quickstart README..."
$readme = @'
Sofa Jobs Navigator (Windows)
=============================

How to run:
 - Double-click: Sofa Jobs Navigator\Sofa Jobs Navigator.exe

Reset preferences:
 - In-app: use the Reset option from the menu
 - Command line: "Sofa Jobs Navigator.exe" --factory-reset

First run (Google credentials):
 - Put your OAuth client JSON as credentials.json at:
   %APPDATA%\sofa_jobs_navigator\credentials.json
   (Or set env var SJN_CREDENTIALS_FILE=C:\path\to\credentials.json)

Logs:
 - %LOCALAPPDATA%\sofa_jobs_navigator\console_log.txt
 - %LOCALAPPDATA%\sofa_jobs_navigator\events.log
'
Set-Content -Path (Join-Path $DistDir 'README-FIRST.txt') -Value $readme -Encoding UTF8

Write-Host "[5/6] Creating Reset command..."
$resetCmd = "@echo off`r`n" + '"%~dp0Sofa Jobs Navigator.exe" --factory-reset %*' + "`r`n"
Set-Content -Path (Join-Path $DistDir 'Reset.cmd') -Value $resetCmd -Encoding ASCII

Write-Host "[6/6] Zipping artifact..."
$zipPath = Join-Path $ROOT 'dist\Sofa_Jobs_Navigator.zip'
if (Test-Path $zipPath) { Remove-Item $zipPath -Force }
Compress-Archive -Path (Join-Path $ROOT 'dist' $AppName '*') -DestinationPath $zipPath -Force

Write-Host "Build complete: $DistDir"
Write-Host "ZIP: $(Split-Path $zipPath -Leaf)"

