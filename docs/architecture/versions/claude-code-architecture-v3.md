# Claude Code + SQLBot 整合方案 v3（配置固化版）

> 核心Agent：Claude Code（读取MD文件）
> 展示层：SQLBot（保留原样）
> 配置源：SQLBot数据库 → 同步到MD文件
> 设计时间：2026-02-08

---

## 📋 核心思路

### 为什么固化到MD文件？

| 方案 | 工作量 | 优势 | 劣势 |
|------|-------|------|------|
| **方案B**（API主动查询） | 5.5小时 | 灵活、实时 | 需要开发API |
| **方案C**（SQLBot换LLM） | 2.5-4.5小时 | 简单、稳定 | Claude被动 |
| **方案D**（配置固化MD） | **2-3小时** | **零API开发、Claude直接读文件** | 配置有延迟 |

**方案D优势**：
- ✅ **零代码改动**：不需要开发API
- ✅ **Claude Code直接读文件**：简单、高效
- ✅ **版本控制**：MD文件可以git跟踪
- ✅ **离线可用**：不依赖SQLBot后端运行

---

## 🏗️ 架构设计

```
┌─────────────────────────────────────────────────────┐
│                 SQLBot 前端                     │
│              (React - 保留原样）                  │
└───────────────────┬───────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────┐
│              SQLBot 后端                     │
│              (FastAPI - 保留原样）              │
│                                                  │
│  ┌─────────────────────────────────────────┐   │
│  │      定期同步配置到MD文件                │   │
│  │      （新增：sync_config_to_md.py）      │   │
│  ├─────────────────────────────────────────┤   │
│  │  1. 从数据库读取Schema                   │   │
│  │  2. 从数据库读取Terminology              │   │
│  │  3. 从数据库读取SQL Examples             │   │
│  │  4. 从数据库读取Custom Prompt            │   │
│  │  5. 写入到Skill目录的MD文件              │   │
│  └─────────────────────────────────────────┘   │
└───────────────────┬───────────────────────────────┘
                    │ 定期同步（每小时/每天）
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
└───────────────────┬───────────────────────────────┘
                    │ Claude Code读取
                    ▼
┌─────────────────────────────────────────────────────┐
│           Claude Code Agent              │
│                                                  │
│  1. 接收用户问题                                 │
│  2. 读取 SCHEMA.md                              │
│  3. 读取 TERMINOLOGY.md（搜索相关术语）          │
│  4. 读取 EXAMPLES.md                             │
│  5. 读取 PROMPT.md                               │
│  6. 自己构建Prompt                               │
│  7. 自己生成SQL                                  │
│  8. 调用SQLBot API执行SQL（保留）               │
│  9. 返回结果给用户                               │
└─────────────────────────────────────────────────────┘
```

---

## 📁 目录结构

```
/Users/guchuan/codespace/SQLBot/
├── backend/
│   ├── apps/
│   │   └── config_sync/              # 新增：配置同步模块
│   │       ├── __init__.py
│   │       ├── sync_config_to_md.py  # 主同步脚本
│   │       └── models.py             # 数据模型
│   └── main.py                       # 注册路由
│
├── skills/
│   └── sqlbot-knowledge/             # 新增：Skill目录
│       ├── SKILL.md                  # Skill配置（Claude Code读取）
│       ├── SCHEMA.md                 # 表结构（自动生成）
│       ├── TERMINOLOGY.md            # 术语库（自动生成）
│       ├── EXAMPLES.md               # SQL示例（自动生成）
│       ├── PROMPT.md                 # 自定义Prompt（自动生成）
│       └── RELATIONS.md             # 表关系（自动生成）
│
└── frontend/                         # 保留原样
```

---

## 🔧 实施步骤

### 阶段 1：创建配置同步脚本（1.5小时）

**文件**：`apps/config_sync/sync_config_to_md.py`

