# PowerShell script to create a Windows shortcut that runs the bot

# Get the script directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Create a shortcut in the Windows Startup folder
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\HustleXBot.lnk")
$Shortcut.TargetPath = "powershell.exe"
$Shortcut.Arguments = "-ExecutionPolicy Bypass -WindowStyle Hidden -File `"$scriptDir\run_bot.ps1`""
$Shortcut.WorkingDirectory = $scriptDir
$Shortcut.Description = "Start HustleX Telegram Bot"
$Shortcut.IconLocation = "$env:SystemRoot\System32\SHELL32.dll,71"
$Shortcut.WindowStyle = 7  # Minimized
$Shortcut.Save()

Write-Host "Startup shortcut created successfully at:" 
Write-Host "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\HustleXBot.lnk"
Write-Host "The bot will now start automatically when you log in to Windows."