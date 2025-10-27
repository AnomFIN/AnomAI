@echo off
setlocal EnableExtensions
set "SCRIPT_DIR=%~dp0"
pushd "%SCRIPT_DIR%"

chcp 65001 >nul

echo Käynnistetään JugiAI...

if exist "%SCRIPT_DIR%AnomAI.exe" (
  start "" "%SCRIPT_DIR%AnomAI.exe"
  goto :done
)

if exist "%SCRIPT_DIR%dist\AnomAI\AnomAI.exe" (
  start "" "%SCRIPT_DIR%dist\AnomAI\AnomAI.exe"
  goto :done
)

set "VENV_PYTHONW=%SCRIPT_DIR%\.venv\Scripts\pythonw.exe"
set "VENV_PYTHON=%SCRIPT_DIR%\.venv\Scripts\python.exe"

if exist "%VENV_PYTHONW%" (
  "%VENV_PYTHONW%" "%SCRIPT_DIR%jugiai.py"
  goto :done
)

if exist "%VENV_PYTHON%" (
  "%VENV_PYTHON%" "%SCRIPT_DIR%jugiai.py"
  goto :done
)

where pythonw >nul 2>&1
if %ERRORLEVEL%==0 (
  pythonw "%SCRIPT_DIR%jugiai.py"
  goto :done
)

where py >nul 2>&1
if %ERRORLEVEL%==0 (
  py -3 "%SCRIPT_DIR%jugiai.py"
  goto :done
)

where python >nul 2>&1
if %ERRORLEVEL%==0 (
  python "%SCRIPT_DIR%jugiai.py"
  goto :done
)

echo Python 3 ei löytynyt eikä AnomAI.exe ole saatavilla.
echo Aja install.bat varmistaaksesi asennuksen tai asenna Python osoitteesta:
echo https://www.python.org/downloads/windows/
pause

:done
popd
endlocal
