# SQLBot 架构演进对比分析

> **文档版本**: v1.0
> **创建日期**: 2026-02-11
> **维护者**: SQLBot Team

---

## 1. 文档说明

本文档对比 SQLBot **当前架构**（Current Architecture）与 **双方案切换架构**（Switch Architecture）之间的差异，帮助理解系统演进方向。

| 文档 | 版本 | 日期 | 状态 |
|-------|-------|-------|-------|
| [SQLBot-Current-Architecture-Design.md](./SQLBot-Current-Architecture-Design.md) | v1.0 | 2026-02-11 | 当前生产环境 |
| [SQLBot-SWITCH-DETAILED-DESIGN.md](./switch-design/SQLBot-SWITCH-DETAILED-DESIGN.md) | v6.0 | 2026-02-09 | 待实施 |

---

## 2. 架构演进概览

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                       架构演进路径                                    │
└─────────────────────────────────────────────────────────────────────────────────┘

    当前架构 (v1.0)                   双方案架构 (v6.0)
         │                                    │
         ▼                                    ▼
    ┌─────────┐                         ┌─────────────────────────┐
    │ LLM方案  │                         │ LLM方案 │ Claude Code方案│
    │ (单一)  │                         │  (可切换)              │
    └─────────┘                         └─────────────────────────┘
         │                                    │
         │                         ┌──────────▼──────────┐
         │                         │  功能开关/工厂模式  │
         │                         └─────────────────────┘
         │                                    │
         ▼                                    ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │              SQLBot 后端 (执行+图表)                    │
    └─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                         ┌─────────────┐
                         │  前端展示   │
                         └─────────────┘
```

---

## 3. 核心差异对比

### 3.1 SQL 生成方案

| 维度 | 当前架构 | 双方案架构 |
|-----|---------|-----------|
| **方案数量** | 单一方案（仅 LLM） | 双方案（LLM + Claude Code） |
| **切换方式** | 无需切换 | 功能开关动态切换 |
| **设计模式** | 直接调用 | 策略模式 + 工厂模式 |
| **降级机制** | 无 | Claude Code 失败自动回退到 LLM |

### 3.2 上下文获取方式

| 方案 | 当前架构 | 双方案架构 |
|-----|---------|-----------|
| **LLM 方案** | RAG 三路召回 | RAG 三路召回（保持不变） |
| **Claude Code 方案** | 不支持 | 读取 MD 文件获取上下文 |

#### LLM 方案 RAG 检索（两种架构相同）

```
用户问题
    ↓
┌─────────────────────────────────────────────────────────┐
│ 1. 表结构召回 (Phase 0.1)                              │
│    - 计算问题与表名/表注释的余弦相似度                   │
│    - 阈值过滤 (≥ 0.3)                                   │
│    - 返回 Top N 相关表                                  │
└─────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────┐
│ 2. 术语召回 (Phase 0.2)                                 │
│    - 过滤: scope IN ('global', 'table')                 │
│    - 过滤: table_ids && 召回表_ids != {}                │
│    - 计算相似度                                         │
│    - 返回相关术语                                       │
└─────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────┐
│ 3. SQL 示例召回 (Phase 0.3)                             │
│    - 过滤: table_ids && 召回表_ids != {}                │
│    - 计算相似度                                         │
│    - 返回相关 SQL 示例                                  │
└─────────────────────────────────────────────────────────┘
    ↓
