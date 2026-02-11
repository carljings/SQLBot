# SQLBot vs Claude Code - SQL生成逻辑对比

> 深入分析SQLBot的SQL生成逻辑，对比换成Claude Code的可行性和优劣
> 分析时间：2026-02-08

---

## 📊 SQLBot 的 SQL 生成逻辑详解

### 1. 核心流程

```
用户问题 → LLMService → Prompt构建 → LLM调用 → SQL生成 → 执行 → 返回结果
```

### 2. Prompt 构建逻辑（关键！）

#### 2.1 sql_sys_question() 方法

```python
def sql_sys_question(self, db_type, enable_query_limit=True):
    """构建SQL生成的系统Prompt"""
    
    # 从模板中获取各部分
    _sql_template = get_sql_example_template(db_type)
    _base_template = get_sql_template()
    
    # 组装Prompt的各个部分
    prompt = _base_template['system'].format(
        engine=self.engine,           # 数据库类型（PostgreSQL/MySQL等）
        schema=self.db_schema,        # 数据库Schema信息
        question=self.question,       # 用户问题
        lang=self.lang,              # 语言（zh/en）
        
        # ⭐ RAG增强部分
        terminologies=self.terminologies,      # 术语库
        data_training=self.data_training,        # SQL训练示例
        custom_prompt=self.custom_prompt,        # 自定义Prompt（业务规则）
        
        # ⭐ SQL规则部分
        process_check=_process_check,            # 流程检查
        base_sql_rules=_base_sql_rules,          # 基础SQL规则
        basic_sql_examples=_sql_examples,         # 基础SQL示例
        example_engine=_example_engine,           # 示例引擎
        example_answer_1=_example_answer_1,       # 示例答案1
        example_answer_2=_example_answer_2,       # 示例答案2
        example_answer_3=_example_answer_3        # 示例答案3
    )
    
    return prompt
```

#### 2.2 RAG 增强组成部分

| 组成部分 | 内容 | 来源 |
|---------|------|------|
| **Schema** | 数据库表结构、字段信息 | 数据库元数据 |
| **Terminologies** | 术语库（解决口语化表达） | `terminology` 表 |
| **Data Training** | SQL训练示例（Few-shot learning） | `data_training` 表 |
| **Custom Prompt** | 自定义Prompt（业务规则） | `custom_prompt` 表 |
| **SQL Rules** | SQL生成规则（Limit、Joins等） | 模板文件 |
| **SQL Examples** | 基础SQL示例（1-3个） | 模板文件 |

#### 2.3 Prompt 结构（伪代码）

```
你是一个SQL生成专家。请根据以下信息生成SQL查询语句。

## 数据库信息
引擎：{engine}
Schema：
{schema}

## 术语说明（Terminologies）
{terminologies}
（例如：垂管系统 = 垂管类型 = '省垂'）

## SQL训练示例（Data Training）
{data_training}
（例如：Q: 2025年系统数量
      A: SELECT COUNT(*) FROM t_sys WHERE year = 2025）

## 业务规则（Custom Prompt）
{custom_prompt}

## SQL生成规则
- 使用标准SQL语法
- JOIN操作要明确关联条件
- 查询结果要限制行数（防止数据过大）
{base_sql_rules}

## SQL示例
{basic_sql_examples}

## 用户问题
{lang}://{question}

请生成SQL查询语句。
```

### 3. LLM 调用逻辑

```python
# 通过LangChain调用LLM
class LLMService:
    def __init__(self, session, current_user, chat_question):
        # 1. 获取默认LLM配置
        config = await get_default_config()
        
        # 2. 创建LLM实例（LangChain Factory）
        llm_instance = LLMFactory.create_llm(config)
        self.llm = llm_instance.llm
        
        # 3. 构建Prompt（包含RAG增强）
        prompt = self.chat_question.sql_sys_question(self.ds.type)
        
        # 4. 调用LLM生成SQL
        response = self.llm.invoke(prompt)
        return response.content
```

### 4. RAG 数据来源

#### 4.1 术语库（Terminology）

```sql
CREATE TABLE terminology (
    id INT PRIMARY KEY,
    name VARCHAR(255),      -- 术语名称（如"垂管系统"）
    content TEXT,           -- 术语说明
    business VARCHAR(500),  -- SQL条件（如"垂管类型 = '省垂'"）
    oid INT,               -- 所属组织
    ds_id INT              -- 所属数据源
);
```

**用途**：解决口语化表达
- 用户说："垂管系统数量"
- RAG检索：`{"name": "垂管系统", "business": "垂管类型 = '省垂'"}`
- Prompt增强：注入到Prompt中

#### 4.2 SQL训练示例（Data Training）

