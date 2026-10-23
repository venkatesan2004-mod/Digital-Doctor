@echo off
echo ==============================================================================
echo [DIGITAL DOCTOR] Running Automated Test Suite
echo ==============================================================================

where docker >nul 2>nul
if %errorlevel% neq 0 (
    echo [INFO] Docker not detected. Attempting to run test suite with host Python...
    where python >nul 2>nul
    if %errorlevel% neq 0 (
        echo [ERROR] Neither Docker nor local Python found.
        pause
        exit /b 1
    )
    cd backend
    python -m pytest tests/ -v
    cd ..
    pause
    exit /b 0
)

echo Executing backend pytest in container...
docker compose exec backend pytest -v
echo.
pause
