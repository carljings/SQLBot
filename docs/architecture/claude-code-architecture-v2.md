# Claude Code + SQLBot 整合方案 v2

> 核心Agent：Claude Code（主动查询配置）
> 展示层：SQLBot（保留配置和展示能力）
> 设计时间：2026-02-08

---

## 📋 架构对比

### 方案B（之前的方案）vs 方案C（新需求）

| 维度 | 方案B（之前） | 方案C（现在） |
|------|-------------|-------------|
| **核心Agent** | SQLBot的LLMService（被动） | Claude Code（主动） |
| **信息流动** | SQLBot主动注入上下文到LLM | Claude Code主动查询上下文 |
| **Prompt构建** | SQLBot自动构建 | Claude Code自己构建 |
| **SQLBot角色** | Agent + 展示层 | 展示层 + 配置库 |
| **改动量** | 小（只换LLM） | 中（需要桥接层） |
| **Claude Code能力** | 作为LLM（被动） | 作为Agent（主动） |

---

## 🎯 核心架构图

```
┌─────────────────────────────────────────────────────┐
│                 SQLBot 前端                     │
│              (React - 保留原样）                  │
└───────────────────┬───────────────────────────────┘
                    │ HTTP/WebSocket
                    ▼
┌─────────────────────────────────────────────────────┐
│              SQLBot 后端桥接层              │
│              (新增：claude_code_bridge.py）        │
│                                                  │
│  ┌─────────────────────────────────────────┐   │
│  │      知识库服务              │   │
│  │      Claude Code调用这个API获取上下文      │   │
│  ├─────────────────────────────────────────┤   │
│  │  GET /knowledge/schema/:datasource_id   │   │
│  │  → 返回：表结构（带embedding）           │   │
│  ├─────────────────────────────────────────┤   │
│  │  GET /knowledge/terminology/:query      │   │
│  │  → 返回：相关术语（带embedding）         │   │
│  ├─────────────────────────────────────────┤   │
│  │  GET /knowledge/examples/:datasource_id │   │
│  │  → 返回：SQL示例（Few-shot）             │   │
│  ├─────────────────────────────────────────┤   │
│  │  GET /knowledge/prompt/:datasource_id   │   │
│  │  → 返回：自定义Prompt                   │   │
│  ├─────────────────────────────────────────┤   │
│  │  GET /knowledge/relations/:datasource_id │   │
│  │  → 返回：表关系（外键关联）              │   │
│  └─────────────────────────────────────────┘   │
│                                                  │
│  ┌─────────────────────────────────────────┐   │
│  │      Claude Code执行接口      │   │
│  │      Claude Code生成SQL后调用执行      │   │
│  ├─────────────────────────────────────────┤   │
│  │  POST /claude-code/execute-sql         │   │
│  │  → 执行SQL，返回结果                    │   │
│  ├─────────────────────────────────────────┤   │
│  │  POST /claude-code/stream-answer       │   │
│  │  → 流式返回Claude Code的响应            │   │
│  └─────────────────────────────────────────┘   │
└───────────────────┬───────────────────────────────┘
                    │ HTTP调用
                    ▼
┌─────────────────────────────────────────────────────┐
│           Claude Code Agent              │
│           (通过OpenClaw管理）                  │
│                                                  │
│  1. 接收用户问题                                 │
│  2. 调用 /knowledge/* 获取上下文                  │
│  3. 自己构建Prompt                               │
│  4. 自己生成SQL                                  │
│  5. 调用 /claude-code/execute-sql 执行           │
│  6. 通过 /claude-code/stream-answer 流式返回     │
└─────────────────────────────────────────────────────┘
                    │ 读取配置
                    ▼
┌─────────────────────────────────────────────────────┐
│              PostgreSQL 数据库                 │
│  ├─→ 业务数据表（苏政源一本账）                │
│  ├─→ SQLBot 系统表                         │
│  ├─→ terminology (术语库)                    │
│  ├─→ data_training (SQL示例)                │
│  ├─→ custom_prompt (自定义Prompt)            │
│  └─→ core_table, core_field (表结构)        │
└─────────────────────────────────────────────────────┘
```

