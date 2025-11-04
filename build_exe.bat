@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "BUILD_STATUS=FAIL"

set "SCRIPT_DIR=%~dp0"
pushd "%SCRIPT_DIR%"

chcp 65001 >nul
title AnomFIN · JugiAI · EXE-rakennin
color 0b

set "LOG_FILE=%SCRIPT_DIR%build_exe.log"
if exist "%LOG_FILE%" del "%LOG_FILE%" >nul 2>&1

call :log "=============================================="
call :log "   AnomFIN · JugiAI - EXE-rakennus"
call :log "=============================================="
call :log ""
call :log "Lokit tallentuvat tiedostoon: %LOG_FILE%"
call :log "Haetaan Python-tulkki..."

set "PYTHON_CMD="

call :find_python "py -3"
if defined PYTHON_CMD goto :python_ready
call :find_python "python"
if defined PYTHON_CMD goto :python_ready
call :find_python "python3"
if defined PYTHON_CMD goto :python_ready

call :log "Python 3 -tulkkia ei löytynyt. Asenna uusin versio osoitteesta:"
call :log "https://www.python.org/downloads/windows/"
call :maybe_pause
goto :cleanup

:python_ready
call :log "Käytetään Python-tulkkia: %PYTHON_CMD%"

for /f "usebackq tokens=*" %%V in (`%PYTHON_CMD% -c "import platform; print(platform.python_version())" 2^>nul`) do set "PYTHON_VERSION=%%V"
for /f "usebackq tokens=*" %%B in (`%PYTHON_CMD% -c "import struct; print(struct.calcsize('P')*8)" 2^>nul`) do set "PYTHON_BITS=%%B"

if defined PYTHON_VERSION (
    call :log "Python-versio: %PYTHON_VERSION%"
) else (
    call :log "Varoitus: Python-version selvitys epäonnistui."
)

if defined PYTHON_BITS (
    call :log "Arkkitehtuuri: %PYTHON_BITS%-bittinen"
)

%PYTHON_CMD% -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
if errorlevel 1 (
    call :log "Virhe: Tarvitaan vähintään Python 3.10. Päivitä tulkki ja yritä uudelleen."
    goto :summary_fail
)

%PYTHON_CMD% -c "import struct,sys; sys.exit(0 if struct.calcsize('P')*8 == 64 else 1)" >nul 2>&1
if errorlevel 1 (
    call :log "Virhe: Tarvitaan 64-bittinen Python. Asenna 64-bittinen versio ja yritä uudelleen."
    goto :summary_fail
)

if not exist .venv_build (
    call :log "Luodaan rakennusympäristö (.venv_build)..."
    %PYTHON_CMD% -m venv .venv_build
    if errorlevel 1 (
        call :log "Virhe: virtuaaliympäristöä ei voitu luoda."
        set "BUILD_STATUS=FAIL"
        goto :summary_fail
    )
)

if not exist .venv_build\Scripts\activate.bat (
    call :log "Virhe: .venv_build\Scripts\activate.bat puuttuu."
    set "BUILD_STATUS=FAIL"
    goto :summary_fail
)

call .venv_build\Scripts\activate.bat
set "BUILD_STATUS=OK"

call :run_with_retry "python -m pip install --upgrade pip" "Pipin päivitys" 1
call :run_with_retry "python -m pip install --upgrade pyinstaller pillow pyinstaller-hooks-contrib" "PyInstaller-riippuvuuksien asennus" 0
if errorlevel 1 (
    call :log "PyInstaller-riippuvuuksia ei saatu asennettua. Keskeytetään."
    set "BUILD_STATUS=FAIL"
    goto :summary_fail
)

set "INSTALL_LLAMA=K"
if /I not "%CI%"=="true" if not "%BUILD_NONINTERACTIVE%"=="1" (
    set /p INSTALL_LLAMA=Lisätäänkö paikallisen mallin tuki (llama-cpp-python)? [K/E] (oletus K):
)
if /I "%INSTALL_LLAMA%"=="K" (
    call :run_with_retry "python -m pip install --upgrade --prefer-binary llama-cpp-python" "llama-cpp-pythonin asennus" 0
    if errorlevel 1 (
        call :log "Huom: paikallisen mallin tuki ei sisälly buildiin ennen kuin asennus onnistuu."
    ) else (
        set "LLAMA_AVAILABLE=1"
    )
) else (
    call :log "Paikallisen mallin tuki ohitettiin käyttäjän pyynnöstä."
)

if not defined LLAMA_AVAILABLE (
    python -c "import importlib.util, sys; sys.exit(0 if importlib.util.find_spec('llama_cpp') else 1)" >nul 2>&1
    if not errorlevel 1 set "LLAMA_AVAILABLE=1"
)

if exist logo.png (
    call :run_with_retry "python make_ico.py logo.png logo.ico" "logo.ico (ikoni)" 0
    if errorlevel 1 (
        call :log "logon muunto epäonnistui. Käytetään PyInstallerin oletusikonia."
    ) else (
        set "ICON_PATH=%SCRIPT_DIR%logo.ico"
    )
) else (
    call :log "logo.png puuttuu - käytetään oletusikonia."
)

