@echo off
REM VibeZoo MCP Bridge - Auto-start script for Windows
REM Launches the VibeZoo MCP Bridge on port 9027
REM Designed to run from %USERPROFILE%\mcp-servers\vibezoo\

setlocal enabledelayedexpansion
cd /d "%~dp0"
set "PORT=9027"
set "LOG_FILE=%~dp0vibezoo_bridge.log"

netstat -ano 2>nul | findstr ":%PORT% " | findstr "LISTENING" >nul 2>&1
if !ERRORLEVEL! equ 0 (
    echo [%date% %time%] VibeZoo Bridge already running on port %PORT%. Skipping. >> "%LOG_FILE%"
    exit /b 0
)

echo [%date% %time%] Starting VibeZoo MCP Bridge on port %PORT%... >> "%LOG_FILE%"

powershell -NoProfile -ExecutionPolicy Bypass -Command "$p = Start-Process -FilePath 'python' -ArgumentList '-X utf8 vibezoo_mcp_bridge.py --port %PORT%' -WorkingDirectory '%~dp0' -WindowStyle Hidden -PassThru; Write-Output $p.Id" >> "%LOG_FILE%" 2>&1

echo [%date% %time%] VibeZoo Bridge started (PID: see above). >> "%LOG_FILE%"
endlocal
