@echo off
echo ========================================
echo SupermaulTD Build Script
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python and try again
    pause
    exit /b 1
)

echo Building SupermaulTD executable...
echo.

REM Run the Python build script
python build.py

echo.
echo Build process completed!
pause 