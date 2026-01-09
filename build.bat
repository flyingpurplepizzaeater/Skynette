@echo off
echo ============================================
echo Skynette Windows Build
echo ============================================
echo.

REM Check for Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.10+ from https://python.org
    pause
    exit /b 1
)

REM Run the build script
python build_windows.py

echo.
pause
