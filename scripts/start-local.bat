@echo off
setlocal enabledelayedexpansion

echo ==============================================================================
echo [DIGITAL DOCTOR] Starting Local Standalone Development Environment
echo [No Docker Desktop required -- runs directly using host Python and Node.js]
echo ==============================================================================

cd /d "%~dp0\.."

if not exist .env (
    echo [.env] not found. Copying .env.example to .env...
    copy .env.example .env
)

echo [1/2] Launching Backend API Server (FastAPI + Uvicorn) on http://localhost:8000...
start "Digital Doctor - Backend API (Port 8000)" cmd /k "cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

echo [2/2] Launching Frontend Interface (React + Vite) on http://localhost:5173...
start "Digital Doctor - Frontend Kiosk (Port 5173)" cmd /k "cd frontend && npm.cmd run dev"

echo.
echo ==============================================================================
echo Digital Doctor is starting up!
echo   * Kiosk Welcome View:     http://localhost:5173/kiosk
echo   * Front-Office Intake:    http://localhost:5173/front-office
echo   * Staff & Doctor Console: http://localhost:5173/staff
echo   * Interactive API Docs:   http://localhost:8000/docs
echo ==============================================================================
echo Opening browser in 4 seconds...
timeout /t 4 >nul
start http://localhost:5173/kiosk