```python
# apps/config_sync/sync_config_to_md.py

"""
SQLBot配置同步到MD文件
用途：让Claude Code直接读取配置，无需API调用
"""

import os
from datetime import datetime
from typing import List, Optional
from sqlalchemy import and_, select
from sqlmodel import Session

from apps.datasource.crud.datasource import get_ds, get_table_schema
from apps.terminology.curd.terminology import get_all_terminology
from apps.data_training.curd.data_training import get_training_template
from apps.datasource.models.datasource import CoreDatasource
from common.core.db import engine

# Skill目录路径
SKILL_DIR = "/Users/guchuan/codespace/SQLBot/skills/sqlbot-knowledge"


def sync_schema_to_md(session: Session, datasource_id: int, output_path: str):
    """
    同步Schema到MD文件

    Args:
        session: 数据库Session
        datasource_id: 数据源ID
        output_path: 输出MD文件路径
    """
    print(f"[{datetime.now()}] 同步Schema...")

    ds = get_ds(session, datasource_id)
    if not ds:
        print(f"错误：数据源 {datasource_id} 不存在")
        return

    # 获取Schema
    schema_str = get_table_schema(
        session=session,
        current_user=None,  # 同步脚本不需要用户权限
        ds=ds,
        question="",  # 不用embedding过滤
        embedding=False
    )

    # 写入MD文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"# SQLBot Schema - {ds.name}\n\n")
        f.write(f"**数据源ID**: {datasource_id}\n")
        f.write(f"**数据源名称**: {ds.name}\n")
        f.write(f"**数据库类型**: {ds.type_name}\n")
        f.write(f"**同步时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("---\n\n")
        f.write(schema_str)

    print(f"✓ Schema已同步到: {output_path}")


def sync_terminology_to_md(session: Session, output_path: str, oid: int = 1):
    """
    同步术语库到MD文件

    Args:
        session: 数据库Session
        output_path: 输出MD文件路径
        oid: 组织ID
    """
    print(f"[{datetime.now()}] 同步术语库...")

    # 获取所有术语
    terminologies = get_all_terminology(session=session, oid=oid)

    # 写入MD文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"# SQLBot 术语库\n\n")
        f.write(f"**组织ID**: {oid}\n")
        f.write(f"**术语数量**: {len(terminologies)}\n")
        f.write(f"**同步时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("---\n\n")

        for term in terminologies:
            f.write(f"## {term.word}\n\n")
            f.write(f"**描述**: {term.description}\n\n")

            if term.other_words and len(term.other_words) > 0:
                f.write(f"**同义词**: {', '.join(term.other_words)}\n\n")

            if term.datasource_ids and len(term.datasource_ids) > 0:
                f.write(f"**关联数据源ID**: {', '.join(map(str, term.datasource_ids))}\n\n")

            if term.enabled is not None:
                f.write(f"**状态**: {'启用' if term.enabled else '禁用'}\n\n")

            f.write("---\n\n")

    print(f"✓ 术语库已同步到: {output_path}")


def sync_examples_to_md(session: Session, datasource_id: int, output_path: str):
    """
    同步SQL示例到MD文件

    Args:
        session: 数据库Session
        datasource_id: 数据源ID
        output_path: 输出MD文件路径
    """
    print(f"[{datetime.now()}] 同步SQL示例...")

    # 获取SQL示例
    examples = get_training_template(
        session=session,
        datasource_id=datasource_id,
        question=""
    )

    # 写入MD文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"# SQLBot SQL示例（Few-shot）\n\n")
        f.write(f"**数据源ID**: {datasource_id}\n")
        f.write(f"**示例数量**: {len(examples) if examples else 0}\n")
        f.write(f"**同步时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("---\n\n")

        if examples:
            for i, example in enumerate(examples, 1):
                f.write(f"## 示例 {i}\n\n")

                if hasattr(example, 'question') and example.question:
                    f.write(f"**问题**: {example.question}\n\n")

                if hasattr(example, 'sql') and example.sql:
                    f.write(f"**SQL**:\n```sql\n{example.sql}\n```\n\n")

                if hasattr(example, 'explanation') and example.explanation:
                    f.write(f"**说明**: {example.explanation}\n\n")

                f.write("---\n\n")

    print(f"✓ SQL示例已同步到: {output_path}")


def sync_prompt_to_md(session: Session, datasource_id: int, output_path: str):
    """
    同步自定义Prompt到MD文件

    Args:
        session: 数据库Session
        datasource_id: 数据源ID
        output_path: 输出MD文件路径
    """
    print(f"[{datetime.now()}] 同步自定义Prompt...")

    from sqlbot_xpack.custom_prompt.curd.custom_prompt import find_custom_prompts

    prompts = find_custom_prompts(
        session=session,
        datasource_id=datasource_id,
        enabled=True
    )

    # 写入MD文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"# SQLBot 自定义Prompt\n\n")
        f.write(f"**数据源ID**: {datasource_id}\n")
        f.write(f"**Prompt数量**: {len(prompts) if prompts else 0}\n")
        f.write(f"**同步时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("---\n\n")

        if prompts:
            for i, prompt in enumerate(prompts, 1):
                f.write(f"## Prompt {i}\n\n")

                if hasattr(prompt, 'type') and prompt.type:
                    f.write(f"**类型**: {prompt.type}\n\n")

                if hasattr(prompt, 'content') and prompt.content:
                    f.write(f"**内容**:\n```\n{prompt.content}\n```\n\n")

                if hasattr(prompt, 'enabled') and prompt.enabled is not None:
                    f.write(f"**状态**: {'启用' if prompt.enabled else '禁用'}\n\n")

                f.write("---\n\n")

    print(f"✓ 自定义Prompt已同步到: {output_path}")


def sync_relations_to_md(session: Session, datasource_id: int, output_path: str):
    """
    同步表关系到MD文件

    Args:
        session: 数据库Session
        datasource_id: 数据源ID
        output_path: 输出MD文件路径
    """
    print(f"[{datetime.now()}] 同步表关系...")

    ds = get_ds(session, datasource_id)
    if not ds:
        print(f"错误：数据源 {datasource_id} 不存在")
        return

    # 获取表关系
    relations = ds.table_relation or []

    # 写入MD文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"# SQLBot 表关系（外键）\n\n")
        f.write(f"**数据源ID**: {datasource_id}\n")
        f.write(f"**数据源名称**: {ds.name}\n")
        f.write(f"**关系数量**: {len(relations) if relations else 0}\n")
        f.write(f"**同步时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("---\n\n")

        if relations and isinstance(relations, list):
            for relation in relations:
                if relation.get("shape") == "edge":
                    source = relation.get("source", {})
                    target = relation.get("target", {})

                    f.write(f"## 外键关系\n\n")
                    f.write(f"- **源表ID**: {source.get('cell')}\n")
                    f.write(f"- **源字段ID**: {source.get('port')}\n")
                    f.write(f"- **目标表ID**: {target.get('cell')}\n")
                    f.write(f"- **目标字段ID**: {target.get('port')}\n")
                    f.write(f"- **关系类型**: {relation.get('shape')}\n\n")
                    f.write("---\n\n")

    print(f"✓ 表关系已同步到: {output_path}")


def sync_all(datasource_id: int = 1, oid: int = 1):
    """
    同步所有配置到MD文件

    Args:
        datasource_id: 数据源ID
        oid: 组织ID
    """
    print(f"\n{'='*60}")
    print(f"开始同步SQLBot配置到MD文件")
    print(f"{'='*60}\n")

    # 确保目录存在
    os.makedirs(SKILL_DIR, exist_ok=True)

    with Session(engine) as session:
        # 同步各个模块
        sync_schema_to_md(
            session=session,
            datasource_id=datasource_id,
            output_path=os.path.join(SKILL_DIR, "SCHEMA.md")
        )

        sync_terminology_to_md(
            session=session,
            output_path=os.path.join(SKILL_DIR, "TERMINOLOGY.md"),
            oid=oid
        )

        sync_examples_to_md(
            session=session,
            datasource_id=datasource_id,
            output_path=os.path.join(SKILL_DIR, "EXAMPLES.md")
        )

        sync_prompt_to_md(
            session=session,
            datasource_id=datasource_id,
            output_path=os.path.join(SKILL_DIR, "PROMPT.md")
        )

        sync_relations_to_md(
            session=session,
            datasource_id=datasource_id,
            output_path=os.path.join(SKILL_DIR, "RELATIONS.md")
        )

    print(f"\n{'='*60}")
    print(f"✓ 所有配置已同步完成！")
    print(f"{'='*60}\n")
    print(f"输出目录: {SKILL_DIR}\n")


if __name__ == "__main__":
    # 手动执行同步
    sync_all(datasource_id=1, oid=1)
```

