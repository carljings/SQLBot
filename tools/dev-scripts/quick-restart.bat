@echo off
echo ============================================
echo SQLBot Service Restart
echo ============================================
echo.

echo [1/4] Stopping all services...
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM node.exe >nul 2>&1
timeout /t 5 /nobreak >nul

echo [2/4] Starting backend service (port 8000)...
cd /d "%~dp0backend"
start "SQLBot Backend" cmd /k ".venv\Scripts\python.exe -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"
cd ..

echo [3/4] Waiting for backend to start...
timeout /t 8 /nobreak >nul

echo [4/4] Starting frontend service (port 5173)...
cd frontend
start "SQLBot Frontend" cmd /k "npm run dev"
cd ..

echo.
echo ============================================
echo Services are starting!
echo ============================================
echo   Backend:  http://localhost:8000
echo   Frontend: http://localhost:5173
echo   API Docs: http://localhost:8000/docs
echo ============================================
echo.
echo Login credentials:
echo   Username: admin
echo   Password: SQLBot@123456
echo.
echo Press any key to close this window...
pause >nul
