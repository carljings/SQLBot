# Claude Code + SQLBot 整合方案 v6（SQLBot极简版）

> 核心思路：SQLBot只保留前端 + 执行层 + 图表生成，所有智能工作交给Claude Code
> 设计时间：2026-02-08

---

## 📋 核心思路

### SQLBot职责拆分

| 模块 | 之前（SQLBot） | 现在（方案F） |
|------|---------------|--------------|
| **前端** | SQLBot前端 | ✅ **保留** |
| **RAG检索** | SQLBot后端 | ⬅️ **Claude Code** |
| **Prompt构建** | SQLBot后端 | ⬅️ **Claude Code** |
| **SQL生成** | SQLBot LLM | ⬅️ **Claude Code** |
| **SQL执行** | SQLBot后端 | ✅ **保留** |
| **图表生成** | SQLBot后端 | ✅ **保留** |
| **历史记录** | SQLBot后端 | ✅ **保留** |

### 方案F架构

```
┌─────────────────────────────────────────────────────┐
│                 SQLBot 前端                     │
│              (React - 保留原样）                  │
│                                                  │
│  用户在前端输入问题："垂管系统数量"               │
└───────────────────┬───────────────────────────────┘
                    │ HTTP/WebSocket
                    ▼
┌─────────────────────────────────────────────────────┐
│              SQLBot 后端（极简版）           │
│              (FastAPI - 只保留执行层）         │
│                                                  │
│  ┌─────────────────────────────────────────┐   │
│  │      HTTP接收用户问题                  │   │
│  │      POST /chat/question               │   │
│  ├─────────────────────────────────────────┤   │
│  │  1. 接收用户问题                        │   │
│  │  2. 转发给Claude Code                  │   │
│  │  3. 等待Claude Code返回SQL            │   │
│  │  4. 执行SQL                             │   │
│  │  5. 生成图表                            │   │
│  │  6. 保存历史记录                        │   │
│  │  7. 返回结果和图表                      │   │
│  └─────────────────────────────────────────┘   │
│                                                  │
│  ┌─────────────────────────────────────────┐   │
│  │      数据访问层（保留）               │   │
│  ├─→ SQL 执行                              │   │
│  ├─→ 结果格式化                            │   │
│  ├─→ 图表生成                              │   │
│  └─→ 历史记录保存                          │   │
│  └─────────────────────────────────────────┘   │
└───────────────────┬───────────────────────────────┘
                    │ 调用Claude Code（HTTP）
                    ▼
┌─────────────────────────────────────────────────────┐
│           Claude Code Agent              │
│           （通过OpenClaw管理）                  │
│                                                  │
│  步骤1：接收SQLBot的用户问题                 │
│                                                  │
│  步骤2：RAG检索                             │
│  ├─ 读取 skills/sqlbot-knowledge/SCHEMA.md     │
│  ├─ 读取 skills/sqlbot-knowledge/TERMINOLOGY.md│
│  ├─ 读取 skills/sqlbot-knowledge/EXAMPLES.md   │
│  └─ 读取 skills/sqlbot-knowledge/RELATIONS.md  │
│                                                  │
│  步骤3：Prompt构建                           │
│  ├─ 组合Schema                             │
│  ├─ 注入相关Terminology                    │
│  ├─ 注入相关Examples                       │
│  └─ 注入自定义Prompt                        │
│                                                  │
│  步骤4：生成SQL                              │
│  └─ 基于以上Prompt生成SQL                   │
│                                                  │
│  步骤5：返回SQL给SQLBot                       │
│                                                  │
└─────────────────────────────────────────────────────┘
                    │ 读取配置文件
                    ▼
┌─────────────────────────────────────────────────────┐
│           Skill目录（MD文件）                    │
│           (Claude Code直接读取）                  │
│                                                  │
│  📄 skills/sqlbot-knowledge/                     │
│    ├─ SCHEMA.md              (表结构)          │
│    ├─ TERMINOLOGY.md         (术语库)          │
│    ├─ EXAMPLES.md            (SQL示例)         │
│    ├─ PROMPT.md              (自定义Prompt)   │
│    └─ RELATIONS.md           (表关系)          │
└─────────────────────────────────────────────────────┘
                    │ 配置同步
                    ▼
┌─────────────────────────────────────────────────────┐
│              SQLBot 数据库                 │
│                                                  │
│  ├─→ 业务数据表（苏政源一本账）                │
│  ├─→ terminology (术语库)                    │
│  ├─→ data_training (SQL示例)                │
│  ├─→ custom_prompt (自定义Prompt)            │
│  └─→ core_table, core_field (表结构)        │
└─────────────────────────────────────────────────────┘
```

