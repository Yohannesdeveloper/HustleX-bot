@echo off
echo Starting HustleX Bot...

REM Set the working directory to the script location
cd /d "%~dp0"

REM Create log directory if it doesn't exist
if not exist "C:\nssm" mkdir "C:\nssm"

REM Full path to Python executable in virtual environment
set PYTHON="%~dp0.venv\Scripts\python.exe"

REM Check if Python exists
if not exist %PYTHON% (
    echo ERROR: Python executable not found at %PYTHON% > C:\nssm\hustlex_bot_output.log
    exit /b 1
)

REM Log startup information
echo Starting bot at %date% %time% > C:\nssm\hustlex_bot_output.log
echo Working directory: %CD% >> C:\nssm\hustlex_bot_output.log
echo Python path: %PYTHON% >> C:\nssm\hustlex_bot_output.log

REM Run the bot with output redirected to log file
start "HustleX Bot" /min powershell -Command "& %PYTHON% -m bot.main >> C:\nssm\hustlex_bot_output.log 2>&1"

echo Bot started in background. Check C:\nssm\hustlex_bot_output.log for output.