上下文合并 → 提示词构建 → LLM 生成 SQL
```

#### Claude Code 方案上下文获取（双方案架构新增）

```
┌─────────────────────────────────────────────────────────────────┐
│                    Claude Code 上下文获取                     │
├─────────────────────────────────────────────────────────────────┤
│                                                          │
│  1. 自动读取 MD 文件                                      │
│     ├── skills/sqlbot-knowledge/SCHEMA.md       (表结构)      │
│     ├── skills/sqlbot-knowledge/TERMINOLOGY.md (术语库)     │
│     ├── skills/sqlbot-knowledge/EXAMPLES.md     (SQL示例)    │
│     ├── skills/sqlbot-knowledge/PROMPT.md       (自定义Prompt)│
│     └── skills/sqlbot-knowledge/RELATIONS.md    (表关系)     │
│                                                          │
│  2. 可选：问题智能增强 (claude_code_query_enhancement_enabled)   │
│     ├── 智能判断问题复杂度                                   │
│     ├── LLM 增强问题表达                                     │
│     └── 缺失信息时反问用户                                   │
│                                                          │
│  3. 生成 SQL                                             │
│     └── 返回 JSON: {sql, chart_type, brief}              │
│                                                          │
└─────────────────────────────────────────────────────────────────┘
```

### 3.3 问题智能增强（双方案架构新增）

**当前架构**: 无问题增强功能

**双方案架构**: 新增问题智能增强模块（可选开启）

```
┌─────────────────────────────────────────────────────────────────┐
│                   问题智能增强模块 (可选)                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  用户问题输入                                                    │
│     ↓                                                           │
│  ┌─────────────────┐                                           │
│  │ 智能判断         │                                           │
│  │ - 问题长度       │                                           │
│  │ - 是否含SQL关键词 │                                           │
│  │ - 是否含表/字段名 │                                           │
│  └────┬────────────┘                                           │
│       │                                                         │
│       ├──────────────┬──────────────┐                          │
│       ↓              ↓              ↓                          │
│   简单明确问题    复杂模糊问题    缩写/术语问题                   │
│       │              │              │                          │
│       │         ┌────┴──────────────┘                          │
│       │         ↓                                                 │
│       │    ┌─────────────────┐                                 │
│       │    │ LLM问题增强      │                                 │
│       │    │ - 标准化表达     │                                 │
│       │    │ - 展开缩写       │                                 │
│       │    │ - 明确时间表达   │                                 │
│       │    └────────┬────────┘                                 │
│       │             │                                           │
│       │             ├──────────────┐                           │
│       │             ↓              ↓                           │
│       │        信息完整      信息缺失                           │
│       │             │              │                           │
│       │             ↓              ↓                           │
│       │      返回增强问题    反问用户补充                        │
│       │             │              │                           │
│       └──────┬──────┘              │                           │
│              ↓                      ↓                           │
│         增强后问题          用户提供补充信息                     │
│              │                      │                           │
│              └──────────┬───────────┘                          │
│                         ↓                                       │
│                    进入方案选择                                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**增强规则**:
1. **简单问题直接通过**：长度 ≥ 10字 或 包含明确的SQL关键词
2. **复杂问题智能增强**：含模糊时间词（"今年"、"最近"）需明确
3. **缩写自动映射**："DAU" → "日活跃用户数"，"GMV" → "成交总额"
4. **缺失信息主动反问**：聚合查询缺少分组维度时，反问用户

### 3.4 三端职责划分

| 端 | 当前架构 | 双方案架构 |
|-----|---------|-----------|
| **LLM** | 生成 SQL + 执行 + 图表 | 仅生成 SQL（Claude Code 不负责执行） |
| **SQLBot 后端** | 生成 SQL + 执行 + 图表 | **执行 SQL** + 生成图表 + 返回结果 |
| **前端** | 展示结果 | 展示结果（无变化） |

**双方案架构的职责明确**:

```
┌─────────────────────────────────────────────────────────────────┐
│                    三端职责划分                               │
└─────────────────────────────────────────────────────────────────┘

    ┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
    │  Claude Code    │         │  SQLBot 后端    │         │     前端       │
    └────────┬────────┘         └────────┬────────┘         └────────┬────────┘
             │                           │                           │
             │                           │                           │
    ┌────────▼────────┐           ┌───────▼───────┐           │
    │ • 读取 MD 文件  │           │ • 执行 SQL     │           │
    │ • 生成 SQL      │           │ • 生成图表     │     ┌─────▼─────┐
    │ • 问题增强(可选) │           │ • 返回结果     │     │ • 展示结果 │
    └─────────────────┘           └───────────────┘     │ • 用户交互  │
                                                      └───────────┘
```

