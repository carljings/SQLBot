# 苏政源一本账智能问数 - Claude Code 架构设计方案

> 基于 Claude Code 主 Agent + 智能问数技能 + SQLBot 的综合架构方案
> 设计时间：2026-02-08

---

## 📐 整体架构设计

```
┌─────────────────────────────────────────────────────────┐
│                        用户界面层                              │
│  (React Web App - SQLBot Frontend)                              │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       │ HTTP/WebSocket
                       ▼
┌─────────────────────────────────────────────────────────┐
│                   Claude Code 主 Agent                         │
│  (Claude Code - Agent Orchestration)                            │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Claude Code 职责：                                  │  │
│  │  1. 意图识别（理解用户问题）                           │  │
│  │  2. 任务编排（调用 Skills）                             │  │
│  │  3. 结果聚合（整合多个 Skill 输出）                      │  │
│  │  4. 对话管理（维护多轮对话上下文）                         │  │
│  │  5. 技能路由（根据问题类型选择 Skill）                      │  │
│  └──────────────────────────────────────────────────┘  │
└───────┬───────────────────────┬───────────────────────┬─────────┘
        │                       │                       │
        │ 调用智能问数 Skill       │ 调用指标选择 Skill      │ 直接调用 SQLBot API
        ▼                       ▼                       ▼
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────────────────────┐
│ 智能问数 Skill    │    │ 指标选择 Skill    │    │    SQLBot REST API             │
│ (Smart Query)    │    │ (Metric Selector) │    │    (LangChain + OpenAI/通义千问)  │
│                   │    │                   │    │                                  │
│ 模块：            │    │ 模块：            │    │ API：                            │
│ 1. 表理解         │    │ 1. 指标分类       │    │ 1. /api/v1/chat/question        │
│ 2. 指标识别       │    │ 2. 指标搜索       │    │ 2. /api/v1/chat/sql             │
│ 3. 维度提取       │    │ 3. 指标解释       │    │ 3. /api/v1/chat/sql_exec       │
│ 4. 术语匹配       │    │ 4. 多选/单选      │    │ 4. /api/v1/terminology         │
│ 5. 业务规则       │    │                   │    │ 5. /api/v1/training_data        │
│                   │    │                   │    │                                  │
│ 输出：            │    │ 输出：            │    │ 输出：                           │
│ - 指标识别       │    │ - 指标列表       │    │ - SQL 语句                      │
│ - 维度提取       │    │ - 指标详情       │    │ - 执行结果                      │
│ - 术语匹配       │    │                   │    │ - 图表配置                      │
│ - 业务规则       │    │                   │    │                                  │
└──────────────────┘    └──────────────────┘    └───────────┬──────────────────────┘
                                                            │
                                                            ▼
                                              ┌──────────────────────────────────┐
                                              │       SQLBot 后端服务           │
                                              │     (Python + FastAPI)           │
                                              │                                  │
                                              │ 模块：                           │
                                              │ 1. LLMService (SQL生成)        │
                                              │ 2. LLMFactory (模型工厂)       │
                                              │ 3. RAG 增强                     │
                                              │ 4. 结果可视化                   │
                                              └──────────────────────────────────┘
```

---

## 🎯 Claude Code 主 Agent 职责

### 核心流程

