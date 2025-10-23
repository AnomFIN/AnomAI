@echo off
:: Switch to UTF-8 code page and delegate to install.bat
chcp 65001 >nul
call "%~dp0install.bat"
