# SQLBot 产品迭代路书

## 📁 文档说明

本文档是 SQLBot 产品的完整迭代路书，包含两个主要迭代方向：

1. **RAG 检索系统优化** - 提升 Text-to-SQL 的召回准确率
2. **SQLBot 双方案切换** - 支持 LLM 方案和 Claude Code 方案的灵活切换

---

## 📋 当前版本 (v1.0)

### ✅ 已完成功能

| 功能模块 | 状态 | 说明 |
|---------|------|------|
| Text-to-SQL 核心 | ✅ | LLM 生成 SQL 查询 |
| 三路 RAG 召回 | ✅ | 业务术语、SQL 示例、表结构 |
| 向量语义检索 | ✅ | text2vec-base-chinese + pgvector |
| ILIKE 模糊匹配 | ✅ | 关键词模糊匹配 |
| 多数据源支持 | ✅ | MySQL、PostgreSQL、Oracle、SQL Server、ClickHouse 等 |
| 图表自动生成 | ✅ | 自动选择图表类型并渲染 |
| 多轮对话 | ✅ | 上下文管理 |
| 权限控制 | ✅ | 行级数据过滤 |

### 🎯 核心指标 (当前)

| 指标 | 数值 | 说明 |
|-----|------|------|
| 召回率 | 65% | 检索到相关结果的比率 |
| 准确率 | 70% | 检索结果中相关的比率 |
| MRR | 0.55 | 平均倒数排名 |
| SQL 一次生成成功率 | 68% | 无需修改即执行成功的比率 |

---

## 🚀 迭代路线总览

SQLBot 有两个并行迭代的优化方向，但**战略定位不同**：

| 迭代方向 | 周期 | 推荐指数 | 战略定位 | 负责人 |
|---------|------|----------|----------|--------|
| **路线 A: RAG 检索优化** | 1-6 个月 | ⭐⭐⭐ | 备选方案 | 算法团队 |
| **路线 B: 双方案切换** | 2-3 周 | ⭐⭐⭐⭐ | **需验证** | 架构团队 |

### 🎯 战略决策

```
┌─────────────────────────────────────────────────────────────┐
│                    SQLBot 演进战略                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  当前状态 ──→ 过渡期 ──→ 最终状态                            │
│  (LLM方案)    (并行测试)   (Claude Code方案)                 │
│     │            │              │                           │
│     │    ┌───────┴───────┐      │                           │
│     │    │               │      │                           │
│     ▼    ▼               ▼      ▼                           │
│  ┌────────┐        ┌──────────┐  ┌────────────────────┐     │
│  │路线A   │        │路线A+B   │  │路线B全面接管        │     │
│  │RAG优化  │        │并行运行  │  │路线A逐步淘汰        │     │
│  │(可选)   │        │A/B测试  │  │(最终目标)          │     │
│  └────────┘        └──────────┘  └────────────────────┘     │
│     │                │              │                       │
│     └────────────────┴──────────────┘                       │
│                      ▼                                       │
│            ┌────────────────────┐                           │
│            │ Claude Code 方案    │                           │
│            │ • 无需复杂RAG优化   │                           │
│            │ • 直接读取MD文档    │                           │
│            │ • 更好的理解能力    │                           │
│            │ • 更低的维护成本    │                           │
│            └────────────────────┘                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 📋 决策建议（更新版）

| 决策点 | 建议 | 理由 |
|-------|------|------|
| **是否启动路线A** | ⚠️ 有条件启动 | 仅作为备选方案；路线B验证失败时继续投入；优先级降低 |
| **是否启动路线B** | ✅ 优先推荐 | 周期短、可验证；但需全面评估稳定性和时效性 |
| **资源分配** | 70% 路线B，30% 路线A | 路线B快速验证；路线A作为保险保留 |
| **评估周期** | 路线B上线后2-4周 | 延长评估期，充分测试稳定性和时效性 |
| **最终策略** | 🔄 双方案共存 | 根据场景智能路由，而非全面取代 |

---

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## 📍 路线 A: RAG 检索系统优化
## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

> **⚠️ 战略提示**: 本路线为**过渡方案**，建议在路线B（Claude Code方案）验证效果后再决定是否继续投入。
> 如果路线B效果优于预期，本路线可**终止或降级为备选方案**。

**目标**: 提升 Text-to-SQL 的召回准确率和用户提问容错性

### ⚖️ 路线A vs 路线B 对比

| 对比维度 | 路线A (RAG优化) | 路线B (双方案切换) |
|---------|----------------|-------------------|
| 实施周期 | 1-6 个月 | 2-3 周 |
| 技术复杂度 | 高 (ES/Qdrant/混合检索) | 低 (功能开关) |
| 维护成本 | 高 (多组件运维) | 低 (复用现有) |
| 效果提升 | +20-30% (预估) | 未知 (需实测) |
| 风险等级 | 🟡 中 (技术债务) | 🟢 低 (可回退) |
| **推荐度** | ⭐⭐⭐ (过渡方案) | ⭐⭐⭐⭐⭐ (最终方案) |

### 阶段规划

| 阶段 | 名称 | 周期 | 推荐指数 |
|-----|------|------|----------|
| **Phase 0** | **召回顺序与关联优化** | **1-2 周** | ⭐⭐⭐⭐⭐ |
| Phase 1 | RAG 检索优化 | 1-2 个月 | ⭐⭐⭐⭐ |
| Phase 2 | 向量检索升级 | 2-3 个月 | ⭐⭐⭐⭐ |
| Phase 3 | 智能检索增强 | 3-6 个月 | ⭐⭐⭐⭐ |

---

### Phase 0: 召回顺序与关联优化 (短期高优先级)

**时间周期**: 1-2 周
**推荐指数**: ⭐⭐⭐⭐⭐
**优先级**: **P0 (最高优先级)**

#### 问题分析

**当前召回顺序** ([llm.py:638-644](../backend/apps/chat/task/llm.py#L638-L644)):
```
1. filter_terminology_template()   → 术语召回 (基于问题语义 + 数据源过滤)
2. filter_training_template()       → SQL 示例召回 (基于问题语义 + 数据源过滤)
3. filter_custom_prompts()          → 自定义提示词
4. init_messages() → choose_table_schema() → 表结构召回
```

**当前数据模型关联**:
| 类型 | 当前关联字段 | 缺失的关联 |
|------|-------------|-----------|
| 术语 | `datasource_ids` (数据源级别) | ❌ 无表/字段级关联 |
| SQL 示例 | `datasource` (数据源级别) | ❌ 无表关联 |
| 维度值 | 通过 `CoreField.dimension_id` 与字段关联 | ✅ 已实现 |

**核心痛点**:
- 术语和 SQL 示例只基于问题语义召回，可能召回不相关的内容
- 无法根据表结构精准召回相关术语和示例
- 召回内容污染提示词，增加 Token 消耗

#### 优化方案

**优化后的召回顺序**:
```
1. choose_table_schema()            → 先召回表结构 (最基础的元数据)
2. 从表结构中提取表ID列表
3. filter_terminology_v2()          → 基于表ID + 问题召回术语
4. filter_training_v2()             → 基于表ID + 问题召回 SQL 示例
5. 维度值已在 get_table_schema 中处理 (datasource.py:482-485)
```

**收益评估**:
| 指标 | 当前 | 优化后 | 提升 |
|-----|------|--------|------|
| 召回精准度 | 70% | 90% | +20% |
| 无关内容召回 | 30% | 5% | -83% |
| Token 消耗 | 100% | 75% | -25% |
| SQL 一次成功率 | 68% | 80% | +12% |

#### 实施任务

##### 0.1 数据模型扩展

**优先级**: P0
**工作量**: 0.5 天

```sql
-- ===================================================
-- 术语表扩展：支持表/字段级关联
-- ===================================================
ALTER TABLE terminology ADD COLUMN table_ids JSONB DEFAULT '[]';
ALTER TABLE terminology ADD COLUMN field_ids JSONB DEFAULT '[]';
ALTER TABLE terminology ADD COLUMN scope VARCHAR(20) DEFAULT 'global';
COMMENT ON COLUMN terminology.scope IS '术语范围: global(全局) / table(表级) / field(字段级)';

