# SQLBot 系统架构详细设计文档

> **文档版本**: v1.0
> **创建日期**: 2026-02-11
> **维护者**: SQLBot Team

---

## 1. 文档概述

本文档详细描述 SQLBot 系统的代码架构设计，包括后端服务架构、前端应用架构、数据模型设计、RAG 检索架构以及 LLM 编排架构。

### 1.1 系统简介

SQLBot 是一个智能数据查询系统（ChatBI），使用大语言模型（LLM）和 RAG（检索增强生成）技术将自然语言问题转换为 SQL 查询。系统采用前后端分离架构，支持多种数据库类型和 LLM 提供商。

### 1.2 技术栈

| 层级 | 技术栈 |
|-----|-------|
| **后端** | Python 3.11+ / FastAPI / SQLModel / SQLAlchemy |
| **数据库** | PostgreSQL (with pgvector) |
| **LLM 框架** | LangChain / LangGraph |
| **前端** | Vue 3 / TypeScript / Element Plus / Pinia |
| **图表渲染** | AntV G2 / g2-ssr (Node.js) |
| **ORM** | SQLModel (Pydantic + SQLAlchemy) |
| **数据库迁移** | Alembic |

---

## 2. 整体架构设计

### 2.1 系统分层架构

```
┌─────────────────────────────────────────────────────────────────┐
│                         前端层 (Vue 3)                          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │ 聊天界面  │ │ 仪表板   │ │ 数据源   │ │ 系统设置  │          │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              ↓ HTTP/SSE
┌─────────────────────────────────────────────────────────────────┐
│                       API 网关层 (FastAPI)                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │ 认证中间件│ │ 权限中间件│ │ 响应中间件│ │ 异常处理  │          │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                         业务逻辑层                              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │ 聊天服务  │ │ 数据源   │ │ 系统管理  │ │ 术语管理  │          │
│  │ (LLM)    │ │          │ │          │ │ (RAG)    │          │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │ 模型工厂 │ │ 训练数据  │ │ 仪表板   │ │ MCP服务  │          │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                         数据访问层                              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │ CRUD操作 │ │ 数据库会话│ │ 嵌入向量  │ │ 缓存管理  │          │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                         数据存储层                              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │ PostgreSQL│ │ pgvector │ │ Redis    │ │ 外部数据库 │         │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 部署架构

#### 开发模式

```
┌─────────────────────────────────────────────────────────────────┐
│                         开发环境                                │
└─────────────────────────────────────────────────────────────────┘
     ┌─────────────────┐         ┌──────────────────────────────┐
     │  前端开发服务器  │         │       后端服务               │
     │  Vite Dev Server│◄───────►│   FastAPI (port 8000)        │
     │   (port 5173)   │  HTTP   │  - API 服务                  │
     │                 │         │  - Swagger 文档              │
     │  - 热重载 (HMR) │         │                              │
     │  - TS 编译      │         └──────────────────────────────┘
     │  - ESLint       │                    │
     └─────────────────┘                    │
                                           ▼
                            ┌──────────────────────────────┐
                            │       数据库服务              │
                            │   PostgreSQL (port 5432)     │
                            │  - 应用数据库                 │
                            │  - pgvector 扩展              │
                            └──────────────────────────────┘
```

#### 生产模式

```
┌─────────────────────────────────────────────────────────────────┐
│                    Docker 容器 (生产环境)                      │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  ┌─────────────────────────────────────────────────┐   │  │
│  │  │  FastAPI 主服务 (port 8000)                      │   │  │
│  │  │  - API 服务                                      │   │  │
│  │  │  - 静态文件服务 (前端打包后的 Vite 构建产物)      │   │  │
│  │  │  - Swagger 文档                                  │   │  │
│  │  │  注：前端通过 npm run build 打包为静态文件        │   │  │
│  │  └─────────────────────────────────────────────────┘   │  │
│  │  ┌─────────────────────────────────────────────────┐   │  │
│  │  │  MCP 服务器 (port 8001)                          │   │  │
│  │  │  - Model Context Protocol                       │   │  │
│  │  │  - Claude Desktop 集成                           │   │  │
│  │  └─────────────────────────────────────────────────┘   │  │
│  │  ┌─────────────────────────────────────────────────┐   │  │
│  │  │  g2-ssr 服务 (port 3000)                        │   │  │
│  │  │  - 图表服务端渲染                               │   │  │
│  │  └─────────────────────────────────────────────────┘   │  │
│  │  ┌─────────────────────────────────────────────────┐   │  │
│  │  │  PostgreSQL (port 5432)                         │   │  │
│  │  │  - 应用数据库                                    │   │  │
│  │  │  - pgvector 扩展                                │   │  │
│  │  └─────────────────────────────────────────────────┘   │  │
│  └─────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

