# Installs and starts HustleXBot as a Windows service using NSSM

$ErrorActionPreference = 'Stop'

$proj = Split-Path -Parent $MyInvocation.MyCommand.Path
$logDir = 'C:\nssm'
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir | Out-Null }

# Ensure NSSM is available
$nssmZip = Join-Path $logDir 'nssm-2.24.zip'
$nssmRoot = Join-Path $logDir 'nssm-2.24'
if (-not (Test-Path $nssmRoot)) {
  Invoke-WebRequest -UseBasicParsing -Uri 'https://nssm.cc/release/nssm-2.24.zip' -OutFile $nssmZip
  Expand-Archive -Path $nssmZip -DestinationPath $logDir -Force
}
$nssm = Join-Path $nssmRoot 'win64\nssm.exe'
if (-not (Test-Path $nssm)) { $nssm = Join-Path $nssmRoot 'win32\nssm.exe' }
if (-not (Test-Path $nssm)) { throw 'nssm.exe not found after download/extract.' }

# Paths
$pythonExe = Join-Path $proj '.venv\Scripts\python.exe'
$runner = Join-Path $proj 'service_runner.py'
if (-not (Test-Path $pythonExe)) { throw "Python venv not found: $pythonExe" }
if (-not (Test-Path $runner)) { throw "Missing service runner: $runner" }

# Install/Configure service
& $nssm remove HustleXBot confirm | Out-Null 2>$null
& $nssm install HustleXBot $pythonExe $runner
& $nssm set HustleXBot AppDirectory $proj
& $nssm set HustleXBot Start SERVICE_AUTO_START
& $nssm set HustleXBot AppStdout (Join-Path $logDir 'hustlex_service.log')
& $nssm set HustleXBot AppStderr (Join-Path $logDir 'hustlex_service.log')
& $nssm set HustleXBot AppThrottle 1500

# Start if BOT_TOKEN present
$botToken = [Environment]::GetEnvironmentVariable('BOT_TOKEN','Machine')
if ([string]::IsNullOrWhiteSpace($botToken)) { $botToken = [Environment]::GetEnvironmentVariable('BOT_TOKEN','User') }
if ([string]::IsNullOrWhiteSpace($botToken)) {
  Write-Host 'BOT_TOKEN not set in Machine/User environment. Service installed but not started.'
} else {
  & $nssm start HustleXBot | Out-Null
  Write-Host 'HustleXBot service started.'
}

& $nssm status HustleXBot
if (Test-Path (Join-Path $logDir 'hustlex_service.log')) {
  Get-Content -Path (Join-Path $logDir 'hustlex_service.log') -Tail 50
} else {
  Write-Host 'Log file not found yet.'
}




