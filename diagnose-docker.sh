#!/bin/bash

echo "=== Docker Desktop 诊断脚本 ==="
echo ""

# 检查Docker应用
echo "1. 检查Docker Desktop应用..."
if [ -d "/Applications/Docker.app" ]; then
    echo "   ✓ Docker Desktop应用已安装"
else
    echo "   ✗ Docker Desktop应用未安装"
    exit 1
fi
echo ""

# 检查Docker命令
echo "2. 检查Docker命令..."
if command -v docker >/dev/null 2>&1; then
    echo "   ✓ Docker命令在PATH中"
    docker --version
else
    echo "   ✗ Docker命令不在PATH中"
    echo ""
    echo "   可能的原因："
    echo "   1. Docker Desktop还未启动"
    echo "   2. Docker Desktop启动中（需要1-2分钟）"
    echo "   3. 需要重新打开终端"
    echo ""
fi
echo ""

# 检查Docker Desktop进程
echo "3. 检查Docker Desktop进程..."
pgrep -fl "Docker Desktop" >/dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "   ✓ Docker Desktop进程正在运行"
else
    echo "   ✗ Docker Desktop进程未运行"
    echo "   提示：请启动Docker Desktop应用"
    echo "   open /Applications/Docker.app"
fi
echo ""

# 检查Docker daemon
echo "4. 检查Docker daemon进程..."
pgrep -fl "com.docker.backend" >/dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "   ✓ Docker daemon正在运行"
else
    echo "   ✗ Docker daemon未运行"
    echo "   提示：Docker Desktop需要几分钟才能完全启动"
fi
echo ""

# 尝试使用完整路径执行Docker
echo "5. 尝试使用完整路径执行Docker..."
if [ -f "/Applications/Docker.app/Contents/Resources/bin/docker" ]; then
    echo "   找到Docker命令：/Applications/Docker.app/Contents/Resources/bin/docker"
    echo ""
    echo "   尝试执行："
    /Applications/Docker.app/Contents/Resources/bin/docker --version
    if [ $? -eq 0 ]; then
        echo ""
        echo "   ✓ Docker命令可以执行"
    else
        echo "   ✗ Docker命令执行失败"
    fi
else
    echo "   ✗ Docker命令未找到"
fi
echo ""

echo "=== 诊断完成 ==="
echo ""

echo "【解决方案】"
echo ""
echo "1. 如果Docker Desktop已启动但仍无法使用命令："
echo "   - 重新打开终端"
echo "   - 或者运行：source ~/.zshrc"
echo ""
echo "2. 如果Docker Desktop还未启动："
echo "   - 打开Docker Desktop应用"
echo "   - 等待1-2分钟让Docker完全启动"
echo "   - 重新打开终端"
echo ""
echo "3. 添加Docker到PATH（如果已启动但仍找不到命令）："
echo "   export PATH=\"/Applications/Docker.app/Contents/Resources/bin:$PATH\""
echo ""
echo "4. 检查Docker状态："
echo "   /Applications/Docker.app/Contents/Resources/bin/docker ps"
echo ""
