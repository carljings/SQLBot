#!/bin/bash

echo "=== Docker Desktop 手动安装脚本 ==="
echo ""

# 下载Docker Desktop
echo "1. 下载Docker Desktop for Mac (Apple Silicon)..."
curl -L -o ~/Downloads/Docker.dmg "https://desktop.docker.com/mac/main/arm64/Docker.dmg"
echo "   ✓ 下载完成"
echo ""

# 挂载DMG
echo "2. 挂载DMG文件..."
hdiutil attach ~/Downloads/Docker.dmg
echo "   ✓ 挂载完成"
echo ""

# 复制到Applications
echo "3. 复制Docker.app到Applications文件夹..."
cp -R /Volumes/Docker/Docker.app /Applications/
echo "   ✓ 复制完成"
echo ""

# 卸载DMG
echo "4. 卸载DMG文件..."
hdiutil detach /Volumes/Docker
echo "   ✓ 卸载完成"
echo ""

# 清理下载文件
echo "5. 清理下载文件..."
rm ~/Downloads/Docker.dmg
echo "   ✓ 清理完成"
echo ""

echo "=== 安装完成 ==="
echo ""
echo "【下一步】"
echo "1. 启动Docker Desktop："
echo "   open /Applications/Docker.app"
echo ""
echo "2. 等待Docker启动（需要1-2分钟）"
echo ""
echo "3. 检查Docker状态："
echo "   docker --version"
echo "   docker ps"
echo ""
