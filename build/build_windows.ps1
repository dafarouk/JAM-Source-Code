$ErrorActionPreference = "Stop"

$Root = (Resolve-Path "$PSScriptRoot\..").Path
Set-Location $Root

$ConfigText = Get-Content ".\src\config.py" -Raw
$VersionMatch = [regex]::Match($ConfigText, 'APP_VERSION\s*=\s*"([^"]+)"')
if (-not $VersionMatch.Success) {
    throw "Unable to read APP_VERSION from src\config.py"
}
$Version = $VersionMatch.Groups[1].Value

Write-Host "== JAM $Version Windows build ==" -ForegroundColor Cyan

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    throw "Missing .venv. Create it first with: python -m venv .venv"
}

$Python = ".\.venv\Scripts\python.exe"

Write-Host "Checking build dependencies..." -ForegroundColor DarkCyan
& $Python -m pip install -r ".\requirements.txt"
if ($LASTEXITCODE -ne 0) {
    throw "Dependency installation failed."
}

Write-Host "Preparing the offline multilingual Analyzer model..." -ForegroundColor DarkCyan
& $Python ".\build\prepare_semantic_model.py"
if ($LASTEXITCODE -ne 0) {
    throw "Semantic model preparation failed."
}

Write-Host "Generating Windows version metadata..." -ForegroundColor DarkCyan
& $Python ".\build\generate_version_info.py"
if ($LASTEXITCODE -ne 0) {
    throw "Version metadata generation failed."
}

Write-Host "Running release packaging tests..." -ForegroundColor DarkCyan
& $Python -m pytest -q ".\tests\test_release_packaging.py" ".\tests\test_updater_release.py"
if ($LASTEXITCODE -ne 0) {
    throw "Release tests failed. Build cancelled."
}

Remove-Item -Recurse -Force ".\build\pyinstaller" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force ".\dist\JAM" -ErrorAction SilentlyContinue

Write-Host "Building JAM.exe with PyInstaller..." -ForegroundColor DarkCyan
& $Python -m PyInstaller `
    --noconfirm `
    --clean `
    --workpath ".\build\pyinstaller" `
    ".\build\JAM.spec"

if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller build failed."
}

$Exe = ".\dist\JAM\JAM.exe"
if (-not (Test-Path $Exe)) {
    throw "Expected executable was not created: $Exe"
}

Write-Host ""
Write-Host "WINDOWS BUILD READY" -ForegroundColor Green
Write-Host "  $Exe"
Write-Host ""
Write-Host "The bundled Analyzer model is included for offline first-use." -ForegroundColor Green