#### 部署说明

| 环境模式 | 前端服务 | 后端服务 | 说明 |
|---------|---------|---------|------|
| **开发模式** | Vite Dev Server (5173) | FastAPI (8000) | 前后端分离，支持热重载 |
| **生产模式** | FastAPI 静态服务 (8000) | FastAPI (8000) | 前端打包后由 FastAPI 统一服务 |

**关键差异**:
- **开发模式**: 前端独立运行在 5173 端口，通过代理访问后端 8000 端口 API
- **生产模式**: 前端打包为静态文件，由 FastAPI 在 8000 端口统一提供

---

## 3. 后端架构设计

### 3.1 目录结构

```
backend/
├── main.py                      # FastAPI 应用入口
├── alembic/                     # 数据库迁移
│   └── versions/                # 迁移脚本
├── apps/                        # 业务模块
│   ├── api.py                   # API 路由汇总
│   ├── chat/                    # 聊天与 LLM 编排
│   │   ├── api/                 # 聊天 API 端点
│   │   ├── crud/                # 聊天 CRUD 操作
│   │   ├── models/              # 聊天数据模型
│   │   └── task/                # LLM 服务核心
│   ├── datasource/              # 数据源管理
│   │   ├── api/                 # 数据源 API
│   │   ├── crud/                # 数据源 CRUD
│   │   ├── models/              # 数据源模型
│   │   ├── embedding/           # 嵌入向量工具
│   │   └── task/                # 数据库操作任务
│   ├── ai_model/                # AI 模型配置
│   │   ├── openai/              # OpenAI 集成
│   │   ├── embedding.py         # 嵌入模型缓存
│   │   └── model_factory.py     # LLM 工厂
│   ├── system/                  # 系统管理
│   │   ├── api/                 # 系统 API
│   │   ├── crud/                # 系统 CRUD
│   │   ├── models/              # 系统模型
│   │   └── middleware/          # 中间件
│   ├── terminology/             # 业务术语 (RAG)
│   ├── data_training/           # SQL 训练示例 (RAG)
│   ├── dimension/               # 维度值管理
│   ├── template/                # Jinja2 提示词模板
│   ├── dashboard/               # 仪表板功能
│   ├── settings/                # 应用设置
│   └── mcp/                     # MCP 服务器
├── common/                      # 公共模块
│   ├── core/                    # 核心配置
│   ├── db/                      # 数据库连接
│   ├── utils/                   # 工具函数
│   └── audit/                   # 审计日志
└── tests/                       # 测试代码
```

### 3.2 核心模块详解

#### 3.2.1 聊天与 LLM 编排模块 (`apps/chat/`)

**职责**: 处理用户聊天请求，编排 LLM 调用流程，管理会话状态

**核心文件**:
- [chat/api/chat.py](backend/apps/chat/api/chat.py) - 聊天 API 端点
- [chat/crud/chat.py](backend/apps/chat/crud/chat.py) - 聊天 CRUD 操作
- [chat/task/llm.py](backend/apps/chat/task/llm.py) - LLM 编排核心逻辑

**Text-to-SQL 处理流程**:

```
用户问题
    ↓
┌─────────────────────────────────────────────────────────┐
│ 1. 上下文检索 (RAG)                                      │
│    - 表结构检索 (基于表名嵌入相似度)                      │
│    - 术语检索 (基于术语定义嵌入相似度)                    │
│    - SQL 示例检索 (基于问题嵌入相似度)                    │
└─────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────┐
│ 2. 提示词构建                                            │
│    - 加载数据库 Schema                                   │
│    - 注入检索到的上下文 (表/术语/示例)                    │
│    - 应用自定义提示词模板                                 │
└─────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────┐
│ 3. LLM SQL 生成                                         │
│    - 调用配置的 LLM (OpenAI/通义/vLLM 等)                 │
│    - 流式返回响应                                        │
└─────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────┐
│ 4. SQL 执行                                             │
│    - SQL 安全检查                                        │
│    - 在目标数据库执行                                    │
│    - 结果行级权限过滤                                    │
└─────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────┐
│ 5. 图表生成                                             │
│    - LLM 分析数据生成图表配置                            │
│    - g2-ssr 服务渲染图表图片                             │
└─────────────────────────────────────────────────────────┘
    ↓
返回结果 (SQL + 数据 + 图表)
```