---

### 阶段 2：创建SKILL.md（30分钟）

**文件**：`skills/sqlbot-knowledge/SKILL.md`

```markdown
# SKILL.md - SQLBot知识库

**用途**：让Claude Code直接读取SQLBot配置，无需API调用

## 📁 目录结构

```
sqlbot-knowledge/
├── SKILL.md              # 本文件（Skill配置）
├── SCHEMA.md             # 表结构
├── TERMINOLOGY.md        # 术语库
├── EXAMPLES.md           # SQL示例（Few-shot）
├── PROMPT.md             # 自定义Prompt
└── RELATIONS.md          # 表关系（外键）
```

---

## 🎯 Claude Code使用指南

### 工作流程

当用户问SQL相关问题时，Claude Code应该：

1. **读取SCHEMA.md**
   ```bash
   read skills/sqlbot-knowledge/SCHEMA.md
   ```

2. **读取TERMINOLOGY.md**（搜索相关术语）
   ```bash
   read skills/sqlbot-knowledge/TERMINOLOGY.md
   ```

3. **读取EXAMPLES.md**
   ```bash
   read skills/sqlbot-knowledge/EXAMPLES.md
   ```

4. **读取PROMPT.md**
   ```bash
   read skills/sqlbot-knowledge/PROMPT.md
   ```

5. **构建Prompt**（自己组合以上信息）

6. **生成SQL**

7. **执行SQL**（调用SQLBot API或直接连接数据库）

---

## 📋 配置文件说明

### SCHEMA.md

**内容**：
- 数据源信息（ID、名称、类型）
- 完整表结构（表名、字段名、字段类型、字段注释）
- 表注释

**用途**：Claude Code了解数据库结构

**示例**：
```markdown
# SQLBot Schema - 一本账

