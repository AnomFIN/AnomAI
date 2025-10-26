@echo off
setlocal enabledelayedexpansion

echo --- Install script for AnomAI (Windows) ---
REM Try to find Python 3 executable
where python >nul 2>&1
if %errorlevel%==0 (
  set "PY_CMD=python"
) else (
  where py >nul 2>&1
  if %errorlevel%==0 (
    set "PY_CMD=py -3"
  ) else (
    echo ERROR: Python 3 is not installed or not on PATH.
    echo Please install Python 3.8+ from https://www.python.org/downloads/ and re-run this script.
    pause
    exit /b 1
  )
)

REM Get Python major.minor version
for /f "usebackq delims=" %%V in (`%PY_CMD% -c "import sys; print('.'.join(map(str, sys.version_info[:2])))" 2^>nul`) do set "PY_VER=%%V"
if "%PY_VER%"=="" (
  echo ERROR: Could not determine Python version with %PY_CMD%.
  pause
  exit /b 1
)

for /f "tokens=1 delims=." %%A in ("%PY_VER%") do set "PY_MAJOR=%%A"
for /f "tokens=2 delims=." %%B in ("%PY_VER%") do set "PY_MINOR=%%B"

echo Detected Python version %PY_VER% using %PY_CMD%.

REM Require Python >= 3.8
if %PY_MAJOR% LSS 3 (
  echo ERROR: Python 3.x is required.
  pause
  exit /b 1
)
if %PY_MAJOR% EQU 3 if %PY_MINOR% LSS 8 (
  echo ERROR: Python 3.8+ is required. Detected %PY_VER%.
  pause
  exit /b 1
)

REM Create virtual environment
if not exist ".venv\Scripts\activate" (
  echo Creating virtual environment in .venv...
  %PY_CMD% -m venv .venv
  if %errorlevel% neq 0 (
    echo ERROR: Failed to create virtual environment.
    pause
    exit /b 1
  )
) else (
  echo Using existing virtual environment .venv
)

call ".venv\Scripts\activate"

REM Upgrade pip, setuptools, wheel to avoid build issues (e.g., Pillow)
echo Upgrading pip, setuptools and wheel...
python -m pip install --upgrade pip setuptools wheel
if %errorlevel% neq 0 (
  echo ERROR: Failed to upgrade pip/setuptools/wheel.
  pause
  exit /b 1
)

REM Install requirements if file exists
if exist requirements.txt (
  echo Installing requirements from requirements.txt...
  python -m pip install -r requirements.txt
  if %errorlevel% neq 0 (
    echo ERROR: pip install failed. See output above.
    pause
    exit /b 1
  )
) else (
  echo No requirements.txt found — skipping pip install step.
)

echo ---
echo Install completed successfully.
echo To activate the virtual environment later:
echo    .venv\Scripts\activate
echo Run your scripts with the activated environment (python ...).
pause
endlocal
exit /b 0
