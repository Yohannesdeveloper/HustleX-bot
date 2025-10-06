# HustleX Bot Health Monitor
# This script monitors the bot service and ensures it stays running 24/7

param(
    [Parameter(Mandatory=$false)]
    [int]$CheckInterval = 300,  # 5 minutes default
    [Parameter(Mandatory=$false)]
    [switch]$Continuous
)

$ErrorActionPreference = 'Stop'

# Configuration
$ServiceName = "HustleXBot"
$LogDir = 'C:\nssm'
$LogFile = Join-Path $LogDir 'hustlex_service.log'
$MonitorLogFile = Join-Path $LogDir 'monitor.log'

function Write-MonitorLog {
    param(
        [string]$Message,
        [string]$Level = "INFO"
    )
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    Write-Host $logEntry
    Add-Content -Path $MonitorLogFile -Value $logEntry
}

function Test-ServiceHealth {
    try {
        $service = Get-Service -Name $ServiceName -ErrorAction Stop
        
        if ($service.Status -ne "Running") {
            Write-MonitorLog "Service is not running (Status: $($service.Status))" "ERROR"
            return $false
        }
        
        # Check if bot process is actually running
        $processes = Get-Process | Where-Object { 
            $_.ProcessName -like "*python*" -and 
            $_.CommandLine -like "*bot.main*" 
        }
        
        if (-not $processes) {
            Write-MonitorLog "Service is running but bot process not detected" "WARNING"
            return $false
        }
        
        # Check log file for recent activity
        if (Test-Path $LogFile) {
            $lastLogTime = (Get-Item $LogFile).LastWriteTime
            $timeSinceLastLog = (Get-Date) - $lastLogTime
            
            if ($timeSinceLastLog.TotalMinutes -gt 15) {
                Write-MonitorLog "No recent log activity (last: $($timeSinceLastLog.TotalMinutes.ToString('F1')) minutes ago)" "WARNING"
                return $false
            }
        }
        
        Write-MonitorLog "Service health check passed" "INFO"
        return $true
        
    }
    catch {
        Write-MonitorLog "Health check failed: $($_.Exception.Message)" "ERROR"
        return $false
    }
}

function Restart-Service {
    Write-MonitorLog "Attempting to restart service..." "INFO"
    
    try {
        # Stop the service
        Stop-Service -Name $ServiceName -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 5
        
        # Start the service
        Start-Service -Name $ServiceName
        Start-Sleep -Seconds 10
        
        # Verify it's running
        $service = Get-Service -Name $ServiceName
        if ($service.Status -eq "Running") {
            Write-MonitorLog "Service restarted successfully" "INFO"
            return $true
        } else {
            Write-MonitorLog "Service restart failed - status: $($service.Status)" "ERROR"
            return $false
        }
    }
    catch {
        Write-MonitorLog "Service restart failed: $($_.Exception.Message)" "ERROR"
        return $false
    }
}

function Send-Alert {
    param(
        [string]$Message
    )
    
    # Here you could implement various alert mechanisms:
    # - Email notifications
    # - Telegram notifications
    # - Windows Event Log
    # - Push notifications
    
    Write-MonitorLog "ALERT: $Message" "ALERT"
    
    # Log to Windows Event Log
    try {
        Write-EventLog -LogName "Application" -Source "HustleXBot" -EventId 1001 -EntryType Warning -Message $Message
    }
    catch {
        # Event log might not be available, continue
    }
}

function Main {
    Write-MonitorLog "HustleX Bot Monitor started" "INFO"
    Write-MonitorLog "Check interval: $CheckInterval seconds" "INFO"
    Write-MonitorLog "Continuous mode: $Continuous" "INFO"
    
    $consecutiveFailures = 0
    $maxConsecutiveFailures = 3
    
    do {
        try {
            $isHealthy = Test-ServiceHealth
            
            if ($isHealthy) {
                $consecutiveFailures = 0
                Write-MonitorLog "Service is healthy" "INFO"
            } else {
                $consecutiveFailures++
                Write-MonitorLog "Service health check failed (attempt $consecutiveFailures/$maxConsecutiveFailures)" "WARNING"
                
                if ($consecutiveFailures -ge $maxConsecutiveFailures) {
                    Write-MonitorLog "Maximum consecutive failures reached, attempting restart" "ERROR"
                    
                    if (Restart-Service) {
                        $consecutiveFailures = 0
                        Send-Alert "HustleX Bot service was restarted due to health check failures"
                    } else {
                        Send-Alert "HustleX Bot service restart failed - manual intervention required"
                    }
                }
            }
            
            if ($Continuous) {
                Write-MonitorLog "Waiting $CheckInterval seconds before next check..." "INFO"
                Start-Sleep -Seconds $CheckInterval
            }
            
        }
        catch {
            Write-MonitorLog "Monitor error: $($_.Exception.Message)" "ERROR"
            Send-Alert "HustleX Bot monitor encountered an error: $($_.Exception.Message)"
            
            if ($Continuous) {
                Start-Sleep -Seconds $CheckInterval
            }
        }
        
    } while ($Continuous)
    
    Write-MonitorLog "HustleX Bot Monitor stopped" "INFO"
}

# Run the monitor
Main