```sql
CREATE TABLE data_training (
    id INT PRIMARY KEY,
    question TEXT,          -- 自然语言问题
    sql TEXT,              -- 对应的SQL
    description TEXT,       -- 描述
    oid INT,               -- 所属组织
    ds_id INT              -- 所属数据源
);
```

**用途**：Few-shot learning，提高SQL生成准确性
- 示例1：Q: 2025年系统数量 → A: SELECT COUNT(*) FROM t_sys WHERE year = 2025
- 示例2：Q: 南京市系统数量 → A: SELECT COUNT(*) FROM t_sys WHERE city = '南京市'
- 这些示例会被注入到Prompt中

---

## 🔄 换成 Claude Code 生成的三种方案

### 方案 A：完全替换 Claude Code（激进）

#### 实现方式

```python
# 1. 完全移除SQLBot的LLMService
# 2. 直接用Claude Code生成SQL

class ClaudeCodeSQLGenerator:
    """Claude Code SQL生成器"""
    
    def __init__(self, claude_client):
        self.claude_client = claude_client
    
    async def generate_sql(self, question: str, schema: dict, terminologies: list, 
                         examples: list, custom_prompt: str) -> str:
        """用Claude Code生成SQL"""
        
        # 1. 构建Claude Prompt
        prompt = self._build_claude_prompt(
            question=question,
            schema=schema,
            terminologies=terminologies,
            examples=examples,
            custom_prompt=custom_prompt
        )
        
        # 2. 调用Claude API
        response = await self.claude_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4096,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        # 3. 提取SQL
        sql = self._extract_sql_from_response(response.content)
        return sql
```

#### 优缺点

| 优点 | 缺点 |
|------|------|
| ✅ 无需LangChain依赖 | ❌ 需要重新设计Prompt |
| ✅ Claude能力强 | ❌ 失去SQLBot的优化经验 |
| ✅ 可直接集成到Claude Code Agent | ❌ 需要大量的调试和测试 |
| ✅ 成本可控制 | ❌ RAG需要自己实现 |

#### 工作量估算

- Prompt设计：3-5天
- Claude API集成：1-2天
- RAG实现：3-5天
- 测试和优化：3-5天
- **总计：10-17天**

---

### 方案 B：保留SQLBot的RAG，替换LLM为Claude（推荐）

#### 实现方式

```python
# 1. 保留SQLBot的RAG层
# 2. 只替换LLMFactory，改为调用Claude

class ClaudeLLM(BaseLLM):
    """Claude LLM实现"""
    
    def _init_llm(self) -> BaseChatModel:
        """初始化Claude LLM"""
        
        # 使用LangChain的ChatAnthropic
        from langchain_anthropic import ChatAnthropic
        
        return ChatAnthropic(
            model=self.config.model_name,  # claude-3-5-sonnet-20241022
            api_key=self.config.api_key,
            temperature=0,
            streaming=True,
            **self.config.additional_params
        )

# 注册到LLMFactory
LLMFactory.register_llm("claude", ClaudeLLM)
```

#### 配置修改

```python
# 在数据库中添加Claude模型
INSERT INTO ai_model_detail (
    name,              # Claude 3.5 Sonnet
    base_model,        # claude-3-5-sonnet-20241022
    protocol,          # 1 (OpenAI兼容协议）
    api_domain,        # https://api.anthropic.com
    api_key,           # your-claude-api-key
    type_name,         # claude
    default_model,     # true
    temperature        # 0
);
```

#### 优缺点

| 优点 | 缺点 |
|------|------|
| ✅ 保留SQLBot的RAG和优化经验 | ❌ 依赖LangChain |
| ✅ 最小化代码改动 | ❌ 需要Claude API Key |
| ✅ 可以快速切换LLM | ❌ 成本可能更高 |
| ✅ 保留SQLBot的企业级特性 | ❌ 需要适配LangChain的接口 |

#### 工作量估算

- Claude LLM实现：1-2天
- 数据库配置：0.5天
- 测试和优化：1-2天
- **总计：2.5-4.5天**

---

### 方案 C：Claude Code作为Agent，SQLBot保持原样（最稳健）

#### 实现方式

```python
# 1. Claude Code作为主Agent
# 2. SQLBot保持原样，作为工具被调用
# 3. 通过REST API连接

class SzYbzAgent:
    """苏政源一本账Agent"""
    
    def __init__(self):
        self.sqlbot_client = SQLBotAPIClient()
    
    async def handle_query(self, question: str) -> dict:
        """处理查询"""
        
        # 1. Claude Code理解意图
        intent = self._detect_intent(question)
        
        if intent == "query":
            # 2. 直接调用SQLBot API
            result = await self.sqlbot_client.chat_question(
                question=question,
                chat_id=self.chat_id,
                datasource_id=self.datasource_id
            )
            
            return result
```

