# HustleX Bot 24/7 Setup Script
# This script sets up the HustleX bot to run 24/7 without human intervention

param(
    [Parameter(Mandatory=$false)]
    [string]$BotToken = "",
    [Parameter(Mandatory=$false)]
    [switch]$SkipTokenPrompt
)

$ErrorActionPreference = 'Stop'

function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Test-BotToken {
    param([string]$Token)
    
    if ([string]::IsNullOrWhiteSpace($Token)) {
        return $false
    }
    
    # Basic token validation (Telegram bot tokens are typically 45+ characters)
    if ($Token.Length -lt 40) {
        return $false
    }
    
    # Check if token contains only valid characters
    if ($Token -match '[^A-Za-z0-9:_-]') {
        return $false
    }
    
    return $true
}

function Set-BotToken {
    param([string]$Token)
    
    Write-ColorOutput "Setting bot token..." "Yellow"
    
    # Set as environment variable for current user
    [Environment]::SetEnvironmentVariable("BOT_TOKEN", $Token, "User")
    
    # Set as environment variable for machine (requires admin)
    if (Test-Administrator) {
        [Environment]::SetEnvironmentVariable("BOT_TOKEN", $Token, "Machine")
        Write-ColorOutput "Bot token set for machine (all users)" "Green"
    } else {
        Write-ColorOutput "Bot token set for current user only" "Yellow"
        Write-ColorOutput "Run as administrator to set for all users" "Yellow"
    }
    
    # Also set for current session
    $env:BOT_TOKEN = $Token
}

function Install-Dependencies {
    Write-ColorOutput "Installing Python dependencies..." "Yellow"
    
    $installScript = Join-Path $PSScriptRoot "install_aiohttp.ps1"
    if (Test-Path $installScript) {
        try {
            & $installScript
            Write-ColorOutput "Dependencies installed successfully!" "Green"
        }
        catch {
            Write-ColorOutput "Failed to install dependencies: $($_.Exception.Message)" "Red"
            return $false
        }
    } else {
        Write-ColorOutput "Dependency installation script not found" "Red"
        return $false
    }
    
    return $true
}

function Install-Service {
    Write-ColorOutput "Installing HustleX Bot service..." "Yellow"
    
    $installScript = Join-Path $PSScriptRoot "install_service.ps1"
    if (Test-Path $installScript) {
        try {
            & $installScript
            Write-ColorOutput "Service installed successfully!" "Green"
            return $true
        }
        catch {
            Write-ColorOutput "Failed to install service: $($_.Exception.Message)" "Red"
            return $false
        }
    } else {
        Write-ColorOutput "Service installation script not found" "Red"
        return $false
    }
}

function Setup-Monitoring {
    Write-ColorOutput "Setting up monitoring..." "Yellow"
    
    $monitorScript = Join-Path $PSScriptRoot "setup_monitoring.ps1"
    if (Test-Path $monitorScript) {
        try {
            & $monitorScript
            Write-ColorOutput "Monitoring setup completed!" "Green"
            return $true
        }
        catch {
            Write-ColorOutput "Failed to setup monitoring: $($_.Exception.Message)" "Red"
            return $false
        }
    } else {
        Write-ColorOutput "Monitoring setup script not found" "Red"
        return $false
    }
}

function Test-Setup {
    Write-ColorOutput "Testing setup..." "Yellow"
    
    # Test service
    try {
        $service = Get-Service -Name "HustleXBot" -ErrorAction Stop
        if ($service.Status -eq "Running") {
            Write-ColorOutput "✅ Service is running" "Green"
        } else {
            Write-ColorOutput "⚠️ Service is not running (Status: $($service.Status))" "Yellow"
        }
    }
    catch {
        Write-ColorOutput "❌ Service not found" "Red"
        return $false
    }
    
    # Test monitoring task
    try {
        $task = Get-ScheduledTask -Name "HustleXBotMonitor" -ErrorAction Stop
        Write-ColorOutput "✅ Monitoring task configured" "Green"
    }
    catch {
        Write-ColorOutput "❌ Monitoring task not found" "Red"
    }
    
    # Test bot token
    $currentToken = [Environment]::GetEnvironmentVariable("BOT_TOKEN", "Machine")
    if ([string]::IsNullOrWhiteSpace($currentToken)) {
        $currentToken = [Environment]::GetEnvironmentVariable("BOT_TOKEN", "User")
    }
    
    if (Test-BotToken $currentToken) {
        Write-ColorOutput "✅ Bot token configured" "Green"
    } else {
        Write-ColorOutput "❌ Bot token not configured or invalid" "Red"
    }
    
    return $true
}

