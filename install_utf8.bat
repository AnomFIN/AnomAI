@echo off
rem UTF-8 wrapper for install.bat
rem Sets UTF-8 code page and calls the main installer

chcp 65001 >nul
call "%~dp0install.bat" %*
exit /b %ERRORLEVEL%
