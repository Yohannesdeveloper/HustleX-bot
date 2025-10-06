# Simple Service Installation for HustleX Bot
# This script installs the bot as a Windows service using NSSM

param(
    [string]$ServiceName = "HustleXBot",
    [string]$DisplayName = "HustleX Bot Service"
)

# Get the current directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = $ScriptDir

Write-Host "Installing HustleX Bot Service..." -ForegroundColor Green
Write-Host "Project Directory: $ProjectDir" -ForegroundColor Yellow

# Check if NSSM is available
$nssmPath = "C:\nssm\nssm.exe"
if (-not (Test-Path $nssmPath)) {
    Write-Host "NSSM not found at $nssmPath" -ForegroundColor Red
    Write-Host "Please download NSSM first" -ForegroundColor Yellow
    exit 1
}

# Python executable path
$pythonExe = Join-Path $ProjectDir ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    Write-Host "Python venv not found: $pythonExe" -ForegroundColor Red
    Write-Host "Please create virtual environment first" -ForegroundColor Yellow
    exit 1
}

# Bot main script path
$botScript = Join-Path $ProjectDir "bot\main.py"

Write-Host "Python executable: $pythonExe" -ForegroundColor Cyan
Write-Host "Bot script: $botScript" -ForegroundColor Cyan

# Uninstall existing service if it exists
Write-Host "Removing existing service (if any)..." -ForegroundColor Yellow
& $nssmPath remove $ServiceName confirm

# Install the service
Write-Host "Installing service..." -ForegroundColor Green
& $nssmPath install $ServiceName $pythonExe $botScript

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error creating service!" -ForegroundColor Red
    exit 1
}

# Set service parameters
Write-Host "Configuring service parameters..." -ForegroundColor Green

# Set working directory
& $nssmPath set $ServiceName AppDirectory $ProjectDir

# Set display name
& $nssmPath set $ServiceName DisplayName $DisplayName

# Set description
& $nssmPath set $ServiceName Description "HustleX Telegram Bot - 24/7 Service"

# Set startup type to automatic
& $nssmPath set $ServiceName Start SERVICE_AUTO_START

# Set output files
$logDir = Join-Path $ProjectDir "logs"
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

$stdoutFile = Join-Path $logDir "service_stdout.log"
$stderrFile = Join-Path $logDir "service_stderr.log"

& $nssmPath set $ServiceName AppStdout $stdoutFile
& $nssmPath set $ServiceName AppStderr $stderrFile

# Set environment variables
& $nssmPath set $ServiceName AppEnvironmentExtra "BOT_TOKEN=$env:BOT_TOKEN"

# Start the service
Write-Host "Starting service..." -ForegroundColor Green
& $nssmPath start $ServiceName

if ($LASTEXITCODE -eq 0) {
    Write-Host "HustleXBot service installed and started successfully!" -ForegroundColor Green
    Write-Host "Service Name: $ServiceName" -ForegroundColor Cyan
    Write-Host "Display Name: $DisplayName" -ForegroundColor Cyan
    Write-Host "Working Directory: $ProjectDir" -ForegroundColor Cyan
    Write-Host "Logs: $logDir" -ForegroundColor Cyan
} else {
    Write-Host "Error starting service!" -ForegroundColor Red
    exit 1
}

Write-Host "`nService Management Commands:" -ForegroundColor Yellow
Write-Host "  Start:   .\manage_service.ps1 -Action start" -ForegroundColor White
Write-Host "  Stop:    .\manage_service.ps1 -Action stop" -ForegroundColor White
Write-Host "  Status:  .\manage_service.ps1 -Action status" -ForegroundColor White
Write-Host "  Logs:    .\manage_service.ps1 -Action logs" -ForegroundColor White


