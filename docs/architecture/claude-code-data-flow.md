# Claude Code + SQLBot 数据流设计

> Claude Code生成SQL后，如何调用SQLBot去可视化展示
> 设计时间：2026-02-08

---

## 🏗️ 完整数据流

```
┌─────────────────────────────────────────────────────┐
│                 用户                         │
│              提问："垂管系统数量"                │
└───────────────────┬───────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────┐
│           Claude Code Agent              │
│                                                  │
│  步骤1：读取配置文件                             │
│  ├─ read skills/sqlbot-knowledge/SCHEMA.md       │
│  ├─ read skills/sqlbot-knowledge/TERMINOLOGY.md  │
│  ├─ read skills/sqlbot-knowledge/EXAMPLES.md     │
│  └─ read skills/sqlbot-knowledge/PROMPT.md       │
│                                                  │
│  步骤2：构建Prompt并生成SQL                      │
│  结果：SELECT COUNT(*) FROM t_sys WHERE type = '省垂'│
│                                                  │
│  步骤3：调用SQLBot执行SQL并展示                  │
│  ├─ POST /claude-code/query                       │
│  │   {                                          │
│  │     "sql": "SELECT COUNT(*) FROM t_sys...",   │
│  │     "chat_id": 123,                           │
│  │     "question": "垂管系统数量"                 │
│  │   }                                          │
│  │                                               │
│  ├─ SQLBot执行SQL                               │
│  ├─ SQLBot生成图表配置（ECharts/G2）             │
│  ├─ SQLBot返回图表URL                            │
│  └─ 返回结果给Claude Code                        │
│                                                  │
│  步骤4：返回结果给用户                           │
│  "垂管系统数量为5个"                            │
│  + 图表链接                                      │
└─────────────────────────────────────────────────────┘
                    │ HTTP调用
                    ▼
┌─────────────────────────────────────────────────────┐
│              SQLBot 后端                     │
│              (新增：claude_code_bridge.py）      │
│                                                  │
│  ┌─────────────────────────────────────────┐   │
│  │      POST /claude-code/query          │   │
│  │      Claude Code调用这个接口          │   │
│  ├─────────────────────────────────────────┤   │
│  │  1. 接收SQL和chat_id               │   │
│  │  2. 执行SQL获取数据                 │   │
│  │  3. 调用图表生成模块               │   │
│  │  4. 生成图表URL                   │   │
│  │  5. 保存chat_record               │   │
│  │  6. 返回图表URL                  │   │
│  └─────────────────────────────────────────┘   │
└───────────────────┬───────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────┐
│              PostgreSQL 数据库                 │
│              执行SQL：                         │
│              SELECT COUNT(*) FROM t_sys ...       │
└─────────────────────────────────────────────────────┘
```

---

## 🔧 新增API：/claude-code/query

**文件**：`apps/claude_code_bridge/api/claude_code.py`

```python
# apps/claude_code_bridge/api/claude_code.py

"""
Claude Code桥接层
用途：Claude Code生成SQL后，调用这个接口执行并可视化
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session
from datetime import datetime

from apps.db.db import exec_sql
from apps.chat.models.chat_model import ChatRecord
from apps.template.generate_chart.generator import generate_chart
from common.core.deps import SessionDep, CurrentUser

router = APIRouter(tags=["Claude Code Bridge"], prefix="/claude-code")


@router.post("/query", summary="Claude Code执行SQL并生成图表")
async def execute_sql_and_visualize(
    session: SessionDep,
    current_user: CurrentUser,
    sql: str,
    question: str,
    chat_id: Optional[int] = None,
    limit: int = 1000
):
    """
    Claude Code调用：执行SQL并生成图表

    Args:
        session: 数据库Session
        current_user: 当前用户
        sql: Claude Code生成的SQL
        question: 用户问题
        chat_id: 聊天ID（可选，如果没有则创建新的）
        limit: 最大返回行数

    Returns:
        {
            "success": true/false,
            "data": [...],              # 查询结果
            "fields": [...],            # 字段列表
            "row_count": 10,
            "chart_url": "...",         # 图表URL（如果有）
            "chart_type": "bar",         # 图表类型
            "error": null
        }
    """
    # 1. 添加limit（如果SQL没有LIMIT）
    if "LIMIT" not in sql.upper():
        sql = f"{sql} LIMIT {limit}"

    try:
        # 2. 执行SQL
        result = exec_sql(session, sql, datasource_id=None)

        # 3. 格式化数据
        fields = []
        data = []

        if result and len(result) > 0:
            # 获取字段名
            fields = [{"name": col, "type": str(type(val).__name__)} 
                     for col, val in zip(result[0].keys(), result[0].values())]

            # 转换数据
            for row in result:
                data.append([val for val in row.values()])

        # 4. 生成图表（如果数据适合可视化）
        chart_url = None
        chart_type = None

        if len(data) > 0 and len(fields) >= 1:
            # 调用SQLBot的图表生成模块
            chart_config = generate_chart(
                fields=fields,
                data=data,
                question=question,
                chart_type="auto"  # 自动判断图表类型
            )

            if chart_config:
                # 保存图表（复用SQLBot的图表保存逻辑）
                chart_url = _save_chart(chart_config)
                chart_type = chart_config.get("type")

        # 5. 保存chat_record（如果提供了chat_id）
        if chat_id:
            chat_record = ChatRecord(
                chat_id=chat_id,
                question=question,
                sql=sql,
                data=data,
                chart=chart_url,
                create_by=current_user.id,
                create_time=datetime.now()
            )
            session.add(chat_record)
            session.commit()

        return {
            "success": True,
            "data": data,
            "fields": fields,
            "row_count": len(data),
            "chart_url": chart_url,
            "chart_type": chart_type,
            "error": None
        }

    except Exception as e:
        return {
            "success": False,
            "data": [],
            "fields": [],
            "row_count": 0,
            "chart_url": None,
            "chart_type": None,
            "error": str(e)
        }


def _save_chart(chart_config: dict) -> str:
    """
    保存图表配置并返回URL

    Args:
        chart_config: 图表配置（ECharts/G2格式）

    Returns:
        str: 图表URL
    """
    # 复用SQLBot的图表保存逻辑
    # 参考：apps/chat/task/llm.py 中的 save_chart() 方法

    # 简化版本：返回图表配置的base64编码
    import json
    import base64

    chart_json = json.dumps(chart_config)
    chart_base64 = base64.b64encode(chart_json.encode()).decode()

    # 返回图表URL（前端可以解码base64）
    return f"data:application/json;base64,{chart_base64}"
```

