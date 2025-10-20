@echo off
:: Robust Windows installer/build script
setlocal enabledelayedexpansion
if "%BUILD_NONINTERACTIVE%"=="1" (
  set "NONINTERACTIVE=1"
) else (
  set "NONINTERACTIVE=0"
)
:err_exit
echo.
echo ERROR: %~1
pause
exit /b 1
where python3 >nul 2>&1
if %ERRORLEVEL%==0 (
  set "PY=python3"
) else (
  where python >nul 2>&1
  if %ERRORLEVEL%==0 (
    set "PY=python"
  ) else (
    call :err_exit "Python 3 not found on PATH."
  )
)
echo Using %PY%
"%PY%" -m pip --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
  echo pip not found. Attempting ensurepip...
  "%PY%" -m ensurepip --upgrade >nul 2>&1
  if %ERRORLEVEL% neq 0 (
    echo Could not bootstrap pip. Install pip manually.
    pause
    exit /b 1
  )
)
set "BUILD_VENV=.venv_build"
if "%NONINTERACTIVE%"=="0" (
  set /p CREATE_VENV="Create/use build venv %BUILD_VENV%? [Y/n] "
) else (
  set "CREATE_VENV=Y"
)
if /i "%CREATE_VENV%"=="Y" (
  if exist "%BUILD_VENV%" (
    echo Reusing %BUILD_VENV%
  ) else (
    echo Creating %BUILD_VENV%...
    "%PY%" -m venv "%BUILD_VENV%"
    if %ERRORLEVEL% neq 0 (
      echo Failed to create %BUILD_VENV%; continuing with system python
      set "BUILD_VENV="
    )
  )
)
if exist "%BUILD_VENV%\Scripts\activate.bat" (
  call "%BUILD_VENV%\Scripts\activate.bat"
  if %ERRORLEVEL% neq 0 (
    echo Warning: could not activate %BUILD_VENV%; using system python
  ) else (
    set "PY=%CD%\%BUILD_VENV%\Scripts\python.exe"
  )
)
"%PY%" -m pip install --upgrade pip setuptools wheel
if exist requirements.txt (
  "%PY%" -m pip install -r requirements.txt
)
if "%NONINTERACTIVE%"=="0" (
  set /p BUILD_EXE="Do you want to build a single-file .exe using PyInstaller? [y/N] "
) else (
  set "BUILD_EXE=n"
)
if /i "%BUILD_EXE%"=="y" (
  "%PY%" -m pip show pyinstaller >nul 2>&1
  if %ERRORLEVEL% neq 0 (
    if "%NONINTERACTIVE%"=="0" (
      set /p INSTALL_PYI="PyInstaller not found. Install now? [Y/n] "
    ) else (
      set "INSTALL_PYI=Y"
    )
    if /i "%INSTALL_PYI%"=="Y" (
      "%PY%" -m pip install pyinstaller
      if %ERRORLEVEL% neq 0 (
        echo Failed to install PyInstaller
        pause
        goto done
      )
    ) else (
      echo Skipping exe build.
      goto done
    )
  )
  set "ADD_DATA="
  for %%F in (config2.json history.json requirements.txt logo.ico) do (
    if exist "%%~F" (
      set "ADD_DATA=!ADD_DATA! --add-data "%%~F;%%~F""
    )
  )
  for %%D in (wallps recordings AnomFIN apple) do (
    if exist "%%~D" (
      set "ADD_DATA=!ADD_DATA! --add-data "%%~D;%%~D""
    )
  )
  set "ENTRY=jugiai.py"
  if not exist %ENTRY% (
    echo Entry %ENTRY% not found. Cannot build.
    pause
    goto done
  )
  if "%NONINTERACTIVE%"=="0" (
    set /p EXENAME="Executable name (without extension) [AnomAI]: "
  ) else (
    set "EXENAME=AnomAI"
  )
  if "%EXENAME%"=="" set "EXENAME=AnomAI"
  "%PY%" -m PyInstaller --onefile --noconsole --name "%EXENAME%" %ADD_DATA% %ENTRY%
  if %ERRORLEVEL% neq 0 (
    echo PyInstaller build failed.
    pause
    goto done
  )
  echo Build complete.
  pause
)
:done
endlocal
