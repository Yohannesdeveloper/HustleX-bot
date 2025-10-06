# PowerShell script to set up HustleX Bot for 24/7 operation
# This script installs the service and configures it for automatic startup

$ErrorActionPreference = 'Stop'

Write-Host "Setting up HustleX Bot for 24/7 operation..." -ForegroundColor Cyan

# Get script directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$logDir = 'C:\nssm'

# Create log directory if it doesn't exist
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
    Write-Host "Created log directory: $logDir" -ForegroundColor Green
}

# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")

if (-not $isAdmin) {
    Write-Host "This script requires administrator privileges. Please run as administrator." -ForegroundColor Red
    Write-Host "Right-click PowerShell and select 'Run as administrator'" -ForegroundColor Yellow
    exit 1
}

# Check if NSSM is available
$nssmZip = Join-Path $logDir 'nssm-2.24.zip'
$nssmRoot = Join-Path $logDir 'nssm-2.24'
$nssm = $null

if (-not (Test-Path $nssmRoot)) {
    Write-Host "Downloading NSSM..." -ForegroundColor Yellow
    try {
        Invoke-WebRequest -UseBasicParsing -Uri 'https://nssm.cc/release/nssm-2.24.zip' -OutFile $nssmZip
        Expand-Archive -Path $nssmZip -DestinationPath $logDir -Force
        Write-Host "NSSM downloaded and extracted successfully" -ForegroundColor Green
    } catch {
        Write-Host "Failed to download NSSM: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
}

# Find NSSM executable
$nssm = Join-Path $nssmRoot 'win64\nssm.exe'
if (-not (Test-Path $nssm)) { 
    $nssm = Join-Path $nssmRoot 'win32\nssm.exe' 
}
if (-not (Test-Path $nssm)) { 
    Write-Host "NSSM executable not found after download/extract." -ForegroundColor Red
    exit 1
}

Write-Host "Using NSSM: $nssm" -ForegroundColor Green

# Check required files
$pythonExe = Join-Path $scriptDir '.venv\Scripts\python.exe'
$runner = Join-Path $scriptDir 'service_runner.py'
$healthMonitor = Join-Path $scriptDir 'health_monitor.py'

if (-not (Test-Path $pythonExe)) { 
    Write-Host "Python virtual environment not found: $pythonExe" -ForegroundColor Red
    Write-Host "Please run install_deps.bat first to set up the virtual environment" -ForegroundColor Yellow
    exit 1
}
if (-not (Test-Path $runner)) { 
    Write-Host "Service runner not found: $runner" -ForegroundColor Red
    exit 1
}

# Check for BOT_TOKEN
$botToken = [Environment]::GetEnvironmentVariable('BOT_TOKEN','Machine')
if ([string]::IsNullOrWhiteSpace($botToken)) { 
    $botToken = [Environment]::GetEnvironmentVariable('BOT_TOKEN','User') 
}
if ([string]::IsNullOrWhiteSpace($botToken)) {
    Write-Host "BOT_TOKEN not found in environment variables." -ForegroundColor Red
    Write-Host "Please set your bot token first:" -ForegroundColor Yellow
    Write-Host "  [Environment]::SetEnvironmentVariable('BOT_TOKEN', 'your_token_here', 'Machine')" -ForegroundColor Cyan
    exit 1
}

Write-Host "Bot token found in environment variables" -ForegroundColor Green

# Remove existing service if it exists
Write-Host "Removing existing HustleXBot service..." -ForegroundColor Yellow
& $nssm remove HustleXBot confirm 2>$null | Out-Null

# Install the service
Write-Host "Installing HustleXBot service..." -ForegroundColor Yellow
& $nssm install HustleXBot $pythonExe $runner
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to install service" -ForegroundColor Red
    exit 1
}

# Configure the service
Write-Host "Configuring service settings..." -ForegroundColor Yellow

# Set working directory
& $nssm set HustleXBot AppDirectory $scriptDir
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to set working directory" -ForegroundColor Red
    exit 1
}

