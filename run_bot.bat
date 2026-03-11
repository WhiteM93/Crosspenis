@echo off
chcp 65001 >nul
cd /d "%~dp0"
if "%~1"=="" (
    powershell -ExecutionPolicy Bypass -File "%~dp0run_bot.ps1" status
) else (
    powershell -ExecutionPolicy Bypass -File "%~dp0run_bot.ps1" %*
)