---

## 🔧 实施步骤

### 阶段 1：SQLBot配置同步到MD（已完成的方案D）

**文件**：`apps/config_sync/sync_config_to_md.py`

**功能**：
- 从数据库读取Schema/Terminology/Examples/Prompt/Relations
- 写入到MD文件
- 定期同步（每小时/每天）

**已创建**：
- ✅ `/Users/guchuan/codespace/SQLBot/backend/apps/config_sync/sync_config_to_md.py`
- ✅ `/Users/guchuan/codespace/SQLBot/skills/sqlbot-knowledge/SKILL.md`

---

### 阶段 2：创建SQLBot简化API（1小时）

**文件**：`apps/claude_bridge/api/claude_bridge.py`

**新增代码**：

```python
# apps/claude_bridge/api/claude_bridge.py

"""
SQLBot简化桥接层
用途：接收用户问题，调用Claude Code，执行SQL，生成图表
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session
from datetime import datetime
import httpx

from apps.db.db import exec_sql
from apps.chat.models.chat_model import ChatRecord, Chat
from apps.template.generate_chart.generator import generate_chart
from common.core.deps import SessionDep, CurrentUser

router = APIRouter(tags=["Claude Bridge"], prefix="/claude-bridge")

# Claude Code服务地址（OpenClaw Gateway）
CLAUDE_CODE_URL = "http://localhost:6800/v1/chat/completions"
CLAUDE_CODE_API_KEY = "your-openclaw-token-here"


@router.post("/chat", summary="用户提问（通过Claude Code生成SQL）")
async def chat_with_claude_code(
    session: SessionDep,
    current_user: CurrentUser,
    question: str,
    chat_id: Optional[int] = None,
    datasource_id: Optional[int] = None
):
    """
    用户提问 → 调用Claude Code → 获取SQL → 执行SQL → 生成图表

    Args:
        session: 数据库Session
        current_user: 当前用户
        question: 用户问题
        chat_id: 聊天ID（可选，如果没有则创建新的）
        datasource_id: 数据源ID（可选）

    Returns:
        {
            "success": true/false,
            "sql": "...",
            "data": [...],
            "fields": [...],
            "row_count": 10,
            "chart_url": "...",
            "chart_type": "bar",
            "error": null
        }
    """
    # 步骤1：调用Claude Code生成SQL
    sql = await _call_claude_code_for_sql(question)

    if not sql:
        return {
            "success": False,
            "sql": None,
            "data": [],
            "fields": [],
            "row_count": 0,
            "chart_url": None,
            "chart_type": None,
            "error": "Claude Code未生成SQL"
        }

    # 步骤2：执行SQL
    try:
        result = exec_sql(session, sql, datasource_id)

        # 步骤3：格式化数据
        fields = []
        data = []

        if result and len(result) > 0:
            # 获取字段名
            fields = [{"name": col, "type": str(type(val).__name__)} 
                     for col, val in zip(result[0].keys(), result[0].values())]

            # 转换数据
            for row in result:
                data.append([val for val in row.values()])

        # 步骤4：生成图表
        chart_url = None
        chart_type = None

        if len(data) > 0 and len(fields) >= 1:
            chart_config = generate_chart(
                fields=fields,
                data=data,
                question=question,
                chart_type="auto"
            )

            if chart_config:
                chart_url = _save_chart(chart_config)
                chart_type = chart_config.get("type")

        # 步骤5：保存历史记录
        if chat_id is None:
            # 创建新的chat
            new_chat = Chat(
                brief=question[:50],
                datasource=datasource_id,
                create_by=current_user.id,
                create_time=datetime.now()
            )
            session.add(new_chat)
            session.flush()
            session.refresh(new_chat)
            chat_id = new_chat.id

        # 保存chat_record
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
            "sql": sql,
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
            "sql": sql,
            "data": [],
            "fields": [],
            "row_count": 0,
            "chart_url": None,
            "chart_type": None,
            "error": str(e)
        }


async def _call_claude_code_for_sql(question: str) -> Optional[str]:
    """
    调用Claude Code生成SQL

    Args:
        question: 用户问题

    Returns:
        str: 生成的SQL（如果失败则返回None）
    """
    try:
        # 构建系统Prompt（让Claude Code知道如何工作）
        system_prompt = """你是苏政源一本账的智能问数Agent。你的工作流程如下：

1. 接收用户问题
2. 读取配置文件：
   - read skills/sqlbot-knowledge/SCHEMA.md
   - read skills/sqlbot-knowledge/TERMINOLOGY.md
   - read skills/sqlbot-knowledge/EXAMPLES.md
   - read skills/sqlbot-knowledge/PROMPT.md
3. 查找相关信息：
   - 从SCHEMA.md中找到相关表
   - 从TERMINOLOGY.md中找到相关术语（如"垂管系统"→"省垂"）
   - 从EXAMPLES.md中找到相似SQL示例
4. 构建Prompt（自己组合以上信息）
5. 生成SQL
6. 只返回SQL，不要解释

示例：
用户问题：垂管系统数量
你的回答：SELECT COUNT(*) FROM t_sys WHERE type = '省垂'
"""

        # 调用OpenClaw Gateway（兼容OpenAI API）
        async with httpx.AsyncClient() as client:
            response = await client.post(
                CLAUDE_CODE_URL,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {CLAUDE_CODE_API_KEY}"
                },
                json={
                    "model": "claude-code",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": question}
                    ],
                    "temperature": 0,
                    "max_tokens": 4096
                },
                timeout=60.0
            )

            if response.status_code != 200:
                print(f"Error: Claude Code API returned {response.status_code}")
                print(f"Response: {response.text}")
                return None

            result = response.json()

            # 解析SQL
            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0]["message"]["content"]

                # 提取SQL（Claude Code应该只返回SQL）
                import re
                sql_match = re.search(r"```sql\n(.*?)\n```", content, re.DOTALL)

                if sql_match:
                    return sql_match.group(1).strip()
                else:
                    # 如果没有```sql```标记，尝试直接使用
                    return content.strip()

            return None

    except Exception as e:
        print(f"Error calling Claude Code: {e}")
        return None


def _save_chart(chart_config: dict) -> str:
    """
    保存图表配置并返回URL

    Args:
        chart_config: 图表配置（ECharts/G2格式）

    Returns:
        str: 图表URL
    """
    # 复用SQLBot的图表保存逻辑
    import json
    import base64

    chart_json = json.dumps(chart_config)
    chart_base64 = base64.b64encode(chart_json.encode()).decode()

    # 返回图表URL（前端可以解码base64）
    return f"data:application/json;base64,{chart_base64}"
```

