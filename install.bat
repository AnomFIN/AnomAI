@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "SCRIPT_DIR=%~dp0"
pushd "%SCRIPT_DIR%"

chcp 65001 >nul
title AnomFIN · JugiAI Asennus
color 0b

echo ======================================================
echo    AnomFIN · JugiAI - ^Älykkyyden käyttöönotto-ohjain
echo ======================================================
echo.
echo Tämä ohjattu toiminto varmistaa, että JugiAI on valmis^
echo toimintaan Windows-ympäristössä.
echo.

set "PYTHON_EXE="
set "PYTHON_FRIENDLY="
set "ACTIVE_PYTHON="
set "BUILD_STATUS=OK"
set "LLAMA_INSTALLED="

call :resolvePython "py -3"
if defined PYTHON_EXE goto :python_found
call :resolvePython "python"
if defined PYTHON_EXE goto :python_found
call :resolvePython "python3"
if defined PYTHON_EXE goto :python_found

echo Python 3 -tulkkia ei löytynyt. Asenna uusin versio osoitteesta:
echo https://www.python.org/downloads/windows/
pause
goto :cleanup

:python_found
echo Löydetty Python: %PYTHON_EXE%

:confirm_python
set "CUSTOM_PY="
set /p CUSTOM_PY=Anna halutessasi toinen Python 3 -tulkki (Enter = käytä löydettyä):
if defined CUSTOM_PY (
    if exist "%CUSTOM_PY%" (
        set "PYTHON_EXE=%CUSTOM_PY%"
        goto :python_version_check
    ) else (
        echo Polkua "%CUSTOM_PY%" ei löytynyt. Yritä uudelleen.
        goto :confirm_python
    )
)

goto :python_version_check

:python_version_check
"%PYTHON_EXE%" -c "import sys; assert sys.version_info >= (3, 9)" >nul 2>&1
if errorlevel 1 (
    echo Python-version on oltava 3.9 tai uudempi.
    goto :confirm_python
)

echo Käytetään Python-tulkkia: %PYTHON_EXE%
set "ACTIVE_PYTHON=%PYTHON_EXE%"

set "VENV_DIR=%SCRIPT_DIR%venv"
set "CREATE_VENV=K"
set /p CREATE_VENV=Luodaanko erillinen virtuaaliympäristö venv-kansioon? [K/E] (oletus K):
if /I "%CREATE_VENV%"=="E" goto :skip_venv

echo Luodaan virtuaaliympäristö...
"%PYTHON_EXE%" -m venv "%VENV_DIR%"
if errorlevel 1 (
    echo Virtuaaliympäristön luonti epäonnistui. Jatketaan järjestelmän Pythonilla.
    goto :skip_venv
)
set "ACTIVE_PYTHON=%VENV_DIR%\Scripts\python.exe"
if not exist "%ACTIVE_PYTHON%" set "ACTIVE_PYTHON=%VENV_DIR%\Scripts\pythonw.exe"
if not exist "%ACTIVE_PYTHON%" set "ACTIVE_PYTHON=%PYTHON_EXE%"
echo Virtuaaliympäristö valmis: %VENV_DIR%

:skip_venv

echo.
call :run_with_retry "\"%ACTIVE_PYTHON%\" -m pip install --upgrade pip" "Pipin päivitys" 1

echo.
set "INSTALL_LLAMA=E"
set /p INSTALL_LLAMA=Asennetaanko paikallisen mallin tuki (llama-cpp-python)? [K/E] (valinnainen):
if /I "%INSTALL_LLAMA%"=="K" (
    call :run_with_retry "\"%ACTIVE_PYTHON%\" -m pip install --upgrade --prefer-binary llama-cpp-python" "llama-cpp-pythonin asennus" 0
    if errorlevel 1 (
        echo Huom: paikallisen mallin tuki ei ole käytettävissä ennen kuin asennus onnistuu.
    ) else (
        set "LLAMA_INSTALLED=1"
    )
)

echo.
echo *** JugiAI:n konfigurointi ***
:ask_api
set "OPENAI_KEY="
set /p OPENAI_KEY=Syötä OpenAI API -avain (pakollinen):
if not defined OPENAI_KEY (
    echo API-avain tarvitaan jatkaaksesi.
    goto :ask_api
)

