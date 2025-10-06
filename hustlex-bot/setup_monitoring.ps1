# Setup HustleX Bot Monitoring
# This script sets up automated monitoring of the HustleX bot service

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

function Setup-MonitoringTask {
    Write-ColorOutput "Setting up HustleX Bot monitoring task..." "Yellow"
    
    $taskName = "HustleXBotMonitor"
    $scriptPath = Join-Path $PSScriptRoot "monitor_bot.ps1"
    
    # Check if task already exists
    $existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    if ($existingTask) {
        Write-ColorOutput "Monitoring task already exists. Updating..." "Yellow"
        Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
    }
    
    # Create the task action
    $action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-ExecutionPolicy Bypass -File `"$scriptPath`" -Continuous -CheckInterval 300"
    
    # Create the task trigger (run at startup and every 5 minutes)
    $trigger1 = New-ScheduledTaskTrigger -AtStartup
    $trigger2 = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 5) -RepetitionDuration (New-TimeSpan -Days 365)
    
    # Create task settings
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RunOnlyIfNetworkAvailable -ExecutionTimeLimit (New-TimeSpan -Hours 1)
    
    # Create the task principal (run as SYSTEM)
    $principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
    
    # Register the task
    Register-ScheduledTask -TaskName $taskName -Action $action -Trigger @($trigger1, $trigger2) -Settings $settings -Principal $principal -Description "Monitors HustleX Bot service and restarts if needed"
    
    Write-ColorOutput "Monitoring task created successfully!" "Green"
    Write-ColorOutput "Task Name: $taskName" "White"
    Write-ColorOutput "Runs: At startup and every 5 minutes" "White"
    Write-ColorOutput "Action: Monitors service health and restarts if needed" "White"
}

function Setup-ServiceAutoStart {
    Write-ColorOutput "Ensuring service auto-start is enabled..." "Yellow"
    
    try {
        $service = Get-Service -Name "HustleXBot" -ErrorAction Stop
        
        if ($service.StartType -ne "Automatic") {
            Set-Service -Name "HustleXBot" -StartupType Automatic
            Write-ColorOutput "Service auto-start enabled!" "Green"
        } else {
            Write-ColorOutput "Service auto-start already enabled!" "Green"
        }
    }
    catch {
        Write-ColorOutput "Could not configure service auto-start: $($_.Exception.Message)" "Red"
        Write-ColorOutput "Make sure the HustleXBot service is installed first." "Yellow"
    }
}

function Test-MonitoringSetup {
    Write-ColorOutput "Testing monitoring setup..." "Yellow"
    
    # Test the monitoring script
    $scriptPath = Join-Path $PSScriptRoot "monitor_bot.ps1"
    if (Test-Path $scriptPath) {
        Write-ColorOutput "Monitoring script found: $scriptPath" "Green"
        
        # Run a quick health check
        try {
            & $scriptPath -CheckInterval 10
            Write-ColorOutput "Monitoring script test completed successfully!" "Green"
        }
        catch {
            Write-ColorOutput "Monitoring script test failed: $($_.Exception.Message)" "Red"
        }
    } else {
        Write-ColorOutput "Monitoring script not found: $scriptPath" "Red"
    }
    
    # Check scheduled task
    $taskName = "HustleXBotMonitor"
    $task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    if ($task) {
        Write-ColorOutput "Scheduled task found: $($task.TaskName)" "Green"
        Write-ColorOutput "Task State: $($task.State)" "White"
    } else {
        Write-ColorOutput "Scheduled task not found: $taskName" "Red"
    }
}

function Show-MonitoringStatus {
    Write-ColorOutput "HustleX Bot Monitoring Status" "Cyan"
    Write-ColorOutput "=============================" "Cyan"
    
    # Service status
    try {
        $service = Get-Service -Name "HustleXBot" -ErrorAction Stop
        Write-ColorOutput "Service Status: $($service.Status)" $(if ($service.Status -eq "Running") { "Green" } else { "Red" })
        Write-ColorOutput "Service Start Type: $($service.StartType)" "White"
    }
    catch {
        Write-ColorOutput "Service Status: NOT INSTALLED" "Red"
    }
    
    # Monitoring task status
    $taskName = "HustleXBotMonitor"
    $task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    if ($task) {
        Write-ColorOutput "Monitoring Task: $($task.State)" $(if ($task.State -eq "Ready") { "Green" } else { "Yellow" })
    } else {
        Write-ColorOutput "Monitoring Task: NOT CONFIGURED" "Red"
    }
    
    # Log files
    $logDir = 'C:\nssm'
    $serviceLog = Join-Path $logDir 'hustlex_service.log'
    $monitorLog = Join-Path $logDir 'monitor.log'
    
    if (Test-Path $serviceLog) {
        $serviceLogSize = (Get-Item $serviceLog).Length
        Write-ColorOutput "Service Log: Found ($serviceLogSize bytes)" "Green"
    } else {
        Write-ColorOutput "Service Log: Not found" "Red"
    }
    
    if (Test-Path $monitorLog) {
        $monitorLogSize = (Get-Item $monitorLog).Length
        Write-ColorOutput "Monitor Log: Found ($monitorLogSize bytes)" "Green"
    } else {
        Write-ColorOutput "Monitor Log: Not found" "Red"
    }
}

# Main execution
if (-not (Test-Administrator)) {
    Write-ColorOutput "This script requires administrator privileges!" "Red"
    Write-ColorOutput "Please run PowerShell as Administrator and try again." "Yellow"
    exit 1
}

Write-ColorOutput "HustleX Bot Monitoring Setup" "Cyan"
Write-ColorOutput "============================" "Cyan"

# Setup monitoring task
Setup-MonitoringTask

# Ensure service auto-start
Setup-ServiceAutoStart

# Test the setup
Test-MonitoringSetup

# Show final status
Write-ColorOutput "`nFinal Status:" "Cyan"
Show-MonitoringStatus

Write-ColorOutput "`nMonitoring setup completed!" "Green"
Write-ColorOutput "The bot will now be monitored 24/7 and automatically restarted if needed." "Green"


