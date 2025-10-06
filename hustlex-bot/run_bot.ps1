# PowerShell script to run the HustleX Bot in the background

# Create log directory if it doesn't exist
$logDir = "C:\nssm"
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

# Log file path
$logFile = "$logDir\hustlex_bot_output.log"
$errorLogFile = "$logDir\hustlex_bot_error.log"

# Get the script directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Python executable path in virtual environment
$pythonExe = Join-Path $scriptDir ".venv\Scripts\python.exe"

# Log startup information
"Starting bot at $(Get-Date)" | Out-File -FilePath $logFile
"Working directory: $scriptDir" | Out-File -FilePath $logFile -Append
"Python path: $pythonExe" | Out-File -FilePath $logFile -Append

# Check if Python exists
if (-not (Test-Path $pythonExe)) {
    "ERROR: Python executable not found at $pythonExe" | Out-File -FilePath $errorLogFile
    exit 1
}

# Start the bot process using the virtual environment's Python
Start-Process -FilePath $pythonExe -ArgumentList "-m", "bot.main" -WorkingDirectory $scriptDir -WindowStyle Hidden -RedirectStandardOutput $logFile -RedirectStandardError $errorLogFile

Write-Host "HustleX Bot has been started in the background."
Write-Host "Check $logFile for output."
Write-Host "Check $errorLogFile for any errors."