# HustleX Bot Service Management Script
# This script provides comprehensive management of the HustleX bot service

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("install", "uninstall", "start", "stop", "restart", "status", "logs", "health", "update")]
    [string]$Action = "status"
)

$ErrorActionPreference = 'Stop'

# Configuration
$ServiceName = "HustleXBot"
$LogDir = 'C:\nssm'
$LogFile = Join-Path $LogDir 'hustlex_service.log'

function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

function Test-ServiceExists {
    try {
        $service = Get-Service -Name $ServiceName -ErrorAction Stop
        return $true
    }
    catch {
        return $false
    }
}

function Install-Service {
    Write-ColorOutput "Installing HustleX Bot service..." "Yellow"
    
    # Check if service already exists
    if (Test-ServiceExists) {
        Write-ColorOutput "Service already exists. Use 'restart' to update it." "Red"
        return
    }
    
    # Run the installation script
    $installScript = Join-Path $PSScriptRoot "install_service.ps1"
    if (Test-Path $installScript) {
        & $installScript
        Write-ColorOutput "Service installed successfully!" "Green"
    } else {
        Write-ColorOutput "Installation script not found: $installScript" "Red"
    }
}

function Uninstall-Service {
    Write-ColorOutput "Uninstalling HustleX Bot service..." "Yellow"
    
    if (-not (Test-ServiceExists)) {
        Write-ColorOutput "Service does not exist." "Red"
        return
    }
    
    # Stop the service first
    Stop-Service -Name $ServiceName -Force -ErrorAction SilentlyContinue
    
    # Remove the service using NSSM
    $nssmRoot = Join-Path $LogDir 'nssm-2.24'
    $nssm = Join-Path $nssmRoot 'win64\nssm.exe'
    if (-not (Test-Path $nssm)) { $nssm = Join-Path $nssmRoot 'win32\nssm.exe' }
    
    if (Test-Path $nssm) {
        & $nssm remove $ServiceName confirm
        Write-ColorOutput "Service uninstalled successfully!" "Green"
    } else {
        Write-ColorOutput "NSSM not found. Cannot uninstall service." "Red"
    }
}

function Start-Service {
    Write-ColorOutput "Starting HustleX Bot service..." "Yellow"
    
    if (-not (Test-ServiceExists)) {
        Write-ColorOutput "Service does not exist. Run 'install' first." "Red"
        return
    }
    
    try {
        Start-Service -Name $ServiceName
        Write-ColorOutput "Service started successfully!" "Green"
    }
    catch {
        Write-ColorOutput "Failed to start service: $($_.Exception.Message)" "Red"
    }
}

function Stop-Service {
    Write-ColorOutput "Stopping HustleX Bot service..." "Yellow"
    
    if (-not (Test-ServiceExists)) {
        Write-ColorOutput "Service does not exist." "Red"
        return
    }
    
    try {
        Stop-Service -Name $ServiceName -Force
        Write-ColorOutput "Service stopped successfully!" "Green"
    }
    catch {
        Write-ColorOutput "Failed to stop service: $($_.Exception.Message)" "Red"
    }
}

function Restart-Service {
    Write-ColorOutput "Restarting HustleX Bot service..." "Yellow"
    
    if (-not (Test-ServiceExists)) {
        Write-ColorOutput "Service does not exist. Run 'install' first." "Red"
        return
    }
    
    try {
        Restart-Service -Name $ServiceName -Force
        Write-ColorOutput "Service restarted successfully!" "Green"
    }
    catch {
        Write-ColorOutput "Failed to restart service: $($_.Exception.Message)" "Red"
    }
}