---

## 🔧 实施方案

### 阶段 1：创建知识库API（新增桥接层）

**文件**：`apps/knowledge_base/api/knowledge.py`

**核心功能**：Claude Code主动查询配置信息

```python
# apps/knowledge_base/api/knowledge.py

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import and_, select
from sqlmodel import Session

from apps.datasource.crud.datasource import get_ds, get_table_schema
from apps.datasource.models.datasource import CoreDatasource
from apps.terminology.curd.terminology import select_terminology_by_word, to_xml_string
from apps.template.generate_chart.generator import get_base_terminology_template
from apps.system.schemas.permission import require_permissions
from common.core.deps import SessionDep, CurrentUser

router = APIRouter(tags=["Knowledge Base"], prefix="/knowledge")


@router.get("/schema/{datasource_id}", summary="获取数据源Schema（表结构）")
async def get_schema_knowledge(
    session: SessionDep,
    current_user: CurrentUser,
    datasource_id: int,
    question: Optional[str] = None,
    include_embedding: bool = True
):
    """
    Claude Code调用：获取数据源的表结构信息

    Args:
        datasource_id: 数据源ID
        question: 用户问题（用于embedding匹配）
        include_embedding: 是否使用embedding过滤

    Returns:
        {
            "datasource_id": 1,
            "datasource_name": "一本账数据库",
            "schema": "完整schema字符串",
            "tables": [
                {
                    "table_name": "t_sys",
                    "table_comment": "系统表",
                    "fields": [
                        {"field_name": "id", "field_type": "BIGINT", "field_comment": "ID"},
                        ...
                    ]
                }
            ]
        }
    """
    # 获取数据源
    ds = get_ds(session, datasource_id)
    if not ds:
        raise HTTPException(status_code=404, detail="Datasource not found")

    # 获取Schema（复用SQLBot现有逻辑）
    schema_str = get_table_schema(
        session=session,
        current_user=current_user,
        ds=ds,
        question=question or "",
        embedding=include_embedding
    )

    return {
        "datasource_id": datasource_id,
        "datasource_name": ds.name,
        "schema": schema_str,
        # 额外返回结构化数据（方便Claude Code理解）
        "tables": _parse_schema_to_structured(schema_str)
    }


@router.get("/terminology", summary="获取相关术语")
async def get_terminology_knowledge(
    session: SessionDep,
    current_user: CurrentUser,
    query: str,
    datasource_id: Optional[int] = None
):
    """
    Claude Code调用：获取与查询相关的术语

    Args:
        query: 用户查询文本
        datasource_id: 数据源ID（可选，用于过滤特定数据源的术语）

    Returns:
        {
            "query": "垂管系统",
            "terminologies": [
                {
                    "word": "垂管系统",
                    "other_words": ["省垂", "垂直管理"],
                    "description": "由省级部门直接管理的系统"
                }
            ],
            "xml_template": "XML格式的术语模板（可直接注入Prompt）"
        }
    """
    # 查询术语（复用SQLBot现有逻辑）
    terminologies = select_terminology_by_word(
        session=session,
        word=query,
        oid=current_user.oid or 1,
        datasource=datasource_id
    )

    # 转换为XML模板（用于Prompt）
    if terminologies:
        xml_template = to_xml_string(terminologies)
    else:
        xml_template = ""

    return {
        "query": query,
        "terminologies": terminologies,
        "xml_template": xml_template
    }


@router.get("/examples/{datasource_id}", summary="获取SQL示例（Few-shot）")
async def get_sql_examples(
    session: SessionDep,
    current_user: CurrentUser,
    datasource_id: int,
    question: Optional[str] = None
):
    """
    Claude Code调用：获取SQL示例（用于Few-shot学习）

    Returns:
        {
            "examples": [
                {
                    "question": "系统数量",
                    "sql": "SELECT COUNT(*) FROM t_sys",
                    "explanation": "查询系统总数"
                }
            ]
        }
    """
    # 复用SQLBot的data_training查询
    from apps.data_training.curd.data_training import get_training_template

    sql_examples = get_training_template(
        session=session,
        datasource_id=datasource_id,
        question=question or ""
    )

    return {
        "datasource_id": datasource_id,
        "examples": sql_examples
    }


@router.get("/prompt/{datasource_id}", summary="获取自定义Prompt模板")
async def get_custom_prompt(
    session: SessionDep,
    current_user: CurrentUser,
    datasource_id: int
):
    """
    Claude Code调用：获取自定义Prompt模板

    Returns:
        {
            "system_prompt": "系统级的Prompt模板",
            "user_prompt": "用户级的Prompt模板"
        }
    """
    from sqlbot_xpack.custom_prompt.curd.custom_prompt import find_custom_prompts

    prompts = find_custom_prompts(
        session=session,
        datasource_id=datasource_id,
        enabled=True
    )

    return {
        "datasource_id": datasource_id,
        "prompts": prompts
    }


@router.get("/relations/{datasource_id}", summary="获取表关系（外键关联）")
async def get_table_relations(
    session: SessionDep,
    current_user: CurrentUser,
    datasource_id: int
):
    """
    Claude Code调用：获取表之间的外键关联关系

    Returns:
        {
            "relations": [
                {
                    "source_table": "t_sys",
                    "source_field": "city_id",
                    "target_table": "t_city",
                    "target_field": "id",
                    "relation_type": "foreign_key"
                }
            ]
        }
    """
    ds = get_ds(session, datasource_id)
    if not ds:
        raise HTTPException(status_code=404, detail="Datasource not found")

    # 复用SQLBot的table_relation
    relations = ds.table_relation or []

    # 解析关系（如果是JSONB格式）
    parsed_relations = []
    if isinstance(relations, list):
        for relation in relations:
            if relation.get("shape") == "edge":
                source = relation.get("source", {})
                target = relation.get("target", {})
                parsed_relations.append({
                    "source_table_id": source.get("cell"),
                    "source_field_id": source.get("port"),
                    "target_table_id": target.get("cell"),
                    "target_field_id": target.get("port"),
                    "relation_type": "foreign_key"
                })

    return {
        "datasource_id": datasource_id,
        "relations": parsed_relations
    }


# 辅助函数：解析Schema为结构化数据
def _parse_schema_to_structured(schema_str: str) -> List[dict]:
    """
    将schema字符串解析为结构化数据（方便Claude Code理解）
    """
    tables = []

    # 简单解析（实际可以更复杂）
    lines = schema_str.split('\n')
    current_table = None

    for line in lines:
        line = line.strip()
        if line.startswith("# Table:"):
            if current_table:
                tables.append(current_table)
            table_name = line.replace("# Table:", "").strip()
            current_table = {
                "table_name": table_name,
                "table_comment": "",
                "fields": []
            }
        elif line.startswith("[") and current_table:
            # 表注释（在 [ 之前）
            comment = current_table["table_name"].split(",")[-1].strip()
            if comment:
                current_table["table_comment"] = comment
        elif line.startswith("(") and current_table:
            # 字段定义
            field_def = line.strip("()[],")
            parts = field_def.split(":")
            if len(parts) >= 2:
                field_name = parts[0].strip()
                field_type = parts[1].split(",")[0].strip()
                field_comment = parts[1].split(",")[1].strip() if "," in parts[1] else ""
                current_table["fields"].append({
                    "field_name": field_name,
                    "field_type": field_type,
                    "field_comment": field_comment
                })

    if current_table:
        tables.append(current_table)

    return tables
```