**数据源ID**: 1
**数据源名称**: 一本账
**数据库类型**: PostgreSQL
**同步时间**: 2026-02-08 10:30:00

---

【DB_ID】一本账
【Schema】

# Table: t_sys, 系统表
[
(id:BIGINT, ID),
(name:VARCHAR, 系统名称),
(type:VARCHAR, 系统类型),
(city:VARCHAR, 城市),
(year:INTEGER, 年份)
]
```

---

### TERMINOLOGY.md

**内容**：
- 术语列表
- 术语描述
- 同义词
- 关联数据源

**用途**：Claude Code理解业务术语

**示例**：
```markdown
# SQLBot 术语库

**组织ID**: 1
**术语数量**: 10
**同步时间**: 2026-02-08 10:30:00

---

## 垂管系统

**描述**: 由省级部门直接管理的系统

**同义词**: 省垂, 垂直管理, 垂直业务系统

**关联数据源ID**: 1

**状态**: 启用

---
```

---

### EXAMPLES.md

**内容**：
- SQL示例（Few-shot学习）
- 问题与SQL的对应关系
- SQL说明

**用途**：Claude Code学习SQL生成模式

**示例**：
```markdown
# SQLBot SQL示例（Few-shot）

**数据源ID**: 1
**示例数量**: 5
**同步时间**: 2026-02-08 10:30:00

---

## 示例 1

**问题**: 系统数量

**SQL**:
```sql
SELECT COUNT(*) FROM t_sys
```

**说明**: 查询系统总数

---

## 示例 2

**问题**: 垂管系统数量

**SQL**:
```sql
SELECT COUNT(*)
FROM t_sys
WHERE type = '省垂'
```

**说明**: 查询垂管系统数量（使用术语"省垂"）

---
```

---

### PROMPT.md

**内容**：
- 自定义Prompt模板
- 系统级和用户级Prompt

**用途**：Claude Code使用业务特定的Prompt风格

**示例**：
```markdown
# SQLBot 自定义Prompt

**数据源ID**: 1
**Prompt数量**: 2
**同步时间**: 2026-02-08 10:30:00

---

## Prompt 1

**类型**: system

**内容**:
```
你是一位专业的SQL查询专家，擅长将自然语言转换为SQL语句。

注意事项：
1. 只生成SQL，不要解释
2. 使用COUNT(*)时，确保正确统计
3. 涉及术语时，使用字段精确匹配
4. 多表查询时，使用JOIN而非子查询
```

**状态**: 启用

---

## Prompt 2

**类型**: user

**内容**:
```
请根据以下信息生成SQL：

表结构：
{{SCHEMA}}

术语：
{{TERMINOLOGY}}

参考示例：
{{EXAMPLES}}

用户问题：
{{QUESTION}}
```

**状态**: 启用

---
```

---

### RELATIONS.md

**内容**：
- 表之间的外键关系
- 关联字段映射

**用途**：Claude Code了解表之间的关联

**示例**：
```markdown
# SQLBot 表关系（外键）

**数据源ID**: 1
**数据源名称**: 一本账
**关系数量**: 3
**同步时间**: 2026-02-08 10:30:00

---

## 外键关系