function Get-ServiceStatus {
    Write-ColorOutput "HustleX Bot Service Status" "Cyan"
    Write-ColorOutput "=========================" "Cyan"
    
    if (-not (Test-ServiceExists)) {
        Write-ColorOutput "Service Status: NOT INSTALLED" "Red"
        return
    }
    
    try {
        $service = Get-Service -Name $ServiceName
        $status = $service.Status
        $startType = $service.StartType
        
        Write-ColorOutput "Service Name: $($service.Name)" "White"
        Write-ColorOutput "Display Name: $($service.DisplayName)" "White"
        Write-ColorOutput "Status: $status" $(if ($status -eq "Running") { "Green" } else { "Red" })
        Write-ColorOutput "Start Type: $startType" "White"
        
        # Check if service is configured for auto-start
        if ($startType -eq "Automatic") {
            Write-ColorOutput "Auto-start: ✅ Enabled" "Green"
        } else {
            Write-ColorOutput "Auto-start: ❌ Disabled" "Red"
        }
        
        # Show process information if running
        if ($status -eq "Running") {
            $processes = Get-Process | Where-Object { $_.ProcessName -like "*python*" -and $_.CommandLine -like "*bot.main*" }
            if ($processes) {
                Write-ColorOutput "Bot Process: Running (PID: $($processes[0].Id))" "Green"
            } else {
                Write-ColorOutput "Bot Process: Not detected" "Yellow"
            }
        }
        
    }
    catch {
        Write-ColorOutput "Error getting service status: $($_.Exception.Message)" "Red"
    }
}

function Show-Logs {
    Write-ColorOutput "HustleX Bot Service Logs" "Cyan"
    Write-ColorOutput "=======================" "Cyan"
    
    if (Test-Path $LogFile) {
        Write-ColorOutput "Showing last 50 lines of service log:" "Yellow"
        Write-ColorOutput "-----------------------------------" "Yellow"
        Get-Content -Path $LogFile -Tail 50
    } else {
        Write-ColorOutput "Log file not found: $LogFile" "Red"
    }
}

function Test-ServiceHealth {
    Write-ColorOutput "HustleX Bot Service Health Check" "Cyan"
    Write-ColorOutput "=================================" "Cyan"
    
    if (-not (Test-ServiceExists)) {
        Write-ColorOutput "❌ Service not installed" "Red"
        return
    }
    
    $service = Get-Service -Name $ServiceName
    if ($service.Status -ne "Running") {
        Write-ColorOutput "❌ Service not running" "Red"
        return
    }
    
    # Check if bot process is running
    $processes = Get-Process | Where-Object { $_.ProcessName -like "*python*" -and $_.CommandLine -like "*bot.main*" }
    if (-not $processes) {
        Write-ColorOutput "❌ Bot process not detected" "Red"
        return
    }
    
    # Check log file for recent activity
    if (Test-Path $LogFile) {
        $lastLogTime = (Get-Item $LogFile).LastWriteTime
        $timeSinceLastLog = (Get-Date) - $lastLogTime
        
        if ($timeSinceLastLog.TotalMinutes -gt 10) {
            Write-ColorOutput "⚠️ No recent log activity (last: $($timeSinceLastLog.TotalMinutes.ToString('F1')) minutes ago)" "Yellow"
        } else {
            Write-ColorOutput "✅ Recent log activity detected" "Green"
        }
    }
    
    Write-ColorOutput "✅ Service appears healthy" "Green"
}

function Update-Service {
    Write-ColorOutput "Updating HustleX Bot service..." "Yellow"
    
    if (-not (Test-ServiceExists)) {
        Write-ColorOutput "Service does not exist. Run 'install' first." "Red"
        return
    }
    
    # Stop the service
    Stop-Service -Name $ServiceName -Force -ErrorAction SilentlyContinue
    
    # Reinstall the service
    $installScript = Join-Path $PSScriptRoot "install_service.ps1"
    if (Test-Path $installScript) {
        & $installScript
        Write-ColorOutput "Service updated successfully!" "Green"
    } else {
        Write-ColorOutput "Installation script not found: $installScript" "Red"
    }
}

# Main execution
switch ($Action.ToLower()) {
    "install" { Install-Service }
    "uninstall" { Uninstall-Service }
    "start" { Start-Service }
    "stop" { Stop-Service }
    "restart" { Restart-Service }
    "status" { Get-ServiceStatus }
    "logs" { Show-Logs }
    "health" { Test-ServiceHealth }
    "update" { Update-Service }
    default { 
        Write-ColorOutput "Usage: .\manage_service.ps1 -Action [install|uninstall|start|stop|restart|status|logs|health|update]" "Yellow"
        Write-ColorOutput "Default action: status" "Yellow"
        Get-ServiceStatus
    }
}


