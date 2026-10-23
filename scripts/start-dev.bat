@echo off
setlocal enabledelayedexpansion

echo ==============================================================================
echo [DIGITAL DOCTOR] Starting Development Environment
echo ==============================================================================

cd /d "%~dp0\.."

if not exist .env (
    echo [.env] not found. Copying .env.example to .env...
    copy .env.example .env
)

where docker >nul 2>nul
if %errorlevel% neq 0 goto :NO_DOCKER

echo Building and launching Docker containers [Backend, Frontend, MySQL, ChromaDB]...
docker compose -f compose.yaml -f compose.dev.yaml up --build -d

echo Waiting for services to reach healthy status...
docker compose ps

echo.
echo ==============================================================================
echo Digital Doctor is running in Docker!
echo Frontend [Kiosk and Dashboard]: http://localhost:5173
echo Backend API Docs:              http://localhost:8000/docs
echo ChromaDB Vector Store:         http://localhost:8001
echo ==============================================================================
echo To view live logs: docker compose logs -f
pause
exit /b 0

:NO_DOCKER
echo [NOTICE] Docker Desktop was not detected on your system PATH.
echo.
echo You have two options:
echo   1. Run in Standalone Local Mode right now using host Python and Node.js.
echo   2. Install Docker Desktop from https://www.docker.com/products/docker-desktop
echo.
set /p choice="Would you like to start in Standalone Local Mode now? [Y/N, Default: Y]: "
if "!choice!"=="" set choice=Y
if /i "!choice!"=="Y" goto :RUN_LOCAL

echo Exiting. Please start Docker Desktop and rerun this script.
pause
exit /b 1

:RUN_LOCAL
echo.
echo Launching Standalone Local Mode...
call "%~dp0start-local.bat"
exit /b 0