- **源表ID**: 1
- **源字段ID**: 5
- **目标表ID**: 2
- **目标字段ID**: 1
- **关系类型**: edge

---

## 外键关系

- **源表ID**: 1
- **源字段ID**: 6
- **目标表ID**: 3
- **目标字段ID**: 1
- **关系类型**: edge

---
```

---

## 🔧 配置同步

### 手动同步

```bash
cd /Users/guchuan/codespace/SQLBot/backend
python apps/config_sync/sync_config_to_md.py
```

### 定时同步（Cron）

在SQLBot后端注册一个定时任务：

```python
# backend/main.py

from apps.config_sync.sync_config_to_md import sync_all

# 每小时同步一次
@router.on_event("startup")
async def schedule_config_sync():
    import asyncio
    while True:
        try:
            await asyncio.to_thread(sync_all, datasource_id=1, oid=1)
            print("✓ 配置同步完成")
        except Exception as e:
            print(f"✗ 配置同步失败: {e}")

        await asyncio.sleep(3600)  # 1小时
```

或者通过系统cron：

```bash
# 每小时同步一次
0 * * * * cd /Users/guchuan/codespace/SQLBot/backend && python apps/config_sync/sync_config_to_md.py >> /tmp/sqlbot_sync.log 2>&1
```

---

## 🎯 Claude Code示例Prompt

```markdown
你是苏政源一本账的智能问数Agent。你的工作流程如下：

1. 接收用户问题（例如："垂管系统数量"）

2. 读取配置文件：
   - read skills/sqlbot-knowledge/SCHEMA.md
   - read skills/sqlbot-knowledge/TERMINOLOGY.md
   - read skills/sqlbot-knowledge/EXAMPLES.md
   - read skills/sqlbot-knowledge/PROMPT.md

3. 查找相关信息：
   - 从SCHEMA.md中找到相关表
   - 从TERMINOLOGY.md中找到相关术语（如"垂管系统"→"省垂"）
   - 从EXAMPLES.md中找到相似SQL示例

4. 构建Prompt：
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

   用户问题：垂管系统数量

   生成SQL：
   ```

5. 生成SQL（基于以上信息）

6. 执行SQL并返回结果

---
```

---

## 📊 优势

相比API方案：

| 维度 | API方案 | MD文件方案 |
|------|--------|-----------|
| **开发工作量** | 5.5小时 | **2-3小时** |
| **代码改动** | 需要开发API | **零代码改动** |
| **Claude Code使用** | HTTP请求 | **直接读文件** |
| **性能** | 网络调用 | **本地读取** |
| **版本控制** | 数据库不可控 | **Git跟踪** |
| **离线可用** | 否 | **是** |

---

## ⚠️ 注意事项

### 配置延迟

- **同步频率**：建议每小时或每天同步一次
- **手动触发**：可以在SQLBot后台添加"同步配置"按钮
- **配置更新**：当在SQLBot中修改配置后，记得手动同步

### 数据权限

- 同步脚本不需要用户权限（内部系统）
- 确保Skill目录有读取权限

### Claude Code配置

- 确保Claude Code可以访问Skill目录
- 在Claude Code的Prompt中指定Skill路径

---

## 🚀 下一步

1. 创建同步脚本 `apps/config_sync/sync_config_to_md.py`
2. 创建Skill目录 `skills/sqlbot-knowledge/`
3. 手动执行同步测试
4. 配置定时同步任务
5. 在Claude Code中配置Skill路径
6. 测试端到端流程

---

**最后更新**: 2026-02-08
```

---

### 阶段 3：注册定时同步任务（30分钟）

**方式 1：通过SQLBot后端注册**

```python
# backend/main.py

from apps.config_sync.sync_config_to_md import sync_all
import asyncio

@app.on_event("startup")
async def start_config_sync():
    """启动配置同步任务"""
    async def sync_loop():
        while True:
            try:
                print("[ConfigSync] 开始同步配置...")
                await asyncio.to_thread(sync_all, datasource_id=1, oid=1)
                print("[ConfigSync] ✓ 配置同步完成")
            except Exception as e:
                print(f"[ConfigSync] ✗ 同步失败: {e}")

            # 每小时同步一次
            await asyncio.sleep(3600)

    # 启动后台任务
    asyncio.create_task(sync_loop())
```

**方式 2：通过系统Cron**

```bash
# 编辑crontab
crontab -e

