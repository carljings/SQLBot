# SQLBot 文档中心

## 目录结构

```
docs/
├── README.md                                   # 本文件
├── roadmap.md                                  # 产品迭代路书（含 Phase 0 召回优化方案）
│
└── architecture/                               # 架构设计文档
    ├── SQLBot-Current-Architecture-Design.md        # 当前系统架构详细设计 ⭐
    ├── SQLBot-SWITCH-DETAILED-DESIGN.md         # 双方案切换详细设计（v6.0 最终版）⭐
    ├── SQLBot-Architecture-Comparison.md          # 架构演进对比分析
    │
    ├── technical/                                 # 技术文档子目录
    │   ├── backend-language-comparison.md           # 后端语言对比
    │   ├── rag-recall-order-optimization.md      # RAG 召回顺序优化
    │   ├── text2sql-flowchart.md                # Text-to-SQL 流程图
    │   └── text2sql-projects-comparison.md      # Text-to-SQL 项目对比
    │
    ├── project-analysis/                          # 项目分析子目录
    │   ├── szy-epoint-aichat-analysis.md       # Epoint AIChat 分析
    │   ├── sz-ybz-agent-architecture.md         # 一本账 Agent 架构
    │   └── sz-ybz-claude-code-architecture.md  # 一本账 Claude Code 架构
    │
    ├── switch-design/                             # 双方案切换设计（历史版本目录）
    │   └── versions/                              # V1 到 V5 历史版本
    │       ├── SQLBot-SWITCH-DESIGN.md          # V1 版本
    │       ├── SQLBot-SWITCH-DESIGN-V2.md        # V2 版本
    │       ├── SQLBot-SWITCH-DESIGN-V3.md        # V3 版本
    │       ├── SQLBot-SWITCH-DESIGN-V4.md        # V4 版本
    │       └── SQLBot-SWITCH-DESIGN-V5.md        # V5 版本
    │
    └── versions/                                  # 架构历史版本文档
        ├── SQLBot-Architecture-Comparison.md     # 架构对比分析
        ├── claude-code-architecture-v2.md          # Claude Code 架构 v2
        ├── claude-code-architecture-v3.md          # Claude Code 架构 v3
        ├── claude-code-architecture-v5.md          # Claude Code 架构 v5
        ├── claude-code-architecture-v6.md          # Claude Code 架构 v6
        ├── claude-code-data-flow.md               # Claude Code 数据流
        ├── dual-mode-architecture.md              # 双模式架构
        ├── solution-b-detailed-implementation.md # 路线 B 详细实现
        └── sqlbot-vs-claude-code-comparison.md  # SQLBot vs Claude Code 对比
```

## 快速导航

### 产品规划

- 📋 **[产品迭代路书](./roadmap.md)** - 完整的产品迭代规划
  - Phase 0: 召回顺序与关联优化（短期高优先级）
  - Phase 1-3: RAG 检索优化路线
  - 路线 B: 双方案切换设计

### 架构设计

**核心文档**:
- 📘 **[当前系统架构设计](./architecture/SQLBot-Current-Architecture-Design.md)** - SQLBot 系统代码架构详细设计 ⭐
- ⭐ **[双方案切换详细设计](./architecture/SQLBot-SWITCH-DETAILED-DESIGN.md)** - LLM 方案与 Claude Code 方案的双方案切换设计（v6.0 最终版）⭐

**架构演进**:
- 📊 **[架构演进对比分析](./architecture/SQLBot-Architecture-Comparison.md)** - 当前架构与双方案架构的差异对比

**历史版本**:
- 📜 **[双方案切换历史版本](./architecture/switch-design/versions/)** - V1 到 V5 的完整演进历史
- 📜 **[架构历史版本](./architecture/versions/)** - Claude Code 架构等历史版本文档

### 项目分析

- 🏢 **[Epoint AIChat 分析](./architecture/project-analysis/szy-epoint-aichat-analysis.md)** - Epoint AIChat 系统分析
- 📔 **[一本账 Agent 架构](./architecture/project-analysis/sz-ybz-agent-architecture.md)** - 江苏省一本账项目 Agent 架构
- 🤖 **[一本账 Claude Code 架构](./architecture/project-analysis/sz-ybz-claude-code-architecture.md)** - 一本账项目的 Claude Code 集成架构

### 技术文档

- 🔧 **[RAG 召回顺序优化](./architecture/technical/rag-recall-order-optimization.md)** - 召回策略优化方案
- 📐 **[Text-to-SQL 流程图](./architecture/technical/text2sql-flowchart.md)** - Text-to-SQL 处理流程详解
- 🐍 **[后端语言对比](./architecture/technical/backend-language-comparison.md)** - 后端技术选型分析
- 📚 **[Text-to-SQL 项目对比](./architecture/technical/text2sql-projects-comparison.md)** - 开源项目对比分析

## 文档版本历史

| 版本 | 日期 | 变更内容 |
|-----|------|----------|
| v1.0 | 2026-02-09 | 初始版本，创建基础文档结构 |
| v1.1 | 2026-02-09 | 添加 Phase 0 召回优化方案 |
| v1.2 | 2026-02-11 | **文档重组**: 整理文档目录结构，分类归档 |
| v1.3 | 2026-02-11 | 添加当前系统架构详细设计文档 |
| v1.4 | 2026-02-11 | 添加架构演进对比分析文档 |
| v1.5 | 2026-02-11 | **目录调整**: 创建 architecture/versions/ 存放历史版本文档 |
| v1.6 | 2026-02-11 | **目录修正**: 修正 switch-design 和 versions 目录结构说明 |

## 文档规范

### 新增文档

1. **架构文档** → 放入 `architecture/` 目录
2. **设计文档** → 放入 `architecture/switch-design/` 目录（历史版本放 versions/ 子目录）
3. **项目分析** → 放入 `architecture/project-analysis/` 目录
4. **技术文档** → 放入 `architecture/technical/` 目录

### 版本迭代

- 对于有版本迭代的文档，在对应目录下创建 `versions/` 子目录
- 保留历史版本以便追踪演进过程
- 最新稳定版本放在目录根目录

### 命名规范

- 使用小写字母和连字符：`document-name.md`
- 版本号格式：`document-name-vN.md` (N 为版本号)
- 最终版本去掉版本号：`document-name.md`

---

**最后更新**: 2026-02-11
**维护者**: SQLBot Team
