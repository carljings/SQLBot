# CLAUDE.md

本文件为 Claude Code (claude.ai/code) 在此代码仓库中工作时提供指导。

## 项目概述

SQLBot 是一个智能数据查询系统（ChatBI），使用大语言模型（LLM）和 RAG（检索增强生成）技术将自然语言问题转换为 SQL 查询。它由三个主要组件组成：

1. **后端** (Python/FastAPI)：核心 API 服务器，负责 LLM 编排
2. **前端** (Vue 3/TypeScript)：聊天界面和数据可视化的 Web UI
3. **g2-ssr** (Node.js)：服务端图表渲染服务

## 开发命令

### 后端 (Python)

后端使用 **uv**（快速 Python 包安装器）进行依赖管理，而不是 pip 或 poetry。

```bash
cd backend

# 安装依赖（需要 Python 3.11）
uv sync --extra cpu              # 仅 CPU 版本的 PyTorch
uv sync --extra cu128            # CUDA 12.8 版本的 PyTorch

# 运行开发服务器
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 运行 MCP 服务器（模型上下文协议）
uvicorn main:mcp_app --reload --host 0.0.0.0 --port 8001

# 代码检查和格式化
ruff check .                     # 检查代码风格
ruff format .                    # 格式化代码
mypy .                          # 类型检查

# 运行测试并生成覆盖率报告
pytest
coverage run --source=. -m pytest
coverage report --show-missing

# 数据库迁移
alembic upgrade head             # 应用迁移
alembic revision --autogenerate -m "description"  # 创建新迁移
```

### 前端 (Vue.js)

```bash
cd frontend

# 安装依赖
npm install

# 运行开发服务器（包含 TypeScript 编译）
npm run dev                      # 运行在 http://localhost:5173

# 生产环境构建
npm run build                    # TypeScript 检查 + Vite 构建

# 代码检查和修复
npm run lint
```

### g2-ssr (图表渲染服务)

```bash
cd g2-ssr

# 安装依赖
npm install

# 运行服务
node app.js                      # 运行在 3000 端口
# 或使用 PM2
pm2 start app.js
```

## 架构概览

### Text-to-SQL 处理流程

将自然语言转换为 SQL 的核心工作流：

1. **用户问题** → 通过 `/api/chat/send` 端点接收
2. **上下文检索 (RAG)**：
   - 使用向量相似度检索相关业务术语（pgvector）
   - 从训练数据中检索相似的 SQL 示例
   - 检索相关的表/列元数据
3. **提示词构建**：使用数据库模式 + 上下文 + 用户问题构建 LLM 提示词
4. **LLM 生成**：调用配置的 LLM（OpenAI/Azure/通义/vLLM）生成 SQL
5. **SQL 执行**：在目标数据库上执行，带有安全限制
6. **图表生成**：LLM 根据结果生成图表配置
7. **图表渲染**：g2-ssr 服务渲染图表图像
8. **响应**：将结果 + 图表返回给用户

### 核心后端模块

- **`apps/chat/`**：聊天会话管理和 LLM 编排
  - `task/llm_service.py`：使用 LangGraph 的核心 LLM 工作流
  - `crud/chat.py`：聊天 CRUD 操作

- **`apps/datasource/`**：数据库连接管理
  - 支持：MySQL、PostgreSQL、SQL Server、Oracle、ClickHouse、Redshift、Elasticsearch
  - `task/datasource_task.py`：数据库操作和元数据提取

- **`apps/data_training/`**：带嵌入向量的 SQL 训练示例
  - 存储问题-SQL 对用于 RAG 检索
  - `task/data_training_task.py`：嵌入向量生成

- **`apps/terminology/`**：业务术语词典
  - 带嵌入向量的自定义术语和定义
  - 在 SQL 生成期间用于语义搜索

- **`apps/ai_model/`**：LLM 模型配置
  - `task/llm_factory.py`：创建 LLM 实例的工厂类
  - 支持多个提供商的统一接口

- **`apps/system/`**：用户、工作空间和权限管理
  - 多工作空间隔离
  - 基于角色的访问控制（管理员/成员）
  - 行级数据权限

- **`apps/mcp/`**：模型上下文协议服务器
  - 支持与 AI 助手（Claude Desktop 等）集成
  - 将 SQLBot 功能暴露为 MCP 工具

### 数据库模式 (PostgreSQL)

核心表：
- `sys_user`、`sys_workspace`、`sys_user_ws`：用户和工作空间管理
- `ai_model`：LLM 配置
- `core_datasource`、`core_table`、`core_field`：数据库元数据
- `terminology`：带嵌入向量的业务术语（pgvector）
- `data_training`：带嵌入向量的 SQL 训练示例（pgvector）
- `chat`、`chat_record`、`chat_log`：聊天会话和详细日志
- `core_dashboard`：仪表板定义

### 前端架构

- **Vue 3** 使用 Composition API 和 `<script setup>` 语法
- **Pinia** 用于状态管理（stores 在 `src/stores/`）
- **Element Plus** 作为主要 UI 组件库
- **AntV G2/S2** 用于数据可视化
- **Vue Router** 用于导航
- **Axios** 用于 API 调用（客户端在 `src/api/`）

核心视图：
- `views/chat/`：带流式响应的聊天界面
- `views/dashboard/`：仪表板构建器和查看器
- `views/ds/`：数据源管理
- `views/system/`：系统设置和用户管理

## 重要开发说明

### RAG 和嵌入向量

