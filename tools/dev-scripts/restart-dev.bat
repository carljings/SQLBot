@echo off
REM SQLBot 本地开发环境重启脚本 (Windows)
REM 使用方法: 双击运行或在 PowerShell 中执行

echo ============================================
echo SQLBot 本地开发环境重启
echo ============================================
echo.

REM 设置项目根目录
set PROJECT_DIR=%~dp0
cd /d "%PROJECT_DIR%"

echo [INFO] 正在停止现有服务...
echo.

REM 停止后端服务 (端口 8000)
echo [INFO] 停止后端服务...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING') do (
    echo [INFO] 发现后端进程 PID: %%a
    taskkill /F /PID %%a >nul 2>nul
)

REM 停止前端服务 (端口 5173, 5174, 5175)
echo [INFO] 停止前端服务...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5173 ^| findstr LISTENING') do (
    echo [INFO] 发现前端进程 PID: %%a (端口 5173)
    taskkill /F /PID %%a >nul 2>nul
)
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5174 ^| findstr LISTENING') do (
    echo [INFO] 发现前端进程 PID: %%a (端口 5174)
    taskkill /F /PID %%a >nul 2>nul
)
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5175 ^| findstr LISTENING') do (
    echo [INFO] 发现前端进程 PID: %%a (端口 5175)
    taskkill /F /PID %%a >nul 2>nul
)

REM 通过窗口标题停止服务（备用方法）
taskkill /FI "WindowTitle eq SQLBot Backend*" /F >nul 2>nul
taskkill /FI "WindowTitle eq SQLBot Frontend*" /F >nul 2>nul

echo [INFO] 等待服务完全停止...
timeout /t 3 /nobreak >nul
echo.

echo ============================================
echo [INFO] 正在重新启动服务...
echo ============================================
echo.

REM 检查是否安装了 uv
where uv >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] uv 未安装，正在安装...
    powershell -Command "irm https://astral.sh/uv/install.ps1 | iex"
    echo [INFO] uv 安装完成，请重新运行此脚本
    pause
    exit /b 1
)

REM 检查后端虚拟环境
if not exist "backend\.venv\Scripts\python.exe" (
    echo [INFO] 后端依赖未安装，正在安装...
    cd backend
    uv sync --extra cpu
    cd ..
)

REM 检查前端依赖
if not exist "frontend\node_modules\" (
    echo [INFO] 前端依赖未安装，正在安装...
    cd frontend
    npm install
    cd ..
)

echo [INFO] 启动后端服务 (端口 8000)...
start "SQLBot Backend" cmd /k "cd /d %PROJECT_DIR%backend && .venv\Scripts\python.exe -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"

REM 等待后端启动
echo [INFO] 等待后端服务启动...
timeout /t 5 /nobreak >nul

echo [INFO] 启动前端服务 (端口 5173)...
start "SQLBot Frontend" cmd /k "cd /d %PROJECT_DIR%frontend && npm run dev"

echo.
echo ============================================
echo SQLBot 重启完成!
echo ============================================
echo   后端 API: http://localhost:8000
echo   API 文档: http://localhost:8000/docs
echo   前端界面: http://localhost:5173
echo ============================================
echo.
echo 按任意键关闭此窗口（服务将继续运行）...
pause >nul