---

### 阶段 3：注册路由（15分钟）

**文件**：`backend/main.py`

**修改**：

```python
# backend/main.py

# 导入新的路由
from apps.claude_bridge.api.claude_bridge import router as claude_bridge_router

# 注册路由
app.include_router(claude_bridge_router)
```

---

### 阶段 4：修改前端API调用（30分钟）

**文件**：`frontend/src/services/chat.ts`（示例）

**修改**：

```typescript
// frontend/src/services/chat.ts

export async function sendQuestion(question: string, chatId?: number, datasourceId?: number) {
  // 之前：调用SQLBot的 /chat/question
  // const response = await fetch('/api/chat/question', ...)

  // 现在：调用简化版API
  const response = await fetch('/api/claude-bridge/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      question,
      chat_id: chatId,
      datasource_id: datasourceId,
    }),
  })

  const result = await response.json()

  return {
    success: result.success,
    sql: result.sql,
    data: result.data,
    fields: result.fields,
    rowCount: result.row_count,
    chartUrl: result.chart_url,
    chartType: result.chart_type,
    error: result.error,
  }
}
```

---

### 阶段 5：配置定时同步（15分钟）

**通过系统Cron**：

```bash
# 编辑crontab
crontab -e

# 添加定时任务（每小时同步配置到MD文件）
0 * * * * cd /Users/guchuan/codespace/SQLBot/backend && python3 apps/config_sync/sync_config_to_md.py >> /tmp/sqlbot_sync.log 2>&1
```

---

### 阶段 6：配置Claude Code（30分钟）

**在Claude Code中配置Skill路径**：

```bash
# Claude Code的Prompt（可以通过环境变量或配置文件设置）
export CLAUDE_CODE_SKILLS_PATH="/Users/guchuan/codespace/SQLBot/skills"
```

**或者通过Claude Code的配置文件**（如果支持）。

---

## 🎯 完整工作流程

### 用户操作

1. **在SQLBot前端输入问题**
   ```
   垂管系统数量
   ```

2. **SQLBot后端接收并转发给Claude Code**
   ```
   POST /claude-bridge/chat
   {
     "question": "垂管系统数量"
   }
   ```

3. **Claude Code处理**
   - 读取MD文件（SCHEMA/Terminology/Examples/Prompt）
   - RAG检索相关配置
   - 构建Prompt
   - 生成SQL
   - 返回SQL：`SELECT COUNT(*) FROM t_sys WHERE type = '省垂'`