set "MODEL="
set /p MODEL=Ensisijainen malli [gpt-4o-mini]:
if not defined MODEL set "MODEL=gpt-4o-mini"

set "SYSTEM_PROMPT="
echo Anna halutessasi mukautettu system-prompt (Enter = käytä oletusta):
set /p SYSTEM_PROMPT=:

set "TEMPERATURE="
set /p TEMPERATURE=Temperature (0-2) [0.7]:
if not defined TEMPERATURE set "TEMPERATURE=0.7"

set "TOP_P="
set /p TOP_P=top_p (0-1) [1.0]:
if not defined TOP_P set "TOP_P=1.0"

set "MAX_TOKENS="
set /p MAX_TOKENS=max_tokens (Enter = ei rajaa):

set "PRESENCE="
set /p PRESENCE=presence_penalty (-2–2) [0.0]:
if not defined PRESENCE set "PRESENCE=0.0"

set "FREQUENCY="
set /p FREQUENCY=frequency_penalty (-2–2) [0.0]:
if not defined FREQUENCY set "FREQUENCY=0.0"

set "BACKEND="
set /p BACKEND=Taustajärjestelmä [openai/local] (oletus openai):
if not defined BACKEND set "BACKEND=openai"

set "BG_CHOICE="
set /p BG_CHOICE=Aktivoidaanko AnomFIN-taustayhdistelmä? [K/E] (oletus K):
if /I "%BG_CHOICE%"=="E" (
    set "BG_ENABLED=0"
) else (
    set "BG_ENABLED=1"
)

set "BG_PATH="
set /p BG_PATH=Taustakuvan polku (Enter = jätä tyhjä):

set "BG_OPACITY="
set /p BG_OPACITY=Taustan peittävyys (0-1) [0.18]:
if not defined BG_OPACITY set "BG_OPACITY=0.18"

set "FONT_SIZE="
set /p FONT_SIZE=Chat-tekstin pistekoko [12]:
if not defined FONT_SIZE set "FONT_SIZE=12"

set "ANOMAI_API_KEY=%OPENAI_KEY%"
set "ANOMAI_MODEL=%MODEL%"
set "ANOMAI_SYSTEM_PROMPT=%SYSTEM_PROMPT%"
set "ANOMAI_TEMPERATURE=%TEMPERATURE%"
set "ANOMAI_TOP_P=%TOP_P%"
set "ANOMAI_MAX_TOKENS=%MAX_TOKENS%"
set "ANOMAI_PRESENCE=%PRESENCE%"
set "ANOMAI_FREQUENCY=%FREQUENCY%"
set "ANOMAI_BACKEND=%BACKEND%"
set "ANOMAI_BG_ENABLED=%BG_ENABLED%"
set "ANOMAI_BG_PATH=%BG_PATH%"
set "ANOMAI_BG_OPACITY=%BG_OPACITY%"
set "ANOMAI_FONT_SIZE=%FONT_SIZE%"
set "ANOMAI_CONFIG_PATH=%SCRIPT_DIR%config.json"
set "ANOMAI_HISTORY_PATH=%SCRIPT_DIR%history.json"

