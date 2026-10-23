@echo off
echo ==============================================================================
echo [DIGITAL DOCTOR] Seeding Synthetic Development Clinical Data
echo ==============================================================================

cd /d "%~dp0\.."

where docker >nul 2>nul
if %errorlevel% neq 0 (
    echo [INFO] Docker not detected. Attempting to seed via host Python...
    cd backend
    python -m app.scripts.seed_data
    cd ..
    pause
    exit /b 0
)

echo Executing seed script in backend container...
docker compose exec backend python -m app.scripts.seed_data
echo Synthetic records loaded successfully.
pause
