# SQLBot Text-to-SQL 召回匹配与提示词构建流程图

## 完整流程图

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              用户提问: "今年销售额是多少？"                          │
└─────────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           LLMService.generate_sql()                             │
│                           (apps/chat/task/llm.py)                               │
└─────────────────────────────────────────────────────────────────────────────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    │                 │                 │
                    ▼                 ▼                 ▼
            ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
            │ 1.业务术语检索 │  │ 2.SQL示例检索 │  │ 3.表结构检索  │
            └──────────────┘  └──────────────┘  └──────────────┘
                    │                 │                 │
                    ▼                 ▼                 ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              RAG 召回阶段                                        │
├─────────────────────────────────────────────────────────────────────────────────┤
│  1. 业务术语检索 (terminology)                                                   │
│     - 位置: apps/terminology/curd/terminology.py                                 │
│     - 检索方式: ILIKE 模糊匹配 + 向量余弦相似度                                   │
│     - 返回: 相关业务术语及其同义词                                               │
│                                                                                 │
│  2. SQL 示例检索 (data_training)                                                │
│     - 位置: apps/data_training/curd/data_training.py                             │
│     - 检索方式: 双向 ILIKE + 向量相似度                                          │
│     - 返回: 相似的历史 SQL 示例                                                 │
│                                                                                 │
│  3. 表结构检索 (table schema)                                                   │
│     - 位置: apps/datasource/crud/datasource.py                                   │
│     - 检索方式: 表嵌入向量排序 (calc_table_embedding)                            │
│     - 返回: 相关性最高的表结构 (M-Schema 格式)                                   │
└─────────────────────────────────────────────────────────────────────────────────┘
                    │                 │                 │
                    └─────────────────┼─────────────────┘
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         提示词模板加载与组装                                      │
│                         (templates/template.yaml)                               │
├─────────────────────────────────────────────────────────────────────────────────┤
│  模板结构:                                                                       │
│  ├── system: 系统指令                                                            │
│  ├── process_check: SQL生成检查流程                                            │
│  ├── query_limit/no_query_limit: 数据量限制规则                                 │
│  ├── multi_table_condition: 多表查询规则                                        │
│  ├── terminology: 业务术语模板                                                   │
│  ├── data_training: SQL示例模板                                                 │
│  └── user: 用户问题模板                                                         │
└─────────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          构建 System Message                                     │
│                          (sql_sys_question)                                     │
├─────────────────────────────────────────────────────────────────────────────────┤
│  [系统指令] + [检查流程] + [数据库规则] + [业务术语] + [SQL示例] + [自定义提示]  │
│                                                                                 │
│  = system + process_check + basic_sql_examples +                                │
│    terminology + data_training + custom_prompt                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          构建 User Message                                       │
│                          (sql_user_question)                                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│  <Info>                                                                          │
│    <db-engine> PostgreSQL 14 </db-engine>                                       │
│    <m-schema>                                                                    │
│      【DB_ID】 mydatabase                                                        │
│      【Schema】                                                                  │
│      # Table: users                                                             │
│      [(id, name, age, create_time)]                                             │
│      # Table: orders                                                            │
│      [(id, user_id, amount, order_date)]                                        │
│    </m-schema>                                                                  │
│    <terminologies>                                                               │
│      <terminology>                                                              │
│        <words><word>销售额</word><word>营收</word></words>                       │
│        <description>订单金额总和</description>                                   │
│      </terminology>                                                             │
│    </terminologies>                                                             │
│    <sql-examples>                                                               │
│      <example>                                                                  │
│        <question>查询今年订单总额</question>                                     │
│        <suggestion-answer>SELECT SUM(amount) FROM orders WHERE...</suggestion-answer>│
│      </example>                                                                 │
│    </sql-examples>                                                              │
│  </Info>                                                                         │
│  <user-question>今年销售额是多少？</user-question>                              │
└─────────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        构建 Messages 列表                                         │
├─────────────────────────────────────────────────────────────────────────────────┤
│  messages = [                                                                    │
│    SystemMessage(content=系统提示词),                                           │
│    ...历史对话消息... (如果有多轮对话)                                           │
│    HumanMessage(content=用户问题+上下文)                                         │
│  ]                                                                              │
└─────────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           调用 LLM 生成 SQL                                      │
│                           llm.stream(messages)                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          流式返回结果                                             │
├─────────────────────────────────────────────────────────────────────────────────┤
│  {                                                                               │
│    "sql": "SELECT SUM(amount) FROM orders WHERE ...",                          │
│    "thinking": "用户问的是销售额，需要计算订单金额总和...",                       │
│    "chart_type": "table",                                                       │
│    "title": "今年销售额统计"                                                     │
│  }                                                                              │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## 详细检索流程

### 1. 业务术语检索 (Terminology Retrieval)

```
┌─────────────────────────────────────────────────────────────┐
│           select_terminology_by_word(sentence)              │
└─────────────────────────────────────────────────────────────┘
                            │
                ┌───────────┴───────────┐
                │                       │
                ▼                       ▼
    ┌───────────────────┐   ┌───────────────────────┐
    │  关键词模糊匹配     │   │  向量相似度匹配        │
    │  ILIKE '%word%'   │   │  余弦相似度计算        │
    └───────────────────┘   └───────────────────────┘
                │                       │
                └───────────┬───────────┘
                            ▼
                ┌───────────────────────┐
                │  合并去重，按相似度排序  │
                │  LIMIT TOP_COUNT      │
                └───────────────────────┘
                            │
                            ▼
            ┌───────────────────────────────────────┐
            │  <terminologies>                       │
            │    <terminology>                       │
            │      <words>                          │
            │        <word>销售额</word>             │
            │        <word>营收</word>               │
            │      </words>                         │
            │      <description>订单金额总和</description>│
            │    </terminology>                      │
            │  </terminologies>                      │
            └───────────────────────────────────────┘
```