---

## 4. 数据库设计差异

### 4.1 新增功能开关配置

**当前架构**: 无功能开关表

**双方案架构**: 复用现有 `system_variable` 表存储配置

```sql
-- 新增配置项
INSERT INTO system_variable (name, var_type, type, value, create_time, create_by)
VALUES
-- 1. SQL生成方案切换
('sql_solution_type', 'string', 'system', ['llm'], NOW(), 1),

-- 2. Claude Code Skill目录
('claude_code_skill_dir', 'string', 'custom',
 ['/path/to/skills/sqlbot-knowledge'], NOW(), 1),

-- 3. 是否自动同步配置到MD文件
('claude_code_sync_enabled', 'boolean', 'custom', [true], NOW(), 1),

-- 4. LLM方案是否启用RAG检索
('llm_rag_enabled', 'boolean', 'system', [true], NOW(), 1),

-- 5. Claude Code方案是否启用问题增强（可选）
('claude_code_query_enhancement_enabled', 'boolean', 'custom', [false], NOW(), 1),

-- 6. 问题增强复杂度阈值（字符数）
('claude_code_enhancement_threshold', 'number', 'custom', [10], NOW(), 1),

-- 7. 是否允许反问用户补充信息
('claude_code_allow_followup', 'boolean', 'custom', [true], NOW(), 1);
```

### 4.2 配置字段说明

| 变量名 | 类型 | 默认值 | 说明 |
|---------|-------|-------|------|
| `sql_solution_type` | string | 'llm' | SQL生成方案：'llm' 或 'claude_code' |
| `claude_code_skill_dir` | string | /path/to/skills | Claude Code Skill 目录 |
| `claude_code_sync_enabled` | boolean | true | 是否自动同步配置到 MD 文件 |
| `llm_rag_enabled` | boolean | true | LLM 方案是否启用 RAG 检索 |
| `claude_code_query_enhancement_enabled` | boolean | false | Claude Code 方案是否启用问题增强 |
| `claude_code_enhancement_threshold` | number | 10 | 问题增强复杂度阈值 |
| `claude_code_allow_followup` | boolean | true | 是否允许反问用户补充信息 |

---

## 5. 代码架构差异

### 5.1 目录结构对比

**当前架构**:
```
backend/apps/
├── chat/
│   ├── api/chat.py              # 聊天 API
│   ├── crud/chat.py            # CRUD 操作
│   ├── task/llm.py           # LLM 服务
│   └── models/chat_model.py     # 数据模型
└── ...
```

**双方案架构**:
```
backend/apps/
├── chat/
│   ├── api/chat.py              # 聊天 API（改造：使用工厂）
│   ├── crud/chat.py            # CRUD 操作（保持不变）
│   ├── task/
│   │   ├── llm.py            # LLM 方案（保持不变）
│   │   ├── claude_code.py    # 新增：Claude Code 方案
│   │   └── strategy_factory.py # 新增：策略工厂
│   └── models/chat_model.py     # 数据模型（保持不变）
├── system/
│   ├── crud/
│   │   └── feature_flag.py  # 新增：功能开关 CRUD
│   └── api/
│       └── feature_flag.py   # 新增：功能开关 API
└── config_sync/
    ├── sync_config_to_md.py     # 现有：配置同步
    └── claude_code_client.py  # 新增：Claude Code 客户端

skills/                           # 新增目录
└── sqlbot-knowledge/
    ├── SKILL.md               # Skill 配置
    ├── SCHEMA.md              # 表结构（自动生成）
    ├── TERMINOLOGY.md         # 术语库（自动生成）
    ├── EXAMPLES.md            # SQL 示例（自动生成）
    ├── PROMPT.md              # 自定义 Prompt（自动生成）
    └── RELATIONS.md           # 表关系（自动生成）
```

### 5.2 核心设计模式差异

