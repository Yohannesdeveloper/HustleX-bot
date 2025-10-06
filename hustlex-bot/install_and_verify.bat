@echo off
echo Installing aiohttp in virtual environment...
cd /d "%~dp0"
call .venv\Scripts\activate.bat
pip install aiohttp
echo.
echo Verifying installation...
pip list | findstr aiohttp
if %ERRORLEVEL% EQU 0 (
    echo aiohttp is installed successfully.
) else (
    echo ERROR: aiohttp installation failed.
)
echo.
pause