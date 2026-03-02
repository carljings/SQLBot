#!/bin/bash

echo "=== 启动SQLBot PostgreSQL数据库 ==="
echo ""

DOCKER_CMD="/Applications/Docker.app/Contents/Resources/bin/docker"

# 检查PostgreSQL容器是否存在
echo "1. 检查PostgreSQL容器..."
$DOCKER_CMD ps -a | grep sqlbot-pg
if [ $? -eq 0 ]; then
    echo "   PostgreSQL容器已存在"
    $DOCKER_CMD ps | grep sqlbot-pg | grep -q Up
    if [ $? -eq 0 ]; then
        echo "   ✓ PostgreSQL容器正在运行"
    else
        echo "   PostgreSQL容器未运行，正在启动..."
        $DOCKER_CMD start sqlbot-pg
    fi
else
    echo "   PostgreSQL容器不存在，正在创建..."
    $DOCKER_CMD run -d \
      --name sqlbot-pg \
      -p 5432:5432 \
      -e POSTGRES_PASSWORD=Password123@pg \
      -e POSTGRES_USER=root \
      -e POSTGRES_DB=sqlbot \
      postgres:16
fi
echo ""

# 等待PostgreSQL启动
echo "2. 等待PostgreSQL启动（需要30-60秒）..."
sleep 30

# 检查PostgreSQL连接
echo "3. 检查PostgreSQL连接..."
$DOCKER_CMD exec sqlbot-pg pg_isready -U root
if [ $? -eq 0 ]; then
    echo "   ✓ PostgreSQL已就绪"
else
    echo "   PostgreSQL还未就绪，继续等待..."
    sleep 30
    $DOCKER_CMD exec sqlbot-pg pg_isready -U root
    if [ $? -eq 0 ]; then
        echo "   ✓ PostgreSQL已就绪"
    else
        echo "   ✗ PostgreSQL启动失败"
        exit 1
    fi
fi
echo ""

# 初始化vector扩展
echo "4. 初始化vector扩展..."
$DOCKER_CMD exec -it sqlbot-pg psql -U root -d sqlbot -c "CREATE EXTENSION IF NOT EXISTS vector;" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "   ✓ Vector扩展已初始化"
else
    echo "   Vector扩展初始化失败（可能已经存在）"
fi
echo ""

echo "=== PostgreSQL启动完成 ==="
echo ""
echo "【数据库连接信息】"
echo "   Host: localhost"
echo "   Port: 5432"
echo "   User: root"
echo "   Password: Password123@pg"
echo "   Database: sqlbot"
echo ""
echo "【Docker命令】"
echo "   查看容器状态：/Applications/Docker.app/Contents/Resources/bin/docker ps"
echo "   查看日志：/Applications/Docker.app/Contents/Resources/bin/docker logs sqlbot-pg"
echo "   进入数据库：/Applications/Docker.app/Contents/Resources/bin/docker exec -it sqlbot-pg psql -U root -d sqlbot"
echo ""
echo "【下一步】"
echo "   cd /Users/guchuan/codespace/SQLBot-ClaudeCode/backend"
echo "   python3 main.py"
echo ""
