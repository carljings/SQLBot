# SQLBot 本地开发环境停止脚本
# 使用方法: .\stop-dev.ps1

$colors = @{
    Header = "Cyan"
    Success = "Green"
    Warning = "Yellow"
    Error = "Red"
    Info = "White"
}

function Write-ColorMessage {
    param([string]$Message, [string]$Color = "White")
    Write-Host $Message -ForegroundColor $Color
}

Write-Separator {
    Write-ColorMessage ("=" * 50) $colors.Header
}

$ProjectDir = $PSScriptRoot

Write-Separator
Write-ColorMessage "  SQLBot 停止所有开发服务" $colors.Header
Write-Separator
Write-Host ""

# 停止 uvicorn 进程
Write-ColorMessage "[INFO] 查找后端进程..." $colors.Info
$BackendProcesses = Get-Process python -ErrorAction SilentlyContinue | Where-Object {
    $_.CommandLine -like "*uvicorn*main:app*"
}

if ($BackendProcesses) {
    foreach ($proc in $BackendProcesses) {
        Write-ColorMessage "[INFO] 停止后端进程 (PID: $($proc.Id))" $colors.Warning
        Stop-Process -Id $proc.Id -Force
    }
    Write-ColorMessage "[SUCCESS] 后端服务已停止" $colors.Success
} else {
    Write-ColorMessage "[INFO] 未找到运行中的后端服务" $colors.Info
}

Write-Host ""

# 停止 node/vite 进程
Write-ColorMessage "[INFO] 查找前端进程..." $colors.Info
$FrontendProcesses = Get-Process node -ErrorAction SilentlyContinue | Where-Object {
    $_.CommandLine -like "*vite*"
}

if ($FrontendProcesses) {
    foreach ($proc in $FrontendProcesses) {
        Write-ColorMessage "[INFO] 停止前端进程 (PID: $($proc.Id))" $colors.Warning
        Stop-Process -Id $proc.Id -Force
    }
    Write-ColorMessage "[SUCCESS] 前端服务已停止" $colors.Success
} else {
    Write-ColorMessage "[INFO] 未找到运行中的前端服务" $colors.Info
}

Write-Host ""

# 清理进程信息文件
$ProcessInfoFile = Join-Path $ProjectDir ".dev-processes.json"
if (Test-Path $ProcessInfoFile) {
    Remove-Item $ProcessInfoFile
    Write-ColorMessage "[INFO] 已清理进程信息文件" $colors.Info
}

Write-Separator
Write-ColorMessage "  所有服务已停止" $colors.Success
Write-Separator
Write-Host ""
