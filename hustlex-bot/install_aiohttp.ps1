# PowerShell script to install aiohttp in the virtual environment

# Get the script directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Python executable path in virtual environment
$pythonExe = Join-Path $scriptDir ".venv\Scripts\python.exe"

# Check if Python exists
if (-not (Test-Path $pythonExe)) {
    Write-Host "ERROR: Python executable not found at $pythonExe" -ForegroundColor Red
    exit 1
}

Write-Host "Installing aiohttp in virtual environment..." -ForegroundColor Cyan

# Install aiohttp using the virtual environment's pip
& $pythonExe -m pip install aiohttp

Write-Host "\nVerifying installation..." -ForegroundColor Cyan

# Check if aiohttp is installed
$packages = & $pythonExe -m pip list
$aiohttp = $packages | Select-String "aiohttp"

if ($aiohttp) {
    Write-Host "aiohttp is installed successfully." -ForegroundColor Green
    Write-Host $aiohttp
} else {
    Write-Host "ERROR: aiohttp installation failed." -ForegroundColor Red
}

Write-Host "\nPress any key to continue..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")