```python
# Claude Code Agent (伪代码）
class SzYbzAgent:
    """苏政源一本账智能问数 Agent"""

    def __init__(self):
        self.skills = {
            "smart_query": SmartQuerySkill(),
            "metric_selector": MetricSelectorSkill()
        }
        self.sqlbot_client = SQLBotAPIClient()

    async def handle_question(self, user_question: str, context: dict = None) -> dict:
        """处理用户问题"""

        # 1. 意图识别（Claude Code 内置能力）
        intent = self._detect_intent(user_question)

        # 2. 技能路由
        if intent == "query":
            return await self._handle_query(user_question, context)
        elif intent == "select_metrics":
            return await self._handle_select_metrics(user_question, context)
        elif intent == "explain_metrics":
            return await self._handle_explain_metrics(user_question, context)
        else:
            return await self._handle_general(user_question, context)

    async def _handle_query(self, question: str, context: dict = None) -> dict:
        """处理查询类问题"""

        # 1. 调用智能问数 Skill - 表理解
        table_info = await self.skills["smart_query"].analyze_table()

        # 2. 调用智能问数 Skill - 指标识别
        metrics = await self.skills["smart_query"].identify_metrics(question)

        # 3. 调用智能问数 Skill - 维度提取
        dimensions = await self.skills["smart_query"].extract_dimensions(question)

        # 4. 调用智能问数 Skill - 术语匹配
        terms = await self.skills["smart_query"].match_terms(question)

        # 5. 调用智能问数 Skill - 业务规则
        business_rules = await self.skills["smart_query"].extract_business_rules(question)

        # 6. 构建 Claude Code 请求（包含 Skill 输出）
        claude_prompt = self._build_claude_prompt(
            question=question,
            table_info=table_info,
            metrics=metrics,
            dimensions=dimensions,
            terms=terms,
            business_rules=business_rules,
            context=context
        )

        # 7. 调用 SQLBot API 生成 SQL
        sql_result = await self.sqlbot_client.generate_sql(claude_prompt)

        # 8. 结果聚合
        return self._aggregate_result(sql_result, metrics, dimensions)

    async def _handle_select_metrics(self, question: str, context: dict = None) -> dict:
        """处理指标选择"""

        # 直接调用指标选择 Skill
        return await self.skills["metric_selector"].list_metrics(question)

    def _detect_intent(self, question: str) -> str:
        """意图识别（Claude Code 内置）"""

        # Claude Code 通过语义理解自动识别
        # 关键词匹配作为辅助
        if any(kw in question for kw in ["查询", "多少", "数量", "费用"]):
            return "query"
        elif any(kw in question for kw in ["指标", "选择", "查看指标"]):
            return "select_metrics"
        elif any(kw in question for kw in ["什么", "解释", "说明"]):
            return "explain_metrics"
        else:
            return "general"
```

---

## 🎨 Claude Code Skill 设计

### 1. 智能问数 Skill（Smart Query）

```python
# SKILL.md
name: "smart-query"
description: "苏政源一本账智能问数核心技能，负责表理解、指标识别、维度提取、术语匹配"

triggers:
  - "智能问数"
  - "查询数据"
  - "生成SQL"
  - "指标识别"
  - "维度提取"

commands:
  analyze_table:
    description: "分析表结构，识别指标和维度"
    output:
      metrics: []
      dimensions: []

  identify_metrics:
    description: "从用户问题中识别指标"
    input: question
    output:
      - name: "系统数量"
        field: "信息系统编码"
        operation: "COUNT"

  extract_dimensions:
    description: "从用户问题中提取维度"
    input: question
    output:
      time: {year: 2025}
      location: {city: "南京市"}
      business: {}

  match_terms:
    description: "匹配问题中的术语"
    input: question
    output:
      - term: "垂管系统"
        sql_condition: "垂管类型 = '省垂'"
```

### 2. 指标选择 Skill（Metric Selector）

```python
# SKILL.md
name: "metric-selector"
description: "指标选择功能，提供指标分类、搜索、解释"

triggers:
  - "指标选择"
  - "查看指标"
  - "选择指标"
  - "指标列表"

commands:
  list_metrics:
    description: "列出所有可用指标"
    output:
      - category: "财务指标"
        metrics:
          - name: "系统数量"
            description: "..."
          - name: "建设费用"
            description: "..."

  search_metrics:
    description: "搜索指标"
    input: keyword
    output: []

  explain_metric:
    description: "解释指标含义"
    input: metric_name
    output:
      name: "系统数量"
      description: "..."
      calculation: "COUNT(信息系统编码)"
```

---

## 🔄 SQLBot API 调用

### API 接口适配

```python
# sqlbot_api_client.py
class SQLBotAPIClient:
    """SQLBot API 客户端"""

    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = httpx.AsyncClient()

    async def generate_sql(self, prompt: str, context: dict = None) -> dict:
        """调用 SQLBot 生成 SQL"""

        # 调用 SQLBot API
        response = await self.session.post(
            f"{self.base_url}/api/v1/chat/question",
            json={
                "question": prompt,
                "chat_id": context.get("chat_id"),
                "datasource_id": context.get("datasource_id")
            }
        )

        return response.json()

    async def get_terminology(self) -> list:
        """获取术语库"""
        response = await self.session.get(
            f"{self.base_url}/api/v1/terminology"
        )
        return response.json()

    async def get_training_data(self) -> list:
        """获取 SQL 示例"""
        response = await self.session.get(
            f"{self.base_url}/api/v1/training_data"
        )
        return response.json()
```

---

## 🚀 工作流程示例

