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

REM Detect Python interpreter (prefer local virtualenv, then system pythonw/python)
set "PYTHON_EXE="
if exist "%~dp0venv\Scripts\pythonw.exe" (
    set "PYTHON_EXE=%~dp0venv\Scripts\pythonw.exe"
) else if exist "%~dp0venv\Scripts\python.exe" (
    set "PYTHON_EXE=%~dp0venv\Scripts\python.exe"
) else (
    where pythonw >nul 2>&1
    if !ERRORLEVEL! equ 0 (
        set "PYTHON_EXE=pythonw"
    ) else (
        set "PYTHON_EXE=python"
    )
)

start "" /b "%PYTHON_EXE%" -X utf8 "%~dp0vibezoo_mcp_bridge.py" --port %PORT%

REM Wait up to 15 seconds for the server to come up
set /a WAIT=0
:waitloop
if !WAIT! GEQ 30 goto :timeout
netstat -ano 2>nul | findstr ":%PORT% " | findstr "LISTENING" >nul 2>&1
if !ERRORLEVEL! equ 0 goto :ready
ping -n 2 127.0.0.1 >nul 2>&1
set /a WAIT+=1
goto :waitloop

:timeout
echo [%date% %time%] WARNING: Bridge did not respond within 15s on port %PORT%. >> "%LOG_FILE%"
exit /b 1

:ready
echo [%date% %time%] VibeZoo Bridge is ready on port %PORT%. >> "%LOG_FILE%"
endlocal
