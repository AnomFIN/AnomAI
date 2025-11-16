@echo off
:: AnomAI/JugiAI - Installation Launcher
:: This script ensures UTF-8 encoding is properly set before running the main installer.
:: Simply double-click this file to start the installation.

setlocal

:: Get the directory where this script is located
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

:: Check if install_utf8.bat exists
if not exist "install_utf8.bat" (
    echo ERROR: install_utf8.bat not found in %SCRIPT_DIR%
    echo Please ensure all installation files are present.
    pause
    exit /b 1
)

:: Launch the UTF-8 wrapper which will handle encoding and call the main installer
echo Starting AnomAI installation...
echo.
call "install_utf8.bat"

:: Exit with the same code as install_utf8.bat
exit /b %errorlevel%
