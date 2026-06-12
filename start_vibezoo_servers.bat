@echo off
REM VibeZoo Servers — Crow Memory (9020) + VibeZoo Bridge (9027) Auto-start Script
REM Launches both MCP servers in background and waits for them to become healthy.
REM
REM Crow Memory: delegates to REAL Crow's start_crow_sse.bat (NOT the FAKE server)
REM VibeZoo Bridge: starts via vibezoo_mcp_bridge.py

setlocal enabledelayedexpansion

cd /d "%~dp0"
set "SCRIPT_DIR=%~dp0"
set "LOG_DIR=%USERPROFILE%\.vibezoo"
set "LOG_FILE=%SCRIPT_DIR%vibezoo_servers.log"
set "PYTHON=python"
set "CROW_DIR=..\Crow Memory"
set "VIBEZOO_DIR=%~dp0"
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

echo [%date% %time%] ====== VibeZoo Servers Launcher ====== >> "%LOG_FILE%"

REM ─────────────────────────────────────────────
REM  1. Check Python availability
REM ─────────────────────────────────────────────
if not exist "%PYTHON%" (
    echo [%date% %time%] ERROR: Python not found at %PYTHON% >> "%LOG_FILE%"
    echo ERROR: Python not found at %PYTHON%
    pause
    exit /b 1
)
echo [%date% %time%] Python found: %PYTHON% >> "%LOG_FILE%"

REM ─────────────────────────────────────────────
REM  2. Start REAL Crow Memory Server (port 9020) via start_crow_sse.bat
REM ─────────────────────────────────────────────
set "CROW_PORT=9020"

echo. >> "%LOG_FILE%"
echo [%date% %time%] --- Crow Memory Server (port !CROW_PORT!) --- >> "%LOG_FILE%"

REM Check if already listening on port CROW_PORT
netstat -ano 2>nul | findstr ":%CROW_PORT% " | findstr "LISTENING" >nul 2>&1
if !ERRORLEVEL! equ 0 (
    echo [%date% %time%] Crow Memory Server already running on port !CROW_PORT!. Skipping. >> "%LOG_FILE%"
    set "CROW_STARTED=skip"
) else (
    echo [%date% %time%] Starting REAL Crow Memory Server via start_crow_sse.bat... >> "%LOG_FILE%"
    start "CrowMemory" /MIN cmd /c ""%CROW_DIR%\start_crow_sse.bat" >> "%LOG_FILE%" 2>&1"
    echo [%date% %time%] Crow Memory Server launch command issued. >> "%LOG_FILE%"
    set "CROW_STARTED=yes"
)

REM ─────────────────────────────────────────────
REM  3. Start VibeZoo Bridge (port 9027)
REM ─────────────────────────────────────────────
set "BRIDGE_PORT=9027"

echo. >> "%LOG_FILE%"
echo [%date% %time%] --- VibeZoo MCP Bridge (port !BRIDGE_PORT!) --- >> "%LOG_FILE%"

REM Check if already listening on port BRIDGE_PORT
netstat -ano 2>nul | findstr ":%BRIDGE_PORT% " | findstr "LISTENING" >nul 2>&1
if !ERRORLEVEL! equ 0 (
    echo [%date% %time%] VibeZoo Bridge already running on port !BRIDGE_PORT!. Skipping. >> "%LOG_FILE%"
    set "BRIDGE_STARTED=skip"
) else (
    echo [%date% %time%] Starting VibeZoo MCP Bridge on port !BRIDGE_PORT!... >> "%LOG_FILE%"
    powershell -NoProfile -ExecutionPolicy Bypass -Command ^
        "$p = Start-Process -FilePath '%PYTHON%' -ArgumentList '-X utf8 mcp-servers\vibezoo_mcp_bridge.py --port !BRIDGE_PORT!' -WorkingDirectory '%VIBEZOO_DIR%' -WindowStyle Hidden -PassThru -RedirectStandardError '%LOG_DIR%\bridge_stderr.log' -RedirectStandardOutput '%LOG_DIR%\bridge_stdout.log'; Write-Output $p.Id" >> "%LOG_FILE%" 2>&1
    echo [%date% %time%] VibeZoo Bridge launch command issued. >> "%LOG_FILE%"
    set "BRIDGE_STARTED=yes"
)

