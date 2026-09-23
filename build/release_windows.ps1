$ErrorActionPreference = "Stop"

$Root = (Resolve-Path "$PSScriptRoot\..").Path
Set-Location $Root

$ConfigText = Get-Content ".\src\config.py" -Raw
$VersionMatch = [regex]::Match($ConfigText, 'APP_VERSION\s*=\s*"([^"]+)"')
if (-not $VersionMatch.Success) {
    throw "Unable to read APP_VERSION from src\config.py"
}
$Version = $VersionMatch.Groups[1].Value

Write-Host "== JAM $Version release build ==" -ForegroundColor Cyan

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    throw "Missing .venv. Create it once with: python -m venv .venv"
}

# Remove development-only caches. User runtime data lives outside the project.
Write-Host "Cleaning development caches..." -ForegroundColor DarkCyan
Get-ChildItem -Path "." -Directory -Recurse -Force -Filter "__pycache__" -ErrorAction SilentlyContinue |
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force ".\.pytest_cache" -ErrorAction SilentlyContinue

& powershell -ExecutionPolicy Bypass -File ".\build\build_windows.ps1"
if ($LASTEXITCODE -ne 0) {
    throw "Application build failed."
}

$ProgramFilesX86 = [Environment]::GetFolderPath("ProgramFilesX86")
$ProgramFiles64 = [Environment]::GetFolderPath("ProgramFiles")
$LocalPrograms = Join-Path $env:LOCALAPPDATA "Programs"

$InnoCandidates = @(
    (Join-Path $ProgramFilesX86 "Inno Setup 6\ISCC.exe"),
    (Join-Path $ProgramFiles64 "Inno Setup 6\ISCC.exe"),
    (Join-Path $LocalPrograms "Inno Setup 6\ISCC.exe")
)

$ISCC = $InnoCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $ISCC) {
    throw @"
Inno Setup 6 is required on your development PC to create JAM Setup.exe.
Install it, then run this script again.
Quick option:
winget install JRSoftware.InnoSetup
"@
}

# Keep the Inno compiler output outside the Desktop/project tree. This mirrors
# the proven CVM workaround for EndUpdateResource error 110 on this PC.
$InstallerBuildDir = Join-Path $env:LOCALAPPDATA "JAMInstallerBuild"
Remove-Item -Recurse -Force $InstallerBuildDir -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path $InstallerBuildDir | Out-Null

Write-Host "Building branded bilingual JAM installer..." -ForegroundColor DarkCyan
& $ISCC "-o$InstallerBuildDir" "/DMyAppVersion=$Version" ".\build\JAM.iss"
if ($LASTEXITCODE -ne 0) {
    throw "Inno Setup build failed."
}

$Installer = Join-Path $InstallerBuildDir "JAM-Setup-$Version.exe"
if (-not (Test-Path $Installer)) {
    throw "Installer was not created at $Installer"
}

$ReleaseDir = ".\release"
$PackageDir = Join-Path $ReleaseDir "JAM-v$Version-Windows-x64"
$ZipPath = Join-Path $ReleaseDir "JAM-v$Version-Windows-x64.zip"
$SetupCopy = Join-Path $ReleaseDir "JAM-Setup-$Version.exe"
$HashFile = Join-Path $ReleaseDir "SHA256.txt"

Remove-Item -Recurse -Force $ReleaseDir -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path $PackageDir | Out-Null

Copy-Item $Installer $SetupCopy -Force
Copy-Item $Installer (Join-Path $PackageDir "JAM-Setup-$Version.exe") -Force

$ReadmeTemplate = Get-Content ".\build\README-FIRST.txt" -Raw
$ReadmeText = $ReadmeTemplate.Replace("{{VERSION}}", $Version)
$ReadmeText | Set-Content -Path (Join-Path $PackageDir "README.txt") -Encoding UTF8

Compress-Archive -Path "$PackageDir\*" -DestinationPath $ZipPath -CompressionLevel Optimal -Force

$SetupHash = (Get-FileHash -Algorithm SHA256 $SetupCopy).Hash.ToLowerInvariant()
$ZipHash = (Get-FileHash -Algorithm SHA256 $ZipPath).Hash.ToLowerInvariant()

@"
JAM $Version - SHA256

$SetupHash JAM-Setup-$Version.exe
$ZipHash JAM-v$Version-Windows-x64.zip
"@ | Set-Content -Path $HashFile -Encoding UTF8

Remove-Item -Recurse -Force $PackageDir

Write-Host ""
Write-Host "RELEASE READY" -ForegroundColor Green
Write-Host "  $SetupCopy"
Write-Host "  $ZipPath"
Write-Host "  $HashFile"
Write-Host ""
Write-Host "Normal users download the ZIP. It extracts to Setup.exe + README.txt." -ForegroundColor Green
Write-Host "For GitHub Releases upload Setup EXE, ZIP and SHA256.txt." -ForegroundColor Green
Write-Host "The updater specifically needs the Setup EXE + SHA256.txt on the Release." -ForegroundColor Yellow