-- 添加索引
CREATE INDEX idx_terminology_table_ids ON terminology USING GIN(table_ids);
CREATE INDEX idx_terminology_field_ids ON terminology USING GIN(field_ids);
CREATE INDEX idx_terminology_scope ON terminology(scope);

-- ===================================================
-- SQL 示例表扩展：支持表关联
-- ===================================================
ALTER TABLE data_training ADD COLUMN table_ids JSONB DEFAULT '[]';
COMMENT ON COLUMN data_training.table_ids IS '关联的表ID列表，用于精准召回';

-- 添加索引
CREATE INDEX idx_data_training_table_ids ON data_training USING GIN(table_ids);

-- ===================================================
-- 数据迁移：为现有数据设置默认范围
-- ===================================================
UPDATE terminology SET scope = 'global' WHERE scope IS NULL;
```

**数据模型变更**:

```python
# backend/apps/terminology/models/terminology_model.py
class Terminology(SQLModel, table=True):
    # ... existing fields ...
    table_ids: Optional[list[int]] = Field(sa_column=Column(JSONB), default=[])
    field_ids: Optional[list[int]] = Field(sa_column=Column(JSONB), default=[])
    scope: Optional[str] = Field(sa_column=Column(VARCHAR(20)), default='global')

# backend/apps/data_training/models/data_training_model.py
class DataTraining(SQLModel, table=True):
    # ... existing fields ...
    table_ids: Optional[list[int]] = Field(sa_column=Column(JSONB), default=[])
```

##### 0.2 前端表单改造

**优先级**: P0
**工作量**: 1 天

**术语配置页面** (`views/system/terminology/`):
- 添加"术语范围"选择器：全局 / 表级 / 字段级
- 表级术语：添加表选择器（多选）
- 字段级术语：添加字段选择器（多选，支持按表过滤）

**SQL 示例配置页面** (`views/system/data-training/`):
- 添加"关联表"选择器（多选）
- 支持从数据源导入所有表

##### 0.3 后端召回逻辑改造

**优先级**: P0
**工作量**: 2 天

**新增召回方法** ([llm.py](../backend/apps/chat/task/llm.py)):

```python
def filter_terminology_v2(self, _session: Session, table_ids: List[int] = None):
    """
    基于表结构优化的术语召回

    Args:
        table_ids: 相关表ID列表（从表结构召回中获取）

    召回策略:
        1. 优先召回：关联到这些表的术语 (scope='table' AND table_ids && ?)
        2. 次要召回：关联到这些表字段的术语 (scope='field' AND field_ids && ?)
        3. 补充召回：基于语义相似度的全局术语 (scope='global')
        4. 去重合并，按相似度排序
    """
    pass

