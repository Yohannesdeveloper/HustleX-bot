# Setup HustleX Bot to run at Windows startup
# This creates a startup shortcut and scheduled task

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$StartupDir = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup"
$BotShortcut = Join-Path $StartupDir "HustleX Bot.lnk"

Write-Host "Setting up HustleX Bot for automatic startup..." -ForegroundColor Green

# Create startup shortcut
$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($BotShortcut)
$Shortcut.TargetPath = Join-Path $ScriptDir "start_bot.bat"
$Shortcut.WorkingDirectory = $ScriptDir
$Shortcut.Description = "HustleX Telegram Bot - Auto Start"
$Shortcut.Save()

Write-Host "Startup shortcut created: $BotShortcut" -ForegroundColor Green

# Create scheduled task for better reliability
$TaskName = "HustleXBot"
$TaskAction = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$ScriptDir\start_bot.bat`""
$TaskTrigger = New-ScheduledTaskTrigger -AtStartup
$TaskSettings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

# Remove existing task if it exists
try {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
} catch {}

# Register the new task
Register-ScheduledTask -TaskName $TaskName -Action $TaskAction -Trigger $TaskTrigger -Settings $TaskSettings -Description "HustleX Telegram Bot - 24/7 Service"

Write-Host "Scheduled task created: $TaskName" -ForegroundColor Green

Write-Host "`nHustleX Bot is now configured to start automatically!" -ForegroundColor Yellow
Write-Host "The bot will start when Windows boots up." -ForegroundColor Cyan
Write-Host "`nTo test immediately, run: .\start_bot.bat" -ForegroundColor White