function Show-Status {
    Write-ColorOutput "`nHustleX Bot 24/7 Status" "Cyan"
    Write-ColorOutput "=======================" "Cyan"
    
    # Service status
    try {
        $service = Get-Service -Name "HustleXBot" -ErrorAction Stop
        Write-ColorOutput "Service: $($service.Status)" $(if ($service.Status -eq "Running") { "Green" } else { "Red" })
        Write-ColorOutput "Start Type: $($service.StartType)" "White"
    }
    catch {
        Write-ColorOutput "Service: NOT INSTALLED" "Red"
    }
    
    # Monitoring status
    try {
        $task = Get-ScheduledTask -Name "HustleXBotMonitor" -ErrorAction Stop
        Write-ColorOutput "Monitoring: $($task.State)" $(if ($task.State -eq "Ready") { "Green" } else { "Yellow" })
    }
    catch {
        Write-ColorOutput "Monitoring: NOT CONFIGURED" "Red"
    }
    
    # Bot token status
    $token = [Environment]::GetEnvironmentVariable("BOT_TOKEN", "Machine")
    if ([string]::IsNullOrWhiteSpace($token)) {
        $token = [Environment]::GetEnvironmentVariable("BOT_TOKEN", "User")
    }
    
    if (Test-BotToken $token) {
        Write-ColorOutput "Bot Token: ✅ Configured" "Green"
    } else {
        Write-ColorOutput "Bot Token: ❌ Not configured" "Red"
    }
    
    # Log files
    $logDir = 'C:\nssm'
    $serviceLog = Join-Path $logDir 'hustlex_service.log'
    $monitorLog = Join-Path $logDir 'monitor.log'
    
    if (Test-Path $serviceLog) {
        $logSize = (Get-Item $serviceLog).Length
        Write-ColorOutput "Service Log: Found ($logSize bytes)" "Green"
    } else {
        Write-ColorOutput "Service Log: Not found" "Red"
    }
    
    if (Test-Path $monitorLog) {
        $logSize = (Get-Item $monitorLog).Length
        Write-ColorOutput "Monitor Log: Found ($logSize bytes)" "Green"
    } else {
        Write-ColorOutput "Monitor Log: Not found" "Red"
    }
}

# Main execution
Write-ColorOutput "HustleX Bot 24/7 Setup" "Cyan"
Write-ColorOutput "=====================" "Cyan"

# Check administrator privileges
if (-not (Test-Administrator)) {
    Write-ColorOutput "❌ This script requires administrator privileges!" "Red"
    Write-ColorOutput "Please run PowerShell as Administrator and try again." "Yellow"
    exit 1
}

# Get bot token if not provided
if ([string]::IsNullOrWhiteSpace($BotToken) -and -not $SkipTokenPrompt) {
    Write-ColorOutput "`nBot Token Configuration" "Yellow"
    Write-ColorOutput "=======================" "Yellow"
    Write-ColorOutput "To run 24/7, the bot needs a valid Telegram token." "White"
    Write-ColorOutput "Get your token from @BotFather on Telegram." "White"
    
    do {
        $BotToken = Read-Host "Enter your Telegram Bot token"
        if (-not (Test-BotToken $BotToken)) {
            Write-ColorOutput "Invalid token format. Please try again." "Red"
        }
    } while (-not (Test-BotToken $BotToken))
}

# Set bot token
if (-not [string]::IsNullOrWhiteSpace($BotToken)) {
    Set-BotToken $BotToken
}

# Install dependencies
Write-ColorOutput "`nStep 1: Installing Dependencies" "Cyan"
if (-not (Install-Dependencies)) {
    Write-ColorOutput "❌ Dependency installation failed!" "Red"
    exit 1
}

# Install service
Write-ColorOutput "`nStep 2: Installing Service" "Cyan"
if (-not (Install-Service)) {
    Write-ColorOutput "❌ Service installation failed!" "Red"
    exit 1
}

# Setup monitoring
Write-ColorOutput "`nStep 3: Setting up Monitoring" "Cyan"
if (-not (Setup-Monitoring)) {
    Write-ColorOutput "❌ Monitoring setup failed!" "Red"
    exit 1
}

# Test setup
Write-ColorOutput "`nStep 4: Testing Setup" "Cyan"
Test-Setup

# Show final status
Show-Status

Write-ColorOutput "`n🎉 HustleX Bot 24/7 Setup Complete!" "Green"
Write-ColorOutput "The bot is now configured to run 24/7 without human intervention." "Green"
Write-ColorOutput "`nManagement Commands:" "Yellow"
Write-ColorOutput "• .\manage_service.ps1 -Action status    # Check service status" "White"
Write-ColorOutput "• .\manage_service.ps1 -Action restart  # Restart service" "White"
Write-ColorOutput "• .\manage_service.ps1 -Action logs    # View logs" "White"
Write-ColorOutput "• .\manage_service.ps1 -Action health  # Health check" "White"


