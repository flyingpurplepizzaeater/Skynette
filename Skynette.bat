@echo off
REM Skynette Launcher - Runs without terminal window
REM Use pythonw to prevent console window from appearing

cd /d "%~dp0"

REM Try pythonw first (no console window)
where pythonw >nul 2>&1
if %errorlevel%==0 (
    start "" pythonw Skynette.py
    exit /b 0
)

REM Fall back to python with hidden window
where python >nul 2>&1
if %errorlevel%==0 (
    start /min "" python Skynette.py
    exit /b 0
)

REM No Python found
echo ERROR: Python is not installed or not in PATH
echo Please install Python 3.10+ from https://python.org
pause
exit /b 1
