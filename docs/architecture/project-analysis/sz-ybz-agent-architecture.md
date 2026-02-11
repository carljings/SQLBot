# 苏政源一本账智能问数 - Agent 架构设计方案

> 基于 SQLBot + 智能问数技能 + 主 Agent 的综合架构方案
> 设计时间：2026-02-08

---

## 📐 整体架构设计

```
┌─────────────────────────────────────────────────────────────────┐
│                        用户界面层                              │
│  (React Web App - SQLBot Frontend)                              │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       │ HTTP/WebSocket
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                        主 Agent 层                                │
│  (OpenClaw Main Agent - 替代 Claude Code)                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  职责：                                                  │  │
│  │  1. 意图识别（用户问题理解）                             │  │
│  │  2. 任务编排（调用子技能）                                 │  │
│  │  3. 结果聚合（整合多个技能输出）                            │  │
│  │  4. 对话管理（多轮对话上下文）                               │  │
│  └──────────────────────────────────────────────────────────┘  │
└───────────┬───────────────────────────────┬───────────────────────┘
            │                               │
            │ 调用技能                      │ 调用技能
            ▼                               ▼
┌──────────────────────┐    ┌──────────────────────────────────┐
│  智能问数技能层       │    │    SQLBot LLM 引擎层            │
│  (Smart Query)       │    │  (LangChain + OpenAI/通义千问)   │
│                      │    │                                  │
│  模块：              │    │  模块：                           │
│  1. 表理解模块       │    │  1. LLMService (SQLBot)        │
│  2. 维度管理模块     │    │  2. LLMFactory (模型工厂)       │
│  3. 指标管理模块     │    │  3. RAG 增强                   │
│  4. 术语管理模块     │    │  4. SQL 生成                    │
│  5. 问答解析模块     │    │  5. 结果可视化                   │
│                      │    │                                  │
│  输出：              │    │  输出：                           │
│  - 指标识别         │    │  - SQL 语句                      │
│  - 维度提取         │    │  - 执行结果                      │
│  - 术语匹配         │    │  - 图表配置                      │
│  - 业务规则         │    │                                  │
└──────────────────────┘    └──────────────────────────────────┘
            │                               │
            │ 辅助信息                      │ SQL 查询
            ▼                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                        数据存储层                              │
│  1. PostgreSQL (业务数据)                                       │
│  2. pgvector (向量存储 - RAG)                                   │
│  3. 术语库 (Terms)                                              │
│  4. SQL 示例库 (Examples)                                        │
│  5. 问答历史 (Chat History)                                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🎯 各层职责详解

### 1. 主 Agent 层（OpenClaw Main Agent）

#### 核心职责
```python
class SzYbzAgent:
    """苏政源一本账智能问数主 Agent"""

    def __init__(self):
        self.smart_query_skill = SmartQuerySkill()
        self.sqlbot_llm = SQLBotLLMService()
        self.context_manager = ContextManager()

    async def handle_question(self, user_question: str) -> dict:
        """处理用户问题"""

        # 1. 意图识别
        intent = self._detect_intent(user_question)

        # 2. 任务编排
        if intent == "query":
            return await self._handle_query(user_question)
        elif intent == "config":
            return await self._handle_config(user_question)
        elif intent == "explain":
            return await self._handle_explain(user_question)
        else:
            return await self._handle_general(user_question)

    async def _handle_query(self, question: str) -> dict:
        """处理查询类问题"""

        # 1. 调用智能问数技能 - 表理解
        table_info = await self.smart_query_skill.analyze_table()

        # 2. 调用智能问数技能 - 指标识别
        metrics = await self.smart_query_skill.identify_metrics(question)

        # 3. 调用智能问数技能 - 维度提取
        dimensions = await self.smart_query_skill.extract_dimensions(question)

        # 4. 调用智能问数技能 - 术语匹配
        terms = await self.smart_query_skill.match_terms(question)

        # 5. 构建 Prompt（包含技能输出）
        prompt = self._build_prompt(
            question=question,
            table_info=table_info,
            metrics=metrics,
            dimensions=dimensions,
            terms=terms
        )

        # 6. 调用 SQLBot LLM 引擎
        sql_result = await self.sqlbot_llm.generate_sql(prompt)

        # 7. 结果聚合
        return self._aggregate_result(sql_result, metrics, dimensions)

    def _detect_intent(self, question: str) -> str:
        """意图识别"""
        # 使用关键词 + 语义理解
        if any(kw in question for kw in ["查询", "多少", "数量", "费用"]):
            return "query"
        elif any(kw in question for kw in ["配置", "设置", "添加", "删除"]):
            return "config"
        elif any(kw in question for kw in ["什么", "怎么", "解释"]):
            return "explain"
        else:
            return "general"