def filter_training_v2(self, _session: Session, table_ids: List[int] = None):
    """
    基于表结构优化的 SQL 示例召回

    Args:
        table_ids: 相关表ID列表（从表结构召回中获取）

    召回策略:
        1. 优先召回：关联到这些表的 SQL 示例 (table_ids && ?)
        2. 次要召回：基于语义相似度的全局示例
        3. 去重合并，按相似度排序
    """
    pass

def init_messages_v2(self, session: Session):
    """
    优化的消息初始化：调整召回顺序

    新顺序:
        1. 先召回表结构
        2. 提取表ID
        3. 基于表ID召回术语和示例
    """
    # 1. 先召回表结构
    self.choose_table_schema(session)

    # 2. 从表结构中提取表ID
    table_ids = self._extract_table_ids_from_schema()

    # 3. 基于表ID召回术语和示例
    self.filter_terminology_v2(session, table_ids=table_ids)
    self.filter_training_v2(session, table_ids=table_ids)

    # 4. 继续原有逻辑...
    self.filter_custom_prompts(session, CustomPromptTypeEnum.GENERATE_SQL, oid, ds_id)
```

**CRUD 操作更新**:

```python
# backend/apps/terminology/curd/terminology.py
def get_terminologies_by_table_ids(session, table_ids: List[int], enabled_only: bool = True):
    """获取关联到指定表的术语"""
    conditions = [
        Terminology.enabled == True,
        Terminology.scope.in_(['table', 'field'])
    ]
    if table_ids:
        conditions.append(Terminology.table_ids.overlap(table_ids))

    stmt = select(Terminology).where(and_(*conditions))
    return session.exec(stmt).all()

# backend/apps/data_training/curd/data_training.py
def get_training_by_table_ids(session, table_ids: List[int], enabled_only: bool = True):
    """获取关联到指定表的 SQL 示例"""
    conditions = [DataTraining.enabled == True]
    if table_ids:
        conditions.append(DataTraining.table_ids.overlap(table_ids))

    stmt = select(DataTraining).where(and_(*conditions))
    return session.exec(stmt).all()
```

##### 0.4 问题智能增强 (Query Enhancement) ⭐ 可选

**优先级**: P1
**工作量**: 1-2 天
**类型**: 可选功能（默认关闭，可配置开启）

> **🔗 与路线B的集成**: 本功能不仅应用于路线A的RAG检索优化，同样已集成到路线B（Claude Code方案）中。详见 [SQLBot-SWITCH-DETAILED-DESIGN.md](./switch-design/SQLBot-SWITCH-DETAILED-DESIGN.md) 中的问题增强模块设计，确保两条优化路线共享相同的问题增强基础能力。

在召回前使用 LLM 对用户问题进行增强和补全，提升召回准确率。

**核心流程**:
```
用户问题 → 智能判断 → LLM增强/反问 → 三路召回 → 生成SQL
              ↓
        简单明确问题 → 直接召回
```

**典型场景**:

| 场景 | 用户问题 | LLM增强后 | 效果 |
|------|---------|----------|------|
| 表达模糊 | "今年卖了多少？" | "查询今年的销售额总额" | 明确指标和时间 |
| 缩写映射 | "DAU是多少？" | "查询日活跃用户数(DAU)" | 术语映射 |
| 缺失信息 | "销售额TOP10地区" | "请提供时间范围：按哪段时间统计？" | 主动反问 |
| 口语化 | "我要看最近的单子" | "查询最近30天的订单列表" | 标准化 |

**智能分流规则**:
```python
def should_enhance_question(question: str, context: dict) -> bool:
    """
    判断是否需要问题增强

    直接召回的情况（返回 False）：
    - 问题长度 ≥ 10字（与配置阈值一致）且 包含明确的表名/字段名
    - 是历史问题的重复
    - 包含明确的SQL关键词（SELECT, 查询等）

    需要 LLM 增强的情况（返回 True）：
    - 问题包含模糊时间词（今年、最近、上月等）
    - 问题包含业务缩写/术语（DAU, MAU, GMV等）
    - 聚合查询但缺少分组维度
    """
    pass
```

**增强模块设计**:

```python
# backend/apps/chat/task/query_enhancement.py

