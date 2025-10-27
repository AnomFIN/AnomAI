@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "BUILD_STATUS=FAIL"

set "SCRIPT_DIR=%~dp0"
pushd "%SCRIPT_DIR%"

chcp 65001 >nul
title AnomFIN · JugiAI · EXE-rakennin
color 0b

echo ======================================================
echo    AnomFIN · JugiAI - EXE-rakennus
echo ======================================================
echo.

set "PYTHON_CMD="

call :find_python "py -3"
if defined PYTHON_CMD goto :python_ready
call :find_python "python"
if defined PYTHON_CMD goto :python_ready
call :find_python "python3"
if defined PYTHON_CMD goto :python_ready

echo Python 3 -tulkkia ei löytynyt. Asenna uusin versio osoitteesta:
echo https://www.python.org/downloads/windows/
pause
goto :cleanup

:python_ready
echo Käytetään Python-tulkkia: %PYTHON_CMD%

if not exist .venv_build (
    echo Luodaan rakennusympäristö (.venv_build)...
    %PYTHON_CMD% -m venv .venv_build
    if errorlevel 1 (
        echo Virhe: virtuaaliympäristöä ei voitu luoda.
        set "BUILD_STATUS=FAIL"
        goto :summary
    )
)

if not exist .venv_build\Scripts\activate.bat (
    echo Virhe: .venv_build\Scripts\activate.bat puuttuu.
    set "BUILD_STATUS=FAIL"
    goto :summary
)

call .venv_build\Scripts\activate.bat
set "BUILD_STATUS=OK"

call :run_with_retry "python -m pip install --upgrade pip" "Pipin päivitys" 1
call :run_with_retry "python -m pip install --upgrade pyinstaller pillow pyinstaller-hooks-contrib" "PyInstaller-riippuvuuksien asennus" 0
if errorlevel 1 (
    echo PyInstaller-riippuvuuksia ei saatu asennettua. Keskeytetään.
    set "BUILD_STATUS=FAIL"
    goto :summary
)

set "INSTALL_LLAMA=K"
set /p INSTALL_LLAMA=Lisätäänkö paikallisen mallin tuki (llama-cpp-python)? [K/E] (oletus K):
if /I "%INSTALL_LLAMA%"=="K" (
    call :run_with_retry "python -m pip install --upgrade --prefer-binary llama-cpp-python" "llama-cpp-pythonin asennus" 0
    if errorlevel 1 (
        echo Huom: paikallisen mallin tuki ei sisälly buildiin ennen kuin asennus onnistuu.
    ) else (
        set "LLAMA_AVAILABLE=1"
    )
) else (
    echo Paikallisen mallin tuki ohitettiin käyttäjän pyynnöstä.
)

if not defined LLAMA_AVAILABLE (
    python -c "import importlib.util, sys; sys.exit(0 if importlib.util.find_spec('llama_cpp') else 1)" >nul 2>&1
    if not errorlevel 1 set "LLAMA_AVAILABLE=1"
)

if exist logo.png (
    call :run_with_retry "python make_ico.py logo.png logo.ico" "logo.ico (ikoni)" 0
    if errorlevel 1 (
        echo logon muunto epäonnistui. Käytetään PyInstallerin oletusikonia.
    ) else (
        set "ICON_PATH=%SCRIPT_DIR%logo.ico"
    )
) else (
    echo logo.png puuttuu - käytetään oletusikonia.
)

set "PYINSTALLER_OPTS=--noconsole --name AnomAI"
if defined ICON_PATH set "PYINSTALLER_OPTS=%PYINSTALLER_OPTS% --icon \"%ICON_PATH%\""
if exist README.MD set "PYINSTALLER_OPTS=%PYINSTALLER_OPTS% --add-data \"README.MD;.\""
if exist logo.png set "PYINSTALLER_OPTS=%PYINSTALLER_OPTS% --add-data \"logo.png;.\""
if defined LLAMA_AVAILABLE set "PYINSTALLER_OPTS=%PYINSTALLER_OPTS% --collect-all llama_cpp"

echo Käynnistetään PyInstaller...
call :run_with_retry "python -m pyinstaller %PYINSTALLER_OPTS% jugiai.py" "AnomAI.exe:n koostaminen" 0
if errorlevel 1 (
    echo EXE:n koostaminen epäonnistui. Tarkista virheilmoitus ja yritä uudelleen.
    set "BUILD_STATUS=FAIL"
    goto :summary
)

set "EXE_PATH=%SCRIPT_DIR%dist\AnomAI\AnomAI.exe"
if not exist "%EXE_PATH%" (
    echo dist\AnomAI\AnomAI.exe puuttuu.
    set "BUILD_STATUS=FAIL"
    goto :summary
)

copy /Y "%EXE_PATH%" "%SCRIPT_DIR%AnomAI.exe" >nul 2>&1
if errorlevel 1 (
    echo AnomAI.exe:n kopiointi juurikansioon epäonnistui. Käytä dist-kansion versiota.
) else (
    echo Suora käynnistin saatavilla: %SCRIPT_DIR%AnomAI.exe
)

echo Luodaan jakopaketti...
powershell -NoProfile -Command "Compress-Archive -Force -Path '%SCRIPT_DIR%dist\AnomAI\*' -DestinationPath '%SCRIPT_DIR%AnomAI_Windows.zip'" >nul 2>&1
if errorlevel 1 (
    echo Zip-paketin luonti epäonnistui. Voit pakata kansion manuaalisesti.
) else (
    echo Zip-valmis: %SCRIPT_DIR%AnomAI_Windows.zip
)

echo Valmis! Löydät tiedoston: %EXE_PATH%

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
echo.
echo === !DESC! ===
call %CMD%
set "ERR=%ERRORLEVEL%"
if !ERR! EQU 0 goto :retry_success
echo.
echo !DESC! epäonnistui (virhekoodi !ERR!).
set "RETRY=K"
set /p RETRY=Yritetäänkö uudelleen? [K/E] (oletus K):
if /I "!RETRY!"=="E" (
    if "!OPTIONAL!"=="1" (
        echo Ohitetaan vaihe: !DESC!.
        set "ERR=0"
        goto :retry_success
    ) else (
        echo Vaihetta ei voitu suorittaa loppuun.
        exit /b 1
    )
)
goto :retry_loop

:retry_success
exit /b !ERR!

:summary
echo.
echo ======================================================
if /I "%BUILD_STATUS%"=="OK" (
    echo AnomAI.exe rakennettu onnistuneesti!
    if exist "%EXE_PATH%" echo - %EXE_PATH%
    if exist "%SCRIPT_DIR%AnomAI.exe" echo - %SCRIPT_DIR%AnomAI.exe
    if exist "%SCRIPT_DIR%AnomAI_Windows.zip" echo - %SCRIPT_DIR%AnomAI_Windows.zip
) else (
    echo Rakennus epäonnistui. Tarkista ilmoitetut virheet ja yritä uudelleen.
)
echo ======================================================

call :maybe_pause

goto :cleanup

:cleanup
popd
endlocal
exit /b

:maybe_pause
if /I "%CI%"=="true" goto :eof
if "%BUILD_NONINTERACTIVE%"=="1" goto :eof
pause
goto :eof