| 设计模式 | 当前架构 | 双方案架构 |
|---------|---------|-----------|
| **调用方式** | 直接调用 `LLMService` | 通过 `SQLGeneratorFactory` 工厂创建 |
| **扩展性** | 修改现有代码 | 新增策略类，开闭原则 |
| **切换方式** | 不支持 | 功能开关动态切换 |
| **降级机制** | 无 | Claude Code 失败自动回退到 LLM |

**双方案架构 - 策略模式设计**:

```python
# 抽象基类
class BaseSQLGenerator(ABC):
    @abstractmethod
    async def create(self): ...
    @abstractmethod
    async def init_record(self): ...
    @abstractmethod
    async def run_task(self): ...

# LLM 方案策略
class LLMSQLGenerator(BaseSQLGenerator):
    # 含 RAG 检索的三路召回
    async def run_task(self): ...

# Claude Code 方案策略
class ClaudeCodeSQLGenerator(BaseSQLGenerator):
    # 读取 MD 文件，无 RAG
    async def run_task(self): ...

# 工厂
class SQLGeneratorFactory:
    @staticmethod
    async def create(...) -> BaseSQLGenerator:
        solution_type = FeatureFlagService.get_sql_solution_type(session)
        if solution_type == 'claude_code':
            return ClaudeCodeSQLGenerator(...)
        else:
            return LLMSQLGenerator(...)
```

---

## 6. API 差异

### 6.1 新增 API 端点

**当前架构**: 无功能开关 API

**双方案架构**: 新增功能开关管理 API

| 端点 | 方法 | 说明 |
|-------|-------|-------|
| `/system/feature-flags/list` | GET | 获取功能开关列表 |
| `/system/feature-flags/{name}` | GET | 获取功能开关值 |
| `/system/feature-flags/toggle` | POST | 切换功能开关 |
| `/system/feature-flags/update` | POST | 更新功能开关 |
| `/system/feature-flags/solution-type` | POST | 设置 SQL 生成方案 |
| `/system/feature-flags/solution-type` | GET | 获取当前 SQL 生成方案 |

### 6.2 现有 API 改造

**文件**: `backend/apps/chat/api/chat.py`

**改造前**（当前架构）:
```python
async def stream_sql(...):
    # 直接创建 LLM 服务
    llm_service = await LLMService.create(...)
    # 运行任务
    llm_service.run_task_async(...)
```

**改造后**（双方案架构）:
```python
async def stream_sql(...):
    # 使用工厂创建 SQL 生成器
    from apps.chat.task.strategy_factory import SQLGeneratorFactory

    sql_generator = await SQLGeneratorFactory.create(
        session, current_user, request_question, current_assistant
    )

    # 初始化记录
    await sql_generator.init_record()

    # 运行任务（根据自动选择的方案）
    async for chunk in sql_generator.run_task(...):
        yield chunk
```

---

## 7. Skill 文件结构

### 7.1 MD 文件组织

**当前架构**: 无 Skill 目录

**双方案架构**: 新增 `skills/sqlbot-knowledge/` 目录

```
skills/sqlbot-knowledge/
├── SKILL.md              # Skill 配置入口
├── SCHEMA.md             # 表结构（自动生成）
├── TERMINOLOGY.md        # 术语库（自动生成）
├── EXAMPLES.md           # SQL 示例（自动生成）
├── PROMPT.md             # 自定义 Prompt（自动生成）
└── RELATIONS.md          # 表关系（自动生成）
```

### 7.2 配置同步机制

**当前架构**: 无配置同步需求

**双方案架构**: 支持自动同步数据库配置到 MD 文件

| 配置项 | 说明 |
|---------|-------|
| `claude_code_sync_enabled` | 是否自动同步 |
| 同步来源 | `core_table`, `core_field`, `terminology`, `data_training` |
| 同步目标 | `SCHEMA.md`, `TERMINOLOGY.md`, `EXAMPLES.md` |

---

## 8. 部署架构差异