- 系统使用 **shibing624/text2vec-base-chinese** 进行文本嵌入
- 嵌入向量使用 **pgvector** 扩展存储在 PostgreSQL 中
- 维护三种类型的嵌入向量：
  1. 术语嵌入（业务术语）
  2. 数据训练嵌入（SQL 示例）
  3. 表/列嵌入（数据库元数据）
- 嵌入向量在启动时和数据变化时异步生成
- 相似度搜索使用余弦距离，阈值可配置

### LLM 集成

- LLM 调用使用 **LangChain** 和 **LangGraph** 进行编排
- `LLMFactory` 模式抽象了不同的 LLM 提供商
- 流式响应使用服务器发送事件（SSE）
- 所有 LLM 交互都记录在 `chat_log` 表中用于调试
- 提示词模板在 `apps/template/` 中，支持多语言

### 数据库迁移

- 使用 **Alembic** 进行模式迁移
- 迁移在应用启动时通过 `main.py:run_migrations()` 自动运行
- 迁移文件在 `backend/alembic/versions/`
- 提交前务必在本地测试迁移

### 安全考虑

- 数据库凭证使用 AES 加密（参见 `common/utils/crypto.py`）
- JWT 令牌用于身份验证（环境变量中的 SECRET_KEY）
- 外部集成的 API 密钥
- 查询应用行级安全过滤器
- 通过参数化查询防止 SQL 注入

### 测试

- 后端测试使用 **pytest** 和 fixtures
- 测试数据库配置在 `backend/tests/`
- 使用 `coverage` 工具生成覆盖率报告
- 前端测试未广泛实现（有贡献机会）

### Docker 部署

应用在单个容器中运行三个服务：
- 端口 8000：主 FastAPI 应用（Web UI + API）
- 端口 8001：MCP 服务器
- 端口 3000：g2-ssr 图表渲染（内部）
- 端口 5432：PostgreSQL（内部）

`start.sh` 脚本编排服务启动：
1. 启动 PostgreSQL
2. 使用 PM2 启动 g2-ssr
3. 在后台启动 MCP 服务器
4. 启动主 FastAPI 应用

### 环境变量

关键环境变量（参见 `docker-compose.yaml`）：
- `POSTGRES_*`：数据库连接设置
- `SECRET_KEY`：JWT 签名密钥
- `DEFAULT_PWD`：默认管理员密码
- `SERVER_IMAGE_HOST`：MCP 图像服务 URL
- `BACKEND_CORS_ORIGINS`：CORS 允许的源
- `LOG_LEVEL`：日志详细程度

## 常见开发工作流

### 添加新的 LLM 提供商

1. 在 `apps/ai_model/task/llm_factory.py` 中创建提供商类
2. 实现 LLM 接口（继承自 LangChain 基类）
3. 在 `apps/ai_model/schemas/ai_model.py` 中添加提供商配置
4. 在 `views/system/ai-model/` 中更新前端模型选择 UI

### 添加新的数据库类型

1. 在 `apps/datasource/task/datasource_task.py` 中添加数据库引擎
2. 实现连接字符串生成
3. 在 `apps/template/` 中添加 SQL 方言特定的模板
4. 在 `views/ds/` 中更新前端数据源表单

### 修改 Text-to-SQL 提示词

1. 编辑 `apps/template/` 中的提示词模板
2. 模板支持带占位符的 Jinja2 语法
3. 使用不同的数据库模式和问题类型进行测试
4. 监控 `chat_log` 表以调试 LLM 响应

### 添加新的 RAG 上下文

1. 创建带嵌入列的新表（类型：`vector(768)`）
2. 添加嵌入生成逻辑（参见 `common/utils/embedding_threads.py`）
3. 在 `apps/chat/task/llm_service.py` 中集成检索
4. 更新提示词构建以包含新上下文

## 代码风格和约定

### 后端 (Python)

- 遵循 **PEP 8** 风格指南
- 所有函数签名使用**类型提示**（由 mypy 强制执行）
- 使用 **Ruff** 进行代码检查和格式化（在 `pyproject.toml` 中配置）
- I/O 操作使用 Async/await
- 请求/响应模式使用 Pydantic 模型
- CRUD 模式：将 CRUD 操作与 API 路由分离

### 前端 (TypeScript/Vue)

- 使用 **Composition API** 和 `<script setup>` 语法
- TypeScript 用于类型安全
- ESLint + Prettier 用于代码格式化
- 组件命名：组件使用 PascalCase，文件使用 kebab-case
- Props 和 emits 应该有类型
- 使用 Pinia stores 管理共享状态

## 故障排除

### 后端无法启动
- 检查 Python 版本（必须是 3.11）
- 确保 PostgreSQL 正在运行且可访问
- 验证环境变量已设置
- 检查 `backend/logs/` 中的日志

### 嵌入向量未生成
- 检查嵌入模型是否已下载（首次运行会下载模型）
- 验证 PostgreSQL 中已安装 pgvector 扩展
- 检查启动日志中的 `fill_empty_*_embeddings()` 函数

### LLM 调用失败
- 验证系统设置中已配置 LLM API 密钥
- 检查到 LLM 提供商的网络连接
- 查看 `chat_log` 表获取详细错误消息
- 确保 LLM 模型名称对提供商正确

### 前端构建错误
- 清除 node_modules 并重新安装：`rm -rf node_modules && npm install`
- 检查 TypeScript 错误：`vue-tsc -b`
- 验证所有导入是否正确（Linux 上区分大小写）