class QueryEnhancer:
    """问题增强器"""

    def enhance(self, question: str, context: dict) -> EnhancedResult:
        """
        增强用户问题

        Returns:
            EnhancedResult:
                - enhanced_question: 增强后的问题
                - needs_clalification: 是否需要用户补充信息
                - clarification_question: 反问用户的问题
                - detected_entities: 识别出的实体（表、字段、指标等）
        """
        pass

    def _detect_ambiguity(self, question: str) -> list[str]:
        """检测问题中的模糊点"""
        ambiguities = []

        # 检测时间模糊性
        if self._has_fuzzy_time(question):
            ambiguities.append("time_range")

        # 检测缩写/术语
        abbreviations = self._extract_abbreviations(question)
        if abbreviations:
            ambiguities.extend(abbreviations)

        # 检测缺失维度
        if self._is_aggregation_without_group_by(question):
            ambiguities.append("group_dimension")

        return ambiguities

    def _rewrite_question(self, question: str) -> str:
        """重写问题为标准形式"""
        prompt = f"""
将以下用户问题重写为更标准的查询问题：

原始问题：{question}

要求：
1. 保留原意
2. 明确模糊的时间表达（如"今年" → "2026年"）
3. 展开业务缩写（如"DAU" → "日活跃用户数"）
4. 补充可能缺失的信息（用方括号标注需要用户提供的信息）

重写后的问题：
"""
        # 调用 LLM
        return self.llm.predict(prompt)
```

**配置开关**:

```python
# backend/common/core/config.py

class Settings(BaseSettings):
    # 问题增强配置
    QUERY_ENHANCEMENT_ENABLED: bool = False  # 是否启用问题增强
    QUERY_ENHANCEMENT_THRESHOLD: int = 10  # 简单问题阈值（字符数）
    QUERY_ENHANCEMENT_ALLOW_FOLLOWUP: bool = True  # 是否允许反问用户
```

**收益评估**:
| 指标 | 不启用 | 启用后 | 提升 |
|-----|-------|--------|------|
| 召回准确率 | 70% | 88% | +18% |
| 用户满意度 | 75% | 92% | +17% |
| 平均响应时间 | 2.5s | 4.0s | +60% |
| Token消耗 | 基准 | +15% | +15% |

##### 0.5 嵌入向量更新

**优先级**: P1
**工作量**: 1 天

为新增的关联字段生成嵌入向量：

```python
# backend/common/utils/embedding_threads.py
def run_save_terminology_embeddings(terminology_ids: List[int] = None):
    """异步更新术语嵌入向量（包含新的关联信息）"""
    pass

def run_save_training_embeddings(training_ids: List[int] = None):
    """异步更新 SQL 示例嵌入向量（包含新的关联信息）"""
    pass
```

#### 实施计划

| 任务 | 工作量 | 负责人 | 依赖 | 类型 |
|-----|--------|--------|------|------|
| 0.1 数据模型扩展 | 0.5 天 | 后端 | - | 必须 |
| 0.2 前端表单改造 | 1 天 | 前端 | 0.1 | 必须 |
| 0.3 后端召回逻辑 | 2 天 | 后端 | 0.1 | 必须 |
| 0.4 问题智能增强 | 1-2 天 | 后端 | 0.1, 0.3 | **可选** |
| 0.5 嵌入向量更新 | 1 天 | 后端 | 0.1, 0.3 | 必须 |
| 0.6 测试验证 | 1 天 | 测试 | 全部 | 必须 |
| **总计（不含0.4）** | **5.5 天** | - | - | - |
| **总计（含0.4）** | **6.5-7.5 天** | - | - | - |

#### 验收标准

**必须完成**:
- [ ] 术语可配置为全局/表级/字段级
- [ ] SQL 示例可关联多个表
- [ ] 召回顺序调整为：表结构 → 术语 → 示例
- [ ] 术语和示例召回优先基于表关联过滤
- [ ] 召回精准度提升至 90%+
- [ ] 无关内容召回率降至 5% 以下
- [ ] 单元测试覆盖率 > 80%

**可选（如果启用 0.4）**:
- [ ] 问题可自动重写为标准形式
- [ ] 模糊问题可自动识别并增强
- [ ] 缩写/术语可自动映射
- [ ] 支持反问用户补充信息
- [ ] 问题增强可配置开关

---

### Phase 1: RAG 检索优化 (中期)

**时间周期**: 1-2 个月
**推荐指数**: ⭐⭐⭐⭐⭐

#### 1.1 关键词匹配增强

| 优先级 | 功能项 | 技术方案 | 预期收益 | 工作量 |
|-------|--------|----------|----------|--------|
| P0 | 中文分词支持 | jieba 分词 + ILIKE 优化 | +15-20% | 2天 |
| P0 | 多字段组合匹配 | word + description + question | +10% | 1天 |
| P1 | 拼音检索支持 | pinyin 转换匹配 | +8% | 2天 |
| P1 | 模糊匹配优化 | pg_trgm 词汇相似度 | +12% | 2天 |

**数据库变更**:
```sql
-- 安装 PostgreSQL 扩展
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS zhparser;

-- 添加全文检索索引
ALTER TABLE terminology ADD COLUMN word_tsv tsvector;
CREATE INDEX idx_terminology_tsv ON terminology USING GIN(word_tsv);

