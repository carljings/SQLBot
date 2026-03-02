#!/bin/bash

echo "=== SQLBot 本地启动脚本 ==="
echo ""

# 检查Python版本
echo "1. 检查Python版本..."
python3 --version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "   Python版本: $PYTHON_VERSION"
echo "   需要Python 3.11.x，当前版本可能有兼容性问题"
echo ""

# 检查依赖
echo "2. 检查依赖包..."
python3 -c "import fastapi" 2>/dev/null && echo "   ✓ fastapi已安装" || echo "   ✗ fastapi未安装"
python3 -c "import uvicorn" 2>/dev/null && echo "   ✓ uvicorn已安装" || echo "   ✗ uvicorn未安装"
python3 -c "import sqlmodel" 2>/dev/null && echo "   ✓ sqlmodel已安装" || echo "   ✗ sqlmodel未安装"
python3 -c "import psycopg2" 2>/dev/null && echo "   ✓ psycopg2已安装" || echo "   ✗ psycopg2未安装"
echo ""

# 检查数据库
echo "3. 检查数据库..."
which psql >/dev/null 2>&1 && echo "   ✓ PostgreSQL已安装" || echo "   ✗ PostgreSQL未安装"
echo "   配置: localhost:5432, 用户: root, 数据库: sqlbot"
echo ""

# 检查Docker
echo "4. 检查Docker..."
which docker >/dev/null 2>&1 && echo "   ✓ Docker已安装" || echo "   ✗ Docker未安装"
echo ""

echo "=== 环境检查完成 ==="
echo ""
echo "【启动前需要做的事情】"
echo ""
echo "方案A: 使用Docker（推荐）"
echo "1. 安装Docker: https://docs.docker.com/get-docker/"
echo "2. 启动PostgreSQL和Redis:"
echo "   docker run -d --name sqlbot-pg -p 5432:5432 -e POSTGRES_PASSWORD=Password123@pg -e POSTGRES_USER=root -e POSTGRES_DB=sqlbot postgres:16"
echo "   docker run -d --name sqlbot-redis -p 6379:6379 redis:7"
echo ""
echo "方案B: 本地安装PostgreSQL"
echo "1. 安装PostgreSQL: brew install postgresql@16"
echo "2. 初始化数据库:"
echo "   initdb -D /usr/local/var/postgres"
echo "   pg_ctl -D /usr/local/var/postgres start"
echo "   createdb -U postgres sqlbot"
echo "   psql -U postgres -c \"CREATE USER root WITH PASSWORD 'Password123@pg';\""
echo "   psql -U postgres -c \"GRANT ALL PRIVILEGES ON DATABASE sqlbot TO root;\""
echo ""
echo "方案C: 使用云数据库"
echo "1. 修改backend/common/core/config.py中的数据库配置"
echo "2. 提供正确的数据库连接信息"
echo ""
echo "【启动SQLBot后端】"
echo "cd /Users/guchuan/codespace/SQLBot-ClaudeCode/backend"
echo "python3 main.py"
echo ""
