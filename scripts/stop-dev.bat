@echo off
echo ==============================================================================
echo [DIGITAL DOCTOR] Stopping Development Environment
echo Note: Named volumes are preserved to protect MySQL and ChromaDB clinical data.
echo ==============================================================================

where docker >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Docker was not found on PATH.
    pause
    exit /b 1
)

docker compose -f compose.yaml -f compose.dev.yaml down
echo Digital Doctor containers stopped successfully.
pause