REM ─────────────────────────────────────────────
REM  4. Health Check — wait for servers to become ready
REM ─────────────────────────────────────────────
echo. >> "%LOG_FILE%"
echo [%date% %time%] --- Health Check --- >> "%LOG_FILE%"

set "MAX_RETRIES=30"
set "RETRY_INTERVAL=2"

REM ── Crow Memory Health Check ──
if /i not "!CROW_STARTED!"=="yes" goto :skip_crow_health

echo [%date% %time%] Waiting for Crow Memory Server to be ready... >> "%LOG_FILE%"
set "CROW_READY=no"
set "RETRY_COUNT=0"

:retry_crow
if !RETRY_COUNT! geq !MAX_RETRIES! goto :crow_timeout

>nul 2>&1 "%SYSTEMROOT%\System32\curl.exe" -s -f http://127.0.0.1:!CROW_PORT!/health
if !ERRORLEVEL! equ 0 (
    set "CROW_READY=yes"
    echo [%date% %time%] Crow Memory Server is ready! >> "%LOG_FILE%"
    goto :crow_done
)

set /a RETRY_COUNT+=1
>nul ping -n !RETRY_INTERVAL! 127.0.0.1
goto :retry_crow

:crow_timeout
echo [%date% %time%] WARNING: Crow Memory Server did not respond within timeout. >> "%LOG_FILE%"

:crow_done
goto :skip_crow_health

:skip_crow_health
if /i "!CROW_STARTED!"=="skip" (
    echo [%date% %time%] Crow Memory Server was already running. >> "%LOG_FILE%"
)

REM ── VibeZoo Bridge Health Check ──
if /i not "!BRIDGE_STARTED!"=="yes" goto :skip_bridge_health

echo [%date% %time%] Waiting for VibeZoo Bridge to be ready... >> "%LOG_FILE%"
set "BRIDGE_READY=no"
set "RETRY_COUNT=0"

:retry_bridge
if !RETRY_COUNT! geq !MAX_RETRIES! goto :bridge_timeout

>nul 2>&1 "%SYSTEMROOT%\System32\curl.exe" -s -f http://127.0.0.1:!BRIDGE_PORT!/health
if !ERRORLEVEL! equ 0 (
    set "BRIDGE_READY=yes"
    echo [%date% %time%] VibeZoo Bridge is ready! >> "%LOG_FILE%"
    goto :bridge_done
)

set /a RETRY_COUNT+=1
>nul ping -n !RETRY_INTERVAL! 127.0.0.1
goto :retry_bridge

:bridge_timeout
echo [%date% %time%] WARNING: VibeZoo Bridge did not respond within timeout. >> "%LOG_FILE%"

:bridge_done
goto :skip_bridge_health

:skip_bridge_health
if /i "!BRIDGE_STARTED!"=="skip" (
    echo [%date% %time%] VibeZoo Bridge was already running. >> "%LOG_FILE%"
)

REM ─────────────────────────────────────────────
REM  5. Summary
REM ─────────────────────────────────────────────
echo. >> "%LOG_FILE%"
echo [%date% %time%] ====== VibeZoo Servers Launcher Complete ====== >> "%LOG_FILE%"
echo. >> "%LOG_FILE%"

echo.
echo ===== VibeZoo Servers =====
echo   Crow Memory Server : http://127.0.0.1:%CROW_PORT%/health
echo   VibeZoo Bridge     : http://127.0.0.1:%BRIDGE_PORT%/health
echo.
echo Log file: %LOG_FILE%
echo.

endlocal
