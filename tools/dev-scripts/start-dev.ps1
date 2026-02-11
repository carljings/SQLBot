# SQLBot 本地开发一键启动脚本 (PowerShell)
# 使用方法: .\start-dev.ps1

param(
    [switch]$SkipBackend = $false,
    [switch]$SkipFrontend = $false,
    [switch]$OpenBrowser = $true
)

# 设置颜色主题
$colors = @{
    Header = "Cyan"
    Success = "Green"
    Warning = "Yellow"
    Error = "Red"
    Info = "White"
}

# 打印彩色消息
function Write-ColorMessage {
    param([string]$Message, [string]$Color = "White")
    Write-Host $Message -ForegroundColor $Color
}

# 打印分隔线
function Write-Separator {
    Write-ColorMessage ("=" * 60) $colors.Header
}

# 检查命令是否存在
function Test-Command {
    param([string]$Command)
    $null = Get-Command $Command -ErrorAction SilentlyContinue
    return $?
}

# 设置项目根目录
$ProjectDir = $PSScriptRoot
Set-Location $ProjectDir

Write-Separator
Write-ColorMessage "  SQLBot 本地开发环境启动" $colors.Header
Write-Separator
Write-Host ""

# 检查 uv 是否安装
if (-not (Test-Command "uv")) {
    Write-ColorMessage "[INFO] uv 未安装，正在安装..." $colors.Warning
    try {
        irm https://astral.sh/uv/install.ps1 | iex
        Write-ColorMessage "[SUCCESS] uv 安装完成" $colors.Success
    } catch {
        Write-ColorMessage "[ERROR] uv 安装失败: $_" $colors.Error
        exit 1
    }
}

# 检查后端虚拟环境
$BackendVenv = Join-Path $ProjectDir "backend\.venv\Scripts\python.exe"
if (-not (Test-Path $BackendVenv)) {
    Write-ColorMessage "[INFO] 后端依赖未安装，正在安装..." $colors.Warning
    Set-Location (Join-Path $ProjectDir "backend")
    uv sync --extra cpu
    Set-Location $ProjectDir
    Write-ColorMessage "[SUCCESS] 后端依赖安装完成" $colors.Success
}

# 检查前端依赖
$FrontendModules = Join-Path $ProjectDir "frontend\node_modules"
if (-not (Test-Path $FrontendModules)) {
    Write-ColorMessage "[INFO] 前端依赖未安装，正在安装..." $colors.Warning
    Set-Location (Join-Path $ProjectDir "frontend")
    npm install
    Set-Location $ProjectDir
    Write-ColorMessage "[SUCCESS] 前端依赖安装完成" $colors.Success
}

Write-Host ""

# 启动后端服务
if (-not $SkipBackend) {
    $BackendScript = Join-Path $ProjectDir "backend\.venv\Scripts\python.exe"
    $BackendScriptEscaped = $BackendScript.Replace('\', '\\')

    Write-ColorMessage "[INFO] 启动后端服务 (端口 8000)..." $colors.Info

    $BackendArgs = @(
        "-NoExit"
        "-Command"
        "cd '$ProjectDir\backend'; & '$BackendScriptEscaped' -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"
    )

    $BackendProcess = Start-Process powershell -ArgumentList $BackendArgs -PassThru -WindowStyle Minimized

    # 等待后端启动
    Write-Host ""
    Write-ColorMessage "[INFO] 等待后端服务启动..." $colors.Info
    Start-Sleep -Seconds 8

    # 检查后端是否启动成功
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/docs" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
        Write-ColorMessage "[SUCCESS] 后端服务启动成功" $colors.Success
    } catch {
        Write-ColorMessage "[WARNING] 后端服务可能需要更多时间启动" $colors.Warning
    }
}

Write-Host ""

# 启动前端服务
if (-not $SkipFrontend) {
    Write-ColorMessage "[INFO] 启动前端服务 (端口 5173)..." $colors.Info

    $FrontendCmd = "npm run dev"
    $null = Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$ProjectDir\frontend'; $FrontendCmd" -WindowStyle Minimized

    # 等待前端启动
    Start-Sleep -Seconds 5
    Write-ColorMessage "[SUCCESS] 前端服务启动成功" $colors.Success
}

Write-Host ""
Write-Separator
Write-ColorMessage "  SQLBot 启动完成!" $colors.Success
Write-Separator
Write-Host ""
Write-ColorMessage "  后端 API:      http://localhost:8000" $colors.Info
Write-ColorMessage "  API 文档:      http://localhost:8000/docs" $colors.Info
Write-ColorMessage "  前端界面:      http://localhost:5173" $colors.Info
Write-ColorMessage "  MCP 服务:      http://localhost:8001" $colors.Info
Write-Separator
Write-Host ""

# 打开浏览器
if ($OpenBrowser) {
    Write-ColorMessage "[INFO] 正在打开浏览器..." $colors.Info
    Start-Process "http://localhost:5173"
}

Write-Host ""
Write-ColorMessage "提示: 服务将在独立窗口中运行，关闭此窗口不会停止服务" $colors.Warning
Write-ColorMessage "      要停止所有服务，请运行: .\stop-dev.ps1" $colors.Warning
Write-Host ""

# 保存进程信息用于停止脚本
$ProcessInfo = @{
    Backend = $BackendProcess.Id
    StartTime = Get-Date
}
$ProcessInfo | ConvertTo-Json | Out-File (Join-Path $ProjectDir ".dev-processes.json") -Encoding utf8