```

#### 关键能力
1. **意图识别**：判断用户问题类型（查询/配置/解释）
2. **任务编排**：协调多个技能的调用顺序
3. **结果聚合**：整合多个技能的输出
4. **对话管理**：维护多轮对话的上下文
5. **错误恢复**：处理技能调用失败的情况

---

### 2. 智能问数技能层（Smart Query Skill）

#### 模块结构
```python
class SmartQuerySkill:
    """智能问数技能"""

    # 2.1 表理解模块
    async def analyze_table(self, table_name: str) -> dict:
        """
        分析表结构，识别指标和维度
        输入：表名
        输出：{
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
        """

    # 2.2 指标管理模块
    async def identify_metrics(self, question: str) -> list:
        """
        从用户问题中识别指标
        输入："2025年南京市系统数量"
        输出：[{"name": "系统数量", "field": "信息系统编码", "operation": "COUNT"}]
        """

    # 2.3 维度管理模块
    async def extract_dimensions(self, question: str) -> dict:
        """
        从用户问题中提取维度
        输入："2025年南京市系统数量"
        输出：{
            "time": {"year": 2025},
            "location": {"city": "南京市"},
            "business": {}
        }
        """

    # 2.4 术语管理模块
    async def match_terms(self, question: str) -> list:
        """
        匹配问题中的术语
        输入："垂管系统"
        输出：[
            {"term": "垂管系统", "sql_condition": "垂管类型 = '省垂'", "description": "..."}
        ]
        """

    # 2.5 问答解析模块
    async def parse_query(self, question: str, metrics: list, dimensions: dict) -> dict:
        """
        解析用户问题
        输入：问题 + 指标 + 维度
        输出：{"parsed_query": {...}, "business_rules": [...]}
        """
```

#### 与 SQLBot 的集成
```python
# 智能问数技能 → SQLBot 术语库
async def sync_terms_to_sqlbot():
    """同步术语到 SQLBot"""
    terms = await SmartQuerySkill.get_all_terms()

    # 调用 SQLBot API
    for term in terms:
        await sqlbot_api.create_terminology({
            "name": term.name,
            "content": term.description,
            "business": term.sql_condition
        })

# 智能问数技能 → SQLBot SQL 示例
async def sync_examples_to_sqlbot():
    """同步 SQL 示例到 SQLBot"""
    examples = await SmartQuerySkill.get_all_examples()

    for example in examples:
        await sqlbot_api.create_training_data({
            "question": example.question,
            "sql": example.sql,
            "description": example.description
        })
```

---

### 3. SQLBot LLM 引擎层（LangChain）

#### 核心服务
```python
# SQLBot 的 LLMService（已存在，无需修改）
class LLMService:
    """SQLBot 的 LLM 服务"""

    def __init__(self, session, current_user, chat_question):
        self.config = get_default_config()  # 从数据库获取 LLM 配置
        self.llm = LLMFactory.create_llm(self.config).llm  # 创建 LLM 实例

    async def generate_sql(self, prompt: str) -> str:
        """生成 SQL"""
        response = self.llm.invoke(prompt)
        return response.content
```

#### 改造点：接受 Agent 输入
```python
# 改造后的 SQLBot LLMService
class LLMServiceV2(LLMService):
    """SQLBot LLM 服务 V2 - 支持 Agent 输入"""

    def __init__(self, session, current_user, chat_question, agent_context: dict = None):
        super().__init__(session, current_user, chat_question)
        self.agent_context = agent_context  # 新增：Agent 上下文

    def build_system_prompt(self) -> str:
        """构建系统 Prompt"""
        base_prompt = self.chat_question.sql_sys_question(self.ds.type)

        # 如果有 Agent 上下文，增强 Prompt
        if self.agent_context:
            agent_prompt = f"""

以下是智能问数技能提供的辅助信息：

### 指标信息
{json.dumps(self.agent_context.get('metrics', []), ensure_ascii=False)}

### 维度信息
{json.dumps(self.agent_context.get('dimensions', {}), ensure_ascii=False)}

### 术语信息
{json.dumps(self.agent_context.get('terms', []), ensure_ascii=False)}

### 业务规则
{json.dumps(self.agent_context.get('business_rules', []), ensure_ascii=False)}
"""
            return base_prompt + agent_prompt

        return base_prompt
```

---

## 🔄 工作流程

### 场景 1：标准查询流程

```
用户："2025年南京市省垂系统数量"
   │
   ▼