### 场景 1：标准查询流程

```
用户："2025年南京市省垂系统数量"
   │
   ▼
Claude Code 意图识别 → "query"
   │
   ▼
Claude Code 技能路由 → 智能问数 Skill
   │
   ├─→ 智能问数 Skill：表理解
   │    返回：{metrics: [...], dimensions: [...]}
   │
   ├─→ 智能问数 Skill：指标识别
   │    返回：[{name: "系统数量", operation: "COUNT", field: "..."}]
   │
   ├─→ 智能问数 Skill：维度提取
   │    返回：{time: {year: 2025}, location: {city: "南京市"}}
   │
   ├─→ 智能问数 Skill：术语匹配
   │    返回：[{term: "省垂", sql: "垂管类型 = '省垂'"}]
   │
   ▼
Claude Code 构建 Prompt（包含 Skill 输出）
   │
   ▼
Claude Code 调用 SQLBot API
   │
   ▼
SQLBot 生成 SQL（通过 LangChain + LLM）
   │
   ▼
SQLBot 执行 SQL → PostgreSQL
   │
   ▼
返回给用户：{sql: "...", data: [...], chart: {...}}
```

---

### 场景 2：指标选择流程

```
用户："查看所有可用的指标"
   │
   ▼
Claude Code 意图识别 → "select_metrics"
   │
   ▼
Claude Code 技能路由 → 指标选择 Skill
   │
   ▼
指标选择 Skill 返回：{
    "metrics": [
        {"name": "系统数量", "description": "...", "category": "统计"},
        {"name": "建设费用", "description": "...", "category": "财务"},
        ...
    ]
}
   │
   ▼
返回给用户
```

---

### 场景 3：指标解释流程

```
用户："什么是系统数量"
   │
   ▼
Claude Code 意图识别 → "explain_metrics"
   │
   ▼
Claude Code 技能路由 → 智能问数 Skill
   │
   ├─→ 指标识别 Skill：解释指标
   │    返回：{
   │        "name": "系统数量",
   │        "description": "统计系统中信息系统的数量",
   │        "calculation": "COUNT(信息系统编码)"
   │    }
   │
   ▼
返回给用户
```

---

## 📁 文件结构

```
sz-ybz/                         # 项目根目录
├── claude_code_skills/            # Claude Code Skills
│   ├── SKILL.md                  # Skill 配置（智能问数）
│   ├── smart_query/               # 智能问数实现
│   │   ├── table_understanding.py
│   │   ├── metric_identifier.py
│   │   ├── dimension_extractor.py
│   │   ├── term_matcher.py
│   │   └── business_rules.py
│   │
│   └── metric_selector/           # 指标选择实现
│       ├── SKILL.md
│       ├── metric_lister.py
│       ├── metric_searcher.py
│       └── metric_explainer.py
│
├── sqlbot/                        # SQLBot 源码（已下载）
│   ├── backend/
│   ├── frontend/
│   └── ...
│
├── agent/                         # Claude Code Agent（主编排）
│   ├── sz_ybz_agent.py            # 主 Agent 实现
│   ├── intent_detector.py         # 意图识别
│   ├── skill_router.py             # 技能路由
│   └── context_manager.py          # 上下文管理
│
├── api/                           # SQLBot API 客户端
│   └── sqlbot_client.py
│
├── database/                      # 苏政源数据库
│   └── schema.sql
│
└── config/                        # 配置文件
    ├── claude_code.yaml
    └── sqlbot_config.yaml
```

---

## 🔧 技术实现要点

### 1. Claude Code Agent 配置

```yaml
# config/claude_code.yaml
agent:
  name: "sz-ybz-agent"
  model: "claude-3-5-sonnet-20241022"
  temperature: 0
  max_tokens: 8192

skills:
  - name: "smart-query"
    path: "./claude_code_skills/"
    description: "智能问数核心技能"

  - name: "metric-selector"
    path: "./claude_code_skills/metric_selector/"
    description: "指标选择技能"

integrations:
  - name: "sqlbot"
    type: "http_api"
    config:
      base_url: "http://localhost:8000"
      api_key: "your-api-key"
```

### 2. Claude Code Skill 实现

