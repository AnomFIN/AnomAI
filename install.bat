@echo off
setlocal enabledelayedexpansion

echo ============================================
echo    AnomAI/JugiAI Installation Script
echo ============================================
echo.
echo This script will set up AnomAI on your system.
echo.

REM Store the script directory
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

REM Try to find Python 3 executable
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

REM If Python not found, offer to download and guide user
if not defined PY_CMD (
  echo WARNING: Python 3 is not installed or not on PATH.
  echo.
  echo Python 3.10+ ^(64-bit^) is required for AnomAI.
  echo.
  echo Please follow these steps:
  echo 1. Download Python 3.10+ ^(64-bit^) from:
  echo    https://www.python.org/downloads/windows/
  echo.
  echo 2. During installation, MAKE SURE to check:
  echo    [X] Add python.exe to PATH
  echo.
  echo 3. After installation, close this window and run install.bat again.
  echo.
  set /p OPEN_BROWSER=Would you like to open the Python download page now? [Y/N] (default Y): 
  if /I "!OPEN_BROWSER!"=="" set "OPEN_BROWSER=Y"
  if /I "!OPEN_BROWSER!"=="Y" (
    echo Opening browser...
    start https://www.python.org/downloads/windows/
  )
  echo.
  echo After installing Python, please run this script again.
  call :maybe_pause
  endlocal
  exit /b 1
)

REM Get Python version and architecture
echo.
echo Checking Python installation...
for /f "usebackq tokens=*" %%V in (`%PY_CMD% -c "import sys; print('.'.join(map(str, sys.version_info[:2])))" 2^>nul`) do set "PY_VER=%%V"
for /f "usebackq tokens=*" %%B in (`%PY_CMD% -c "import struct; print(struct.calcsize('P')*8)" 2^>nul`) do set "PY_BITS=%%B"

if not defined PY_VER (
  echo ERROR: Could not determine Python version with %PY_CMD%.
  echo Please ensure Python is properly installed.
  call :maybe_pause
  endlocal
  exit /b 1
)

REM Parse major and minor version
for /f "tokens=1 delims=." %%A in ("%PY_VER%") do set "PY_MAJOR=%%A"
for /f "tokens=2 delims=." %%B in ("%PY_VER%") do set "PY_MINOR=%%B"

echo [OK] Detected Python version %PY_VER% using %PY_CMD%
if defined PY_BITS echo [OK] Architecture: %PY_BITS%-bit

REM Validate Python version
if not defined PY_MAJOR set "PY_MAJOR=0"
if not defined PY_MINOR set "PY_MINOR=0"

if %PY_MAJOR% LSS 3 (
  echo [ERROR] Python 3.x is required, but found version %PY_VER%
  echo Please install Python 3.10+ from https://www.python.org/downloads/windows/
  call :maybe_pause
  endlocal
  exit /b 1
)
if %PY_MAJOR% EQU 3 if %PY_MINOR% LSS 10 (
  echo [ERROR] Python 3.10+ is required, but found version %PY_VER%
  echo Please install Python 3.10 or newer from https://www.python.org/downloads/windows/
  call :maybe_pause
  endlocal
  exit /b 1
)

if not "%PY_BITS%"=="64" (
  echo [ERROR] 64-bit Python is required, but found %PY_BITS%-bit version
  echo Please install the 64-bit edition of Python 3.10+ from:
  echo https://www.python.org/downloads/windows/
  echo.
  echo Make sure to download the "Windows installer (64-bit)" version.
  call :maybe_pause
  endlocal
  exit /b 1
)

echo [OK] Python version meets requirements (3.10+ 64-bit)

echo.
echo ============================================
echo    Step 1: Virtual Environment Setup
echo ============================================

REM Create virtual environment
if not exist ".venv\Scripts\activate.bat" (
  echo Creating virtual environment in .venv...
  %PY_CMD% -m venv .venv
  if !errorlevel! neq 0 (
    echo [ERROR] Failed to create virtual environment.
    echo This might happen if the venv module is not installed.
    echo.
    echo Try running: %PY_CMD% -m pip install --user virtualenv
    call :maybe_pause
    endlocal
    exit /b 1
  )
  echo [OK] Virtual environment created successfully
) else (
  echo [OK] Using existing virtual environment .venv
)

echo Activating virtual environment...
call ".venv\Scripts\activate.bat"
if !errorlevel! neq 0 (
  echo [ERROR] Failed to activate virtual environment.
  call :maybe_pause
  endlocal
  exit /b 1
)
echo [OK] Virtual environment activated

echo.
echo ============================================
echo    Step 2: Upgrading pip and tools
echo ============================================