---

## 📋 注册路由

**文件**：`backend/main.py`

```python
# backend/main.py

# 导入新的路由
from apps.claude_code_bridge.api.claude_code import router as claude_code_router

# 注册路由
app.include_router(claude_code_router)
```

---

## 🎯 Claude Code工作流

### 完整Prompt示例

```markdown
你是苏政源一本账的智能问数Agent。你的工作流程如下：

## 步骤1：读取配置文件

当用户问SQL相关问题时，首先读取配置文件：

```bash
read skills/sqlbot-knowledge/SCHEMA.md
read skills/sqlbot-knowledge/TERMINOLOGY.md
read skills/sqlbot-knowledge/EXAMPLES.md
read skills/sqlbot-knowledge/PROMPT.md
```

## 步骤2：构建Prompt并生成SQL

基于以上信息，构建Prompt并生成SQL：

```
表结构：
# Table: t_sys, 系统表
[(id:BIGINT, ID), (name:VARCHAR, 系统名称), (type:VARCHAR, 系统类型), ...]

术语：
## 垂管系统
**描述**: 由省级部门直接管理的系统
**同义词**: 省垂, 垂直管理

参考示例：
## 示例 1
**问题**: 系统数量
**SQL**: SELECT COUNT(*) FROM t_sys

用户问题：{{用户问题}}

生成SQL：
```

## 步骤3：调用SQLBot执行SQL并生成图表

使用curl调用SQLBot的API：

```bash
curl -X POST "http://localhost:8000/claude-code/query" \
  -H "Content-Type: application/json" \
  -d '{
    "sql": "{{生成的SQL}}",
    "question": "{{用户问题}}",
    "chat_id": 123,
    "limit": 1000
  }'
```

## 步骤4：处理返回结果

如果成功：
```json
{
  "success": true,
  "data": [[5]],
  "fields": [{"name": "count", "type": "int"}],
  "row_count": 1,
  "chart_url": "data:application/json;base64,...",
  "chart_type": "bar",
  "error": null
}
```

返回给用户：
- 文字描述：垂管系统数量为5个
- 图表链接：chart_url

如果失败：
```json
{
  "success": false,
  "error": "..."
}
```

返回错误信息给用户。

---

## 示例

用户问题："垂管系统数量"

你的回答：

1. 读取配置文件（如上）
2. 生成SQL：SELECT COUNT(*) FROM t_sys WHERE type = '省垂'
3. 调用SQLBot API（如上）
4. 返回结果：
   ```
   垂管系统数量为5个

   📊 图表：data:application/json;base64,...
   ```
```

---

## 🔌 前端展示

### 方式1：直接嵌入图表（推荐）

前端解码base64并渲染ECharts/G2图表：

```javascript
// 解码图表配置
const chartBase64 = response.chart_url.replace('data:application/json;base64,', '');
const chartJson = atob(chartBase64);
const chartConfig = JSON.parse(chartJson);

// 渲染ECharts图表
const chart = echarts.init(document.getElementById('chart-container'));
chart.setOption(chartConfig);
```

### 方式2：返回图表URL

如果SQLBot生成了图表文件（PNG/JPG），直接返回URL：

```javascript
// 显示图表图片
<img src={response.chart_url} alt="图表" />
```

---

