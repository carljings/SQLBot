#!/bin/bash

echo "=== 创建SQLBot系统目录 ==="
echo ""
echo "sudo密码：guchuan123"
echo ""

# 创建目录结构
sudo -S mkdir -p /opt/sqlbot/data/file
sudo -S mkdir -p /opt/sqlbot/data/excel
sudo -S mkdir -p /opt/sqlbot/images
sudo -S mkdir -p /opt/sqlbot/app/logs
sudo -S mkdir -p /opt/sqlbot/models
sudo -S mkdir -p /opt/sqlbot/scripts

echo "=== 目录创建完成 ==="
echo ""

# 设置权限
sudo -S chown -R $USER:staff /opt/sqlbot
sudo -S chmod -R 755 /opt/sqlbot

echo "=== 权限设置完成 ==="
echo ""

# 验证
echo "=== 验证目录 ==="
ls -la /opt/sqlbot/
echo ""

echo "【下一步】"
echo "cd /Users/guchuan/codespace/SQLBot-ClaudeCode/backend"
echo "python3 main.py"
echo ""
