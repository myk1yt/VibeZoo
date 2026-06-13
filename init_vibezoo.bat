@echo off
set "TARGET_DIR=%USERPROFILE%\mcp-servers\vibezoo"
set "REPO_DIR=%~dp0"

echo ===================================================
echo   VibeZoo Universal UX Bootstrapper (Windows)
echo ===================================================
echo.

echo [1/6] Creating standard target directory...
if not exist "%TARGET_DIR%" mkdir "%TARGET_DIR%"

echo [2/6] Copying startup scripts...
copy /Y "%REPO_DIR%start_vibezoo_bridge.bat" "%TARGET_DIR%\" >nul
copy /Y "%REPO_DIR%start_vibezoo_servers.bat" "%TARGET_DIR%\" >nul
copy /Y "%REPO_DIR%watch_vibezoo_bridge.bat" "%TARGET_DIR%\" >nul

echo [3/6] Copying Python bridge files...
copy /Y "%REPO_DIR%extension\mcp-servers\vibezoo_mcp_bridge.py" "%TARGET_DIR%\" >nul
copy /Y "%REPO_DIR%extension\mcp-servers\crow_memory_server.py" "%TARGET_DIR%\" >nul
xcopy /E /I /Y "%REPO_DIR%extension\mcp-servers\bridge" "%TARGET_DIR%\bridge\" >nul
xcopy /E /I /Y "%REPO_DIR%extension\mcp-servers\tools" "%TARGET_DIR%\tools\" >nul

echo [4/6] Creating Python Virtual Environment...
cd /d "%TARGET_DIR%"
python -m venv venv
if %ERRORLEVEL% neq 0 (
    echo Failed to create virtual environment. Make sure python is installed.
    exit /b %ERRORLEVEL%
)

echo [5/6] Installing Python Dependencies...
call venv\Scripts\activate.bat
pip install fastmcp starlette requests tree_sitter_languages
if %ERRORLEVEL% neq 0 (
    echo Failed to install pip packages.
    exit /b %ERRORLEVEL%
)

echo [6/6] Building Frontend Extension...
cd /d "%REPO_DIR%extension"
call npm install
if %ERRORLEVEL% neq 0 (
    echo Failed to run npm install in extension directory.
    exit /b %ERRORLEVEL%
)

call npx tsc
if %ERRORLEVEL% neq 0 (
    echo Failed to compile typescript extension.
    exit /b %ERRORLEVEL%
)

echo.
echo ===================================================
echo   VibeZoo is ready!
echo ===================================================
echo.
echo Runtime directory: %TARGET_DIR%
echo.
echo Next steps:
echo 1. Open VS Code or your MCP client.
echo 2. Install the VibeZoo VSIX from extension/.
echo 3. The init script has copied bridge files to %TARGET_DIR%.
echo 4. autoStartCommand in global MCP settings:
echo    cd /d "%%USERPROFILE%%\mcp-servers\vibezoo" ^&^& start_vibezoo_bridge.bat
echo.
pause
