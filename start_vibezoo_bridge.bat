@echo off
REM VibeZoo MCP Bridge - Auto-start script for Windows
REM Launches the VibeZoo MCP Bridge on port 9027

setlocal enabledelayedexpansion
cd /d "%~dp0"
set "PORT=9027"
set "LOG_FILE=%~dp0vibezoo_bridge.log"

set "BRIDGE_SCRIPT=%~dp0extension\mcp-servers\vibezoo_mcp_bridge.py"
if not exist "%BRIDGE_SCRIPT%" set "BRIDGE_SCRIPT=%~dp0vibezoo_mcp_bridge.py"

set "PYTHON_EXE=python"
if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" set "PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"

netstat -ano 2>nul | findstr ":%PORT% " | findstr "LISTENING" >nul 2>&1
if !ERRORLEVEL! equ 0 (
    echo [%date% %time%] VibeZoo Bridge already running on port %PORT%. Skipping. >> "%LOG_FILE%"
    exit /b 0
)

echo [%date% %time%] Starting VibeZoo MCP Bridge on port %PORT%... >> "%LOG_FILE%"

powershell -NoProfile -ExecutionPolicy Bypass -Command "$p = Start-Process -FilePath '%PYTHON_EXE%' -ArgumentList @('-X', 'utf8', '\"%BRIDGE_SCRIPT%\"', '--port', '%PORT%') -WorkingDirectory '%~dp0' -WindowStyle Hidden -PassThru; Write-Output $p.Id; $sw = [Diagnostics.Stopwatch]::StartNew(); while ($sw.ElapsedMilliseconds -lt 10000) { if (netstat -ano 2^>$null | Select-String ':%PORT% ' | Select-String 'LISTENING') { break }; Start-Sleep -Milliseconds 200 }" >> "%LOG_FILE%" 2>&1

echo [%date% %time%] VibeZoo Bridge started. >> "%LOG_FILE%"
endlocal
