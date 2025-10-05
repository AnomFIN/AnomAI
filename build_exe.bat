@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
pushd "%SCRIPT_DIR%"

echo === JugiAI .exe build (PyInstaller) ===

REM Ensure Python is present
where py >nul 2>&1
if %ERRORLEVEL%==0 (
  set PY=py -3
) else (
  where python >nul 2>&1
  if %ERRORLEVEL%==0 (
    set PY=python
  ) else (
    echo Python 3 not found. Install from https://www.python.org/downloads/windows/
    pause
    exit /b 1
  )
)

REM Create/activate build venv
if not exist .venv_build (
  %PY% -m venv .venv_build
)
call .venv_build\Scripts\activate.bat

REM Install build deps (PyInstaller, Pillow, hooks, and local LLM runtime)
python -m pip install --upgrade pip
python -m pip install pyinstaller pillow pyinstaller-hooks-contrib llama-cpp-python

REM Convert logo.png -> app.ico if logo exists
if exist logo.png (
  python make_ico.py logo.png app.ico
) else (
  echo logo.png not found; using default PyInstaller icon.
)

REM Build executable
set ICON_ARG=
if exist app.ico set ICON_ARG=--icon app.ico

pyinstaller --noconsole --name JugiAI %ICON_ARG% ^
  --collect-all llama_cpp ^
  --add-data "README.md;." ^
  --add-data "README.txt;." ^
  --add-data "logo.png;." ^
  jugiai.py

if %ERRORLEVEL% NEQ 0 (
  echo Build failed.
  pause
  exit /b 1
)

REM Package dist into a zip for distribution
set DIST_DIR=dist\JugiAI
if exist "%DIST_DIR%" (
  powershell -NoProfile -Command "Compress-Archive -Force -Path '%DIST_DIR%\*' -DestinationPath 'JugiAI_Windows.zip'"
  echo Built: %CD%\JugiAI_Windows.zip
  echo EXE:   %CD%\dist\JugiAI\JugiAI.exe
) else (
  echo dist\JugiAI not found
)

echo Done.
popd
endlocal