主 Agent 意图识别 → "query"
   │
   ▼
主 Agent 任务编排
   │
   ├─→ 智能问数技能：表理解
   │    返回：表结构（指标、维度）
   │
   ├─→ 智能问数技能：指标识别
   │    返回：{"name": "系统数量", "operation": "COUNT", "field": "信息系统编码"}
   │
   ├─→ 智能问数技能：维度提取
   │    返回：{"time": {"year": 2025}, "location": {"city": "南京市"}}
   │
   ├─→ 智能问数技能：术语匹配
   │    返回：[{"term": "省垂", "sql": "垂管类型 = '省垂'"}]
   │
   ▼
主 Agent 构建 Prompt（包含所有技能输出）
   │
   ▼
SQLBot LLM 引擎生成 SQL
   │
   ▼
PostgreSQL 执行 SQL
   │
   ▼
主 Agent 聚合结果
   │
   ▼
返回给用户：{"sql": "...", "data": [...], "chart": {...}}
```

---

### 场景 2：指标选择流程

```
用户："查看所有可用的指标"
   │
   ▼
主 Agent 意图识别 → "explain"
   │
   ▼
主 Agent 调用智能问数技能：获取所有指标
   │
   ▼
返回给用户：{
    "metrics": [
        {"name": "系统数量", "description": "...", "field": "..."},
        {"name": "建设费用", "description": "...", "field": "..."},
        ...
    ]
}
```

---

### 场景 3：多轮对话流程

```
用户："系统数量"
   │
   ▼
主 Agent 意图识别 + 上下文 → "query"（从上下文推断维度）
   │
   ▼
主 Agent 任务编排（复用之前上下文）
   │
   ▼
SQLBot LLM 引擎生成 SQL（包含历史上下文）
   │
   ▼
返回给用户
   │
   ▼
用户："只看南京市的"
   │
   ▼
主 Agent 更新上下文（增加地区维度）
   │
   ▼
重新生成 SQL
```

---

## 📁 文件结构

```
sz-ybz/                         # 项目根目录
├── agent/                       # 主 Agent 层
│   ├── main_agent.py           # 主 Agent 实现
│   ├── intent_detector.py      # 意图识别器
│   ├── task_orchestrator.py   # 任务编排器
│   ├── result_aggregator.py    # 结果聚合器
│   └── context_manager.py     # 对话上下文管理
│
├── skills/                     # 智能问数技能层
│   ├── table_understanding.py  # 表理解模块
│   ├── metric_manager.py      # 指标管理模块
│   ├── dimension_manager.py    # 维度管理模块
│   ├── term_manager.py        # 术语管理模块
│   └── query_parser.py        # 问答解析模块
│
├── sqlbot/                     # SQLBot 引擎层（集成）
│   ├── backend/                # SQLBot 后端（无需修改）
│   ├── frontend/               # SQLBot 前端（无需修改）
│   └── adapter/                # 适配器层
│       ├── llm_service_v2.py   # 改造后的 LLMService
│       └── agent_bridge.py     # Agent 与 SQLBot 的桥接
│
├── database/                   # 数据库层
│   ├── schema.sql              # 数据库结构
│   └── migrations/            # 数据迁移
│
├── config/                     # 配置文件
│   ├── agent_config.yaml       # Agent 配置
│   ├── skill_config.yaml       # 技能配置
│   └── sqlbot_config.yaml     # SQLBot 配置
│
└── tests/                      # 测试
    ├── test_agent.py
    ├── test_skills.py
    └── test_integration.py
```

---

## 🔧 技术实现要点

### 1. Agent 与 SQLBot 的桥接

```python
# agent/adapter/agent_bridge.py
class AgentBridge:
    """Agent 与 SQLBot 的桥接"""

    def __init__(self, sqlbot_llm_service):
        self.sqlbot_llm = sqlbot_llm_service

    async def call_sqlbot_with_context(
        self,
        question: str,
        agent_context: dict
    ) -> dict:
        """调用 SQLBot LLM（传入 Agent 上下文）"""

        # 创建 LLMServiceV2 实例
        llm_service_v2 = LLMServiceV2(
            session=self.sqlbot_llm.session,
            current_user=self.sqlbot_llm.current_user,
            chat_question=self.sqlbot_llm.chat_question,
            agent_context=agent_context
        )

        # 生成 SQL
        sql = await llm_service_v2.generate_sql(question)

        # 执行 SQL
        result = await self.sqlbot_llm.exec_sql(sql)

        return {
            "sql": sql,
            "data": result,
            "agent_context": agent_context
        }
