# SQLBot 双方案切换设计

## 📋 概要设计

### 1. 现状分析

#### 方案A：原始LLM API方案
**实现方式**：
- `LLMService` 通过 `LLMFactory` 创建 LLM 实例
- 调用 OpenAI 兼容接口生成 SQL
- 在后端完成 SQL 生成和执行

**核心流程**：
```
用户问题 → LLMService → LLM API → 生成SQL → 执行SQL → 返回结果
```

**优势**：
- 完全在后端处理，无需外部依赖
- 支持流式输出
- 配置存储在数据库中

#### 方案B：Claude Code Skills方案
**实现方式**：
- 通过 `sync_config_to_md.py` 将配置同步到MD文件
- Claude Code 读取 Skill 文件（SCHEMA.md, TERMINOLOGY.md等）
- Claude Code 本地生成 SQL
- 调用 SQLBot API 执行 SQL

**核心流程**：
```
用户问题 → Claude Code → 读取Skill文件 → 生成SQL → 调用SQLBot API执行 → 返回结果
```

**优势**：
- 充分利用 Claude Code 的理解能力
- 配置可版本控制（Git）
- 无需 API Token 调用成本

---

### 2. 切换方案设计

#### 2.1 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                    SQLBot 后端                                │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           配置层（新增）                                │  │
│  │  - feature_flags 表：存储功能开关                      │  │
│  │  - ClaudeCodeService：CC方案服务类                    │  │
│  └──────────────────────────────────────────────────────┘  │
│                          ↓                                  │
│  ┌──────────────────────┬──────────────────────────────┐  │
│  │  方案A（原始）        │  方案B（CC）                   │  │
│  │  LLMService          │  ClaudeCodeService            │  │
│  │  - 生成SQL            │  - 调用Claude Code API        │  │
│  │  - 执行SQL            │  - 获取生成的SQL              │  │
│  │  - 返回结果           │  - 执行SQL                    │  │
│  │                       │  - 返回结果                   │  │
│  └──────────────────────┴──────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

#### 2.2 数据库设计

**新增表：`feature_flags`**

```sql
CREATE TABLE feature_flags (
    id BIGSERIAL PRIMARY KEY,
    flag_key VARCHAR(100) UNIQUE NOT NULL,  -- 功能键
    flag_value BOOLEAN NOT NULL DEFAULT FALSE,  -- 开关状态
    flag_type VARCHAR(50),  -- 类型：global/assistant/datasource
    scope_id BIGINT,  -- 范围ID：assistant_id/datasource_id（全局时为NULL）
    description TEXT,  -- 描述
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by BIGINT,
    updated_by BIGINT
);

-- 插入默认配置
INSERT INTO feature_flags (flag_key, flag_value, flag_type, description) VALUES
('use_claude_code', FALSE, 'global', '是否使用Claude Code方案生成SQL');
```

#### 2.3 代码结构设计

```
backend/apps/chat/
├── api/
│   └── chat.py  -- 现有API（新增切换逻辑）
├── task/
│   ├── llm.py  -- 原始LLM方案
│   └── claude_code.py  -- 新增：Claude Code方案
└── models/
    └── chat_model.py  -- 现有模型

backend/apps/chat/service/  -- 新增目录
├── __init__.py
├── sql_generator_factory.py  -- SQL生成工厂（核心切换逻辑）
└── feature_flag_service.py  -- 功能开关服务

backend/apps/config_sync/
├── sync_config_to_md.py  -- 现有配置同步
└── claude_code_api.py  -- 新增：Claude Code API封装
```

#### 2.4 核心代码设计

##### 2.4.1 功能开关服务

```python
# backend/apps/chat/service/feature_flag_service.py
from sqlalchemy import select
from sqlmodel import Session
from typing import Optional

class FeatureFlagService:
    @staticmethod
    async def is_enabled(session: Session, flag_key: str,
                          flag_type: str = 'global',
                          scope_id: Optional[int] = None) -> bool:
        """
        检查功能开关是否启用

        Args:
            session: 数据库会话
            flag_key: 功能键（如 'use_claude_code'）
            flag_type: 类型（global/assistant/datasource）
            scope_id: 范围ID（assistant_id/datasource_id）

        Returns:
            bool: 是否启用
        """
        # 优先级：具体范围 > 全局
        stmt = select(FeatureFlag).where(
            FeatureFlag.flag_key == flag_key
        ).order_by(
            FeatureFlag.scope_id.desc().nulls_last()  # 有scope_id的优先
        )

        result = session.execute(stmt).first()
        if not result:
            return False

        flag = result[0]

        # 如果指定了scope，优先匹配scope
        if scope_id is not None and flag.scope_id == scope_id:
            return flag.flag_value

        # 如果是全局flag或未指定scope
        if flag_type == 'global' and flag.scope_id is None:
            return flag.flag_value

        return False

    @staticmethod
    async def set_flag(session: Session, flag_key: str, flag_value: bool,
                       flag_type: str = 'global',
                       scope_id: Optional[int] = None,
                       user_id: Optional[int] = None):
        """
        设置功能开关

        Args:
            session: 数据库会话
            flag_key: 功能键
            flag_value: 开关值
            flag_type: 类型
            scope_id: 范围ID
            user_id: 操作用户ID
        """
        # 查找是否存在
        stmt = select(FeatureFlag).where(
            FeatureFlag.flag_key == flag_key,
            FeatureFlag.flag_type == flag_type,
            (FeatureFlag.scope_id == scope_id) if scope_id else True
        )
        result = session.execute(stmt).first()

        if result:
            flag = result[0]
            flag.flag_value = flag_value
            flag.updated_by = user_id
        else:
            flag = FeatureFlag(
                flag_key=flag_key,
                flag_value=flag_value,
                flag_type=flag_type,
                scope_id=scope_id,
                created_by=user_id,
                updated_by=user_id
            )
            session.add(flag)

        session.commit()
```