ALTER TABLE data_training ADD COLUMN question_tsv tsvector;
CREATE INDEX idx_data_training_tsv ON data_training USING GIN(question_tsv);
```

#### 1.2 混合检索 (Hybrid Search) ⭐

**架构图**:
```
                    用户问题
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
   ┌─────────┐     ┌─────────┐     ┌─────────┐
   │ 关键词   │     │ 向量     │     │ 模糊     │
   │ BM25    │     │ Embedding│     │ ILIKE   │
   └─────────┘     └─────────┘     └─────────┘
        │                │                │
        └────────────────┼────────────────┘
                         ▼
                  ┌──────────────┐
                  │  RRF 融合     │
                  │  倒数排名融合  │
                  └──────────────┘
                         │
                         ▼
                    最终召回结果
```

**收益评估**:
| 指标 | 当前 | 优化后 | 提升 |
|-----|------|--------|------|
| 召回准确率 | 70% | 90% | +20% |
| 提问容错性 | 50% | 70% | +40% |
| 复杂问题解决率 | 60% | 75% | +25% |

#### 1.3 智能召回策略

**策略矩阵**:

| 问题类型 | 检索策略 | 关键词权重 | 向量权重 | 示例权重 |
|---------|---------|-----------|---------|---------|
| 简单查询 (单表) | 关键词优先 | 70% | 30% | - |
| 复杂查询 (多表) | 语义优先 | 40% | 60% | - |
| 聚合统计 | SQL 示例优先 | 10% | 10% | 80% |
| 模糊提问 | 均衡策略 | 50% | 50% | - |
| 专业术语 | 术语优先 | 70% | 30% | - |

### Phase 2: 向量检索升级 (中期)

**时间周期**: 2-3 个月
**推荐指数**: ⭐⭐⭐⭐

#### 2.1 向量模型升级

| 对比项 | 当前 | 升级方案 A | 升级方案 B |
|-------|------|-----------|-----------|
| 模型 | text2vec-base | bge-large-zh | m3e-base |
| 维度 | 768 | 1024 | 768 |
| 语义理解 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 中文优化 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 性能 | 快 | 中等 | 快 |
| 准确率提升 | - | +20-25% | +15-20% |
| **推荐** | - | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |

#### 2.2 向量库选型

| 方案 | 优势 | 劣势 | 复杂度 | 推荐度 |
|-----|------|------|--------|--------|
| **pgvector** | 架构简单，无需迁移 | 性能有限，功能单一 | 低 | ⭐⭐⭐ |
| **Milvus** | 功能强大，性能优秀 | 架构复杂，需额外运维 | 高 | ⭐⭐⭐⭐⭐ |
| **Qdrant** | 轻量，Rust 实现 | 生态相对较小 | 中 | ⭐⭐⭐⭐ |
| **Elasticsearch** | 全文检索强，向量支持 | 资源消耗大 | 高 | ⭐⭐⭐ |

**推荐路径**: `pgvector → Qdrant` (轻量级方案)

### Phase 3: 智能检索增强 (长期)

**时间周期**: 3-6 个月
**推荐指数**: ⭐⭐⭐⭐

#### 3.1 查询重写 (Query Rewriting)

```
┌─────────────────────────────────────────────────────────┐
│                    查询重写流程                          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  原始提问: "今年卖了多少？"                            │
│     ↓                                                  │
│  ┌─────────────┐                                        │
│  │ LLM 重写     │ → "查询今年的销售额总额"              │
│  └─────────────┘                                        │
│     ↓                                                  │
│  ┌─────────────┐                                        │
│  │ 意图识别     │ → 聚合统计查询                       │
│  └─────────────┘                                        │
│     ↓                                                  │
│  优化召回: sales, revenue, SUM(amount), YEAR(order_date)│
│                                                         │
└─────────────────────────────────────────────────────────┘
```

#### 3.2 意图识别与路由

```
用户提问 → 意图分析 → 检索策略选择
    │           │              │
    │      ┌─────┴─────┐    ┌───┴───┐
    │      │ 简单查询  │    │关键词优先│
    │      │ 复杂查询  │    │语义优先  │
    │      │ 聚合统计  │    │示例优先  │
    │      │ 趋势分析  │    │历史问题  │
    │      │ 对比分析  │    │多表联合  │
    └──────→────────────┘    └─────────┘
```

#### 3.3 自适应召回调优

```python
class AdaptiveRetriever:
    """自适应召回器 - 根据用户反馈优化参数"""

    def __init__(self):
        self.params = {
            'keyword_weight': 0.5,
            'vector_weight': 0.5,
            'similarity_threshold': 0.6,
            'top_k': 10
        }

    def adjust_by_feedback(self, query, result, feedback):
        """根据用户反馈调整参数"""
        if feedback.satisfaction < 0.6:
            self.params['top_k'] = min(self.params['top_k'] + 5, 50)
            self.params['similarity_threshold'] = max(self.params['similarity_threshold'] - 0.05, 0.3)

        if feedback.used_sql_example:
            self.params['example_weight'] = self.params.get('example_weight', 0) + 0.1

        return self.params
