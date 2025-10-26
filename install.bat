@echo off
:: Robust install.bat for Windows
:: - Finds python (python3 then python)
:: - Ensures pip (uses ensurepip if necessary)
:: - Optionally creates a venv
:: - Installs requirements.txt
:: - Optionally installs PyInstaller and builds a single-file .exe of jugiai.py (with user's consent)

setlocal enabledelayedexpansion

REM Helper: print error and pause
:errpause
echo.
echo ERROR: %~1
pause
exit /b 1

REM Find python interpreter
where python3 >nul 2>&1
if %ERRORLEVEL%==0 (
  set "PY=python3"
) else (
  where python >nul 2>&1
  if %ERRORLEVEL%==0 (
    set "PY=python"
  ) else (
    call :errpause "Python 3 not found on PATH. Install Python 3.9+ and re-run. See https://www.python.org/downloads/"
  )
)

echo Using %PY%

REM Ensure pip is available
"%PY%" -m pip --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
  echo pip not found. Attempting to bootstrap pip via ensurepip...
  "%PY%" -m ensurepip --upgrade >nul 2>&1
  if %ERRORLEVEL% neq 0 (
    echo Failed to bootstrap pip automatically.
    echo You can install pip manually: "%PY%" -m ensurepip --upgrade
    pause
    exit /b 1
  )
  REM Re-check
  "%PY%" -m pip --version >nul 2>&1
  if %ERRORLEVEL% neq 0 (
    call :errpause "pip still not available after ensurepip."
  )
)

REM Optionally create a venv
set /p USE_VENV="Create and use a virtual environment? [Y/n] "
if /i "%USE_VENV%"=="Y" goto create_venv
if /i "%USE_VENV%"=="" goto create_venv

goto install_reqs

:create_venv
if exist ".venv" (
  echo Existing .venv found. Reusing.
) else (
  echo Creating virtual environment in .venv...
  "%PY%" -m venv .venv
  if %ERRORLEVEL% neq 0 (
    echo Failed to create venv. Continuing with system python.
    goto install_reqs
  )
)
REM Activate venv for the rest of the script
call .venv\Scripts\activate.bat
if %ERRORLEVEL% neq 0 (
  echo Warning: could not activate .venv; attempting to use it directly.
) else (
  set "PY=%~dp0.venv\Scripts\python.exe"
)

:install_reqs
echo Upgrading pip...
"%PY%" -m pip install --upgrade pip setuptools wheel

if exist requirements.txt (
  echo Installing requirements from requirements.txt...
  "%PY%" -m pip install -r requirements.txt
  if %ERRORLEVEL% neq 0 (
    echo Failed to install some requirements. You can try manually:
    echo %PY% -m pip install -r requirements.txt
    pause
  )
) else (
  echo requirements.txt not found, skipping.
)

REM Ask user about building an .exe with PyInstaller
set /p BUILD_EXE="Do you want to build a single-file .exe using PyInstaller? [y/N] "

if /i "%BUILD_EXE%"=="y" (
  echo Checking for PyInstaller...
  "%PY%" -m pip show pyinstaller >nul 2>&1
  if %ERRORLEVEL% neq 0 (
    set /p INSTALL_PYI="PyInstaller is not installed. Install it now? [Y/n] "
    if /i "%INSTALL_PYI%"=="Y" goto install_pyinstaller
    if /i "%INSTALL_PYI%"=="" goto install_pyinstaller
    echo Skipping .exe build.
    goto done
  ) else (
    goto run_pyinstaller
  )
) else (
  goto done
)

:install_pyinstaller
echo Installing PyInstaller...
"%PY%" -m pip install pyinstaller
if %ERRORLEVEL% neq 0 (
  echo Failed to install PyInstaller automatically.
  echo Try running: %PY% -m pip install pyinstaller
  pause
  goto done
)
goto run_pyinstaller

:run_pyinstaller
echo Building single-file executable with PyInstaller...
REM Choose entrypoint and output name
set ENTRY=jugiai.py
if not exist %ENTRY% (
  echo Entry file %ENTRY% not found in current folder: %CD%
  pause
  goto done
)
set /p EXENAME="Executable name (without extension) [AnomAI]: "
if "%EXENAME%"=="" set EXENAME=AnomAI

REM Optionally include icon if make_icon or icon file exists (logo.ico)
set ICON=""
if exist logo.ico (
  set ICON=--icon=logo.ico
)

REM Run PyInstaller (onefile, no console)
"%PY%" -m PyInstaller --onefile --noconsole --name "%EXENAME%" %ICON% %ENTRY%
if %ERRORLEVEL% neq 0 (
  echo PyInstaller build failed.
  echo Check the PyInstaller output above for details.
  pause
  goto done
)

echo Build finished.
echo The executable will be in the "dist" folder:
echo %CD%\dist\%EXENAME%.exe
pause
goto done

:done
echo Installation / build finished.
echo You can run the app with:
echo %PY% jugiai.py
pause
endlocal