echo Upgrading pip, setuptools and wheel...
python -m pip install --upgrade pip setuptools wheel >nul 2>&1
if !errorlevel! neq 0 (
  echo [WARNING] Failed to upgrade pip/setuptools/wheel silently, trying with output...
  python -m pip install --upgrade pip setuptools wheel
  if !errorlevel! neq 0 (
    echo [ERROR] Failed to upgrade pip/setuptools/wheel.
    echo This might be a network issue. Check your internet connection.
    call :maybe_pause
    endlocal
    exit /b 1
  )
)
echo [OK] pip, setuptools, and wheel upgraded successfully

echo.
echo ============================================
echo    Step 3: Installing Dependencies
echo ============================================

REM Install requirements if file exists
if exist requirements.txt (
  echo Installing requirements from requirements.txt...
  echo This may take a few minutes...
  python -m pip install -r requirements.txt
  if !errorlevel! neq 0 (
    echo [ERROR] pip install failed. See output above.
    echo Check your internet connection and try again.
    call :maybe_pause
    endlocal
    exit /b 1
  )
  echo [OK] Requirements installed successfully
) else (
  echo [WARNING] No requirements.txt found — skipping pip install step.
)

echo.
echo ========================================
echo Local GGUF/LLM Model Support
echo ========================================
echo.
echo AnomAI can run local GGUF models offline using llama-cpp-python.
echo.
echo Standard installation includes CPU support only.
echo For GPU acceleration (CUDA), you'll need to manually install
echo a CUDA-enabled wheel after this installation completes.
echo.
echo GPU installation example (after this script):
echo   python -m pip install llama-cpp-python --extra-index-url https://jllllll.github.io/llama-cpp-python-cuBLAS-wheels/AVX2/cu121
echo.
set "INSTALL_LLAMA="
set /p INSTALL_LLAMA=Install local GGUF/llama support (llama-cpp-python)? [Y/N] (default Y): 
if /I "%INSTALL_LLAMA%"=="" set "INSTALL_LLAMA=Y"
if /I "%INSTALL_LLAMA%"=="N" (
  echo Skipping llama-cpp-python installation at user request.
  echo You can always install it later with:
  echo   .\.venv\Scripts\python.exe -m pip install --upgrade --prefer-binary llama-cpp-python
) else (
  echo Installing llama-cpp-python with --prefer-binary...
  echo This may take several minutes...
  python -m pip install --upgrade --prefer-binary llama-cpp-python
  if %errorlevel% neq 0 (
    echo WARNING: llama-cpp-python installation failed. You can retry manually with:
    echo   %PY_CMD% -m pip install --upgrade --prefer-binary llama-cpp-python
    echo or follow Windows-specific wheel instructions from the README.
    echo.
    echo For GPU support (CUDA), visit:
    echo   https://github.com/abetlen/llama-cpp-python#installation-with-hardware-acceleration
  ) else (
    echo.
    echo Local model support ready (llama-cpp-python installed in CPU mode).
    echo.
    echo For GPU acceleration, you can upgrade to a CUDA wheel:
    echo   python -m pip install llama-cpp-python --force-reinstall --no-cache-dir --extra-index-url https://jllllll.github.io/llama-cpp-python-cuBLAS-wheels/AVX2/cu121
  )
)

echo.
echo ============================================
echo    Step 5: Configuration Setup
echo ============================================
echo.

REM Check if config.json already exists
if exist config.json (
  echo [OK] Configuration file already exists: config.json
  set /p RECONFIG=Would you like to reconfigure? [Y/N] (default N): 
  if /I "!RECONFIG!"=="" set "RECONFIG=N"
  if /I "!RECONFIG!"=="N" (
    echo [SKIP] Keeping existing configuration
    goto :skip_config
  )
)

echo Let's set up your AnomAI configuration...
echo.
echo Press ENTER to use default values shown in [brackets]
echo.

REM Get API Key
set "API_KEY="
set /p API_KEY=OpenAI API Key (leave empty if using local models only): 
if not defined API_KEY set "API_KEY="

REM Get Model
set "MODEL=gpt-4o-mini"
set /p MODEL=OpenAI Model [gpt-4o-mini]: 
if "!MODEL!"=="" set "MODEL=gpt-4o-mini"

REM Get Temperature
set "TEMPERATURE=0.7"
set /p TEMPERATURE=Temperature (0.0-2.0) [0.7]: 
if "!TEMPERATURE!"=="" set "TEMPERATURE=0.7"

REM Get Max Tokens
set "MAX_TOKENS=4000"
set /p MAX_TOKENS=Max Tokens [4000]: 
if "!MAX_TOKENS!"=="" set "MAX_TOKENS=4000"

REM Create config.json using Python for proper JSON encoding
echo Creating config.json...
python -c "import json; config = {'api_key': '''!API_KEY!''', 'model': '''!MODEL!''', 'temperature': float('''!TEMPERATURE!'''), 'max_tokens': int('''!MAX_TOKENS!'''), 'backend': 'openai' if '''!API_KEY!''' else 'local', 'offline_mode': False}; json.dump(config, open('config.json', 'w', encoding='utf-8'), indent=2)"
if !errorlevel! neq 0 (
  echo [ERROR] Failed to create config.json
  call :maybe_pause
  endlocal
  exit /b 1
)
echo [OK] Configuration saved to config.json

