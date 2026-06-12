@echo off
title VibeZoo Bridge Watchdog
REM ============================================================
REM Watchdog — VibeZoo MCP Bridge (port 9027)
REM Restarts the bridge if it becomes unresponsive.
REM Logs to %USERPROFILE%\.vibezoo\watchdog_bridge.log
REM ============================================================
setlocal enabledelayedexpansion
cd /d "%~dp0"
set "PORT=9027"
set "PYTHON=python"
set "LOG_DIR=%USERPROFILE%\.vibezoo"
set "LOG_FILE=%LOG_DIR%\watchdog_bridge.log"
set "FAIL_COUNT=0"
set "MAX_FAIL=5"

if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
echo [%date% %time%] [Watchdog] Started. Polling port %PORT% every 30s. >> "%LOG_FILE%"

:loop
timeout /t 30 /nobreak >nul

REM Check if port is listening
netstat -ano 2>nul | findstr /R " 127\.0\.0\.1:%PORT% " | findstr "LISTENING" >nul 2>&1
if !ERRORLEVEL! neq 0 (
    set /a FAIL_COUNT+=1
    echo [%date% %time%] [WATCHDOG] Bridge is DOWN on port !PORT! (fail !FAIL_COUNT!/!MAX_FAIL!). Restarting... >> "%LOG_FILE%"
    if !FAIL_COUNT! lss !MAX_FAIL! (
        powershell -NoProfile -ExecutionPolicy Bypass -Command "$p = Start-Process -FilePath '!PYTHON!' -ArgumentList '-X utf8 \"%~dp0mcp-servers\vibezoo_mcp_bridge.py\" --port !PORT!' -WorkingDirectory '%~dp0' -WindowStyle Hidden -PassThru; Write-Output $p.Id" >> "%LOG_FILE%" 2>&1
    ) else (
        echo [%date% %time%] [WATCHDOG] Max failures (!MAX_FAIL!) reached. Stopping watchdog. >> "%LOG_FILE%"
        exit /b 1
    )
) else (
    set "FAIL_COUNT=0"
    echo [%date% %time%] [WATCHDOG] Bridge is running on port !PORT!. >> "%LOG_FILE%"
)
goto loop
endlocal