**关键代码模式** (llm.py):

```python
# 流式响应处理
async def generate_stream(
    question: str,
    datasource_id: int,
    llm: BaseChatModel,
    session: Session
) -> Iterator[Dict]:
    # 1. 检索相关上下文
    context = retrieve_context(question, datasource_id, session)

    # 2. 构建提示词
    prompt = build_prompt(context, question)

    # 3. LLM 生成 (流式)
    async for chunk in llm.astream(prompt):
        yield {"type": "sql", "content": chunk}

    # 4. 执行 SQL
    result = execute_sql(generated_sql)

    # 5. 生成图表
    chart = generate_chart(result)

    yield {"type": "chart", "content": chart}
```

#### 3.2.2 数据源管理模块 (`apps/datasource/`)

**职责**: 管理数据库连接，提取元数据，生成嵌入向量

**支持的数据库**:
- MySQL
- PostgreSQL
- SQL Server
- Oracle
- ClickHouse
- Redshift
- Elasticsearch

**核心功能**:
1. **连接管理**: 动态创建数据库连接池
2. **元数据提取**: 提取表结构、列信息、注释
3. **嵌入生成**: 为表和列生成语义嵌入向量
4. **SQL 执行**: 安全执行查询并返回结果

**关键文件**:
- [datasource/models/datasource.py](backend/apps/datasource/models/datasource.py) - 数据源模型
- [datasource/task/datasource_task.py](backend/apps/datasource/task/datasource_task.py) - 数据库操作任务
- [datasource/embedding/](backend/apps/datasource/embedding/) - 嵌入向量工具

#### 3.2.3 LLM 模型工厂 (`apps/ai_model/`)

**职责**: 抽象不同 LLM 提供商，统一接口

**设计模式**: 工厂模式 + 策略模式

**支持的提供商**:
- OpenAI (GPT-4, GPT-3.5)
- Azure OpenAI
- 通义千问 (Alibaba)
- Moonshot
- vLLM (本地部署)
- 其他兼容 OpenAI API 的服务

**核心文件**:
- [model_factory.py](backend/apps/ai_model/model_factory.py) - LLM 工厂类
- [embedding.py](backend/apps/ai_model/embedding.py) - 嵌入模型缓存

**使用示例**:
```python
from apps.ai_model.model_factory import LLMFactory, LLMConfig

# 创建 LLM 实例
config = LLMConfig(
    provider="openai",
    model_name="gpt-4",
    api_key="sk-..."
)
llm = LLMFactory.create_llm(config)

# 统一调用接口
response = await llm.ainvoke(prompt)
```

#### 3.2.4 RAG 检索模块

**术语管理** ([apps/terminology/](backend/apps/terminology/)):
- 存储业务术语及其定义
- 使用 pgvector 存储嵌入向量
- 支持表/字段级关联 (table_ids, field_ids)
- 支持作用域级别 (global/table/field)

**训练数据管理** ([apps/data_training/](backend/apps/data_training/)):
- 存储问题-SQL 对示例
- 使用 pgvector 存储问题嵌入
- 支持表级关联 (table_ids)

**三路召回顺序** (Phase 0 优化):
```
1. 表结构召回 (Table First)
   ↓ 基于召回的表
2. 术语召回 (Terminology v2)
   ↓ 基于召回的表
3. SQL 示例召回 (SQL Examples v2)
```

### 3.3 API 路由设计

**主路由文件**: [apps/api.py](backend/apps/api.py)

