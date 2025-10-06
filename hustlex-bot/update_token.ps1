# PowerShell script to update the Telegram Bot token

# Get the script directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Main.py file path
$mainPyPath = Join-Path $scriptDir "bot\main.py"

# Check if the file exists
if (-not (Test-Path $mainPyPath)) {
    Write-Host "ERROR: Bot main.py file not found at $mainPyPath" -ForegroundColor Red
    exit 1
}

Write-Host "Updating Telegram Bot token..." -ForegroundColor Cyan

# Ask for the bot token
$botToken = Read-Host -Prompt "Enter your Telegram Bot token"

if ([string]::IsNullOrWhiteSpace($botToken)) {
    Write-Host "ERROR: Bot token cannot be empty" -ForegroundColor Red
    exit 1
}

# Read the file content
$content = Get-Content -Path $mainPyPath -Raw

# Replace the dummy token with the actual token
# This assumes the token is defined in a variable like TOKEN = "dummy_token"
$updatedContent = $content -replace '(TOKEN\s*=\s*["''])([^"'']*?)(["''])', "\`$1$botToken\`$3"

# Write the updated content back to the file
Set-Content -Path $mainPyPath -Value $updatedContent

Write-Host "Bot token updated successfully!" -ForegroundColor Green
Write-Host "\nPress any key to continue..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")