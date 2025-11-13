@echo off
:: EqualNet Launcher - Run as Administrator
:: This script ensures EqualNet runs with admin rights for QoS control

echo.
echo ============================================
echo   EqualNet - Bandwidth Management System
echo ============================================
echo.

:: Check if running as admin
net session >nul 2>&1
if %errorLevel% == 0 (
    echo [OK] Running with administrator privileges
    echo.
) else (
    echo [ERROR] This script requires administrator privileges!
    echo.
    echo Please right-click this file and select "Run as administrator"
    echo.
    pause
    exit /b 1
)

:: Navigate to project directory
cd /d "%~dp0"

:: Check if Python is installed
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Python not found!
    echo Please install Python from https://python.org
    pause
    exit /b 1
)

:: Check if requirements are installed
echo Checking dependencies...
python -c "import flask" >nul 2>&1
if %errorLevel% neq 0 (
    echo [INFO] Installing dependencies...
    python -m pip install -r requirements-service.txt
)

:: Display mode information
echo.
echo ============================================
echo   Configuration
echo ============================================
findstr /C:"HOTSPOT_MODE = True" api_server.py >nul
if %errorLevel% == 0 (
    echo Mode: HOTSPOT (ACTUAL bandwidth control)
    echo Status: Windows QoS policies will be applied
    echo.
    echo Requirements:
    echo  - Enable Windows Mobile Hotspot
    echo  - Connect devices to your hotspot
    echo  - Apply limits from dashboard
    echo.
) else (
    echo Mode: ROUTER (Simulation mode)
    echo Status: No actual bandwidth control
    echo.
    echo To enable ACTUAL control:
    echo  1. Edit api_server.py
    echo  2. Set HOTSPOT_MODE = True
    echo  3. Restart this script
    echo.
)

echo ============================================
echo   Starting EqualNet Server
echo ============================================
echo.
echo Dashboard: http://localhost:5000
echo Press Ctrl+C to stop
echo.

:: Start the server
python api_server.py

pause