**路由结构**:
```
/api/v1
├── /chat          # 聊天相关
│   ├── GET  /list           # 获取会话列表
│   ├── GET  /{id}           # 获取会话详情
│   ├── POST /question       # 发送问题 (流式)
│   ├── PUT  /{id}           # 重命名会话
│   └── DELETE /{id}         # 删除会话
├── /datasource    # 数据源管理
│   ├── GET  /list           # 获取数据源列表
│   ├── POST /               # 创建数据源
│   ├── PUT  /{id}           # 更新数据源
│   └── DELETE /{id}         # 删除数据源
├── /system        # 系统管理
│   ├── /login            # 登录
│   ├── /user             # 用户管理
│   ├── /workspace        # 工作空间管理
│   ├── /aimodel          # AI 模型配置
│   └── /assistant        # 助手配置
├── /terminology   # 术语管理
├── /data_training # 训练数据管理
├── /dashboard     # 仪表板管理
├── /dimension     # 维度值管理
└── /mcp           # MCP 服务
```

### 3.4 中间件设计

**认证中间件** ([system/middleware/auth.py](backend/apps/system/middleware/auth.py)):
- JWT 令牌验证
- 用户身份解析
- 请求上下文注入

**权限中间件** ([RequestContextMiddleware](backend/apps/system/schemas/permission.py)):
- 行级权限过滤
- 工作空间隔离
- 操作审计

**响应中间件** ([ResponseMiddleware](backend/common/core/response_middleware.py)):
- 统一响应格式
- 异常处理
- 请求日志

### 3.5 数据库模型设计

**核心模型文件**:
- [system/models/user.py](backend/apps/system/models/user.py) - 用户模型
- [datasource/models/datasource.py](backend/apps/datasource/models/datasource.py) - 数据源模型
- [chat/models/chat_model.py](backend/apps/chat/models/chat_model.py) - 聊天模型
- [terminology/models/terminology_model.py](backend/apps/terminology/models/terminology_model.py) - 术语模型
- [data_training/models/data_training_model.py](backend/apps/data_training/models/data_training_model.py) - 训练数据模型
- [dimension/models/dimension_model.py](backend/apps/dimension/models/dimension_model.py) - 维度值模型

**核心表结构**:

| 表名 | 用途 | 关键字段 |
|-----|------|---------|
| `sys_user` | 用户管理 | id, account, password, email |
| `sys_workspace` | 工作空间 | id, name, oid |
| `sys_user_ws` | 用户-工作空间关联 | user_id, workspace_id |
| `core_datasource` | 数据源配置 | id, db_type, host, port, database |
| `core_table` | 表元数据 | id, datasource_id, table_name, embedding |
| `core_field` | 列元数据 | id, table_id, field_name, data_type |
| `chat` | 聊天会话 | id, user_id, title, datasource_id |
| `chat_record` | 聊天记录 | id, chat_id, question, sql, result |
| `chat_log` | LLM 交互日志 | id, prompt, response, tokens |
| `terminology` | 业务术语 | id, name, description, embedding, table_ids, field_ids, scope |
| `data_training` | SQL 训练示例 | id, question, sql, embedding, table_ids |
| `dimension` | 维度值 | id, name, table_id, field_id, values |
| `ai_model` | LLM 配置 | id, model_name, provider, api_key |
| `core_dashboard` | 仪表板定义 | id, name, config |

---

## 4. 前端架构设计

### 4.1 目录结构

```
frontend/
├── src/
│   ├── api/                    # API 客户端
│   │   ├── chat.ts             # 聊天 API
│   │   ├── datasource.ts       # 数据源 API
│   │   └── dimension.ts        # 维度值 API
│   ├── assets/                 # 静态资源
│   │   └── svg/                # SVG 图标
│   ├── components/             # 组件
│   │   ├── layout/             # 布局组件
│   │   ├── drawer-filter/      # 筛选抽屉
│   │   └── icon-custom/        # 自定义图标
│   ├── views/                  # 页面组件
│   │   ├── chat/               # 聊天页面
│   │   ├── dashboard/          # 仪表板
│   │   ├── ds/                 # 数据源管理
│   │   ├── system/             # 系统设置
│   │   ├── embedded/           # 嵌入式页面
│   │   └── login/              # 登录页
│   ├── stores/                 # Pinia 状态管理
│   │   ├── user.ts             # 用户状态
│   │   ├── assistant.ts        # 助手状态
│   │   └── appearance.ts       # 外观设置
│   ├── router/                 # Vue Router
│   │   └── index.ts            # 路由配置
│   ├── i18n/                   # 国际化
│   │   └── locales/            # 语言文件
│   ├── utils/                  # 工具函数
│   └── types/                  # TypeScript 类型
├── public/                     # 公共静态文件
├── index.html                  # HTML 入口
├── vite.config.ts              # Vite 配置
└── tsconfig.json               # TypeScript 配置
```

