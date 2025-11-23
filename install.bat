@echo off
:: AnomAI/JugiAI Unified Installer - Windows Wrapper
:: This script ensures UTF-8 compatibility and delegates to install.py

setlocal enabledelayedexpansion
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

:: Enable UTF-8 console if supported
chcp 65001 >nul 2>&1

:: Try to find Python
set "PY_CMD="
where python >nul 2>&1
if %errorlevel%==0 (
  set "PY_CMD=python"
) else (
  where py >nul 2>&1
  if %errorlevel%==0 (
    set "PY_CMD=py -3"
  )
)

:: Check if Python is available
if not defined PY_CMD (
  echo ERROR: Python 3 is not installed or not found in PATH.
  echo.
  echo Please install Python 3.10+ from:
  echo https://www.python.org/downloads/windows/
  echo.
  echo Make sure to check "Add Python to PATH" during installation.
  echo.
  pause
  exit /b 1
)

:: Run the unified installer
echo Launching AnomAI Unified Installer...
echo.
%PY_CMD% install.py %*
set "EXIT_CODE=%errorlevel%"

:: Pause only if there was an error or running interactively
if not "%EXIT_CODE%"=="0" (
  echo.
  echo Installation failed with exit code %EXIT_CODE%.
  pause
) else (
  if not "%CI%"=="true" (
    if not "%BATCH_MODE%"=="1" (
      echo.
      echo Installation completed successfully!
      pause
    )
  )
)

endlocal
exit /b %EXIT_CODE%