---

### 阶段 2：创建Claude Code执行接口

**文件**：`apps/claude_code_bridge/api/claude_code.py`

**核心功能**：Claude Code生成SQL后，调用这个接口执行

```python
# apps/claude_code_bridge/api/claude_code.py

from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session

from apps.db.db import exec_sql
from common.core.deps import SessionDep, CurrentUser
from common.utils.data_format import DataFormat

router = APIRouter(tags=["Claude Code Bridge"], prefix="/claude-code")


@router.post("/execute-sql", summary="Claude Code执行SQL")
async def execute_sql(
    session: SessionDep,
    current_user: CurrentUser,
    sql: str,
    datasource_id: int,
    limit: Optional[int] = 1000
):
    """
    Claude Code调用：执行生成的SQL

    Args:
        sql: Claude Code生成的SQL语句
        datasource_id: 数据源ID
        limit: 最大返回行数（防止大数据）

    Returns:
        {
            "success": true/false,
            "data": [...],
            "fields": [...],
            "row_count": 10,
            "error": null
        }
    """
    # 添加limit（如果SQL没有LIMIT）
    if "LIMIT" not in sql.upper():
        sql = f"{sql} LIMIT {limit}"

    try:
        # 执行SQL（复用SQLBot现有逻辑）
        result = exec_sql(session, sql, datasource_id)

        # 格式化数据
        fields = []
        data = []

        if result and len(result) > 0:
            # 获取字段名
            fields = [{"name": col, "type": str(type(val).__name__)} for col, val in zip(result[0].keys(), result[0].values())]

            # 转换数据
            for row in result:
                data.append([val for val in row.values()])

        return {
            "success": True,
            "data": data,
            "fields": fields,
            "row_count": len(data),
            "error": None
        }

    except Exception as e:
        return {
            "success": False,
            "data": [],
            "fields": [],
            "row_count": 0,
            "error": str(e)
        }


@router.post("/validate-sql", summary="Claude Code验证SQL语法")
async def validate_sql(
    sql: str,
    datasource_id: int
):
    """
    Claude Code调用：验证SQL语法（不执行）

    Returns:
        {
            "valid": true/false,
            "error": null
        }
    """
    import sqlparse

    try:
        # 解析SQL（不执行）
        parsed = sqlparse.parse(sql)
        if not parsed:
            return {
                "valid": False,
                "error": "Empty or invalid SQL"
            }

        return {
            "valid": True,
            "error": None
        }

    except Exception as e:
        return {
            "valid": False,
            "error": str(e)
        }
```

