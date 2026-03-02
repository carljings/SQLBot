#!/bin/bash

echo "=== 检查Docker Desktop安装状态 ==="
echo ""

# 检查Docker命令
echo "1. 检查Docker命令..."
which docker
if [ $? -eq 0 ]; then
    echo "   ✓ Docker已安装"
    docker --version
else
    echo "   ✗ Docker未安装"
fi
echo ""

# 检查Docker应用
echo "2. 检查Docker Desktop应用..."
if [ -d "/Applications/Docker.app" ]; then
    echo "   ✓ Docker Desktop应用已安装"
else
    echo "   ✗ Docker Desktop应用未安装"
fi
echo ""

# 检查Docker进程
echo "3. 检查Docker进程..."
docker ps >/dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "   ✓ Docker daemon正在运行"
else
    echo "   ✗ Docker daemon未运行"
    echo "   提示：请启动Docker Desktop应用"
fi
echo ""

# 检查Homebrew安装进程
echo "4. 检查Homebrew安装进程..."
ps aux | grep "brew install --cask docker" | grep -v grep > /dev/null
if [ $? -eq 0 ]; then
    echo "   ⏳ Docker Desktop正在安装中..."
    echo "   请等待安装完成"
else
    echo "   ✓ 安装进程已完成或未启动"
fi
echo ""

echo "=== 安装状态总结 ==="
echo ""
echo "【如果Docker未安装】"
echo "等待Homebrew安装完成（预计5-10分钟）"
echo "或手动下载Docker Desktop："
echo "https://docs.docker.com/get-docker/"
echo ""

echo "【如果Docker已安装但未运行】"
echo "请启动Docker Desktop应用："
echo "open /Applications/Docker.app"
echo ""

echo "【如果Docker正在运行】"
echo "可以继续启动SQLBot数据库了！"
echo ""