### 8.1 部署方式对比

| 维度 | 当前架构 | 双方案架构 |
|-----|---------|-----------|
| **部署单元** | 单体应用 | 单体应用 + Claude Code 客户端 |
| **外部依赖** | LLM API | LLM API + Claude Code CLI |
| **配置复杂度** | 中等 | 较高（需配置 Skill 路径） |

### 8.2 新增依赖

**双方案架构新增依赖**:

```python
# Claude Code 客户端依赖
- Claude Code CLI (需单独安装)
- subprocess 调用
```

---

## 9. 迁移路径

### 9.1 实施阶段

| 阶段 | 工作量 | 说明 |
|-----|---------|-------|
| Phase 1: 功能开关模块 | 2-3 小时 | 实现功能开关 CRUD |
| Phase 2: Claude Code 客户端 | 3-4 小时 | 实现子进程调用 |
| Phase 3: Claude Code 方案任务 | 2-3 小时 | 实现新方案流程 |
| Phase 4: 策略工厂 | 2-3 小时 | 实现策略模式 |
| Phase 5: API 改造 | 2-3 小时 | 改造现有 API |
| Phase 6: 测试和优化 | 2-3 小时 | 全面测试 |
| **总计** | **13-19 小时** | 约 2-3 个工作日 |

### 9.2 风险评估

| 风险 | 影响 | 缓解措施 |
|-----|-------|---------|
| Claude Code 调用失败 | 功能不可用 | 自动降级到 LLM 方案 |
| 配置同步错误 | 上下文不准确 | 提供手动同步接口 |
| 子进程调用超时 | 响应慢 | 设置超时 + 降级 |

---

## 10. 总结

### 10.1 架构演进核心变化

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     架构演进核心变化                              │
└─────────────────────────────────────────────────────────────────────────────┘

    单一方案 (当前)                          双方案 (未来)
         │                                        │
         ▼                                        ▼
    ┌─────────┐                            ┌─────────────────────────┐
    │  LLM    │                            │  LLM  │ Claude Code   │
    │  方案    │                            │  方案  │     方案        │
    └─────────┘                            └─────────────────────────┘
         │                                        │
         │                                        │
         ▼                                        ▼
    ┌─────────────────────────────────────────────────────────────┐
    │                    SQLBot 后端                         │
    │              (执行 SQL + 生成图表)                   │
    └─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                         ┌─────────────┐
                         │   前端     │
                         └─────────────┘

核心变化:
┌─────────────────────────────────────────────────────────────────┐
│ 1. 新增策略模式 + 工厂模式                               │
│ 2. 新增功能开关系统 (system_variable 表)                    │
│ 3. 新增 Claude Code 客户端                               │
│ 4. 新增问题智能增强模块 (可选)                            │
│ 5. 新增 Skill 目录结构                                   │
│ 6. 职责明确：Claude Code 生成，SQLBot 执行+图表            │
└─────────────────────────────────────────────────────────────────┘
```

### 10.2 向后兼容性

| 功能 | 兼容性 | 说明 |
|-----|---------|-------|
| 现有 LLM 方案 | ✅ 完全兼容 | 保持现有实现 |
| 现有 API | ✅ 完全兼容 | 仅修改内部实现 |
| 现有前端 | ✅ 无需改动 | 仅展示结果 |
| 现有数据库 | ✅ 零表结构变更 | 复用 system_variable |

---

## 附录

### A. 相关文档

- [SQLBot-Current-Architecture-Design.md](./SQLBot-Current-Architecture-Design.md) - 当前架构详细设计
- [SQLBot-SWITCH-DETAILED-DESIGN.md](./switch-design/SQLBot-SWITCH-DETAILED-DESIGN.md) - 双方案切换详细设计

### B. 版本历史

| 版本 | 日期 | 变更内容 |
|-----|------|----------|
| v1.0 | 2026-02-11 | 初始版本，架构对比分析 |

---

**维护者**: SQLBot Team
**最后更新**: 2026-02-11