```

---

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## 📍 路线 B: SQLBot 双方案切换设计
## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

> **✅ 战略定位**: 本路线为**最终方案**，实施成功后可逐步取代路线A，使RAG优化变得不再必要。

**目标**: 支持 LLM 方案和 Claude Code 方案的灵活切换，提升系统的可扩展性

### ⚖️ 路线B 全面的优缺点分析

#### ✅ 优势

| 优势 | 说明 | 影响程度 |
|------|------|----------|
| **快速实施** | 2-3周即可完成，远快于路线A的1-6个月 | ⭐⭐⭐⭐⭐ |
| **零架构变更** | 无需引入ES、Qdrant等新组件 | ⭐⭐⭐⭐⭐ |
| **主动交互能力** | Claude Code可主动要求用户补全缺失信息（如时间范围、具体指标等） | ⭐⭐⭐⭐⭐ |
| **理解能力强** | 直接读取MD文档，对复杂业务逻辑理解可能优于RAG | ⭐⭐⭐⭐ |
| **可随时回退** | 功能开关控制，Claude Code失败自动降级 | ⭐⭐⭐⭐ |
| **维护成本低** | 复用现有SQLBot后端逻辑 | ⭐⭐⭐⭐ |
| **效果可验证** | 可通过A/B测试对比两种方案效果 | ⭐⭐⭐⭐ |

#### ⚠️ 劣势与风险

| 劣势 | 说明 | 影响程度 | 缓解措施 |
|------|------|----------|----------|
| **稳定性不确定** | 智能体输出具有不确定性，难以保证每次结果稳定 | 🔴 高 | 保留LLM方案作为备用；设置重试和降级机制 |
| **时效性波动** | Claude Code响应时间受网络/API影响，可能不稳定 | 🟡 中 | 设置超时机制（如30秒）；超时自动切换LLM方案 |
| **可控性差** | 完全交给智能体，无法精确控制输出格式和逻辑 | 🟡 中 | 使用结构化Prompt；增加后处理验证 |
| **外部依赖** | 依赖Claude API可用性和稳定性 | 🟡 中 | 多区域部署；API失败自动降级 |
| **成本未知** | Claude API调用成本需实测评估 | 🟢 低 | 设置额度限制；监控使用量 |
| **调试困难** | 智能体决策过程不透明，问题定位较难 | 🟢 低 | 详细日志记录；保存完整对话上下文 |

#### 📊 综合评估

| 评估维度 | 路线A (RAG优化) | 路线B (双方案切换) |
|---------|----------------|-------------------|
| 实施速度 | 🐢 慢 (1-6月) | 🚀 快 (2-3周) |
| 架构复杂度 | 🔴 高 | 🟢 低 |
| 稳定性 | 🟢 高 (确定性系统) | 🟡 中 (智能体不确定) |
| 响应时效 | 🟢 稳定可预测 | 🟡 波动不确定 |
| 交互能力 | 🔴 差 (被动) | 🟢 优 (主动补全信息) |
| 长期价值 | 🟡 中 (可能被取代) | 🟢 高 (最终方案) |
| **推荐度** | ⭐⭐⭐ 过渡方案 | ⭐⭐⭐⭐ 需验证 |

### 🔄 路线取代策略（更新版）

```
┌─────────────────────────────────────────────────────────────┐
│                   谨慎的渐进式切换策略                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ⚠️ 核心原则: 保留双方案，根据场景智能选择                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘

阶段1: 双方案并行实施 (2-3周)
├─ 实施路线B功能开关
├─ 保留路线A现有功能（不废弃）
└─ 两种方案同时可用

阶段2: A/B测试与评估 (2-4周，延长)
├─ 对比两种方案效果
├─ 收集用户反馈
├─ 重点关注：稳定性、时效性、用户满意度
└─ 记录Claude Code主动提问的成功率

阶段3: 决策点（基于多维度评估）
├─ 评估维度：
│  ├─ SQL生成准确率（目标：>80%）
│  ├─ 响应时间稳定性（目标：P95 < 10秒）
│  ├─ 系统稳定性（目标：故障率 < 5%）
│  ├─ 用户满意度（目标：>75%）
│  └─ 主动提问有效性（目标：>60%用户觉得有帮助）
│
├─ 决策分支：
│  ├─ 全部达标 → 继续阶段4
│  ├─ 部分达标 → 优化后重新评估
│  └─ 多数不达标 → 终止路线B，继续路线A
│

阶段4: 场景化智能分配（非全面切换）
├─ Claude Code适用场景 (30-50%)：
│  ├─ 复杂业务逻辑查询
│  ├─ 需要补全信息的问题
│  ├─ 跨表关联分析
│  └─ 用户明确表示"不知道怎么问"
│
├─ LLM方案适用场景 (50-70%)：
│  ├─ 简单查询（单表、常用指标）
│  ├─ 时效性要求高的场景
│  ├─ 高频重复性查询
│  └─ Claude Code故障时的降级
│
└─ 路线A的RAG优化：
   ├─ 根据阶段3评估结果决定是否继续
   └─ 即使继续，优先级降低