### 4.2 路由设计

**路由文件**: [src/router/index.ts](frontend/src/router/index.ts)

**主要路由**:

| 路径 | 组件 | 说明 |
|-----|------|-----|
| `/login` | [login](frontend/src/views/login/index.vue) | 登录页面 |
| `/chat` | [chat](frontend/src/views/chat/index.vue) | 聊天主界面 |
| `/dsTable/:dsId/:dsName` | [TableList](frontend/src/views/ds/TableList.vue) | 数据源表列表 |
| `/dashboard` | [dashboard](frontend/src/views/dashboard/index.vue) | 仪表板管理 |
| `/dimension` | [dimension](frontend/src/views/system/dimension/index.vue) | 维度值管理 |
| `/set` | Layout | 设置菜单组 |
| `/system` | Layout | 系统管理菜单组 |
| `/assistant` | [assistant](frontend/src/views/embedded/index.vue) | 嵌入式助手 |

### 4.3 状态管理 (Pinia)

**Store 文件**:
- [stores/user.ts](frontend/src/stores/user.ts) - 用户状态
- [stores/assistant.ts](frontend/src/stores/assistant.ts) - 助手配置
- [stores/appearance.ts](frontend/src/stores/appearance.ts) - 外观设置

**状态模式**:
```typescript
// stores/user.ts
export const useUserStore = defineStore('user', {
  state: () => ({
    userInfo: null as UserInfo | null,
    token: '',
    workspace: null as Workspace | null,
  }),

  actions: {
    async login(account: string, password: string) {
      const res = await loginApi({ account, password });
      this.token = res.token;
      this.userInfo = res.user;
    },
  },

  persist: true, // 持久化
});
```

### 4.4 API 客户端设计

**流式 API 实现** ([api/chat.ts](frontend/src/api/chat.ts)):
```typescript
export async function sendQuestionStream(
  question: string,
  onChunk: (chunk: string) => void,
  onComplete: () => void
) {
  const response = await fetch('/api/v1/chat/question', {
    method: 'POST',
    body: JSON.stringify({ question }),
    headers: {
      'Content-Type': 'application/json',
    },
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    const chunk = decoder.decode(value);
    const lines = chunk.split('\n');

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = JSON.parse(line.slice(6));
        if (data.type === 'sql') {
          onChunk(data.content);
        }
      }
    }
  }

  onComplete();
}
```

### 4.5 组件设计模式

**布局组件** ([components/layout/](frontend/src/components/layout/)):
- `index.vue` - 主布局容器
- `MenuItem.vue` - 侧边栏菜单项
- `LayoutDsl.vue` - 数据问答专用布局

**聊天组件** ([views/chat/](frontend/src/views/chat/)):
- `index.vue` - 聊天主页面
- `ChatMessage.vue` - 消息气泡
- `ChatInput.vue` - 输入框
- `ResultTable.vue` - SQL 结果表格
- `ResultChart.vue` - 图表渲染

---

## 5. RAG 检索架构设计

### 5.1 嵌入向量存储

**嵌入模型**: `shibing624/text2vec-base-chinese` (768 维)

**向量存储** (pgvector):
```sql
-- 术语表
CREATE TABLE terminology (
    id BIGINT PRIMARY KEY,
    name VARCHAR(255),
    description TEXT,
    embedding VECTOR(768),
    table_ids JSONB,
    field_ids JSONB,
    scope VARCHAR(20) DEFAULT 'global'
);

-- 训练数据表
CREATE TABLE data_training (
    id BIGINT PRIMARY KEY,
    question TEXT,
    description TEXT,
    embedding VECTOR(768),
    table_ids JSONB
);

-- 表元数据
CREATE TABLE core_table (
    id BIGINT PRIMARY KEY,
    table_name VARCHAR(255),
    embedding VECTOR(768)
);
```

### 5.2 召回流程