set "CONFIG_WRITER=%TEMP%\anomai_config_writer.py"
>"%CONFIG_WRITER%" (
    echo import copy
    echo import json
    echo import os
    echo import pathlib
    echo from jugiai import DEFAULT_CONFIG, DEFAULT_PROFILE, DEFAULT_PROFILE_NAME
    echo
    echo def _float(value, default):
    echo     try:
    echo         return float(value)
    echo     except (TypeError, ValueError):
    echo         return default
    echo
    echo def _int(value):
    echo     try:
    echo         return int(value)
    echo     except (TypeError, ValueError):
    echo         return None
    echo
    echo config = copy.deepcopy(DEFAULT_CONFIG)
    echo profile = copy.deepcopy(DEFAULT_PROFILE)
    echo
    echo config_path = pathlib.Path(os.environ.get("ANOMAI_CONFIG_PATH", "config.json")).resolve()
    echo history_path = pathlib.Path(os.environ.get("ANOMAI_HISTORY_PATH", "history.json")).resolve()
    echo
    echo api_key = os.environ.get("ANOMAI_API_KEY", "").strip()
    echo if not api_key:
    echo     raise SystemExit("API-avain puuttuu.")
    echo config["api_key"] = api_key
    echo
    echo model = os.environ.get("ANOMAI_MODEL", "").strip() or config["model"]
    echo backend = os.environ.get("ANOMAI_BACKEND", "openai").strip().lower() or "openai"
    echo system_prompt = os.environ.get("ANOMAI_SYSTEM_PROMPT", "").strip()
    echo if system_prompt:
    echo     config["system_prompt"] = system_prompt
    echo     profile["system_prompt"] = system_prompt
    echo
    echo config["model"] = model
    echo config["backend"] = backend
    echo config["temperature"] = _float(os.environ.get("ANOMAI_TEMPERATURE"), config["temperature"])
    echo config["top_p"] = _float(os.environ.get("ANOMAI_TOP_P"), config["top_p"])
    echo config["presence_penalty"] = _float(os.environ.get("ANOMAI_PRESENCE"), config["presence_penalty"])
    echo config["frequency_penalty"] = _float(os.environ.get("ANOMAI_FREQUENCY"), config["frequency_penalty"])
    echo max_tokens = os.environ.get("ANOMAI_MAX_TOKENS", "").strip()
    echo config["max_tokens"] = _int(max_tokens) if max_tokens else None
    echo config["show_background"] = os.environ.get("ANOMAI_BG_ENABLED", "1").strip().lower() not in {"0", "false", "e", "ei"}
    echo config["background_path"] = os.environ.get("ANOMAI_BG_PATH", "").strip()
    echo config["background_opacity"] = _float(os.environ.get("ANOMAI_BG_OPACITY"), config["background_opacity"])
    echo config["font_size"] = _int(os.environ.get("ANOMAI_FONT_SIZE")) or config["font_size"]
    echo
    echo profile.update(
    echo     {
    echo         "model": model,
    echo         "system_prompt": config["system_prompt"],
    echo         "temperature": config["temperature"],
    echo         "top_p": config["top_p"],
    echo         "max_tokens": config["max_tokens"],
    echo         "presence_penalty": config["presence_penalty"],
    echo         "frequency_penalty": config["frequency_penalty"],
    echo         "backend": backend,
    echo     }
    echo )
    echo profiles = copy.deepcopy(config.get("profiles", {}))
    echo profiles[DEFAULT_PROFILE_NAME] = profile
    echo config["profiles"] = profiles
    echo config["active_profile"] = profile.get("name", DEFAULT_PROFILE_NAME)
    echo
    echo config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    echo if not history_path.exists():
    echo     history_path.write_text("[]\n", encoding="utf-8")
    echo print(f"Konfiguraatio tallennettu: {config_path}")
)

"%ACTIVE_PYTHON%" "%CONFIG_WRITER%"
set "CFG_ERROR=%ERRORLEVEL%"
del "%CONFIG_WRITER%" >nul 2>&1
if %CFG_ERROR% NEQ 0 (
    echo Konfiguraation kirjoitus epäonnistui.
    set "BUILD_STATUS=FAIL"
    goto :summary
)

echo.
echo *** Luodaan AnomAI.exe ***
call :run_with_retry "\"%ACTIVE_PYTHON%\" -m pip install --upgrade pyinstaller pillow pyinstaller-hooks-contrib" "PyInstaller-riippuvuuksien asennus" 0
if errorlevel 1 (
    echo PyInstaller-riippuvuuksia ei saatu asennettua. Asennus jatkuu ilman EXE-pakettia.
    set "BUILD_STATUS=FAIL"
    goto :summary
)

set "LLAMA_AVAILABLE="
if defined LLAMA_INSTALLED set "LLAMA_AVAILABLE=1"
if not defined LLAMA_AVAILABLE (
    "%ACTIVE_PYTHON%" -c "import importlib.util, sys; sys.exit(0 if importlib.util.find_spec('llama_cpp') else 1)" >nul 2>&1
    if errorlevel 1 (
        set "LLAMA_AVAILABLE="
        echo Huom: llama-cpp-pythonia ei löytynyt. Paikallisen mallin tuki ei sisälly EXE:hen.
    ) else (
        set "LLAMA_AVAILABLE=1"
    )
)

