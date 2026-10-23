@echo off
echo ==============================================================================
echo [DIGITAL DOCTOR] Stopping Local Standalone Servers
echo ==============================================================================

echo Stopping background servers on ports 8000 (Backend) and 5173 (Frontend)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000') do taskkill /F /PID %%a 2>nul
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5173') do taskkill /F /PID %%a 2>nul

echo Local development servers stopped successfully.
pause
