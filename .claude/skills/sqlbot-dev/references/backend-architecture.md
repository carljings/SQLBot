# SQLBot 后端架构参考

## 核心模块结构

### apps/ 目录组织

```
apps/
├── chat/               # 聊天和问答功能
│   ├── api/           # 路由: /chat/*
│   ├── crud/          # 数据库操作
│   └── task/          # LLM 服务编排
│
├── system/            # 系统管理
│   ├── api/           # 登录、用户、工作空间、AI模型配置
│   ├── crud/          # 用户管理 CRUD
│   └── middleware/    # 认证中间件
│
├── datasource/        # 数据源管理
│   ├── api/           # CRUD + 表结构获取
│   └── task/          # 数据库连接和查询
│
├── data_training/     # SQL 训练数据 (RAG)
├── terminology/       # 业务术语词典 (RAG)
├── dashboard/         # 仪表板
└── mcp/              # MCP 服务器
```

## 依赖注入系统

### 常用依赖

```python
from common.core.deps import (
    SessionDep,      # 数据库会话
    CurrentUser,     # 当前认证用户
    DBSessionDep,    # 数据库会话 (无自动提交)
)
```

### 自定义依赖

```python
from fastapi import Depends
from sqlalchemy.orm import Session

def get_resource(id: int, session: SessionDep) -> Resource:
    return session.get(Resource, id)

@router.get("/{id}")
async def endpoint(
    resource: Resource = Depends(get_resource)
):
    return resource
```

## 认证与授权

### Token 验证流程

```
请求 -> TokenMiddleware -> RequestContextMiddleware -> Handler
         (解析 Token)        (注入 CurrentUser)
```

### 权限检查

```python
from apps.system.crud.user import get_visible_users_stmt

# 行级权限：只返回用户有权限访问的数据
def list_items(session: Session, current_user: CurrentUser):
    user_stmt = get_visible_users_stmt(current_user)
    stmt = select(Item).where(
        Item.created_by.in_(user_stmt)
    )
    return session.scalars(stmt).all()
```

## LLM 集成

### LLM 工厂模式

```python
from apps.ai_model.task.llm_factory import LLMFactory

# 创建 LLM 实例
llm = LLMFactory.create_llm(
    provider="openai",  # openai, azure, moonshot, deepseek, etc.
    model="gpt-4",
    api_key="...",
    base_url="..."
)

# 调用
response = llm.invoke(messages)
```

### LangGraph 工作流

```python
from apps.chat.task.llm_service import LLMService

service = LLMService()
result = await service.generate_sql(
    question="用户问题",
    context=context,
    session=session
)
```

## 数据库操作

### 查询模式

```python
from sqlalchemy import select, func

# 简单查询
stmt = select(Resource).where(Resource.id == id)
result = session.scalar(stmt)

# 列表查询
stmt = select(Resource).offset(skip).limit(limit)
results = session.scalars(stmt).all()

# 关联查询
stmt = select(Resource).join(User).where(User.name == "admin")

# 聚合查询
stmt = select(func.count(Resource.id))
count = session.scalar(stmt)
```

### 事务处理

```python
from sqlalchemy.orm import Session

def create_with_transaction(session: Session, data: ResourceCreate):
    try:
        resource = Resource(**data.model_dump())
        session.add(resource)
        session.flush()  # 获取 ID 但不提交

        # 关联操作
        create_related(session, resource.id)

        session.commit()
        return resource
    except Exception:
        session.rollback()
        raise
```

## 响应格式

### 统一响应

```python
from common.core.response_middleware import success_response

@router.get("/")
async def list_items():
    items = list_items(session)
    return success_response(data=items)
```

### 错误处理

```python
from fastapi import HTTPException

@router.post("/")
async def create_item(data: ItemCreate):
    if not validate(data):
        raise HTTPException(
            status_code=400,
            detail="验证失败"
        )
    return create(data)
```

## 后台任务

### 嵌入向量生成

```python
from common.utils.embedding_threads import (
    fill_empty_table_embeddings,
    fill_empty_datasource_embeddings
)

# 异步填充嵌入向量
fill_empty_table_embeddings()
fill_empty_datasource_embeddings()
```

## 配置管理

### 读取配置

```python
from common.core.config import settings

# 数据库配置
db_url = settings.SQLALCHEMY_DATABASE_URI
postgres_server = settings.POSTGRES_SERVER

# LLM 配置
default_model = settings.DEFAULT_EMBEDDING_MODEL

# 缓存配置
cache_type = settings.CACHE_TYPE
```

### 环境变量

```bash
# .env
POSTGRES_SERVER=localhost
POSTGRES_PORT=5432
POSTGRES_USER=root
POSTGRES_PASSWORD=password
POSTGRES_DB=sqlbot

SECRET_KEY=your-secret-key
DEFAULT_PWD=SQLBot@123456
```

## 中间件

### 认证中间件

```python
from apps.system.middleware.auth import TokenMiddleware

app.add_middleware(TokenMiddleware)
```

### 响应中间件

```python
from common.core.response_middleware import ResponseMiddleware

app.add_middleware(ResponseMiddleware)
```

## 测试

### Pytest 用例

```python
import pytest
from sqlalchemy.orm import Session

def test_create_resource(session: Session):
    data = ResourceCreate(name="Test", description="Test resource")
    resource = create_resource(session, data, user_id="1")
    assert resource.name == "Test"
    assert resource.id is not None

@pytest.fixture
def test_resource(session: Session):
    resource = Resource(name="Test")
    session.add(resource)
    session.commit()
    yield resource
    session.delete(resource)
    session.commit()
```