最终状态：双方案长期共存，智能路由分配
```

### 📑 方案文档系列

> **🔗 与Phase 0的联动**: 路线B（Claude Code方案）已集成Phase 0.4的问题智能增强功能。通过功能开关 `claude_code_query_enhancement_enabled` 可启用/禁用此能力，确保Claude Code方案也能在处理用户问题时获得智能增强和反问补全的能力。详见上文 [Phase 0.4 问题智能增强](#04-问题智能增强-query-enhancement--可选)。

| 版本 | 文件 | 时间 | 核心改进 | 推荐指数 |
|------|------|------|----------|----------|
| V1 | [SQLBot-SWITCH-DESIGN.md](./SQLBot-SWITCH-DESIGN.md) | 09:57 | 基础双方案切换 | ⭐⭐⭐ |
| V2 | [SQLBot-SWITCH-DESIGN-V2.md](./SQLBot-SWITCH-DESIGN-V2.md) | 10:05 | 按SQLBot架构模式设计 | ⭐⭐⭐⭐ |
| V3 | [SQLBot-SWITCH-DESIGN-V3.md](./SQLBot-SWITCH-DESIGN-V3.md) | 10:18 | 增加RAG检索切换 | ⭐⭐⭐⭐ |
| V4 | [SQLBot-SWITCH-DESIGN-V4.md](./SQLBot-SWITCH-DESIGN-V4.md) | 10:25 | 职责明确 | ⭐⭐⭐⭐⭐ |
| V5 | [SQLBot-SWITCH-DESIGN-V5.md](./SQLBot-SWITCH-DESIGN-V5.md) | 10:34 | 三端职责明确 | ⭐⭐⭐⭐⭐ |
| **V6** | [SQLBot-SWITCH-DETAILED-DESIGN.md](./SQLBot-SWITCH-DETAILED-DESIGN.md) | 10:41 | 详细设计（最终版） | ⭐⭐⭐⭐⭐ |

### 🎯 核心设计

#### 三端职责

| 端 | 职责 |
|----|------|
| **Claude Code** | 读取 MD 文件 + 生成 SQL |
| **SQLBot 后端** | 执行 SQL + 生成图表 + 返回结果 |
| **前端** | 展示 SQL、数据、图表 |

#### 架构图

```
                              ┌─────────────────────────────────────┐
                              │           【前端】                    │
                              │  • 用户输入                          │
                              │  • 结果展示                          │
                              └─────────────────┬───────────────────┘
                                                │
                                                ▼
                              ┌─────────────────────────────────────┐
                              │       SQLBot API                    │
                              │    /chat/question                   │
                              └─────────────────┬───────────────────┘
                                                │
                                                ▼
                    ┌───────────────────────────────────────────────────────┐
                    │               问题智能增强 ⚡ (可选)                     │
                    │           claude_code_query_enhancement_enabled        │
                    │  • 智能判断  • LLM增强/反问  • 问题重写                   │
                    └─────────────────────────────┬─────────────────────────┘
                                                  │
                                                  ▼
                              ┌─────────────────────────────────────┐
                              │         功能开关判断                  │
                              │      system_variable                │
                              └─────────────┬───────────────────────┘
                                            │
                    ┌───────────────────────┴───────────────────────┐
                    │                                               │
                    ▼                                               ▼
        ┌───────────────────────┐                   ┌───────────────────────────┐
        │       LLM方案          │                   │      Claude Code 方案      │
        └───────────┬───────────┘                   └───────────────┬───────────┘
                    │                                               │
                    ▼                                               ▼
    ┌─────────────────────────────────────┐           ┌───────────────────────────┐
    │        【SQLBot后端】三路召回         │           │     【Claude Code】        │
    ├─────────────────────────────────────┤           │     读取MD文件             │
    │  ① 表结构召回 → ② 提取表ID           │           └─────────────┬─────────────┘
    │           ↓                         │                           │
    │  ③ 术语/示例召回 v2                 │                           ▼
    │     (基于表ID+语义)                  │           ┌───────────────────────────┐
    │           ↓                         │           │     【Claude Code】        │
    │  【SQLBot后端】LLM生成SQL            │           │     生成SQL               │
    └─────────────────┬───────────────────┘           └─────────────┬─────────────┘
                      │                                               │
                      └───────────────────────────┬───────────────────┘
                                                │
                                                ▼
                    ┌─────────────────────────────────────────────────────────────┐
                    │                    【SQLBot后端】                              │
                    │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
                    │  │  执行SQL    │→ │  生成图表   │→ │  返回结果   │          │
                    │  └─────────────┘  └─────────────┘  └──────┬──────┘          │
                    └───────────────────────────────────────────┼──────────────────┘
                                                                │
                                                                ▼
                                              ┌─────────────────────────────────────┐
                                              │           【前端】展示结果            │
                                              └─────────────────────────────────────┘
