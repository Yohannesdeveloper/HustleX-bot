# HustleX Telegram Bot Service Setup

## Overview

This document explains how to run the HustleX Telegram Bot as a Windows service that starts automatically when you log in to your computer.

## Files

- **run_bot.ps1**: PowerShell script that starts the bot in the background
- **install_aiohttp.ps1**: PowerShell script to install required dependencies
- **update_token.ps1**: PowerShell script to update your Telegram Bot token
- **create_shortcut.ps1**: Creates a shortcut in the Windows Startup folder
- **test_bot_startup.ps1**: Tests if the bot starts correctly

## Setup Instructions

### 1. Install Dependencies

Before running the bot, make sure all required dependencies are installed:

```
powershell -ExecutionPolicy Bypass -File "install_aiohttp.ps1"
```

### 2. Configure Bot Token

The bot requires a valid Telegram Bot token to function. Update your token using the provided script:

```
powershell -ExecutionPolicy Bypass -File "update_token.ps1"
```

Follow the prompts to enter your Telegram Bot token.

### 3. Test the Bot

Test that the bot starts correctly:

```
powershell -ExecutionPolicy Bypass -File "test_bot_startup.ps1"
```

This will start the bot and check if it's running properly.

### 4. Create Startup Shortcut

To make the bot start automatically when you log in:

```
powershell -ExecutionPolicy Bypass -File "create_shortcut.ps1"
```

This creates a shortcut in your Windows Startup folder that will run the bot when you log in.

## Manual Start/Stop

### Starting the Bot Manually

To start the bot manually:

```
powershell -ExecutionPolicy Bypass -File "run_bot.ps1"
```

### Stopping the Bot

To stop the bot:

1. Open Task Manager
2. Find the Python process running the bot
3. Right-click and select "End Task"

## Log Files

The bot creates log files in the `C:\nssm` directory:

- **hustlex_bot_output.log**: Contains standard output from the bot
- **hustlex_bot_error.log**: Contains error messages and exceptions

Check these logs if you encounter any issues with the bot.

## Troubleshooting

### Bot Not Starting

1. Check the error log at `C:\nssm\hustlex_bot_error.log`
2. Verify that all dependencies are installed by running `install_aiohttp.ps1`
3. Make sure your bot token is valid by running `update_token.ps1`
4. Ensure the virtual environment is properly set up

### Missing Dependencies

If you encounter missing dependency errors, run:

```
powershell -ExecutionPolicy Bypass -File "install_aiohttp.ps1"
```

You may need to modify this script to install additional dependencies.

## Automatic Startup Configuration

The bot is configured to start automatically when you log in to Windows. This is done by creating a shortcut in your Windows Startup folder that runs the `run_bot.ps1` script.

If you need to disable automatic startup, simply delete the shortcut from your Startup folder:

```
%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\HustleXBot.lnk
```