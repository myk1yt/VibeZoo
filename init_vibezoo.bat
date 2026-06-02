@echo off
echo ===================================================
echo   VibeZoo Universal UX Bootstrapper (Windows)
echo ===================================================
echo.

echo [1/3] Creating Python Virtual Environment...
python -m venv venv
if %ERRORLEVEL% neq 0 (
    echo Failed to create virtual environment. Make sure python is installed.
    exit /b %ERRORLEVEL%
)

echo [2/3] Installing Python Requirements...
call venv\Scripts\activate.bat
pip install -r requirements.txt
if %ERRORLEVEL% neq 0 (
    echo Failed to install pip requirements.
    exit /b %ERRORLEVEL%
)

echo [3/3] Building Frontend Extension...
cd extension
call npm install
if %ERRORLEVEL% neq 0 (
    echo Failed to run npm install in extension directory.
    cd ..
    exit /b %ERRORLEVEL%
)

call npx tsc
if %ERRORLEVEL% neq 0 (
    echo Failed to compile typescript extension.
    cd ..
    exit /b %ERRORLEVEL%
)
cd ..

echo.
echo ===================================================
echo   VibeZoo is ready!
echo ===================================================
echo Next steps:
echo 1. Open VS Code or your MCP client.
echo 2. Run the agent and it will auto-bootstrap using .zoo/Agent.md guidelines.
echo 3. The agent can configure your mcp.json settings for you!
echo.
pause