```

**图注**:
- ⚡ **问题智能增强模块**：可配置开启/关闭，作用于两种方案
- 当增强功能开启时，会智能判断问题复杂度，对模糊/不完整的问题进行增强或反问
- 详见上文 [Phase 0.4 问题智能增强](#04-问题智能增强-query-enhancement--可选)

### 🎯 核心优势

- ✅ 三端职责明确
- ✅ 零表结构变更
- ✅ 保持代码风格
- ✅ 向后兼容
- ✅ 平滑切换
- ✅ 最小改动
- ✅ 前端无需改动
- ✅ 自动降级
- ✅ 复用现有逻辑

### 📋 实施计划

| 阶段 | 任务 | 时间 | 负责人 |
|-----|------|------|--------|
| Phase 1 | 功能开关模块 | 2-3 小时 | 后端 |
| Phase 2 | Claude Code 客户端 | 3-4 小时 | 后端 |
| Phase 3 | Claude Code 方案任务 | 2-3 小时 | 后端 |
| Phase 4 | 策略工厂 | 2-3 小时 | 后端 |
| Phase 5 | API 改造 | 2-3 小时 | 后端 |
| Phase 6 | 测试和优化 | 2-3 小时 | 测试 |

**总计**: 13-19 小时

### 📁 详细设计文档

- **最终版本**: [SQLBot-SWITCH-DETAILED-DESIGN.md](./SQLBot-SWITCH-DETAILED-DESIGN.md) ⭐

---

## 📊 成功指标汇总

### 路线 A: RAG 检索优化指标

| 指标 | 当前 | Phase 1 | Phase 2 | Phase 3 |
|-----|------|---------|---------|---------|
| 召回率 | 65% | 80% | 90% | 95% |
| 准确率 | 70% | 85% | 92% | 96% |
| MRR | 0.55 | 0.70 | 0.80 | 0.88 |
| 用户满意度 | 72% | 82% | 90% | 94% |

### 路线 B: 双方案切换指标

| 指标 | 目标 | 说明 |
|-----|------|------|
| 方案切换时间 | < 100ms | 功能开关判断耗时 |
| 自动降级率 | < 5% | Claude Code 失败自动回退 |
| 代码改动量 | < 500 行 | 最小化改动原则 |
| 前端改动 | 0 行 | 前端无需改动 |

---

## 📈 资源需求

### 人力需求

| 角色 | 路线 A (RAG) | 路线 B (双方案) |
|-----|-------------|---------------|
| 后端开发 | Phase 1-3 | 13-19 小时 |
| 算法工程师 | Phase 1-3 | - |
| 测试工程师 | Phase 1-3 | Phase 6 |

### 基础设施

| 资源 | 当前 | 路线 A (最终) | 路线 B (最终) |
|-----|------|--------------|--------------|
| 数据库 | PostgreSQL | + Qdrant | 无变化 |
| 存储 | 100GB | 1TB | 无变化 |
| 内存 | 16GB | 64GB | 无变化 |

---

## ⚠️ 技术债务与风险

| 风险项 | 等级 | 路线 | 缓解措施 |
|-------|------|------|----------|
| PostgreSQL 全文检索性能 | 🟡 中 | A | 添加 GIN 索引，评估 ES 迁移 |
| 向量模型升级兼容性 | 🟢 低 | A | 充分测试，保留回滚方案 |
| 混合检索复杂度 | 🟡 中 | A | 分阶段实施，单元测试覆盖 |
| Qdrant 运维成本 | 🟢 低 | A | 轻量级部署，资源监控 |
| 功能开关配置管理 | 🟡 中 | B | 使用 system_variable 表，管理员权限 |
| Claude Code 依赖稳定性 | 🟡 中 | B | 自动降级机制，日志审计 |

---

## 🔗 快速链接

### RAG 检索优化

- 📊 [Text-to-SQL 流程图](./text2sql-flowchart.md)
- 📝 [后端语言对比](./backend-language-comparison.md)
- 🏢 [Epoint 一本账分析](./szy-epoint-aichat-analysis.md)

### 双方案切换

- 🎯 **[详细设计文档 V6](./SQLBot-SWITCH-DETAILED-DESIGN.md)** - 最终版，推荐使用
- 📜 [方案演进历史](./README.md) - V1 到 V6 的完整演进

### 技术参考

| 文档 | 说明 |
|------|------|
| [PostgreSQL 全文检索](https://www.postgresql.org/docs/current/textsearch/) | pg_trgm, zhparser |
| [pgvector 文档](https://github.com/pgvector/pgvector) | 向量相似度搜索 |
| [Qdrant 文档](https://qdrant.tech/documentation/) | 向量库使用指南 |
| [RRF 算法论文](https://plg.uwaterloo.ca/~clottruer/Downloads/SSM09.pdf) | 倒数排名融合 |

---

## 📝 变更记录

| 版本 | 日期 | 变更内容 | 作者 |
|-----|------|----------|------|
| v1.0 | 2026-02-11 | 初始版本，创建 RAG 检索优化路线图 | SQLBot Team |
| v1.1 | 2026-02-11 | 添加 SQLBot 双方案切换设计，整合两条迭代路线 | SQLBot Team |
| v1.2 | 2026-02-11 | **战略调整**: 明确路线B为最终方案，路线A为过渡方案；添加路线取代策略和决策建议 | SQLBot Team |
| v1.3 | 2026-02-11 | **全面评估**: 添加路线B完整优缺点分析（稳定性、时效性风险）；更新为谨慎渐进式切换策略；调整为双方案长期共存而非全面取代 | SQLBot Team |
| v1.4 | 2026-02-11 | **Phase 0 新增**: 添加召回顺序与关联优化方案（增强关联方案）；扩展术语和 SQL 示例数据模型支持表/字段级关联；调整召回顺序为：表结构 → 术语 → 示例 | SQLBot Team |

---

**最后更新**：2026-02-11
**维护者**：SQLBot Team
