# PowerShell script to test the bot startup

Write-Host "Starting bot test..." -ForegroundColor Cyan

# Get the script directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Main.py file path
$mainPyPath = Join-Path $scriptDir "bot\main.py"

# Check if the file exists
if (-not (Test-Path $mainPyPath)) {
    Write-Host "ERROR: Bot main.py file not found at $mainPyPath" -ForegroundColor Red
    exit 1
}

# Check for dummy token in the main.py file
$content = Get-Content -Path $mainPyPath -Raw
if ($content -match 'TOKEN\s*=\s*["'']dummy_token["'']') {
    Write-Host "WARNING: Bot is using a dummy token. Please update the token using update_token.ps1" -ForegroundColor Yellow
}

# Clear existing log files
$logDir = "C:\nssm"
$logFile = "$logDir\hustlex_bot_output.log"
$errorLogFile = "$logDir\hustlex_bot_error.log"

if (Test-Path $logFile) {
    Clear-Content -Path $logFile
}

if (Test-Path $errorLogFile) {
    Clear-Content -Path $errorLogFile
}

# Run the bot
& "$scriptDir\run_bot.ps1"

# Wait for the bot to start
Start-Sleep -Seconds 5

# Check if the bot is running
$botProcess = Get-Process | Where-Object {$_.Path -like "*python*"} | Where-Object {$_.CommandLine -like "*bot.main*"}

if ($botProcess) {
    Write-Host "SUCCESS: Bot process is running!" -ForegroundColor Green
} else {
    Write-Host "WARNING: No Python process found. Bot may not be running." -ForegroundColor Yellow
}

# Check log files
Write-Host "\nChecking log files:" -ForegroundColor Cyan

# Check output log
if (Test-Path $logFile) {
    Write-Host "Output log exists at: $logFile" -ForegroundColor Green
    Write-Host "Log content:"
    Get-Content -Path $logFile
} else {
    Write-Host "Output log file not found at: $logFile" -ForegroundColor Red
}

# Check error log
if (Test-Path $errorLogFile) {
    Write-Host "Error log exists at: $errorLogFile" -ForegroundColor Green
    Write-Host "Error log content:"
    Get-Content -Path $errorLogFile
} else {
    Write-Host "Error log file not found at: $errorLogFile" -ForegroundColor Red
}

Write-Host "\nTest completed. Please check the results above." -ForegroundColor Cyan