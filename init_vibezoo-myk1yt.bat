@echo off
setlocal enabledelayedexpansion
set "TARGET_DIR=%USERPROFILE%\mcp-servers\vibezoo"
set "REPO_DIR=%~dp0"

echo ===================================================
echo   VibeZoo Universal UX Bootstrapper (Windows)
echo ===================================================
echo.

echo [1/9] Creating standard target directory...
if not exist "%TARGET_DIR%" mkdir "%TARGET_DIR%"

echo [2/9] Copying startup scripts...
copy /Y "%REPO_DIR%extension\mcp-servers\start_vibezoo_bridge.bat" "%TARGET_DIR%\" >nul

echo [3/9] Copying Python bridge files...
copy /Y "%REPO_DIR%extension\mcp-servers\vibezoo_mcp_bridge.py" "%TARGET_DIR%\" >nul
copy /Y "%REPO_DIR%extension\mcp-servers\crow_memory_server.py" "%TARGET_DIR%\" >nul
xcopy /E /I /Y "%REPO_DIR%extension\mcp-servers\bridge" "%TARGET_DIR%\bridge\" >nul
xcopy /E /I /Y "%REPO_DIR%extension\mcp-servers\tools" "%TARGET_DIR%\tools\" >nul

echo [4/9] Creating Python Virtual Environment...
cd /d "%TARGET_DIR%"
if not exist "venv\Scripts\python.exe" (
    python -m venv venv
    if !ERRORLEVEL! neq 0 (
        echo Failed to create virtual environment. Make sure python is installed.
        exit /b !ERRORLEVEL!
    )
)

echo [5/9] Installing Python Dependencies...
call venv\Scripts\activate.bat
pip install fastmcp starlette requests tree_sitter_languages
if !ERRORLEVEL! neq 0 (
    echo Failed to install pip packages.
    exit /b !ERRORLEVEL!
)

echo [6/9] Building Frontend Extension & Packaging VSIX...
cd /d "%REPO_DIR%extension"
call npm install
if !ERRORLEVEL! neq 0 (
    echo Failed to run npm install in extension directory.
    exit /b !ERRORLEVEL!
)

call npx tsc
if !ERRORLEVEL! neq 0 (
    echo Failed to compile typescript extension.
    exit /b !ERRORLEVEL!
)

call npx vsce package --no-git-tag-version 2>nul
if !ERRORLEVEL! neq 0 (
    call npx vsce package 2>nul
)

echo [7/9] Installing VSIX Extension into VS Code...
set "VSIX_INSTALLED=0"
for %%f in (vibezoo-*.vsix) do (
    call code --install-extension "%%f" --force 2>nul
    if !ERRORLEVEL! equ 0 (
        echo [OK] VSIX installed: %%f
        set "VSIX_INSTALLED=1"
    )
)
if "!VSIX_INSTALLED!"=="0" (
    echo [INFO] Automatic code CLI install skipped or not available. You can install VSIX manually from VS Code extensions menu.
)

echo [8/9] Configuring Global MCP Settings...
set "MCP_DIR=%APPDATA%\Code\User\globalStorage\zoocodeorganization.zoo-code\settings"
if not exist "%MCP_DIR%" mkdir "%MCP_DIR%"
set "MCP_FILE=%MCP_DIR%\mcp_settings.json"

if not exist "%MCP_FILE%" (
    echo {"mcpServers":{"vibezoo":{"url":"http://127.0.0.1:9027/sse","global":true,"alwaysAllow":["vibezoo_setup","search_codebase","web_search","fetch_page","find_references","summarize_architecture","review_code","analyze_call_graph","map_dependencies","extract_patterns","reverse_engineer","analyze_uploaded_file","capture_screen","draw_on_whiteboard","get_whiteboard_state","auto_fix_status","retry_build","check_intervention","review_project","find_bugs","suggest_refactor","generate_docs","review_pr","refactor_across_files","learn_project","recall_project","learn_preference","get_preferences","aggregate_spatial_pixels","vibezoo_feedback","embedding_health_check","rebuild_code_index","check_uploaded_files"]},"crow-memory":{"type":"streamable-http","url":"http://127.0.0.1:9021/mcp","global":true,"alwaysAllow":["crow_recall","crow_ingest","crow_evolve_propose","crow_diagnostics","crow_check_drift","crow_ingest_from_build","crow_get_user_bias","crow_manage_prompt","crow_manage_backup","crow_project_info"]}}}>"%MCP_FILE%"
    echo [OK] MCP settings created: %MCP_FILE%
) else (
    echo [SKIP] MCP settings already exists: %MCP_FILE%
)

echo [9/9] Starting Background MCP Servers...
set "PYTHON_EXE=%TARGET_DIR%\venv\Scripts\python.exe"
if not exist "%PYTHON_EXE%" set "PYTHON_EXE=python"

REM Start Crow Memory server on port 9021 if not running
netstat -ano 2>nul | findstr ":9021 " | findstr "LISTENING" >nul 2>&1
if !ERRORLEVEL! neq 0 (
    start "" /b "%PYTHON_EXE%" -X utf8 "%TARGET_DIR%\crow_memory_server.py" --port 9021
    echo [OK] Crow Memory server starting on port 9021
) else (
    echo [SKIP] Crow Memory server already running on port 9021
)

REM Start VibeZoo Bridge on port 9027 if not running
netstat -ano 2>nul | findstr ":9027 " | findstr "LISTENING" >nul 2>&1
if !ERRORLEVEL! neq 0 (
    start "" /b "%PYTHON_EXE%" -X utf8 "%TARGET_DIR%\vibezoo_mcp_bridge.py" --port 9027
    echo [OK] VibeZoo Bridge starting on port 9027
) else (
    echo [SKIP] VibeZoo Bridge already running on port 9027
)

echo.
echo ===================================================
echo   VibeZoo One-Shot Installation Complete!
echo ===================================================
echo.
echo Runtime directory: %TARGET_DIR%
echo MCP Configuration: %MCP_FILE%
echo.
echo [Services Status]
echo - VibeZoo MCP Bridge : Port 9027 (Streamable HTTP)
echo - Crow Memory Server : Port 9021 (Streamable HTTP)
echo.
echo [Optional Setup]
echo - Exa Neural Search  : set EXA_API_KEY=your_key (for enhanced web search)
echo - Local Embeddings   : LM Studio / Ollama nomic-embed-text on port 8089
echo.
echo Next steps:
echo 1. Open VS Code.
echo 2. Run 'VibeZoo: Self Check' from Command Palette (Ctrl+Shift+P) to verify.
echo.
pause