---

### 阶段 3：注册路由

**文件**：`backend/main.py`

```python
# backend/main.py

# 导入新的路由
from apps.knowledge_base.api.knowledge import router as knowledge_router
from apps.claude_code_bridge.api.claude_code import router as claude_code_router

# 注册路由
app.include_router(knowledge_router)
app.include_router(claude_code_router)
```

---

### 阶段 4：Claude Code使用这些API

**Claude Code的工作流**（通过OpenClaw管理）：

```python
# Claude Code的Prompt示例（你可以给Claude Code这样的指令）

"""
你是苏政源一本账的智能问数Agent。你的工作流程如下：

1. 接收用户问题
2. 调用 GET /knowledge/schema/{datasource_id} 获取表结构
3. 调用 GET /knowledge/terminology?query=用户问题 获取相关术语
4. 调用 GET /knowledge/examples/{datasource_id} 获取SQL示例
5. 调用 GET /knowledge/prompt/{datasource_id} 获取自定义Prompt
6. 基于以上信息，自己构建Prompt并生成SQL
7. 调用 POST /claude-code/execute-sql 执行SQL
8. 返回结果给用户

示例：

用户问题："系统数量"

你的操作：
1. GET /knowledge/schema/1 → 获取t_sys表结构
2. GET /knowledge/terminology?query=系统数量 → 获取相关术语
3. GET /knowledge/examples/1 → 获取SQL示例（如：SELECT COUNT(*) FROM t_sys）
4. 自己构建Prompt：
   - Schema: # Table: t_sys [ (id:BIGINT), (name:VARCHAR), ... ]
   - Terminology: <terminologies>...</terminologies>
   - Examples: Q: "系统数量" -> A: SELECT COUNT(*) FROM t_sys
   - User Question: "系统数量"
5. 生成SQL：SELECT COUNT(*) FROM t_sys
6. POST /claude-code/execute-sql → 执行SQL
7. 返回结果：系统数量为10个
"""
```

---

### 阶段 5：测试和验证

#### 测试1：获取Schema

```bash
curl "http://localhost:8000/knowledge/schema/1?question=系统数量"
```

