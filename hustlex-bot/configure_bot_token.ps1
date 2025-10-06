# Configure Bot Token Script
# This script helps you set up a real Telegram bot token

$ErrorActionPreference = 'Stop'

function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

function Test-BotToken {
    param([string]$Token)
    
    if ([string]::IsNullOrWhiteSpace($Token)) {
        return $false
    }
    
    # Check if it's still the placeholder
    if ($Token -eq "your_bot_token_here") {
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

function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Show-TokenInstructions {
    Write-ColorOutput "🤖 Telegram Bot Token Setup" "Cyan"
    Write-ColorOutput "============================" "Cyan"
    Write-ColorOutput ""
    Write-ColorOutput "To get a Telegram bot token:" "White"
    Write-ColorOutput "1. Open Telegram and search for @BotFather" "White"
    Write-ColorOutput "2. Send /newbot command" "White"
    Write-ColorOutput "3. Follow the instructions to create your bot" "White"
    Write-ColorOutput "4. Copy the token that BotFather gives you" "White"
    Write-ColorOutput ""
    Write-ColorOutput "The token looks like: 1234567890:ABCdefGHIjklMNOpqrsTUVwxyz" "Yellow"
    Write-ColorOutput ""
}

# Main execution
Write-ColorOutput "HustleX Bot Token Configuration" "Cyan"
Write-ColorOutput "===============================" "Cyan"

# Check current token
$currentToken = [Environment]::GetEnvironmentVariable("BOT_TOKEN", "Machine")
if ([string]::IsNullOrWhiteSpace($currentToken)) {
    $currentToken = [Environment]::GetEnvironmentVariable("BOT_TOKEN", "User")
}

if (Test-BotToken $currentToken) {
    Write-ColorOutput "✅ Bot token is already configured!" "Green"
    Write-ColorOutput "Current token: $($currentToken.Substring(0, 10))..." "White"
    
    $update = Read-Host "Do you want to update it? (y/n)"
    if ($update -ne "y" -and $update -ne "Y") {
        Write-ColorOutput "Token configuration skipped." "Yellow"
        exit 0
    }
} else {
    Show-TokenInstructions
}

# Get new token
do {
    Write-ColorOutput ""
    $newToken = Read-Host "Enter your Telegram Bot token"
    
    if (-not (Test-BotToken $newToken)) {
        Write-ColorOutput "❌ Invalid token format. Please try again." "Red"
        Write-ColorOutput "Token should be at least 40 characters long and contain only letters, numbers, colons, underscores, and hyphens." "Yellow"
    }
} while (-not (Test-BotToken $newToken))

# Set the token
Set-BotToken $newToken

Write-ColorOutput ""
Write-ColorOutput "✅ Bot token configured successfully!" "Green"
Write-ColorOutput ""
Write-ColorOutput "Next steps:" "Yellow"
Write-ColorOutput "1. Test the bot: python test_bot_direct.py" "White"
Write-ColorOutput "2. Restart the service: .\manage_service.ps1 -Action restart" "White"
Write-ColorOutput "3. Check status: .\manage_service.ps1 -Action status" "White"