```python
# claude_code_skills/smart_query/table_understanding.py
from claude_code import Skill

class TableUnderstandingSkill(Skill):
    """表理解技能"""

    def execute(self, context: dict) -> dict:
        """执行表理解"""

        table_name = context.get("table_name")

        # 分析表结构（读取数据库 Schema）
        # 识别指标和维度

        return {
            "metrics": [
                {"name": "系统数量", "field": "信息系统编码", "operation": "COUNT"},
                {"name": "建设费用", "field": "系统建设费用", "operation": "SUM"}
            ],
            "dimensions": [
                {"name": "时间", "type": "time", "field": "系统建成时间"},
                {"name": "地区", "type": "entity", "field": "区划编码"},
                {"name": "系统状态", "type": "category", "field": "系统状态"}
            ]
        }
```

### 3. SQLBot 无需修改

**优点**：
- SQLBot 保持原样，无需改动
- 只需要启动 SQLBot 后端服务
- 通过 HTTP API 调用即可

**部署**：
```bash
# 启动 SQLBot
cd sqlbot/backend
python main.py

# 访问
http://localhost:8000
```

---

## 📊 优势分析

### 相比纯 SQLBot

| 优势 | 说明 |
|------|------|
| **可扩展性** | 高（Claude Code 可轻松扩展新 Skill） |
| **编排能力** | 强（Claude Code 的 Agent 能力） |
| **智能化** | 高（Claude Code 的语义理解） |
| **定制化** | 容易（Skill 级别的定制化） |

### 相比纯 Claude Code

| 优势 | 说明 |
|------|------|
| **SQL 准确性** | 高（SQLBot 的 RAG + 术语库） |
| **开发效率** | 高（复用 SQLBot 已实现的功能） |
| **企业级特性** | 完整（SQLBot 的权限、审计） |

### 相比自定义 Agent

| 优势 | 说明 |
|------|------|
| **编排能力** | 强（Claude Code 专为 Agent 设计） |
| **工具生态** | 丰富（Claude Code 内置工具） |
| **易用性** | 高（声明式配置） |

---

## 🚀 实施步骤

### 阶段 1：基础设施搭建（1-2 天）

- [ ] 项目初始化
- [ ] 安装 Claude Code
- [ ] 启动 SQLBot 后端
- [ ] 配置开发环境

### 阶段 2：Claude Code Skills 开发（3-5 天）

- [ ] 智能问数 Skill - 表理解模块
- [ ] 智能问数 Skill - 指标识别模块
- [ ] 智能问数 Skill - 维度提取模块
- [ ] 智能问数 Skill - 术语匹配模块
- [ ] 智能问数 Skill - 业务规则模块
- [ ] 指标选择 Skill - 列表/搜索/解释模块

### 阶段 3：Claude Code Agent 编排（2-3 天）

- [ ] 意图识别器
- [ ] 技能路由
- [ ] 结果聚合器
- [ ] 上下文管理器

### 阶段 4：SQLBot API 集成（1-2 天）

- [ ] SQLBot API 客户端
- [ ] 数据同步（术语、SQL 示例）
- [ ] 测试 API 调用

### 阶段 5：集成测试（1-2 天）

- [ ] 端到端测试
- [ ] 性能优化
- [ ] 错误处理

### 阶段 6：前端集成（2-3 天）

- [ ] 修改 SQLBot 前端（可选）
- [ ] 添加指标选择界面
- [ ] 添加 Agent 日志查看

---

## 📝 总结

### 核心设计理念

1. **Claude Code 为主**：Claude Code 负责 Agent 编排
2. **SQLBot 为辅**：SQLBot 负责 SQL 生成和执行
3. **Skills 为桥梁**：智能问数和指标选择作为 Claude Code 的 Skills
4. **REST API 为连接**：通过 HTTP API 连接 Claude Code 和 SQLBot
5. **SQLBot 无修改**：SQLBot 保持原样，无需改动

### 关键优势

1. ✅ **编排能力强**：Claude Code 的 Agent 能力
2. ✅ **SQL 准确性高**：SQLBot 的 RAG + 术语库
3. ✅ **开发效率高**：复用 SQLBot，Skills 可快速开发
4. ✅ **可扩展性好**：Claude Code 可轻松扩展新 Skill
5. ✅ **SQLBot 无需修改**：保持原样，降低风险

### 预计工作量

- **总工期**：10-15 天
- **Skills 开发**：3-5 天
- **Agent 编排**：2-3 天
- **SQLBot 集成**：1-2 天
- **测试优化**：2-3 天
- **前端集成**：2-3 天

---

*文档生成时间：2026-02-08*
*最后更新：2026-02-08*