4. **SQLBot执行SQL并生成图表**
   - 执行SQL
   - 生成图表
   - 保存历史记录

5. **前端显示结果**
   ```
   垂管系统数量为5个
   
   📊 [柱状图]
   ```

---

## 📊 对比其他方案

| 维度 | 方案B | 方案D | 方案E | **方案F** |
|------|-------|-------|-------|---------|
| **SQLBot改动** | 小 | 中 | 极小 | **中** |
| **SQLBot保留** | 100% | 100% | 100% | **前端+执行+图表** |
| **Claude Code角色** | 被动LLM | 主动Agent | 被动LLM | **主动Agent** |
| **RAG检索** | SQLBot | Claude Code | SQLBot | **Claude Code** ✅ |
| **Prompt构建** | SQLBot | Claude Code | SQLBot | **Claude Code** ✅ |
| **SQL生成** | Claude | Claude Code | Claude Code | **Claude Code** ✅ |
| **用户流程** | 不变 | 不变 | 不变 | **不变** ✅ |
| **配置同步** | 不需要 | 需要 | 不需要 | **需要** ✅ |
| **工作量** | 2.5-4.5h | 3h | 2h | **3.5h** |

---

## 🎯 方案F优势

### 1. **SQLBot极简**

只保留：
- ✅ 前端（用户界面）
- ✅ 简化的API（接收问题 → 调用Claude Code → 执行SQL → 生成图表）
- ✅ SQL执行
- ✅ 图表生成
- ✅ 历史记录

不再需要：
- ❌ RAG检索逻辑
- ❌ Prompt构建逻辑
- ❌ LLM调用逻辑
- ❌ Embedding搜索

### 2. **Claude Code完全掌控**

Claude Code负责：
- ✅ RAG检索（读取MD文件）
- ✅ Prompt构建（自己组合）
- ✅ SQL生成（自己推理）

### 3. **可扩展性强**

未来可以在Claude Code中：
- ✅ 添加更复杂的RAG策略
- ✅ 添加多步推理
- ✅ 添加数据洞察
- ✅ 添加自然语言解释

---

## 🚀 实施工作量

| 步骤 | 任务 | 时间 |
|------|------|------|
| 第1步 | SQLBot配置同步到MD（已完成的方案D） | 1.5 小时 |
| 第2步 | 创建SQLBot简化API | 1 小时 |
| 第3步 | 注册路由 | 15 分钟 |
| 第4步 | 修改前端API调用 | 30 分钟 |
| 第5步 | 配置定时同步 | 15 分钟 |
| 第6步 | 配置Claude Code | 30 分钟 |
| 第7步 | 测试验证 | 30 分钟 |
| **总计** | | **4.5 小时** |

---

## 📋 检查清单

### 实施前检查

- [ ] 已启动OpenClaw Gateway
- [ ] 已获取Gateway地址（默认：http://localhost:6800）
- [ ] 已获取Gateway Token（如果需要）
- [ ] 已备份SQLBot数据库
- [ ] 已完成SQLBot配置同步到MD（方案D）

### 实施后检查

- [ ] SQLBot简化API已创建
- [ ] 路由已注册
- [ ] 前端API调用已修改
- [ ] 定时同步已配置
- [ ] Claude Code已配置
- [ ] SQLBot后端启动成功
- [ ] 前端可以正常访问
- [ ] 测试查询正常
- [ ] 图表正常生成

---

## 🎯 总结

### 方案F核心特点

1. **SQLBot极简**：只保留前端 + 执行层 + 图表生成
2. **Claude Code全掌控**：RAG检索、Prompt构建、SQL生成全部交给Claude Code
3. **用户流程不变**：在SQLBot前端输入问题，看到结果和图表
4. **可扩展性强**：Claude Code可以添加更复杂的逻辑
5. **需要配置同步**：定期将SQLBot配置同步到MD文件

### 适合场景

✅ **适合方案F的场景**：
- 希望SQLBot极简
- 希望Claude Code完全掌控智能部分
- 需要在Claude Code中添加复杂逻辑
- 可以接受配置延迟（每小时/每天同步）

❌ **不适合方案F的场景**：
- 需要实时配置同步
- 不希望Claude Code处理所有逻辑
- SQLBot配置频繁更新（秒级）

---

## 🚀 下一步

**实施建议**：
1. 先实施方案D（配置同步到MD）
2. 完成步骤1-4（创建简化API）
3. 配置定时同步和Claude Code
4. 测试验证

---

**最后更新**：2026-02-08