if exist logo.png (
    call :run_with_retry "\"%ACTIVE_PYTHON%\" make_ico.py logo.png logo.ico" "logo.ico (pikakuvake ja ikoni)" 0
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

call :run_with_retry "\"%ACTIVE_PYTHON%\" -m pyinstaller %PYINSTALLER_OPTS% jugiai.py" "AnomAI.exe:n koostaminen" 0
if errorlevel 1 (
    echo EXE:n koostaminen epäonnistui. Tarkista yllä oleva virheilmoitus ja yritä uudelleen.
    set "BUILD_STATUS=FAIL"
    goto :summary
)

set "EXE_PATH=%SCRIPT_DIR%dist\AnomAI\AnomAI.exe"
if not exist "%EXE_PATH%" (
    echo Valmista AnomAI.exe-tiedostoa ei löytynyt.
    set "BUILD_STATUS=FAIL"
    goto :summary
)

copy /Y "%EXE_PATH%" "%SCRIPT_DIR%AnomAI.exe" >nul 2>&1
if errorlevel 1 (
    echo AnomAI.exe:n kopiointi juurikansioon epäonnistui. Käytä dist-kansion versiota.
) else (
    echo Suora käynnistin saatavilla: %SCRIPT_DIR%AnomAI.exe
)

echo Pakataan julkaisuversio zip-arkistoon...
powershell -NoProfile -Command "Compress-Archive -Force -Path '%SCRIPT_DIR%dist\AnomAI\*' -DestinationPath '%SCRIPT_DIR%AnomAI_Windows.zip'" >nul 2>&1
if errorlevel 1 (
    echo Zip-paketin luonti ei onnistunut. Voit luoda sen myöhemmin ajamalla build_exe.bat.
)

echo Luodaan työpöydälle pikakuvake...
set "DESKTOP_DIR="
for /f "usebackq tokens=* delims=" %%D in (`powershell -NoProfile -Command "[Environment]::GetFolderPath('Desktop')"`) do set "DESKTOP_DIR=%%D"
if defined DESKTOP_DIR (
    set "SHORTCUT=%DESKTOP_DIR%\AnomAI.lnk"
    set "SC_ICON=%ICON_PATH%"
    if not defined SC_ICON set "SC_ICON=%EXE_PATH%"
    powershell -NoProfile -Command "^$w=New-Object -ComObject WScript.Shell; ^$s=^$w.CreateShortcut('%SHORTCUT%'); ^$s.TargetPath='%EXE_PATH%'; ^$s.WorkingDirectory='%SCRIPT_DIR%'; ^$s.IconLocation='%SC_ICON%'; ^$s.Save()" >nul 2>&1
    if errorlevel 1 (
        echo Pikakuvakkeen luonti epäonnistui. Luo tarvittaessa manuaalisesti kohteeseen: %DESKTOP_DIR%
    ) else (
        echo Pikakuvake luotu: %SHORTCUT%
    )
) else (
    echo Työpöydän polkua ei löytynyt, pikakuvakkeen luonti ohitetaan.
)

:summary
echo.
echo ======================================================
if /I "%BUILD_STATUS%"=="OK" (
    echo Asennus valmis!
    if exist "%SCRIPT_DIR%config.json" echo - Konfiguraatiotiedosto: %SCRIPT_DIR%config.json
    if exist "%EXE_PATH%" echo - Suorituskelpoinen tiedosto: %EXE_PATH%
    if exist "%SCRIPT_DIR%AnomAI.exe" echo - Pikakäynnistin: %SCRIPT_DIR%AnomAI.exe
    if exist "%SCRIPT_DIR%AnomAI_Windows.zip" echo - Jakopaketti: %SCRIPT_DIR%AnomAI_Windows.zip
    echo - Käynnistä sovellus: start_jugiai.bat tai työpöydän AnomAI-pikakuvake
) else (
    echo Asennus suoritettiin, mutta kaikki vaiheet eivät onnistuneet.
    echo Tarkista virheilmoitukset ja aja install.bat uudelleen tarvittaessa.
)
echo.
echo Pidä API-avaimesi tallessa ja nauti JugiAI:n tehostetusta käyttöliittymästä.
echo ======================================================
echo.
pause

goto :cleanup

:resolvePython
set "TRY=%~1"
for /f "usebackq tokens=* delims=" %%P in (`%TRY% -c "import sys; print(sys.executable)" 2^>nul`) do (
    set "PYTHON_EXE=%%P"
    set "PYTHON_FRIENDLY=%TRY%"
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

:cleanup
popd
endlocal
exit /b
