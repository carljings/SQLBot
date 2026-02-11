@echo off
echo Stopping all Python processes...
taskkill /F /IM python.exe >nul 2>&1
timeout /t 3 /nobreak >nul

echo Starting backend service on port 8000...
cd /d "%~dp0backend"
start "SQLBot Backend" cmd /k ".venv\Scripts\python.exe -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"

echo.
echo Backend service is starting...
echo Please wait 10 seconds for the service to be ready.
echo.
echo Access: http://localhost:8000/docs
echo.
pause