**预期响应**：
```json
{
  "datasource_id": 1,
  "datasource_name": "一本账数据库",
  "schema": "【DB_ID】一本账\n【Schema】\n# Table: t_sys\n[(id:BIGINT, ID),\n(name:VARCHAR, 系统名称),\n...]\n",
  "tables": [
    {
      "table_name": "t_sys",
      "table_comment": "系统表",
      "fields": [
        {"field_name": "id", "field_type": "BIGINT", "field_comment": "ID"},
        ...
      ]
    }
  ]
}
```

#### 测试2：获取术语

```bash
curl "http://localhost:8000/knowledge/terminology?query=垂管系统&datasource_id=1"
```

**预期响应**：
```json
{
  "query": "垂管系统",
  "terminologies": [
    {
      "word": "垂管系统",
      "other_words": ["省垂", "垂直管理"],
      "description": "由省级部门直接管理的系统"
    }
  ],
  "xml_template": "<terminologies>\n  <terminology>\n    <word>垂管系统</word>\n    <words>省垂,垂直管理</words>\n    <description>由省级部门直接管理的系统</description>\n  </terminology>\n</terminologies>"
}
```

#### 测试3：执行SQL

```bash
curl -X POST "http://localhost:8000/claude-code/execute-sql" \
  -H "Content-Type: application/json" \
  -d '{
    "sql": "SELECT COUNT(*) FROM t_sys",
    "datasource_id": 1
  }'
```

**预期响应**：
```json
{
  "success": true,
  "data": [[10]],
  "fields": [
    {"name": "count", "type": "int"}
  ],
  "row_count": 1,
  "error": null
}
```

---

## 📊 实施步骤

### 第1步：创建知识库API（2小时）

```bash
# 创建目录
cd /Users/guchuan/codespace/SQLBot/backend/apps
mkdir -p knowledge_base/api
mkdir -p claude_code_bridge/api

# 创建文件
touch knowledge_base/api/__init__.py
touch knowledge_base/api/knowledge.py
touch claude_code_bridge/api/__init__.py
touch claude_code_bridge/api/claude_code.py
```

### 第2步：复制代码（1小时）

将上面的代码复制到对应文件。

### 第3步：注册路由（15分钟）

修改 `main.py`，添加路由注册。

### 第4步：测试API（30分钟）

使用curl测试所有API端点。

### 第5步：配置Claude Code（1小时）

给Claude Code配置系统Prompt，教它如何调用这些API。

### 第6步：端到端测试（1小时）

从用户问题到返回结果的完整流程测试。

---

## 🎯 核心优势

### 相比方案B

| 维度 | 方案B | 方案C（新） |
|------|------|-----------|
| **Claude Code角色** | 被动LLM | 主动Agent |
| **灵活性** | 低（依赖SQLBot的Prompt构建） | 高（Claude Code自己决策） |
| **扩展性** | 中 | 高（Claude Code可以做更复杂的推理） |
| **SQLBot改动** | 小 | 中（新增桥接层） |
| **Claude Code能力** | 只能生成SQL | 可以做复杂的多步推理 |

### 适合场景

✅ **适合方案C的场景**：
- 需要Claude Code做复杂的多步推理
- 需要Claude Code主动查询多个数据源
- 需要Claude Code做数据分析、洞察

❌ **不适合方案C的场景**：
- 只需要简单的SQL生成（方案B更简单）
- 性能要求极高（方案C多了API调用）

---

## 📝 总结

### 核心改动

1. **新增知识库API**：Claude Code主动查询配置
2. **新增Claude Code执行接口**：Claude Code生成SQL后执行
3. **Claude Code作为主动Agent**：自己构建Prompt、生成SQL

### 工作量

| 阶段 | 任务 | 时间 |
|------|------|------|
| 第1步 | 创建知识库API | 2 小时 |
| 第2步 | 复制代码 | 1 小时 |
| 第3步 | 注册路由 | 15 分钟 |
| 第4步 | 测试API | 30 分钟 |
| 第5步 | 配置Claude Code | 1 小时 |
| 第6步 | 端到端测试 | 1 小时 |
| **总计** | | **5.5 小时** |

---

## 🚀 下一步

**你需要决定**：
1. 是否采用方案C？
2. 如果采用，从哪一步开始实施？

---

*文档生成时间：2026-02-08*
