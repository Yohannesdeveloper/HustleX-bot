# HustleX Bot 24/7 Setup Guide

## Overview

This guide explains how to set up your HustleX Telegram Bot to run 24/7 without human intervention. The bot will automatically start when your computer boots up and will restart itself if it encounters any issues.

## What's Included

### Core Components
- **Windows Service**: Runs the bot as a background service
- **Auto-Recovery**: Automatically restarts the bot if it crashes
- **Health Monitoring**: Continuous monitoring with automatic restarts
- **Logging**: Comprehensive logging for troubleshooting
- **Auto-Start**: Starts automatically when Windows boots

### Management Scripts
- `setup_24x7.ps1` - Complete 24/7 setup script
- `manage_service.ps1` - Service management commands
- `monitor_bot.ps1` - Health monitoring script
- `setup_monitoring.ps1` - Sets up automated monitoring

## Quick Setup

### 1. Run the Complete Setup (Recommended)
```powershell
# Run as Administrator
.\setup_24x7.ps1
```

This script will:
- Install all dependencies
- Set up the Windows service
- Configure automatic monitoring
- Test the setup

### 2. Manual Setup (Step by Step)

#### Step 1: Install Dependencies
```powershell
.\install_aiohttp.ps1
```

#### Step 2: Set Bot Token
```powershell
.\update_token.ps1
```

#### Step 3: Install Service
```powershell
.\install_service.ps1
```

#### Step 4: Setup Monitoring
```powershell
.\setup_monitoring.ps1
```

## Service Management

### Check Status
```powershell
.\manage_service.ps1 -Action status
```

### Restart Service
```powershell
.\manage_service.ps1 -Action restart
```

### View Logs
```powershell
.\manage_service.ps1 -Action logs
```

### Health Check
```powershell
.\manage_service.ps1 -Action health
```

### Stop Service
```powershell
.\manage_service.ps1 -Action stop
```

### Start Service
```powershell
.\manage_service.ps1 -Action start
```

## Monitoring Features

### Automatic Health Checks
- Runs every 5 minutes
- Checks if service is running
- Verifies bot process is active
- Monitors log file activity

### Auto-Recovery
- Automatically restarts service if it fails
- Exponential backoff for restart attempts
- Maximum of 50 restart attempts before stopping
- Resets restart counter after 1 hour of stable operation

### Logging
- Service logs: `C:\nssm\hustlex_service.log`
- Monitor logs: `C:\nssm\monitor.log`
- Windows Event Log entries for critical events

## Configuration

### Service Configuration
- **Service Name**: HustleXBot
- **Start Type**: Automatic (starts on boot)
- **Recovery**: Automatic restart on failure
- **Log Directory**: `C:\nssm`

### Monitoring Configuration
- **Check Interval**: 5 minutes
- **Max Consecutive Failures**: 3
- **Restart Delay**: 5 seconds (with exponential backoff)
- **Max Restart Delay**: 5 minutes

## Troubleshooting

### Service Not Starting
1. Check if bot token is set:
   ```powershell
   [Environment]::GetEnvironmentVariable("BOT_TOKEN", "Machine")
   ```

2. Check service logs:
   ```powershell
   Get-Content "C:\nssm\hustlex_service.log" -Tail 50
   ```

3. Restart the service:
   ```powershell
   .\manage_service.ps1 -Action restart
   ```

### Bot Not Responding
1. Check if service is running:
   ```powershell
   Get-Service HustleXBot
   ```

2. Check bot process:
   ```powershell
   Get-Process | Where-Object { $_.ProcessName -like "*python*" }
   ```

3. Check recent logs:
   ```powershell
   .\manage_service.ps1 -Action logs
   ```

### Monitoring Issues
1. Check monitoring task:
   ```powershell
   Get-ScheduledTask -Name "HustleXBotMonitor"
   ```

2. Check monitor logs:
   ```powershell
   Get-Content "C:\nssm\monitor.log" -Tail 20
   ```

3. Restart monitoring:
   ```powershell
   .\setup_monitoring.ps1
   ```

## File Structure

```
hustlex-bot/
├── bot/
│   ├── __init__.py
│   └── main.py              # Main bot code
├── service_runner.py         # Service wrapper
├── install_service.ps1       # Service installation
├── setup_24x7.ps1           # Complete setup script
├── manage_service.ps1        # Service management
├── monitor_bot.ps1           # Health monitoring
├── setup_monitoring.ps1      # Monitoring setup
└── README_24x7_SETUP.md      # This file
```

## Log Files

### Service Log (`C:\nssm\hustlex_service.log`)
- Service startup/shutdown events
- Bot process status
- Error messages and stack traces
- Restart attempts and reasons

### Monitor Log (`C:\nssm\monitor.log`)
- Health check results
- Service restart events
- Alert notifications
- Monitoring status updates

## Security Considerations

- Bot token is stored as environment variable
- Service runs with appropriate permissions
- Log files contain sensitive information (bot token, user data)
- Monitor access to log files

## Performance

- Minimal CPU usage when idle
- Automatic restart prevents memory leaks
- Log rotation prevents disk space issues
- Health checks run every 5 minutes

## Maintenance

### Regular Tasks
- Monitor log file sizes
- Check service status weekly
- Update bot token if needed
- Review error logs for patterns

### Updates
- Stop service before updating code
- Test changes in development first
- Restart service after updates
- Verify monitoring is still active

## Support

If you encounter issues:

1. Check the logs first
2. Use the management scripts
3. Verify all components are installed
4. Check Windows Event Log for system errors

## Success Indicators

Your bot is running 24/7 successfully when:
- ✅ Service status shows "Running"
- ✅ Bot responds to Telegram commands
- ✅ No errors in recent logs
- ✅ Monitoring task is "Ready"
- ✅ Service starts automatically on boot

---

**Note**: This setup ensures your HustleX bot runs continuously without human intervention. The monitoring system will automatically restart the bot if it encounters any issues, providing maximum uptime for your users.