##### 2.4.2 SQL生成器工厂

```python
# backend/apps/chat/service/sql_generator_factory.py
from abc import ABC, abstractmethod
from typing import AsyncIterator, Dict, Any
from sqlmodel import Session

class BaseSQLGenerator(ABC):
    """SQL生成器基类"""

    def __init__(self, session: Session, chat_question, current_user, current_assistant):
        self.session = session
        self.chat_question = chat_question
        self.current_user = current_user
        self.current_assistant = current_assistant
        self.record = None

    @abstractmethod
    async def generate_sql(self) -> AsyncIterator[Dict[str, Any]]:
        """生成SQL（流式返回）"""
        pass

    @abstractmethod
    async def generate_chart(self, chart_type: str = '', schema: str = '') -> AsyncIterator[Dict[str, Any]]:
        """生成图表配置"""
        pass


class LLMSQLGenerator(BaseSQLGenerator):
    """原始LLM方案"""

    def __init__(self, session, chat_question, current_user, current_assistant):
        super().__init__(session, chat_question, current_user, current_assistant)
        from apps.chat.task.llm import LLMService
        self.llm_service = None

    async def _init_service(self):
        self.llm_service = await LLMService.create(
            self.session, self.current_user, self.chat_question, self.current_assistant
        )
        self.record = self.llm_service.init_record(self.session)

    async def generate_sql(self) -> AsyncIterator[Dict[str, Any]]:
        await self._init_service()
        async for chunk in self.llm_service.generate_sql(self.session):
            yield chunk

    async def generate_chart(self, chart_type: str = '', schema: str = '') -> AsyncIterator[Dict[str, Any]]:
        async for chunk in self.llm_service.generate_chart(self.session, chart_type, schema):
            yield chunk


class ClaudeCodeSQLGenerator(BaseSQLGenerator):
    """Claude Code方案"""

    def __init__(self, session, chat_question, current_user, current_assistant):
        super().__init__(session, chat_question, current_user, current_assistant)
        from apps.config_sync.claude_code_api import ClaudeCodeAPI
        self.cc_api = ClaudeCodeAPI()

    async def generate_sql(self) -> AsyncIterator[Dict[str, Any]]:
        # 1. 调用Claude Code生成SQL
        question = self.chat_question.question

        # 同步配置（如果需要）
        # await self.cc_api.sync_config(datasource_id=...)

        # 调用Claude Code
        sql_result = await self.cc_api.generate_sql(question)

        # 2. 保存生成的SQL
        from apps.chat.curd.chat import save_question, save_sql_answer
        self.record = save_question(self.session, self.current_user, self.chat_question)

        # 3. 执行SQL（复用现有逻辑）
        from apps.db.db import exec_sql
        data = await exec_sql(self.session, self.record.datasource, sql_result['sql'])

        yield {
            'content': sql_result['sql'],
            'type': 'sql'
        }

    async def generate_chart(self, chart_type: str = '', schema: str = '') -> AsyncIterator[Dict[str, Any]]:
        # 调用Claude Code生成图表配置
        chart_result = await self.cc_api.generate_chart(
            self.chat_question.question,
            chart_type,
            schema
        )

        yield {
            'content': chart_result['chart'],
            'type': 'chart'
        }


class SQLGeneratorFactory:
    """SQL生成器工厂"""

    @staticmethod
    async def create(session: Session, chat_question, current_user, current_assistant) -> BaseSQLGenerator:
        """
        根据配置创建对应的SQL生成器

        Args:
            session: 数据库会话
            chat_question: 聊天问题
            current_user: 当前用户
            current_assistant: 当前助手

        Returns:
            BaseSQLGenerator: SQL生成器实例
        """
        from apps.chat.service.feature_flag_service import FeatureFlagService

        # 检查功能开关
        use_claude_code = await FeatureFlagService.is_enabled(
            session=session,
            flag_key='use_claude_code',
            flag_type='global'
        )

        if use_claude_code:
            return ClaudeCodeSQLGenerator(session, chat_question, current_user, current_assistant)
        else:
            return LLMSQLGenerator(session, chat_question, current_user, current_assistant)
```