## 📊 图表类型自动判断

根据查询结果自动选择图表类型：

| 数据特征 | 图表类型 | 说明 |
|---------|---------|------|
| 单个数值 | **指标卡片** | 如：系统数量 |
| 时间序列 | **折线图** | 如：近7天系统数量趋势 |
| 分类对比 | **柱状图** | 如：各城市系统数量 |
| 百分比 | **饼图** | 如：各类型系统占比 |
| 多维数据 | **表格** | 如：系统列表 |

---

## 🎯 完整示例

### 用户问题："垂管系统数量"

**Claude Code的操作**：

1. **读取配置文件**
   ```bash
   read skills/sqlbot-knowledge/SCHEMA.md
   read skills/sqlbot-knowledge/TERMINOLOGY.md
   ```

2. **生成SQL**
   ```sql
   SELECT COUNT(*) FROM t_sys WHERE type = '省垂'
   ```

3. **调用SQLBot API**
   ```bash
   curl -X POST "http://localhost:8000/claude-code/query" \
     -H "Content-Type: application/json" \
     -d '{
       "sql": "SELECT COUNT(*) FROM t_sys WHERE type = '\''省垂'\''",
       "question": "垂管系统数量",
       "chat_id": 123,
       "limit": 1000
     }'
   ```

4. **SQLBot执行并返回**
   ```json
   {
     "success": true,
     "data": [[5]],
     "fields": [{"name": "count", "type": "int"}],
     "row_count": 1,
     "chart_url": "data:application/json;base64,eyJjaGFydFR5cGUiOiJiYXIiLCJ4QXhpcyI6WyL+WxhumXtCJdLCJ5QXhpcyI6WzVdfQ==",
     "chart_type": "bar",
     "error": null
   }
   ```

5. **返回给用户**
   ```
   垂管系统数量为5个

   📊 图表：
   [前端渲染柱状图]
   ```

---

## 🚀 实施步骤

### 步骤1：创建Claude Code桥接层（1小时）

**文件**：`apps/claude_code_bridge/api/claude_code.py`

参考上面的代码，创建API接口。

### 步骤2：注册路由（15分钟）

修改 `backend/main.py`，注册路由。

### 步骤3：测试API（30分钟）

```bash
# 启动SQLBot后端
cd /Users/guchuan/codespace/SQLBot/backend
python main.py

# 测试API
curl -X POST "http://localhost:8000/claude-code/query" \
  -H "Content-Type: application/json" \
  -d '{
    "sql": "SELECT COUNT(*) FROM t_sys",
    "question": "系统数量",
    "limit": 1000
  }'
```

### 步骤4：配置Claude Code（1小时）

给Claude Code配置完整的Prompt（如上）。

### 步骤5：前端集成（1小时）

实现图表渲染逻辑（解码base64并渲染ECharts/G2）。

---

## 📊 总架构图

```
┌─────────────────────────────────────────────────────┐
│              前端（React）                     │
│                                                 │
│  ├─ 用户提问                                    │
│  ├─ 显示结果                                    │
│  └─ 渲染图表（ECharts/G2）                     │
└───────────────────┬───────────────────────────────┘
                    │ HTTP
                    ▼
┌─────────────────────────────────────────────────────┐
│           Claude Code Agent              │
│                                                 │
│  1. 读取MD文件                                 │
│  2. 生成SQL                                    │
│  3. 调用SQLBot API                             │
│  4. 返回结果                                    │
└───────────────────┬───────────────────────────────┘
                    │ HTTP调用
                    ▼
┌─────────────────────────────────────────────────────┐
│              SQLBot 后端                     │
│                                                 │
│  ┌─────────────────────────────────────────┐     │
│  │  POST /claude-code/query             │     │
│  ├─────────────────────────────────────────┤     │
│  │  - 接收SQL                            │     │
│  │  - 执行SQL                             │     │
│  │  - 生成图表                            │     │
│  │  - 返回结果                            │     │
│  └─────────────────────────────────────────┘     │
└───────────────────┬───────────────────────────────┘
                    │ SQL
                    ▼
┌─────────────────────────────────────────────────────┐
│              PostgreSQL 数据库                 │
└─────────────────────────────────────────────────────┘
```

---

## 🎯 总结

### 核心要点

1. **Claude Code生成SQL**：通过读取MD文件
2. **调用SQLBot API**：`POST /claude-code/query`
3. **SQLBot执行并生成图表**：返回图表URL或base64
4. **前端渲染图表**：解码并显示

### 工作量

| 步骤 | 任务 | 时间 |
|------|------|------|
| 第1步 | 创建Claude Code桥接层 | 1 小时 |
| 第2步 | 注册路由 | 15 分钟 |
| 第3步 | 测试API | 30 分钟 |
| 第4步 | 配置Claude Code | 1 小时 |
| 第5步 | 前端集成 | 1 小时 |
| **总计** | | **3.5 小时** |

---

**最后更新**：2026-02-08
