@echo off
cd /d "%~dp0"
call .venv\Scripts\activate.bat
pip install aiohttp
echo Installation complete.
pause