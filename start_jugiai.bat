@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
pushd "%SCRIPT_DIR%"
echo Käynnistetään JugiAI...

REM Yritä ensin pythonw (ei konsoli-ikkunaa)
where pythonw >nul 2>&1
if %ERRORLEVEL%==0 (
  pythonw "%SCRIPT_DIR%jugiai.py"
  goto :done
)

REM Fallback: py -3 (voi avata konsoli-ikkunan)
where py >nul 2>&1
if %ERRORLEVEL%==0 (
  py -3 "%SCRIPT_DIR%jugiai.py"
  goto :done
)

REM Fallback: python
where python >nul 2>&1
if %ERRORLEVEL%==0 (
  python "%SCRIPT_DIR%jugiai.py"
  goto :done
)

echo Python 3 ei löytynyt. Asenna Windowsille: https://www.python.org/downloads/windows/
pause

:done
popd
endlocal