##### 2.4.3 Claude Code API封装

```python
# backend/apps/config_sync/claude_code_api.py
import asyncio
import subprocess
import json
from typing import Dict, Any, Optional

class ClaudeCodeAPI:
    """Claude Code API封装"""

    def __init__(self, claude_code_path: str = "/usr/local/bin/claude"):
        self.claude_code_path = claude_code_path
        self.skill_dir = "/Users/guchuan/codespace/SQLBot/skills/sqlbot-knowledge"

    async def generate_sql(self, question: str, **kwargs) -> Dict[str, Any]:
        """
        调用Claude Code生成SQL

        Args:
            question: 用户问题
            **kwargs: 其他参数

        Returns:
            Dict: {'sql': str, 'chart_type': Optional[str], 'brief': Optional[str]}
        """
        # 构建Claude Code命令
        prompt = f"""
你是SQLBot的智能问数Agent。请根据以下信息生成SQL：

用户问题：{question}

请读取以下配置文件：
- {self.skill_dir}/SCHEMA.md
- {self.skill_dir}/TERMINOLOGY.md
- {self.skill_dir}/EXAMPLES.md
- {self.skill_dir}/PROMPT.md

生成SQL并返回JSON格式：
{{
  "sql": "SELECT ...",
  "chart_type": "line|bar|pie",
  "brief": "简短描述"
}}
"""

        # 调用Claude Code（通过subprocess或HTTP API）
        result = await self._call_claude_code(prompt)

        return result

    async def generate_chart(self, question: str, chart_type: str, schema: str, **kwargs) -> Dict[str, Any]:
        """
        调用Claude Code生成图表配置

        Args:
            question: 用户问题
            chart_type: 图表类型
            schema: 数据Schema

        Returns:
            Dict: {'chart': dict}
        """
        prompt = f"""
请为以下SQL结果生成图表配置：

用户问题：{question}
图表类型：{chart_type}
数据结构：{schema}

返回JSON格式：
{{
  "type": "{chart_type}",
  "x": "字段名",
  "y": "字段名",
  "series": [...],
  ...
}}
"""

        result = await self._call_claude_code(prompt)

        return result

    async def _call_claude_code(self, prompt: str) -> Dict[str, Any]:
        """
        调用Claude Code（子进程方式）

        Args:
            prompt: 提示词

        Returns:
            Dict: Claude Code返回的JSON结果
        """
        # 方式1：子进程调用（推荐用于生产）
        cmd = [
            self.claude_code_path,
            "prompt",
            prompt,
            "--output", "json"
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            raise Exception(f"Claude Code执行失败: {stderr.decode()}")

        result = json.loads(stdout.decode())
        return result

    async def sync_config(self, datasource_id: int, oid: int = 1):
        """
        同步配置到MD文件

        Args:
            datasource_id: 数据源ID
            oid: 组织ID
        """
        from apps.config_sync.sync_config_to_md import sync_all
        await asyncio.to_thread(sync_all, datasource_id, oid)
```

##### 2.4.4 修改现有API

```python
# backend/apps/chat/api/chat.py 修改部分

async def stream_sql(session: SessionDep, current_user: CurrentUser, request_question: ChatQuestion,
                     current_assistant: Optional[CurrentAssistant] = None, in_chat: bool = True, stream: bool = True,
                     finish_step: ChatFinishStep = ChatFinishStep.GENERATE_CHART, embedding: bool = False):
    try:
        # 原代码：
        # llm_service = await LLMService.create(...)

        # 新代码：使用工厂模式创建SQL生成器
        from apps.chat.service.sql_generator_factory import SQLGeneratorFactory

        sql_generator = await SQLGeneratorFactory.create(
            session, current_user, request_question, current_assistant
        )

        # 初始化记录
        if hasattr(sql_generator, '_init_service'):
            await sql_generator._init_service()
        else:
            from apps.chat.curd.chat import save_question
            sql_generator.record = save_question(session, current_user, request_question)

        # 执行SQL生成
        sql_generator.run_task_async(in_chat=in_chat, stream=stream, finish_step=finish_step)

    except Exception as e:
        # ... 错误处理保持不变
        pass
```

---

### 3. 管理界面设计

#### 3.1 功能开关管理页面

**路由**：`/admin/feature-flags`

**功能**：
- 查看所有功能开关
- 切换开关状态
- 按类型筛选（全局/Assistant/数据源）
- 查看开关使用日志