```
用户问题
    ↓
┌─────────────────────────────────────────────────────────┐
│ 1. 问题嵌入生成                                         │
│    - 使用 text2vec 模型生成 768 维向量                  │
└─────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────┐
│ 2. 表结构召回 (Phase 0.1)                               │
│    - 计算问题与表名/表注释的余弦相似度                   │
│    - 阈值过滤 (≥ 0.3)                                   │
│    - 返回 Top N 相关表                                  │
└─────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────┐
│ 3. 术语召回 (Phase 0.2)                                 │
│    - 过滤: scope IN ('global', 'table')                 │
│    - 过滤: table_ids && 召回表_ids != {}                │
│    - 计算相似度                                         │
│    - 返回相关术语                                       │
└─────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────┐
│ 4. SQL 示例召回 (Phase 0.3)                             │
│    - 过滤: table_ids && 召回表_ids != {}                │
│    - 计算相似度                                         │
│    - 返回相关 SQL 示例                                  │
└─────────────────────────────────────────────────────────┘
    ↓
上下文合并 → 提示词构建 → LLM 生成
```

### 5.3 相似度搜索 SQL

```sql
-- 表结构召回
SELECT ct.id, ct.table_name, ct.comment,
       1 - (ct.embedding <=> :question_embedding) as similarity
FROM core_table ct
WHERE ct.datasource_id = :datasource_id
  AND 1 - (ct.embedding <=> :question_embedding) >= 0.3
ORDER BY ct.embedding <=> :question_embedding
LIMIT 10;

-- 术语召回 (带表关联过滤)
SELECT t.id, t.name, t.description,
       1 - (t.embedding <=> :question_embedding) as similarity
FROM terminology t
WHERE t.datasource_id = :datasource_id
  AND t.scope IN ('global', 'table')
  AND (t.table_ids && :recalled_table_ids::jsonb)
  AND t.enabled = true
ORDER BY t.embedding <=> :question_embedding
LIMIT 10;

-- SQL 示例召回 (带表关联过滤)
SELECT dt.id, dt.question, dt.description,
       1 - (dt.embedding <=> :question_embedding) as similarity
FROM data_training dt
WHERE dt.datasource_id = :datasource_id
  AND (dt.table_ids && :recalled_table_ids::jsonb)
  AND dt.enabled = true
ORDER BY dt.embedding <=> :question_embedding
LIMIT 10;
```

---

## 6. LLM 编排架构设计

### 6.1 LangGraph 工作流

```python
# llm_service.py 中的 LangGraph 定义
from langgraph.graph import StateGraph, END

workflow = StateGraph(GraphState)

# 添加节点
workflow.add_node("retrieve_context", retrieve_context_node)
workflow.add_node("generate_sql", generate_sql_node)
workflow.add_node("execute_sql", execute_sql_node)
workflow.add_node("generate_chart", generate_chart_node)

# 添加边
workflow.set_entry_point("retrieve_context")
workflow.add_edge("retrieve_context", "generate_sql")
workflow.add_edge("generate_sql", "execute_sql")
workflow.add_edge("execute_sql", "generate_chart")
workflow.add_edge("generate_chart", END)

# 编译图
app = workflow.compile()
```

### 6.2 提示词模板系统

**模板目录**: [apps/template/](backend/apps/template/)

**模板类型**:
- `generate_sql/` - SQL 生成提示词
- `generate_chart/` - 图表生成提示词
- `generate_analysis/` - 分析生成提示词

**模板示例**:
```jinja2
{# apps/template/generate_sql/default.sql.jinja2 #}
你是一个专业的 SQL 专家。请根据以下信息生成 SQL 查询：

## 数据库类型
{{ db_type }}

## 表结构
{% for table in tables %}
表名: {{ table.table_name }}
注释: {{ table.comment }}
字段:
{% for field in table.fields %}
  - {{ field.field_name }} ({{ field.data_type }}): {{ field.comment }}
{% endfor %}
{% endfor %}

## 业务术语
{% for term in terminology %}
- {{ term.name }}: {{ term.description }}
{% endfor %}

## 相似 SQL 示例
{% for example in examples %}
Q: {{ example.question }}
A: {{ example.sql }}
{% endfor %}

## 用户问题
{{ question }}

请只输出 SQL，不要有任何解释。
```

---

## 7. 安全设计

### 7.1 认证与授权

**JWT 认证流程**:
```
登录请求
    ↓
验证账号密码
    ↓
生成 JWT Token (有效期 24h)
    ↓
返回 Token
    ↓
后续请求携带 Authorization: Bearer {token}
    ↓
TokenMiddleware 验证
    ↓
解析用户信息注入上下文
```