### 2. SQL 示例检索 (Data Training Retrieval)

```
┌─────────────────────────────────────────────────────────────┐
│           select_training_by_question(question)            │
└─────────────────────────────────────────────────────────────┘
                            │
                ┌───────────┴───────────┐
                │                       │
                ▼                       ▼
    ┌───────────────────┐   ┌───────────────────────┐
    │  双向模糊匹配      │   │  向量相似度匹配        │
    │  question ILIKE   │   │  嵌入向量余弦相似度    │
    │  sentence OR      │   │                      │
    │  sentence ILIKE   │   │                      │
    │  question         │   │                      │
    └───────────────────┘   └───────────────────────┘
                │                       │
                └───────────┬───────────┘
                            ▼
                ┌───────────────────────┐
                │  按相似度排序           │
                │  LIMIT TOP_COUNT      │
                └───────────────────────┘
                            │
                            ▼
            ┌───────────────────────────────────────┐
            │  <sql-examples>                        │
            │    <example>                           │
            │      <question>查询今年订单总额</question>│
            │      <suggestion-answer>               │
            │        SELECT SUM(amount)...           │
            │      </suggestion-answer>              │
            │    </example>                          │
            │  </sql-examples>                       │
            └───────────────────────────────────────┘
```

### 3. 表结构检索 (Table Schema Retrieval)

```
┌─────────────────────────────────────────────────────────────┐
│              get_table_schema(datasource_id)                │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
                ┌───────────────────────┐
                │  获取数据源所有表和字段  │
                └───────────────────────┘
                            │
                            ▼
                ┌───────────────────────┐
                │  表嵌入相似度计算      │
                │  (TABLE_EMBEDDING)    │
                └───────────────────────┘
                            │
                            ▼
                ┌───────────────────────┐
                │  按相关性排序           │
                │  LIMIT TOP_COUNT      │
                └───────────────────────┘
                            │
                            ▼
            ┌───────────────────────────────────────┐
            │  <m-schema>                            │
            │    【DB_ID】 mydatabase                │
            │    【Schema】                          │
            │    # Table: users                     │
            │    [                                   │
            │      (id: bigint, PK, 用户ID),         │
            │      (name: varchar, 用户名),          │
            │      (age: integer, 年龄),             │
            │      (create_time: timestamp, 创建时间)│
            │    ]                                   │
            │    # Table: orders                    │
            │    [                                   │
            │      (id: bigint, PK, 订单ID),         │
            │      (user_id: bigint, 用户ID),        │
            │      (amount: decimal, 订单金额),      │
            │      (order_date: date, 订单日期)      │
            │    ]                                   │
            │  </m-schema>                           │
            └───────────────────────────────────────┘
```

## 最终提示词结构

```xml
你是"SQLBOT"，智能问数小助手...

<SQL-Generation-Process>
  <step>1. 分析用户问题，确定查询需求</step>
  <step>2. 根据表结构生成基础SQL</step>
  <step>3. 强制检查：验证表名和字段名</step>
  <step>4. 强制检查：应用数据量限制</step>
  <step>5. 应用其他规则</step>
  <step>6. 强制检查：验证SQL语法</step>
  <step>7. 确定图表类型</step>
  <step>8. 确定对话标题</step>
  <step>9. 返回JSON结果</step>
</SQL-Generation-Process>

<Rules>
  <rule>使用语言: {lang}</rule>
  <rule>只能生成查询SQL</rule>
  <rule>不要编造表结构</rule>
  <rule>符合数据库引擎规范</rule>
  <rule>数据量限制策略</rule>
  <rule>多表查询字段限定</rule>
</Rules>

<Info>
  <db-engine> PostgreSQL 14 </db-engine>

  <m-schema>
    【DB_ID】 mydatabase
    【Schema】
    # Table: users
    [(id: bigint, PK, 用户ID), (name: varchar, 用户名), ...]
    # Table: orders
    [(id: bigint, PK, 订单ID), (amount: decimal, 订单金额), ...]
  </m-schema>

  <terminologies>
    <terminology>
      <words>
        <word>销售额</word>
        <word>营收</word>
      </words>
      <description>订单金额总和</description>
    </terminology>
  </terminologies>

  <sql-examples>
    <example>
      <question>查询今年订单总额</question>
      <suggestion-answer>
        SELECT SUM(amount) FROM orders
        WHERE order_date >= '2024-01-01'
      </suggestion-answer>
    </example>
  </sql-examples>
</Info>

<user-question>今年销售额是多少？</user-question>
<current-time>2024-08-08 11:23:00</current-time>
```

## 核心代码位置

| 功能模块 | 文件路径 |
|---------|----------|
| LLM 服务 | `apps/chat/task/llm.py` |
| 业务术语检索 | `apps/terminology/curd/terminology.py` |
| SQL 示例检索 | `apps/data_training/curd/data_training.py` |
| 表结构检索 | `apps/datasource/crud/datasource.py` |
| 提示词模板 | `templates/template.yaml` |
| 嵌入向量生成 | `common/utils/embedding_threads.py` |
| 向量模型 | `text2vec-base-chinese` (768维) |