:skip_config

REM Create empty history.json if it doesn't exist
if not exist history.json (
  echo Creating history.json...
  echo [] > history.json
  echo [OK] History file created
)

echo.
echo ============================================
echo    Step 6: Building Executable (Optional)
echo ============================================
echo.
echo Would you like to build AnomAI.exe?
echo This allows you to run AnomAI without activating the virtual environment.
echo.

set "BUILD_EXE="
set /p BUILD_EXE=Build AnomAI.exe? [Y/N] (default Y): 
if /I "!BUILD_EXE!"=="" set "BUILD_EXE=Y"
if /I "!BUILD_EXE!"=="N" (
  echo [SKIP] Skipping EXE build at user request.
  goto :skip_exe_build
)

echo Installing PyInstaller...
python -m pip install --upgrade pyinstaller pillow >nul 2>&1
if !errorlevel! neq 0 (
  echo [WARNING] Failed to install PyInstaller. Skipping EXE build.
  goto :skip_exe_build
)

echo Building executable...
echo This may take several minutes...

REM Convert logo.png to logo.ico if Pillow is available
if exist logo.png (
  if not exist logo.ico (
    echo Converting logo.png to logo.ico...
    python -c "from PIL import Image; img = Image.open('logo.png'); img.save('logo.ico', format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])" >nul 2>&1
    if !errorlevel! equ 0 (
      echo [OK] Icon created
    )
  )
)

REM Build with PyInstaller
set "ICON_ARG="
if exist logo.ico set "ICON_ARG=--icon=logo.ico"

python -m PyInstaller --onefile --windowed --name AnomAI !ICON_ARG! jugiai.py >nul 2>&1
if !errorlevel! neq 0 (
  echo [WARNING] PyInstaller build failed. See error above.
  echo You can still run the application using start_jugiai.bat
  goto :skip_exe_build
)

REM Copy executable to root directory
if exist dist\AnomAI.exe (
  copy /Y dist\AnomAI.exe AnomAI.exe >nul 2>&1
  echo [OK] AnomAI.exe created successfully
) else (
  echo [WARNING] AnomAI.exe was not created in the expected location
)

:skip_exe_build

echo.
echo ============================================
echo    Step 7: Desktop Shortcut (Optional)
echo ============================================
echo.

set "CREATE_SHORTCUT="
set /p CREATE_SHORTCUT=Create desktop shortcut? [Y/N] (default Y): 
if /I "!CREATE_SHORTCUT!"=="" set "CREATE_SHORTCUT=Y"
if /I "!CREATE_SHORTCUT!"=="N" (
  echo [SKIP] Skipping desktop shortcut creation.
  goto :skip_shortcut
)

REM Try to create desktop shortcut using PowerShell
echo Creating desktop shortcut...
set "TARGET_EXE=%SCRIPT_DIR%AnomAI.exe"
if not exist "!TARGET_EXE!" set "TARGET_EXE=%SCRIPT_DIR%start_jugiai.bat"

powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\AnomAI.lnk'); $Shortcut.TargetPath = '!TARGET_EXE!'; $Shortcut.WorkingDirectory = '%SCRIPT_DIR%'; if (Test-Path '%SCRIPT_DIR%logo.ico') { $Shortcut.IconLocation = '%SCRIPT_DIR%logo.ico' }; $Shortcut.Save()" >nul 2>&1

if !errorlevel! equ 0 (
  echo [OK] Desktop shortcut created
) else (
  echo [WARNING] Failed to create desktop shortcut automatically.
  echo You can manually create a shortcut by right-clicking on:
  echo !TARGET_EXE!
  echo and selecting "Send to" ^> "Desktop (create shortcut)"
)

:skip_shortcut

echo.
echo ============================================
echo    Installation Complete!
echo ============================================
echo.
echo AnomAI has been installed successfully!
echo.
echo To start AnomAI:

if exist AnomAI.exe (
  echo   - Double-click the AnomAI desktop shortcut, or
  echo   - Run: AnomAI.exe
) else (
  echo   - Run: start_jugiai.bat
  echo   - Or: .\.venv\Scripts\python.exe jugiai.py
)

echo.
echo To activate the virtual environment manually:
echo   .\.venv\Scripts\activate.bat
echo.
echo Configuration file: config.json
echo History file: history.json
echo.
echo For help and documentation, see README.MD
echo.
call :maybe_pause
endlocal
exit /b 0

:maybe_pause
REM Skip pause when running in CI or in non-interactive builds
if /I "%CI%"=="true" goto :eof
if "%BUILD_NONINTERACTIVE%"=="1" goto :eof
pause
goto :eof