**权限控制**:
- 基于角色的访问控制 (RBAC)
- 行级数据权限
- 工作空间隔离

### 7.2 数据安全

**敏感数据加密**:
- 数据库密码: AES 加密存储
- API 密钥: 独立加密存储
- 连接字符串: 动态解密

**SQL 注入防护**:
- 参数化查询
- SQL 关键词黑名单
- 查询超时限制
- 结果集行数限制

### 7.3 审计日志

**日志记录**:
- 所有 API 请求/响应
- LLM 交互详情 (prompt/response/tokens)
- SQL 执行记录
- 用户操作审计

---

## 8. 性能优化设计

### 8.1 缓存策略

**Redis 缓存**:
- 用户会话信息
- 频繁访问的元数据
- LLM 响应缓存
- 嵌入向量缓存

**本地缓存**:
- 嵌入模型加载
- 提示词模板编译
- 数据库连接池

### 8.2 异步处理

**异步任务**:
- 嵌入向量生成 (启动时/数据变更时)
- 大规模数据导入
- 长时间查询

**流式响应**:
- LLM 生成流式返回
- 大数据集分页查询

### 8.3 数据库优化

**索引设计**:
- 主键索引
- 外键索引
- JSONB GIN 索引 (table_ids, field_ids)
- pgvector 向量索引

**查询优化**:
- 预加载关联数据
- 分页查询
- 连接池管理

---

## 9. 扩展性设计

### 9.1 多数据库支持

**扩展新数据库类型**:
1. 在 `datasource_task.py` 添加数据库引擎
2. 实现连接字符串生成
3. 添加 SQL 方言模板
4. 更新前端数据源表单

### 9.2 多 LLM 支持

**扩展新 LLM 提供商**:
1. 在 `ai_model/` 下创建提供商目录
2. 实现提供商类 (继承基类)
3. 在 `model_factory.py` 注册
4. 更新前端模型选择 UI

### 9.3 MCP 协议支持

**MCP 服务器** ([apps/mcp/](backend/apps/mcp/)):
- 暴露 SQLBot 功能为 MCP 工具
- 支持 Claude Desktop 集成
- 支持其他 AI 助手集成

---

## 10. 部署架构

### 10.1 Docker 部署

**容器编排** (start.sh):
```bash
#!/bin/bash

# 1. 启动 PostgreSQL
docker-entrypoint.sh postgres &

# 2. 启动 g2-ssr
pm2 start app.js &

# 3. 启动 MCP 服务器
uvicorn main:mcp_app --host 0.0.0.0 --port 8001 &

# 4. 启动主应用
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 10.2 环境变量

**关键配置**:
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

---

## 11. 监控与运维

### 11.1 日志系统

**日志级别**:
- DEBUG: 调试信息
- INFO: 一般信息
- WARNING: 警告
- ERROR: 错误
- CRITICAL: 严重错误

**日志存储**:
- 应用日志: `backend/logs/`
- 审计日志: 数据库 `chat_log` 表
- LLM 交互日志: 数据库 `chat_log` 表

### 11.2 健康检查

**健康检查端点**:
- `GET /health` - 应用健康状态
- `GET /api/v1/health` - API 健康状态
- 数据库连接检查
- LLM 服务可用性检查

---

## 12. 开发工作流

### 12.1 后端开发

```bash
# 安装依赖
cd backend
uv sync --extra cpu

# 运行开发服务器
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 代码检查
ruff check .
ruff format .

# 数据库迁移
alembic revision --autogenerate -m "description"
alembic upgrade head
```

### 12.2 前端开发

```bash
# 安装依赖
cd frontend
npm install

# 运行开发服务器
npm run dev

# 类型检查
vue-tsc -b

# 构建
npm run build
```

---

## 13. 附录

### 13.1 相关文档

- [产品迭代路书](./roadmap.md)
- [双方案切换详细设计](./switch-design/SQLBot-SWITCH-DETAILED-DESIGN.md)
- [RAG 召回顺序优化](./technical/rag-recall-order-optimization.md)

### 13.2 版本历史

| 版本 | 日期 | 变更内容 |
|-----|------|----------|
| v1.0 | 2026-02-11 | 初始版本，完整描述当前系统架构 |

---

**维护者**: SQLBot Team
**最后更新**: 2026-02-11
