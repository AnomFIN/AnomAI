@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
pushd "%SCRIPT_DIR%"

title AnomFIN · JugiAI Asennus
color 0b

echo ======================================================
echo    AnomFIN · JugiAI - Älykkyyden käyttöönotto-ohjain
echo ======================================================
echo.
echo Tämä ohjattu toiminto varmistaa, että JugiAI on valmis^
echo toimintaan Windows-ympäristössä.
echo.

set "PYTHON_EXE="
set "PYTHON_FRIENDLY="

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
    echo Virtuaaliympäristön luonti epäonnistui.
    goto :skip_venv
)
set "ACTIVE_PYTHON=%VENV_DIR%\Scripts\python.exe"
if not exist "%ACTIVE_PYTHON%" set "ACTIVE_PYTHON=%VENV_DIR%\Scripts\pythonw.exe"
if not exist "%ACTIVE_PYTHON%" set "ACTIVE_PYTHON=%PYTHON_EXE%"
echo Virtuaaliympäristö valmis: %VENV_DIR%

:skip_venv

echo.
echo Päivitetään pip...
"%ACTIVE_PYTHON%" -m pip install --upgrade pip >nul
if errorlevel 1 (
    echo Pipin päivitys epäonnistui. Jatketaan nykyisellä versiolla.
)

echo.
set "INSTALL_LLAMA=E"
set /p INSTALL_LLAMA=Asennetaanko paikallisen mallin tuki (llama-cpp-python)? [K/E] (valinnainen): 
if /I "%INSTALL_LLAMA%"=="K" (
    echo Asennetaan llama-cpp-python...
    "%ACTIVE_PYTHON%" -m pip install --upgrade llama-cpp-python
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
if errorlevel 1 (
    echo Konfiguraation kirjoitus epäonnistui.
    del "%CONFIG_WRITER%" >nul 2>&1
    goto :cleanup
)
del "%CONFIG_WRITER%" >nul 2>&1

echo.
echo ======================================================
echo Asennus valmis!
echo - Konfiguraatiotiedosto: %SCRIPT_DIR%config.json
echo - Käynnistä sovellus: start_jugiai.bat
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

:cleanup
popd
endlocal
exit /b