```

### 2. OpenClaw Agent 配置

```yaml
# config/agent_config.yaml
agent:
  name: "sz-ybz-agent"
  model: "zai/glm-4.7"
  temperature: 0

skills:
  - name: "smart-query"
    path: "./skills/smart_query.py"
    description: "智能问数核心技能"

  - name: "table-understanding"
    path: "./skills/table_understanding.py"
    description: "表理解模块"

  - name: "metric-manager"
    path: "./skills/metric_manager.py"
    description: "指标管理模块"

  - name: "dimension-manager"
    path: "./skills/dimension_manager.py"
    description: "维度管理模块"

  - name: "term-manager"
    path: "./skills/term_manager.py"
    description: "术语管理模块"

integrations:
  - name: "sqlbot"
    type: "llm_engine"
    config:
      backend_url: "http://localhost:8000"
      api_key: "your-api-key"
```

### 3. 数据同步策略

```python
# skills/sync_manager.py
class SyncManager:
    """数据同步管理器"""

    async def sync_smart_query_to_sqlbot(self):
        """同步智能问数数据到 SQLBot"""

        # 1. 同步术语
        await self._sync_terms()

        # 2. 同步 SQL 示例
        await self._sync_examples()

        # 3. 同步表结构（作为 training data）
        await self._sync_schema()

    async def _sync_terms(self):
        """同步术语"""
        terms = await SmartQuerySkill.get_all_terms()

        for term in terms:
            await sqlbot_api.create_terminology({
                "name": term.name,
                "content": term.description,
                "business": term.sql_condition
            })
```

---

## 🚀 实施步骤

### 阶段 1：基础设施搭建（1-2 天）

- [ ] 项目初始化
- [ ] 安装依赖（OpenClaw Agent、LangChain）
- [ ] 配置开发环境

### 阶段 2：主 Agent 开发（2-3 天）

- [ ] 意图识别器
- [ ] 任务编排器
- [ ] 结果聚合器
- [ ] 上下文管理器

### 阶段 3：智能问数技能开发（3-5 天）

- [ ] 表理解模块
- [ ] 指标管理模块
- [ ] 维度管理模块
- [ ] 术语管理模块
- [ ] 问答解析模块

### 阶段 4：SQLBot 适配（1-2 天）

- [ ] LLMServiceV2 改造
- [ ] Agent 桥接器
- [ ] 数据同步管理器

### 阶段 5：集成测试（1-2 天）

- [ ] 单元测试
- [ ] 集成测试
- [ ] 性能优化

### 阶段 6：前端集成（2-3 天）

- [ ] 修改 SQLBot 前端（可选）
- [ ] 添加指标选择界面
- [ ] 添加 Agent 日志查看

---

## 📊 优势分析

### 相比纯 SQLBot 的优势

| 对比项 | 纯 SQLBot | Agent + 智能问数技能 |
|--------|-----------|---------------------|
| **可扩展性** | 中等 | 高（技能可独立扩展） |
| **可维护性** | 中等 | 高（模块化清晰） |
| **定制化** | 需修改源码 | 技能定制化 |
| **复用性** | 低（限 SQLBot） | 高（技能可复用） |
| **可控性** | 中等 | 高（Agent 全局控制） |
| **灵活性** | 中等 | 高（任务编排灵活） |

### 相比纯 Agent 的优势

| 对比项 | 纯 Agent | Agent + SQLBot |
|--------|---------|---------------|
| **SQL 准确性** | 低（无 RAG） | 高（RAG + 术语库） |
| **开发效率** | 低（从零开始） | 高（复用 SQLBot） |
| **功能完整性** | 低 | 高（SQLBot 已实现） |
| **企业级特性** | 低 | 高（权限、审计） |

---

## 📝 总结

### 核心设计理念

1. **分层清晰**：Agent → 技能 → LLM 引擎 → 数据
2. **职责单一**：每层只负责自己的核心功能
3. **松耦合**：层与层之间通过接口通信
4. **易扩展**：新增功能只需添加新技能
5. **可复用**：技能可在其他项目复用

### 关键创新点

1. **主 Agent 替代 Claude Code**：全局协调，任务编排
2. **智能问数技能化**：将智能问数核心能力封装成技能
3. **SQLBot 增强版**：接受 Agent 上下文，生成更准确的 SQL
4. **技能可复用**：智能问数技能可在其他项目复用

### 预计工作量

- **总工期**：10-15 天
- **核心开发**：7-10 天
- **测试优化**：2-3 天
- **文档编写**：1-2 天

---

*文档生成时间：2026-02-08*
*最后更新：2026-02-08*
