@echo off
:: Windows-native AI. Zero friction, full acceleration.
setlocal enabledelayedexpansion

set "COMPONENT=install_utf8"
set "EXIT_CODE=0"
set "SWITCHED_UTF8=0"
set "INSTALL_SCRIPT=%~dp0install.bat"
set "ORIG_CP="

call :capture_codepage
if defined ORIG_CP (
  call :log INFO "Detected active code page !ORIG_CP!."
) else (
  call :log WARN "Unable to detect active code page before switching."
)

call :switch_to_utf8
call :invoke_install
call :restore_codepage

if not "!EXIT_CODE!"=="0" (
  call :log ERROR "install_utf8 finished with exit code !EXIT_CODE!."
) else (
  call :log INFO "install_utf8 completed successfully."
)

endlocal & exit /b !EXIT_CODE!

goto :eof

:capture_codepage
for /f "tokens=2 delims=:" %%C in ('chcp ^| find ":"') do (
  for /f "tokens=1 delims= " %%D in ("%%C") do set "ORIG_CP=%%D"
)
if defined ORIG_CP (
  set "ORIG_CP=!ORIG_CP: =!"
)
exit /b 0

:switch_to_utf8
if "!ORIG_CP!"=="65001" (
  call :log INFO "Console already using UTF-8 code page."
  goto :eof
)
chcp 65001 >nul 2>&1
if errorlevel 1 (
  call :log WARN "Failed to switch console to UTF-8. Continuing with code page !ORIG_CP!"
  goto :eof
)
set "SWITCHED_UTF8=1"
call :log INFO "Console code page switched to 65001 (UTF-8)."
goto :eof

:invoke_install
if not exist "!INSTALL_SCRIPT!" (
  call :log ERROR "Missing install.bat at !INSTALL_SCRIPT!."
  set "EXIT_CODE=1"
  goto :eof
)
call :log INFO "Delegating to install.bat with UTF-8 environment."
call "!INSTALL_SCRIPT!"
set "EXIT_CODE=!errorlevel!"
if not "!EXIT_CODE!"=="0" (
  call :log ERROR "install.bat exited with code !EXIT_CODE!."
) else (
  call :log INFO "install.bat completed without errors."
)
goto :eof

:restore_codepage
if not defined ORIG_CP goto :eof
if "!SWITCHED_UTF8!"=="0" goto :eof
if "!ORIG_CP!"=="" goto :eof
if "!ORIG_CP!"=="65001" goto :eof
chcp !ORIG_CP! >nul 2>&1
if errorlevel 1 (
  call :log WARN "Failed to restore original code page !ORIG_CP!. Run 'chcp !ORIG_CP!' manually if needed."
) else (
  call :log INFO "Restored original code page !ORIG_CP!."
)
goto :eof

:log
setlocal enabledelayedexpansion
set "LEVEL=%~1"
shift /1
set "MESSAGE="
:log_args
if "%~1"=="" goto log_emit
if defined MESSAGE (
  set "MESSAGE=!MESSAGE! %~1"
) else (
  set "MESSAGE=%~1"
)
shift /1
goto log_args
:log_emit
if not defined MESSAGE set "MESSAGE="
set "MESSAGE=!MESSAGE:"=""!"
echo {"component":"!COMPONENT!","level":"!LEVEL!","message":"!MESSAGE!"}
endlocal & goto :eof