# 添加定时任务（每小时同步）
0 * * * * cd /Users/guchuan/codespace/SQLBot/backend && python apps/config_sync/sync_config_to_md.py >> /tmp/sqlbot_sync.log 2>&1
```

---

### 阶段 4：测试验证（30分钟）

#### 测试1：手动同步

```bash
cd /Users/guchuan/codespace/SQLBot/backend
python apps/config_sync/sync_config_to_md.py
```

**预期输出**：
```
============================================================
开始同步SQLBot配置到MD文件
============================================================

[2026-02-08 10:30:00] 同步Schema...
✓ Schema已同步到: /Users/guchuan/codespace/SQLBot/skills/sqlbot-knowledge/SCHEMA.md

[2026-02-08 10:30:01] 同步术语库...
✓ 术语库已同步到: /Users/guchuan/codespace/SQLBot/skills/sqlbot-knowledge/TERMINOLOGY.md

[2026-02-08 10:30:02] 同步SQL示例...
✓ SQL示例已同步到: /Users/guchuan/codespace/SQLBot/skills/sqlbot-knowledge/EXAMPLES.md

[2026-02-08 10:30:03] 同步自定义Prompt...
✓ 自定义Prompt已同步到: /Users/guchuan/codespace/SQLBot/skills/sqlbot-knowledge/PROMPT.md

[2026-02-08 10:30:04] 同步表关系...
✓ 表关系已同步到: /Users/guchuan/codespace/SQLBot/skills/sqlbot-knowledge/RELATIONS.md

============================================================
✓ 所有配置已同步完成！
============================================================

输出目录: /Users/guchuan/codespace/SQLBot/skills/sqlbot-knowledge/
```

#### 测试2：检查生成的MD文件

```bash
# 查看Schema文件
cat /Users/guchuan/codespace/SQLBot/skills/sqlbot-knowledge/SCHEMA.md

# 查看术语库文件
cat /Users/guchuan/codespace/SQLBot/skills/sqlbot-knowledge/TERMINOLOGY.md

# 查看SQL示例文件
cat /Users/guchuan/codespace/SQLBot/skills/sqlbot-knowledge/EXAMPLES.md
```

#### 测试3：Claude Code读取文件

在Claude Code中测试：

```bash
# 让Claude Code读取配置文件
read skills/sqlbot-knowledge/SCHEMA.md
read skills/sqlbot-knowledge/TERMINOLOGY.md
```

#### 测试4：端到端测试

1. 用户提问："垂管系统数量"
2. Claude Code读取配置文件
3. Claude Code生成SQL
4. Claude Code执行SQL
5. 返回结果

---

## 📊 工作量评估

| 阶段 | 任务 | 时间 |
|------|------|------|
| 第1步 | 创建配置同步脚本 | 1.5 小时 |
| 第2步 | 创建SKILL.md | 30 分钟 |
| 第3步 | 注册定时同步任务 | 30 分钟 |
| 第4步 | 测试验证 | 30 分钟 |
| **总计** | | **3 小时** |

---

## 🎯 核心优势

### 相比API方案（方案C）

| 维度 | API方案 | MD文件方案 |
|------|--------|-----------|
| **开发工作量** | 5.5小时 | **3小时** ✅ |
| **代码改动** | 需要开发API | **零代码改动** ✅ |
| **Claude Code使用** | HTTP请求 | **直接读文件** ✅ |
| **性能** | 网络调用 | **本地读取** ✅ |
| **版本控制** | 数据库不可控 | **Git跟踪** ✅ |
| **离线可用** | 否 | **是** ✅ |
| **配置延迟** | 实时 | 有延迟（可控） |

---

## 📝 总结

### 方案D核心特点

1. **零API开发**：不需要开发新的API接口
2. **Claude Code直接读文件**：简单、高效
3. **版本控制**：MD文件可以git跟踪
4. **离线可用**：不依赖SQLBot后端运行
5. **定期同步**：每小时或每天自动同步配置

### 适合场景

✅ **适合方案D的场景**：
- SQLBot配置相对稳定
- 配置更新频率低（每天/每周几次）
- 希望减少开发工作量
- 需要版本控制

❌ **不适合方案D的场景**：
- SQLBot配置实时更新（秒级）
- 需要实时配置同步

---

## 🚀 下一步

**实施建议**：
1. 先手动同步一次，验证MD文件生成正确
2. 配置定时同步任务
3. 在Claude Code中测试读取文件
4. 测试端到端流程

---

*文档生成时间：2026-02-08*
