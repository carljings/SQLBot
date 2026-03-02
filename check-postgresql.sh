#!/bin/bash

echo "=== 检查PostgreSQL容器状态 ==="
echo ""

DOCKER_CMD="/Applications/Docker.app/Contents/Resources/bin/docker"

# 检查容器
echo "1. 检查PostgreSQL容器..."
$DOCKER_CMD ps -a | grep sqlbot-pg
if [ $? -eq 0 ]; then
    echo "   ✓ PostgreSQL容器已创建"
    $DOCKER_CMD ps | grep sqlbot-pg | grep -q Up
    if [ $? -eq 0 ]; then
        echo "   ✓ PostgreSQL容器正在运行"
    else
        echo "   ✗ PostgreSQL容器未运行，正在启动..."
        $DOCKER_CMD start sqlbot-pg
        sleep 30
    fi
else
    echo "   ✗ PostgreSQL容器不存在，正在创建..."
    $DOCKER_CMD run -d \
      --name sqlbot-pg \
      -p 5432:5432 \
      -e POSTGRES_PASSWORD=Password123@pg \
      -e POSTGRES_USER=root \
      -e POSTGRES_DB=sqlbot \
      postgres:16
    echo "   等待PostgreSQL启动（需要30-60秒）..."
    sleep 60
fi
echo ""

# 检查连接
echo "2. 检查PostgreSQL连接..."
for i in {1..10}; do
    $DOCKER_CMD exec sqlbot-pg pg_isready -U root >/dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "   ✓ PostgreSQL已就绪"
        break
    else
        if [ $i -lt 10 ]; then
            echo "   等待PostgreSQL就绪... ($i/10)"
            sleep 10
        else
            echo "   ✗ PostgreSQL未就绪"
            echo "   请检查Docker日志："
            echo "   $DOCKER_CMD logs sqlbot-pg"
            exit 1
        fi
    fi
done
echo ""

# 初始化vector扩展
echo "3. 初始化vector扩展..."
$DOCKER_CMD exec -it sqlbot-pg psql -U root -d sqlbot -c "CREATE EXTENSION IF NOT EXISTS vector;" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "   ✓ Vector扩展已初始化"
else
    echo "   ⚠ Vector扩展初始化失败（可能已经存在）"
fi
echo ""

echo "=== PostgreSQL就绪 ==="
echo ""
echo "【数据库连接信息】"
echo "   Host: localhost"
echo "   Port: 5432"
echo "   User: root"
echo "   Password: Password123@pg"
echo "   Database: sqlbot"
echo ""
echo "【Docker命令】"
echo "   查看容器：$DOCKER_CMD ps | grep sqlbot"
echo "   查看日志：$DOCKER_CMD logs -f sqlbot-pg"
echo "   进入数据库：$DOCKER_CMD exec -it sqlbot-pg psql -U root -d sqlbot"
echo ""
echo "【下一步】"
echo "   cd /Users/guchuan/codespace/SQLBot-ClaudeCode/backend"
echo "   python3 main.py"
echo ""
