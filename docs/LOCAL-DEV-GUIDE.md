# SQLBot 本地开发指南

> 快速启动前端、后端和查看日志

---

## 1. 启动服务

### 1.1 后端 (FastAPI)

```bash
# 进入后端目录
cd backend

# 安装依赖（首次运行）
uv sync --extra cpu              # 仅 CPU 版本的 PyTorch
# 或
uv sync --extra cu128            # CUDA 12.8 版本的 PyTorch

# 启动主服务 (端口 8000)
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 启动 MCP 服务 (端口 8001，可选)
uvicorn main:mcp_app --reload --host 0.0.0.0 --port 8001
```

**访问地址**:
- API 文档: http://localhost:8000/docs
- API 接口: http://localhost:8000/api/v1

### 1.2 前端 (Vue 3)

```bash
# 进入前端目录
cd frontend

# 安装依赖（首次运行）
npm install

# 启动开发服务器 (端口 5173)
npm run dev
```

**访问地址**: http://localhost:5173

### 1.3 g2-ssr 图表服务 (可选)

```bash
# 进入 g2-ssr 目录
cd g2-ssr

# 安装依赖（首次运行）
npm install

# 启动服务 (端口 3000)
node app.js
# 或使用 PM2
pm2 start app.js
```

---

## 2. 日志查看

### 2.1 日志配置

**配置文件**: `backend/common/core/config.py`

```python
# 日志级别 (DEBUG/INFO/WARNING/ERROR/CRITICAL)
LOG_LEVEL: str = "INFO"

# 日志目录
LOG_DIR: str = "logs"

# 日志格式
LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s:%(lineno)d - %(message)s"
```

### 2.2 日志文件位置

**目录**: `backend/logs/`

| 文件 | 说明 | 查看命令 |
|-------|-------|-----------|
| `info.log` | 一般信息日志 | `tail -f backend/logs/info.log` |
| `error.log` | 错误日志 | `tail -f backend/logs/error.log` |
| `warn.log` | 警告日志 | `tail -f backend/logs/warn.log` |
| `debug.log` | 调试日志 | `tail -f backend/logs/debug.log` |

### 2.3 实时查看日志

```bash
# 查看所有日志
tail -f backend/logs/*.log

# 查看特定级别日志
tail -f backend/logs/error.log    # 仅错误
tail -f backend/logs/debug.log    # 仅调试

# 或使用 multitail 同时查看多个文件
multitail backend/logs/*.log
```

### 2.4 调试模式

修改 `backend/.env` 或环境变量：

```bash
# 启用调试模式（更详细日志）
SQL_DEBUG=true

# 修改日志级别
LOG_LEVEL=DEBUG
```

---

## 3. 开发工具

### 3.1 代码检查

```bash
# 后端代码检查
cd backend
ruff check .                     # 检查代码风格
ruff format .                    # 格式化代码
mypy .                          # 类型检查

# 前端代码检查
cd frontend
npm run lint                     # ESLint 检查
vue-tsc -b                       # TypeScript 类型检查
```

### 3.2 测试

```bash
# 后端测试
cd backend
pytest                            # 运行测试
coverage run --source=. -m pytest # 测试覆盖率
coverage report --show-missing   # 查看覆盖率报告

# 数据库迁移
alembic upgrade head             # 应用迁移
alembic revision --autogenerate -m "description"  # 创建新迁移
```

---

## 4. 常见问题

### 后端无法启动

**检查项**:
1. Python 版本（必须是 3.11）
   ```bash
   python --version
   ```

2. PostgreSQL 是否运行
   ```bash
   # Windows
   pg_ctl status

   # 检查连接
   psql -h localhost -U root -d sqlbot
   ```

3. 端口是否被占用
   ```bash
   # Windows
   netstat -ano | findstr :8000
   ```

4. 查看日志
   ```bash
   tail -f backend/logs/error.log
   ```

### 前端无法启动

**检查项**:
1. 依赖是否安装
   ```bash
   rm -rf node_modules && npm install
   ```

2. 端口是否被占用
   ```bash
   # Windows
   netstat -ano | findstr :5173
   ```

3. TypeScript 错误
   ```bash
   npm run build  # 查看编译错误
   ```

### 嵌入向量未生成

**检查日志中的启动信息**:
- 嵌入模型是否已下载
- PostgreSQL 中是否安装了 pgvector 扩展
- 启动日志中的 `fill_empty_*_embeddings()` 函数

---

## 5. 环境变量

**后端** (`.env` 文件或环境变量):

```bash
# 数据库
POSTGRES_USER=sqlbot
POSTGRES_PASSWORD=***
POSTGRES_DB=sqlbot

# 应用
SECRET_KEY=***
DEFAULT_PWD=***
LOG_LEVEL=INFO

# CORS
BACKEND_CORS_ORIGINS=["http://localhost:5173"]

# MCP
SERVER_IMAGE_HOST=http://localhost:3000
MCP_IMAGE_PATH=/app/images
```

**前端** (`.env.production`):

```bash
VITE_API_BASE_URL=./api/v1
VITE_APP_TITLE=SQLBot
```

---

**维护者**: SQLBot Team
**最后更新**: 2026-02-11