# Set startup type to automatic
& $nssm set HustleXBot Start SERVICE_AUTO_START
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to set startup type" -ForegroundColor Red
    exit 1
}

# Set log files
& $nssm set HustleXBot AppStdout (Join-Path $logDir 'hustlex_service.log')
& $nssm set HustleXBot AppStderr (Join-Path $logDir 'hustlex_service.log')

# Set restart behavior
& $nssm set HustleXBot AppThrottle 1500
& $nssm set HustleXBot AppExit Default Restart
& $nssm set HustleXBot AppRestartDelay 5000

# Set service description
& $nssm set HustleXBot Description "HustleX Telegram Bot - 24/7 Job Posting Service"

# Set service to restart on failure
& $nssm set HustleXBot AppExit Default Restart
& $nssm set HustleXBot AppRestartDelay 5000

Write-Host "Service configured successfully" -ForegroundColor Green

# Start the service
Write-Host "Starting HustleXBot service..." -ForegroundColor Yellow
& $nssm start HustleXBot
if ($LASTEXITCODE -eq 0) {
    Write-Host "HustleXBot service started successfully!" -ForegroundColor Green
} else {
    Write-Host "Failed to start service" -ForegroundColor Red
    exit 1
}

# Check service status
Write-Host "Checking service status..." -ForegroundColor Yellow
& $nssm status HustleXBot

# Set up health monitoring as a scheduled task
Write-Host "Setting up health monitoring..." -ForegroundColor Yellow

$taskName = "HustleXBotHealthMonitor"
$taskAction = New-ScheduledTaskAction -Execute "python.exe" -Argument "`"$healthMonitor`"" -WorkingDirectory $scriptDir
$taskTrigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 5) -RepetitionDuration (New-TimeSpan -Days 365)
$taskSettings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

# Remove existing task if it exists
Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue

# Register the new task
Register-ScheduledTask -TaskName $taskName -Action $taskAction -Trigger $taskTrigger -Settings $taskSettings -Description "Health monitoring for HustleX Bot" | Out-Null

Write-Host "Health monitoring scheduled task created" -ForegroundColor Green

# Create startup shortcut as backup
Write-Host "Creating startup shortcut as backup..." -ForegroundColor Yellow
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\HustleXBot.lnk")
$Shortcut.TargetPath = "$scriptDir\run_bot_with_venv.bat"
$Shortcut.WorkingDirectory = $scriptDir
$Shortcut.Description = "HustleX Bot - Backup Startup"
$Shortcut.WindowStyle = 7  # Minimized
$Shortcut.Save()

Write-Host "Startup shortcut created" -ForegroundColor Green

# Display final status
Write-Host "`n=== HustleX Bot 24/7 Setup Complete ===" -ForegroundColor Green
Write-Host "Service Status:" -ForegroundColor Cyan
& $nssm status HustleXBot

Write-Host "`nLog Files:" -ForegroundColor Cyan
Write-Host "  Service Log: $logDir\hustlex_service.log" -ForegroundColor White
Write-Host "  Health Monitor: $logDir\hustlex_health.log" -ForegroundColor White

Write-Host "`nManagement Commands:" -ForegroundColor Cyan
Write-Host "  Start Service:   sc start HustleXBot" -ForegroundColor White
Write-Host "  Stop Service:   sc stop HustleXBot" -ForegroundColor White
Write-Host "  Service Status: sc query HustleXBot" -ForegroundColor White
Write-Host "  View Logs:      Get-Content $logDir\hustlex_service.log -Tail 50" -ForegroundColor White

Write-Host "`nThe bot will now:" -ForegroundColor Green
Write-Host "  ✓ Start automatically when Windows boots" -ForegroundColor White
Write-Host "  ✓ Restart automatically if it crashes" -ForegroundColor White
Write-Host "  ✓ Monitor its own health every 5 minutes" -ForegroundColor White
Write-Host "  ✓ Log all activity for troubleshooting" -ForegroundColor White

Write-Host "`nYour HustleX Bot is now running 24/7! 🚀" -ForegroundColor Green
