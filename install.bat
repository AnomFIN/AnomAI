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
    echo Please install Python 3.10+ (64-bit) from https://www.python.org/downloads/ and re-run this script.
    call :maybe_pause
    endlocal
    exit /b 1
  )
)

REM Get Python major.minor version and architecture using a temporary .py to avoid inline quoting issues
set "TEMP_INFO=%TEMP%\anomai_pyinfo.txt"
set "TEMP_PY=%TEMP%\anomai_pyinfo.py"
if exist "%TEMP_INFO%" del "%TEMP_INFO%" >nul 2>&1
if exist "%TEMP_PY%" del "%TEMP_PY%" >nul 2>&1

> "%TEMP_PY%" echo import sys, struct
>> "%TEMP_PY%" echo print('.'.join(map(str, sys.version_info[:2])))
>> "%TEMP_PY%" echo print(struct.calcsize('P')*8)

"%PY_CMD%" "%TEMP_PY%" > "%TEMP_INFO%" 2>nul

set "PY_VER="
set "PY_BITS="
if exist "%TEMP_INFO%" (
  for /f "usebackq delims=" %%V in ("%TEMP_INFO%") do (
    if not defined PY_VER (
      set "PY_VER=%%V"
    ) else if not defined PY_BITS (
      set "PY_BITS=%%V"
    )
  )
  del "%TEMP_INFO%" >nul 2>&1
)
if exist "%TEMP_PY%" del "%TEMP_PY%" >nul 2>&1

if "%PY_VER%"=="" (
  echo ERROR: Could not determine Python version with %PY_CMD%.
  call :maybe_pause
  endlocal
  exit /b 1
)

for /f "tokens=1 delims=." %%A in ("%PY_VER%") do set "PY_MAJOR=%%A"
for /f "tokens=2 delims=." %%B in ("%PY_VER%") do set "PY_MINOR=%%B"

echo Detected Python version %PY_VER% using %PY_CMD%.
if not "%PY_BITS%"=="" echo Detected architecture: %PY_BITS%-bit.

REM Require Python >= 3.10
if %PY_MAJOR% LSS 3 (
  echo ERROR: Python 3.x is required.
  call :maybe_pause
  endlocal
  exit /b 1
)
if %PY_MAJOR% EQU 3 if %PY_MINOR% LSS 10 (
  echo ERROR: Python 3.10+ is required. Detected %PY_VER%.
  call :maybe_pause
  endlocal
  exit /b 1
)

if not "%PY_BITS%"=="64" (
  echo ERROR: 64-bit Python is required for local model builds. Please install the 64-bit edition of Python 3.10 or newer.
  call :maybe_pause
  endlocal
  exit /b 1
)

REM Create virtual environment
if not exist ".venv\Scripts\activate.bat" (
  echo Creating virtual environment in .venv...
  %PY_CMD% -m venv .venv
  if %errorlevel% neq 0 (
    echo ERROR: Failed to create virtual environment.
    call :maybe_pause
    endlocal
    exit /b 1
  )
) else (
  echo Using existing virtual environment .venv
)

call ".venv\Scripts\activate.bat"

REM Upgrade pip, setuptools, wheel to avoid build issues (e.g., Pillow)
echo Upgrading pip, setuptools and wheel...
python -m pip install --upgrade pip setuptools wheel
if %errorlevel% neq 0 (
  echo ERROR: Failed to upgrade pip/setuptools/wheel.
  call :maybe_pause
  endlocal
  exit /b 1
)

REM Install requirements if file exists
if exist requirements.txt (
echo Installing requirements from requirements.txt...
  python -m pip install -r requirements.txt
  if %errorlevel% neq 0 (
    echo ERROR: pip install failed. See output above.
    call :maybe_pause
    endlocal
    exit /b 1
  )
) else (
  echo No requirements.txt found — skipping pip install step.
)

echo.
set "INSTALL_LLAMA="
set /p INSTALL_LLAMA=Install local GGUF/llama support (llama-cpp-python)? [Y/N] (default Y):
if /I "%INSTALL_LLAMA%"=="N" (
  echo Skipping llama-cpp-python installation at user request.
) else (
  echo Installing llama-cpp-python with --prefer-binary (this may take a moment)...
  python -m pip install --upgrade --prefer-binary llama-cpp-python
  if %errorlevel% neq 0 (
    echo WARNING: llama-cpp-python installation failed. You can retry manually with:
    echo   %PY_CMD% -m pip install --upgrade --prefer-binary llama-cpp-python
    echo or follow Windows-specific wheel instructions from the README.
  ) else (
    echo Local model support ready (llama-cpp-python installed).
  )
)

REM Build the EXE using build_exe.bat
echo.
echo ---
echo Building AnomAI.exe...
echo ---
if exist build_exe.bat (
  call build_exe.bat
  if %errorlevel% neq 0 (
    echo WARNING: EXE build failed. You can build it manually later by running build_exe.bat
    echo The Python version is fully functional.
  ) else (
    echo EXE built successfully.
  )
) else (
  echo WARNING: build_exe.bat not found. Skipping EXE build.
)

echo ---
echo Install completed successfully.
echo To activate the virtual environment later:
echo    .\.venv\Scripts\activate.bat
echo Run your scripts with the activated environment (python ...).
call :maybe_pause
endlocal
exit /b 0

:maybe_pause
REM Skip pause when running in CI or in non-interactive builds
if /I "%CI%"=="true" goto :eof
if "%BUILD_NONINTERACTIVE%"=="1" goto :eof
pause
goto :eof