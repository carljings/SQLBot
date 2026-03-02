#!/bin/bash

echo "=== 创建SQLBot系统目录 ==="
echo ""

# 创建/opt/sqlbot目录结构
echo "1. 创建/opt/sqlbot目录结构..."
sudo mkdir -p /opt/sqlbot/data/file
sudo mkdir -p /opt/sqlbot/data/excel
sudo mkdir -p /opt/sqlbot/images
sudo mkdir -p /opt/sqlbot/app/logs
sudo mkdir -p /opt/sqlbot/models
sudo mkdir -p /opt/sqlbot/scripts
echo "   ✓ 目录创建完成"
echo ""

# 设置权限
echo "2. 设置目录权限..."
sudo chown -R $USER:staff /opt/sqlbot
sudo chmod -R 755 /opt/sqlbot
echo "   ✓ 权限设置完成"
echo ""

# 验证
echo "3. 验证目录..."
ls -la /opt/sqlbot/
echo ""