#### 优缺点

| 优点 | 缺点 |
|------|------|
| ✅ SQLBot完全不改，风险最低 | ❌ 无法利用Claude的强大能力 |
| ✅ 快速实现 | ❌ 依赖SQLBot的LLM（可能不够强） |
| ✅ 保留SQLBot的企业级特性 | ❌ 不灵活 |
| ✅ 工作量最小 | ❌ 智能化程度低 |

#### 工作量估算

- Claude Code Agent开发：2-3天
- SQLBot API封装：1-2天
- 集成测试：1天
- **总计：4-6天**

---

## 📊 综合对比

### 三种方案对比

| 对比项 | 方案A：完全替换 | 方案B：保留RAG | 方案C：保持原样 |
|--------|--------------|--------------|--------------|
| **SQL准确性** | 中等（需大量调试） | 高（SQLBot的RAG+Claude） | 中等（SQLBot的LLM） |
| **工作量** | 高（10-17天） | 低（2.5-4.5天） | 最低（4-6天） |
| **风险** | 高（需重新实现） | 低（最小改动） | 最低（不改） |
| **可维护性** | 中等（自己维护） | 高（SQLBot维护） | 高（SQLBot维护） |
| **可扩展性** | 高（Claude能力强） | 高（Claude+RAG） | 中等（SQLBot限制） |
| **企业级特性** | 需自己实现 | 保留 | 保留 |
| **成本** | 中等 | 中等 | 低 |

---

## 💡 我的建议

### 🏆 推荐：方案B（保留SQLBot的RAG，替换LLM为Claude）

#### 理由

1. **准确性最高**：SQLBot的RAG（Schema、术语、SQL示例）+ Claude的强大LLM = 最佳组合
2. **风险最低**：只需替换LLM，保留SQLBot的优化经验
3. **工作量最小**：2.5-4.5天完成
4. **可维护性高**：SQLBot团队持续维护RAG层
5. **成本可控**：Claude按使用量付费，可以切换回通义千问

#### 实施步骤

**第1步：Claude LLM实现（1-2天）**
```python
# 1. 创建ClaudeLLM类
# 2. 注册到LLMFactory
# 3. 测试基本功能
```

**第2步：数据库配置（0.5天）**
```python
# 1. 添加Claude模型配置
# 2. 设置为默认模型
# 3. 测试API调用
```

**第3步：测试和优化（1-2天）**
```python
# 1. 端到端测试
# 2. SQL准确性对比
# 3. 性能优化
```

---

## 📝 最终建议

### 长期方案：方案B + Claude Code Agent

```
Claude Code Agent（编排）+ SQLBot（RAG + Claude LLM）
     ↓
最佳组合：Agent能力 + RAG增强 + Claude LLM
```

#### 架构

```
用户问题
   ↓
Claude Code Agent（意图识别、技能路由）
   ↓
智能问数Skills（表理解、指标识别、维度提取）
   ↓
SQLBot REST API
   ↓
SQLBot LLMService（Claude LLM + RAG）
   ↓
生成SQL → 执行 → 返回结果
```

#### 优势

- ✅ Agent编排能力强（Claude Code）
- ✅ SQL准确性高（SQLBot的RAG + Claude LLM）
- ✅ 可扩展性好（Skills可独立开发）
- ✅ 工作量可控（各层独立开发）
- ✅ 风险分散（每层都有回退方案）

#### 总工作量

- 方案B（替换LLM）：2.5-4.5天
- Claude Code Agent开发：2-3天
- Skills开发：3-5天
- 集成测试：1-2天
- **总计：8.5-14.5天**

---

## 📋 总结

### SQLBot的SQL生成逻辑

1. **RAG增强**：Schema + 术语库 + SQL示例 + 自定义Prompt
2. **Prompt Engineering**：精心设计的Prompt模板
3. **LangChain集成**：通过LLMFactory调用各种LLM
4. **企业级特性**：权限控制、审计日志、数据隔离

### 换成Claude Code的可行性

| 方案 | 可行性 | 风险 | 工作量 | 推荐度 |
|------|-------|------|--------|-------|
| 方案A：完全替换 | ✅ 可行 | 高 | 10-17天 | ⭐⭐ |
| 方案B：保留RAG | ✅ 可行 | 低 | 2.5-4.5天 | ⭐⭐⭐⭐⭐ |
| 方案C：保持原样 | ✅ 可行 | 最低 | 4-6天 | ⭐⭐⭐ |

### 最终建议

**推荐方案B：保留SQLBot的RAG，替换LLM为Claude**

**长期架构：Claude Code Agent + SQLBot（RAG + Claude LLM）**

---

*文档生成时间：2026-02-08*
*最后更新：2026-02-08*
