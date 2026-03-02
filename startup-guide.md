# SQLBot 本地启动指南

## 📊 当前状态

| 检查项     | 状态                                          |
| ---------- | --------------------------------------------- |
| Python     | ✅ 3.9.6（项目要求3.11.x）                    |
| 依赖包     | ✅ fastapi, uvicorn, sqlmodel, psycopg2已安装 |
| PostgreSQL | ❌ 未安装                                     |
| Docker     | ⏳ 正在安装Docker Desktop...                  |
| Redis      | ❌ 未安装（可选）                             |

---

## 🚀 启动方案

### 方案A：Docker Desktop（推荐，安装中）

Docker Desktop正在通过Homebrew安装中，预计需要5-10分钟。

**安装完成后，运行以下命令**：

```bash
# 1. 启动PostgreSQL
docker run -d \
  --name sqlbot-pg \
  -p 5432:5432 \
  -e POSTGRES_PASSWORD=Password123@pg \
  -e POSTGRES_USER=root \
  -e POSTGRES_DB=sqlbot \
  postgres:16

# 2. 启动Redis（可选）
docker run -d \
  --name sqlbot-redis \
  -p 6379:6379 \
  redis:7

# 3. 初始化数据库（首次运行）
docker exec -it sqlbot-pg psql -U root -d sqlbot -c "
CREATE EXTENSION IF NOT EXISTS vector;
"

# 4. 启动SQLBot
cd /Users/guchuan/codespace/SQLBot-ClaudeCode/backend
python3 main.py
```

**访问地址**：

- 后端：http://localhost:8000
- API文档：http://localhost:8000/docs
- MCP服务：http://localhost:8001

---

### 方案B：使用在线PostgreSQL服务（快速）

如果你有PostgreSQL服务器，或想用云数据库，可以直接配置。

**推荐服务**：

- **Supabase**（免费，支持Vector扩展）
- **Neon**（免费，Serverless PostgreSQL）
- **Railway**（免费）
- **PlanetScale**（免费）

**配置步骤**：

1. 注册一个Supabase账号：https://supabase.com
2. 创建新项目（免费）
3. 获取数据库连接信息
4. 修改配置文件：`backend/common/core/config.py`

```python
# backend/common/core/config.py

POSTGRES_SERVER = "你的数据库地址"
POSTGRES_PORT = 5432
POSTGRES_USER = "你的用户名"
POSTGRES_PASSWORD = "你的密码"
POSTGRES_DB = "你的数据库名"
```

5. 启动SQLBot

```bash
cd /Users/guchuan/codespace/SQLBot-ClaudeCode/backend
python3 main.py
```

---

### 方案C：本地安装PostgreSQL

**安装**：

```bash
brew install postgresql@16
```

**初始化**：

```bash
# 初始化数据库
initdb -D /usr/local/var/postgres

# 启动PostgreSQL
pg_ctl -D /usr/local/var/postgres start

# 创建数据库和用户
createdb -U postgres sqlbot
psql -U postgres -c "CREATE USER root WITH PASSWORD 'Password123@pg';"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE sqlbot TO root;"
```

**启动SQLBot**：

```bash
cd /Users/guchuan/codespace/SQLBot-ClaudeCode/backend
python3 main.py
```

---

## 🔍 Docker Desktop安装状态检查

Docker Desktop正在安装中，你可以通过以下命令检查安装状态：

```bash
# 检查安装状态
brew list --cask docker

# 安装完成后启动Docker
open /Applications/Docker.app
```

**预计安装时间**：5-10分钟（取决于网络速度）

---

## 💡 我的建议

**如果你想快速启动**：

- 使用方案B（在线PostgreSQL），5分钟内可以启动

**如果你想完整本地环境**：

- 等待Docker Desktop安装完成（5-10分钟）
- 使用方案A启动

**如果你已经有PostgreSQL服务器**：

- 直接配置数据库连接信息，使用方案C

---

## 📞 下一步

**你告诉我**：

1. 是否想等待Docker安装完成？
2. 还是想用在线PostgreSQL快速启动？
3. 还是你有自己的PostgreSQL服务器？

我会根据你的选择，帮你完成后续的配置和启动！谢谢