**API设计**：

```python
# backend/apps/system/api/feature_flags.py

@router.get("/flags", summary="获取功能开关列表")
async def list_flags(session: SessionDep, current_user: CurrentUser):
    # 查询所有功能开关
    pass

@router.post("/flags/{flag_key}/toggle", summary="切换功能开关")
async def toggle_flag(session: SessionDep, current_user: CurrentUser, flag_key: str, value: bool):
    # 切换开关状态
    pass

@router.get("/flags/{flag_key}/status", summary="获取功能开关状态")
async def get_flag_status(session: SessionDep, current_user: CurrentUser, flag_key: str):
    # 获取当前开关状态
    pass
```

#### 3.2 配置同步页面

**路由**：`/admin/config-sync`

**功能**：
- 手动触发配置同步
- 查看同步历史
- 查看同步状态（成功/失败）

**API设计**：

```python
# backend/apps/config_sync/api/sync.py

@router.post("/sync", summary="同步配置到MD文件")
async def sync_config(session: SessionDep, current_user: CurrentUser, datasource_id: int, oid: int = 1):
    # 执行同步
    pass

@router.get("/sync/history", summary="获取同步历史")
async def get_sync_history(session: SessionDep, current_user: CurrentUser):
    # 查询同步日志
    pass
```

---

### 4. 切换流程设计

#### 4.1 从方案A切换到方案B

```
1. 管理员登录后台
2. 进入"功能开关"页面
3. 找到"use_claude_code"开关
4. 切换为"启用"
5. 点击"保存"
6. 系统执行：
   a. 更新数据库配置
   b. 触发配置同步（如果需要）
   c. 发送通知给管理员
7. 后续所有新请求自动使用方案B
```

#### 4.2 从方案B切换到方案A

```
1. 管理员登录后台
2. 进入"功能开关"页面
3. 找到"use_claude_code"开关
4. 切换为"禁用"
5. 点击"保存"
6. 系统执行：
   a. 更新数据库配置
   b. 发送通知给管理员
7. 后续所有新请求自动使用方案A
```

---

### 5. 实施步骤

#### Phase 1: 数据库和基础服务（2-3小时）
1. 创建 `feature_flags` 表
2. 实现 `FeatureFlagService`
3. 编写单元测试

#### Phase 2: Claude Code集成（3-4小时）
1. 实现 `ClaudeCodeAPI`
2. 测试Claude Code调用
3. 完善错误处理

#### Phase 3: 工厂模式改造（2-3小时）
1. 创建 `BaseSQLGenerator` 接口
2. 实现 `LLMSQLGenerator`（封装现有代码）
3. 实现 `ClaudeCodeSQLGenerator`
4. 实现 `SQLGeneratorFactory`

#### Phase 4: API改造（2-3小时）
1. 修改 `/chat/question` 接口
2. 修改 `/chat/recommend_questions` 接口
3. 测试切换逻辑

#### Phase 5: 管理界面（4-6小时）
1. 实现功能开关管理页面
2. 实现配置同步页面
3. 添加权限控制

#### Phase 6: 测试和优化（2-3小时）
1. 端到端测试
2. 性能测试
3. 文档编写

**总计**：15-22小时

---

### 6. 技术要点

#### 6.1 兼容性保证

- **向后兼容**：默认使用方案A，不影响现有功能
- **平滑切换**：切换时无需重启服务
- **数据隔离**：两种方案共享数据库，结果格式一致

#### 6.2 性能考虑

- **方案A**：依赖LLM API响应速度（网络调用）
- **方案B**：依赖Claude Code执行速度（本地进程）+ 同步开销
- **建议**：在高并发场景下优先使用方案A

#### 6.3 监控和日志

- 记录每次使用的方案
- 统计两种方案的成功率、响应时间
- 异常情况自动降级到方案A

#### 6.4 安全性

- Claude Code调用需要权限验证
- 敏感信息（API Key）不存储在Skill文件中
- 同步脚本内部使用，无需暴露API

---

### 7. 风险和应对

| 风险 | 应对措施 |
|------|----------|
| Claude Code调用失败 | 自动降级到方案A，记录日志 |
| 配置同步失败 | 提供重试机制，发送告警 |
| 性能下降 | 添加缓存，监控响应时间 |
| 切换不可控 | 提供回滚功能，保留方案A |

---

### 8. 后续优化

1. **A/B测试**：支持对部分用户使用方案B，对比效果
2. **多模型支持**：同时支持多种LLM方案，动态选择最优
3. **智能切换**：根据问题类型自动选择最合适的方案
4. **缓存机制**：缓存常见问题的SQL，减少重复调用

---

**文档版本**：v1.0
**创建日期**：2026-02-09
**作者**：CodeCraft