set "PYINSTALLER_OPTS=--noconsole --name AnomAI"
if defined ICON_PATH set "PYINSTALLER_OPTS=%PYINSTALLER_OPTS% --icon ""%ICON_PATH%"""
if exist README.MD set "PYINSTALLER_OPTS=%PYINSTALLER_OPTS% --add-data ""README.MD;."""
if exist logo.png set "PYINSTALLER_OPTS=%PYINSTALLER_OPTS% --add-data ""logo.png;."""
if defined LLAMA_AVAILABLE set "PYINSTALLER_OPTS=%PYINSTALLER_OPTS% --collect-all llama_cpp"

set "PYINSTALLER_CMD=python -m pyinstaller %PYINSTALLER_OPTS% jugiai.py"
call :log "Käynnistetään PyInstaller komennolla:"
call :log "  %PYINSTALLER_CMD%"
call :run_with_retry "%PYINSTALLER_CMD%" "AnomAI.exe:n koostaminen" 0
if errorlevel 1 (
    call :log "EXE:n koostaminen epäonnistui. Tarkista virheilmoitus ja yritä uudelleen."
    set "BUILD_STATUS=FAIL"
    goto :summary_fail
)

set "EXE_PATH=%SCRIPT_DIR%dist\AnomAI\AnomAI.exe"
if not exist "%EXE_PATH%" (
    call :log "dist\AnomAI\AnomAI.exe puuttuu."
    set "BUILD_STATUS=FAIL"
    goto :summary_fail
)

copy /Y "%EXE_PATH%" "%SCRIPT_DIR%AnomAI.exe" >nul 2>&1
if errorlevel 1 (
    call :log "AnomAI.exe:n kopiointi juurikansioon epäonnistui. Käytä dist-kansion versiota."
) else (
    call :log "Suora käynnistin saatavilla: %SCRIPT_DIR%AnomAI.exe"
)

call :log "Luodaan jakopaketti..."
powershell -NoProfile -Command "Compress-Archive -Force -Path '%SCRIPT_DIR%dist\AnomAI\*' -DestinationPath '%SCRIPT_DIR%AnomAI_Windows.zip'" >nul 2>&1
if errorlevel 1 (
    call :log "Zip-paketin luonti epäonnistui. Voit pakata kansion manuaalisesti."
) else (
    call :log "Zip-valmis: %SCRIPT_DIR%AnomAI_Windows.zip"
)

call :log "Valmis! Löydät tiedoston: %EXE_PATH%"

goto :summary

:find_python
set "TRY=%~1"
for /f "usebackq tokens=* delims=" %%P in (`%TRY% -c "import sys; print(sys.executable)" 2^>nul`) do (
    set "PYTHON_CMD=%TRY%"
    goto :eof
)
goto :eof

:run_with_retry
set "CMD=%~1"
set "DESC=%~2"
set "OPTIONAL=%~3"
if not defined OPTIONAL set "OPTIONAL=0"
set "RETRY=K"
:retry_loop
call :log ""
call :log "=== !DESC! ==="
call :log "Komento: %CMD%"
if defined LOG_FILE (
    set "BUILD_RUN_CMD=%CMD%"
    powershell -NoProfile -Command "& { $cmd=$env:BUILD_RUN_CMD; $log=$env:LOG_FILE; if (-not $cmd) { exit 0 }; cmd.exe /c $cmd 2>&1 | Tee-Object -FilePath $log -Append; exit $LASTEXITCODE }"
    set "BUILD_RUN_CMD="
) else (
    call %CMD%
)
set "ERR=%ERRORLEVEL%"
if !ERR! EQU 0 goto :retry_success
call :log ""
call :log "!DESC! epäonnistui (virhekoodi !ERR!)."
set "RETRY=K"
if /I not "%CI%"=="true" if not "%BUILD_NONINTERACTIVE%"=="1" (
    set /p RETRY=Yritetäänkö uudelleen? [K/E] (oletus K):
)
if /I "!RETRY!"=="E" (
    if "!OPTIONAL!"=="1" (
        call :log "Ohitetaan vaihe: !DESC!."
        set "ERR=0"
        goto :retry_success
    ) else (
        call :log "Vaihetta ei voitu suorittaa loppuun."
        exit /b 1
    )
)
goto :retry_loop

:retry_success
exit /b !ERR!

:log
set "LOG_MSG=%~1"
if not defined LOG_MSG (
    echo.
    if defined LOG_FILE >>"%LOG_FILE%" echo.
    exit /b 0
)
echo %LOG_MSG%
if defined LOG_FILE (
    >>"%LOG_FILE%" echo [%DATE% %TIME%] %LOG_MSG%
)
exit /b 0

:summary
call :log ""
call :log "======================================================"
if /I "%BUILD_STATUS%"=="OK" (
    call :log "AnomAI.exe rakennettu onnistuneesti!"
    if exist "%EXE_PATH%" call :log "- %EXE_PATH%"
    if exist "%SCRIPT_DIR%AnomAI.exe" call :log "- %SCRIPT_DIR%AnomAI.exe"
    if exist "%SCRIPT_DIR%AnomAI_Windows.zip" call :log "- %SCRIPT_DIR%AnomAI_Windows.zip"
) else (
    call :log "Rakennus epäonnistui. Tarkista ilmoitetut virheet ja yritä uudelleen."
    call :log "Lisätiedot: %LOG_FILE%"
)
call :log "======================================================"

call :maybe_pause

goto :cleanup

:summary_fail
set "BUILD_STATUS=FAIL"
goto :summary

:cleanup
popd
endlocal
exit /b

:maybe_pause
if /I "%CI%"=="true" goto :eof
if "%BUILD_NONINTERACTIVE%"=="1" goto :eof
pause
goto :eof
