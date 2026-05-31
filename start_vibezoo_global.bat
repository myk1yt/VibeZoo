@echo off
REM VibeZoo & Crow Memory — Global SSE MCP Auto-Start Script
REM Installed to Windows Startup folder for automatic boot-time startup.

set "VIBEZOO_DIR=C:\Users\k1yt\OneDrive\문서\각종자료\공부자료들\파이썬_Python\VibeZoo_forZoocode"

echo [1/2] Starting Crow Memory Server (port 9020)...
start /B python "%VIBEZOO_DIR%\mcp-servers\crow_memory_server.py" --port 9020

timeout /t 3 /nobreak >nul

echo [2/2] Starting VibeZoo Bridge (port 9027)...
start /B python "%VIBEZOO_DIR%\mcp-servers\vibezoo_mcp_bridge.py" --port 9027

timeout /t 2 /nobreak >nul

echo.
echo ========================================
echo  Both servers are now running:
echo   Crow Memory: http://127.0.0.1:9020/health
echo   VibeZoo:     http://127.0.0.1:9027/health
echo ========================================
echo.
