# PowerShell script to create a startup shortcut for the HustleX Bot

$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\HustleXBot.lnk")
$Shortcut.TargetPath = "$PSScriptRoot\run_bot.bat"
$Shortcut.WorkingDirectory = "$PSScriptRoot"
$Shortcut.Description = "Start HustleX Telegram Bot"
$Shortcut.WindowStyle = 7  # Minimized
$Shortcut.Save()

Write-Host "Startup shortcut created successfully at:" 
Write-Host "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\HustleXBot.lnk"