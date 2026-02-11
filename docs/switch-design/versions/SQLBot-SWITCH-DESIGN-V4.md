# SQLBot 双方案切换设计（V4 - 职责明确版）

## 📋 概要设计

### 1. 设计原则

按照SQLBot现有架构模式设计，明确职责划分：

**Claude Code职责**：
- 读取MD文件（SCHEMA.md, TERMINOLOGY.md, EXAMPLES.md, PROMPT.md）
- 生成SQL

**SQLBot职责**：
- 执行SQL
- 返回数据
- 生成图表配置
- 提供API接口

---

## 🏗️ 架构设计

### 2. 完整流程对比

#### 方案A：LLM方案（原始）

```
用户问题
    ↓
后端RAG检索（embedding向量）
    ├── 检索表结构
    ├── 检索术语库
    └── 检索SQL示例
    ↓
构建Prompt（含检索上下文）
    ↓
【后端】调用LLM API生成SQL
    ↓
【后端】执行SQL
    ↓
【后端】生成图表配置
    ↓
【后端】返回结果
```

#### 方案B：Claude Code方案

```
用户问题
    ↓
【跳过后端RAG】
    ↓
【Claude Code】读取MD文件
    ├── SCHEMA.md（表结构）
    ├── TERMINOLOGY.md（术语库）
    ├── EXAMPLES.md（SQL示例）
    └── PROMPT.md（自定义Prompt）
    ↓
【Claude Code】生成SQL
    ↓
【后端】执行SQL
    ↓
【后端】生成图表配置（复用现有逻辑）
    ↓
【后端】返回结果
```

---

### 3. 职责划分

| 模块 | LLM方案 | Claude Code方案 |
|------|---------|-----------------|
| **RAG检索** | 后端embedding向量检索 | 跳过（Claude Code读MD） |
| **SQL生成** | 后端调用LLM API | **Claude Code** |
| **SQL执行** | 后端 | **后端** |
| **图表配置** | 后端 | **后端**（复用现有逻辑） |
| **API接口** | 后端 | **后端** |

---

### 4. 目录结构

```
backend/apps/
├── chat/
│   ├── api/
│   │   └── chat.py              # 现有API（添加切换逻辑）
│   ├── task/
│   │   ├── llm.py               # 现有LLM方案（保持不变）
│   │   ├── claude_code.py       # 新增：Claude Code方案（只生成SQL）
│   │   └── strategy_factory.py  # 新增：方案工厂（策略模式）
│   ├── models/
│   │   └── chat_model.py        # 现有模型
│   └── curd/
│       └── chat.py              # 现有CRUD
├── system/
│   ├── crud/
│   │   └── feature_flag.py      # 新增：功能开关CRUD
│   ├── api/
│   │   └── feature_flag.py      # 新增：功能开关API
│   └── models/
│       └── system_variable_model.py  # 现有（复用）
└── config_sync/
    ├── sync_config_to_md.py     # 现有配置同步
    └── claude_code_client.py    # 新增：Claude Code客户端
```

---

## 🗄️ 数据库设计

### 5. 使用现有`system_variable`表

**存储功能开关配置**：

```sql
-- 功能开关配置
INSERT INTO system_variable (name, var_type, type, value, create_time, create_by)
VALUES
-- 1. SQL生成方案切换
('sql_solution_type', 'string', 'system', ['llm'], NOW(), 1),

-- 2. Claude Code Skill目录
('claude_code_skill_dir', 'string', 'custom',
 ['/Users/guchuan/codespace/SQLBot/skills/sqlbot-knowledge'], NOW(), 1),

-- 3. 是否自动同步配置到MD文件
('claude_code_sync_enabled', 'boolean', 'custom', [true], NOW(), 1),

-- 4. LLM方案是否启用RAG检索
('llm_rag_enabled', 'boolean', 'system', [true], NOW(), 1);
```

**字段说明**：

| 变量名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `sql_solution_type` | string | 'llm' | SQL生成方案：'llm'=LLM方案，'claude_code'=Claude Code方案 |
| `claude_code_skill_dir` | string | /path/to/skills | Claude Code Skill目录 |
| `claude_code_sync_enabled` | boolean | true | 是否自动同步配置到MD文件 |
| `llm_rag_enabled` | boolean | true | LLM方案是否启用RAG检索 |

---

## 🔧 核心代码设计

### 6. 功能开关CRUD

```python
# backend/apps/system/crud/feature_flag.py

from typing import List
from sqlmodel import select
from apps.system.models.system_variable_model import SystemVariable
from common.core.deps import SessionDep, Trans


class FeatureFlagService:
    """功能开关服务"""

    @staticmethod
    def get_bool(session: SessionDep, name: str, default: bool = False) -> bool:
        """获取布尔类型的功能开关"""
        stmt = select(SystemVariable).where(SystemVariable.name == name)
        result = session.exec(stmt).first()
        if not result or not result.value:
            return default
        if result.var_type == 'boolean':
            return bool(result.value[0]) if result.value else default
        return default

    @staticmethod
    def get_string(session: SessionDep, name: str, default: str = '') -> str:
        """获取字符串类型的功能开关"""
        stmt = select(SystemVariable).where(SystemVariable.name == name)
        result = session.exec(stmt).first()
        if not result or not result.value:
            return default
        if result.var_type == 'string':
            return str(result.value[0]) if result.value else default
        return default

    @staticmethod
    def set_bool(session: SessionDep, name: str, value: bool, user_id: int = 1) -> bool:
        """设置布尔类型的功能开关"""
        import datetime
        stmt = select(SystemVariable).where(SystemVariable.name == name)
        result = session.exec(stmt).first()
        if result:
            result.value = [value]
            result.create_by = user_id
            session.add(result)
        else:
            variable = SystemVariable(
                name=name, var_type='boolean', type='custom',
                value=[value], create_time=datetime.datetime.now(), create_by=user_id
            )
            session.add(variable)
        session.commit()
        return True

    @staticmethod
    def set_string(session: SessionDep, name: str, value: str, user_id: int = 1) -> bool:
        """设置字符串类型的功能开关"""
        import datetime
        stmt = select(SystemVariable).where(SystemVariable.name == name)
        result = session.exec(stmt).first()
        if result:
            result.value = [value]
            result.create_by = user_id
            session.add(result)
        else:
            variable = SystemVariable(
                name=name, var_type='string', type='custom',
                value=[value], create_time=datetime.datetime.now(), create_by=user_id
            )
            session.add(variable)
        session.commit()
        return True

    @staticmethod
    def get_sql_solution_type(session: SessionDep) -> str:
        """
        获取当前SQL生成方案类型

        Returns:
            str: 'llm' 或 'claude_code'
        """
        return FeatureFlagService.get_string(
            session,
            'sql_solution_type',
            default='llm'
        )

    @staticmethod
    def set_sql_solution_type(session: SessionDep, solution_type: str, user_id: int = 1) -> bool:
        """
        设置SQL生成方案类型

        Args:
            session: 数据库会话
            solution_type: 方案类型（'llm' 或 'claude_code'）
            user_id: 用户ID

        Returns:
            bool: 是否成功

        Raises:
            ValueError: 方案类型无效
        """
        if solution_type not in ['llm', 'claude_code']:
            raise ValueError(f"Invalid solution type: {solution_type}")

        return FeatureFlagService.set_string(
            session,
            'sql_solution_type',
            solution_type,
            user_id
        )

    @staticmethod
    def get_all(session: SessionDep, trans: Trans, keyword: str = None) -> List[SystemVariable]:
        """获取所有功能开关"""
        from sqlalchemy import and_
        if keyword:
            stmt = select(SystemVariable).where(
                and_(
                    SystemVariable.name.like(f'%{keyword}%'),
                    SystemVariable.var_type.in_(['boolean', 'string'])
                )
            )
        else:
            stmt = select(SystemVariable).where(
                SystemVariable.var_type.in_(['boolean', 'string'])
            )
        results = session.exec(stmt).all()
        return results
```

---

### 7. Claude Code客户端

```python
# backend/apps/config_sync/claude_code_client.py

import asyncio
import subprocess
import json
from typing import Dict, Any


class ClaudeCodeClient:
    """
    Claude Code客户端

    职责：
    1. 读取MD文件
    2. 生成SQL

    不负责：
    - 执行SQL（由SQLBot后端完成）
    - 生成图表（由SQLBot后端完成）
    """

    def __init__(self, skill_dir: str = None, claude_path: str = "claude"):
        self.skill_dir = skill_dir or "/Users/guchuan/codespace/SQLBot/skills/sqlbot-knowledge"
        self.claude_path = claude_path

    async def generate_sql(self, question: str, **kwargs) -> Dict[str, Any]:
        """
        调用Claude Code生成SQL

        Claude Code会自动读取以下MD文件获取上下文：
        - SCHEMA.md：表结构
        - TERMINOLOGY.md：术语库
        - EXAMPLES.md：SQL示例
        - PROMPT.md：自定义Prompt

        Args:
            question: 用户问题
            **kwargs: 其他参数

        Returns:
            Dict: {'sql': str, 'chart_type': Optional[str], 'brief': Optional[str]}

        Raises:
            Exception: Claude Code调用失败
        """
        # 构建提示词（Claude Code会自动读取MD文件）
        prompt = f"""
你是SQLBot的智能问数Agent。请根据用户问题生成SQL。

用户问题：{question}

请自动读取以下配置文件获取上下文：
- {self.skill_dir}/SCHEMA.md（表结构）
- {self.skill_dir}/TERMINOLOGY.md（术语库）
- {self.skill_dir}/EXAMPLES.md（SQL示例）
- {self.skill_dir}/PROMPT.md（自定义Prompt）

要求：
1. 只生成SQL，不要解释
2. 使用COUNT(*)时，确保正确统计
3. 涉及术语时，使用字段精确匹配
4. 多表查询时，优先使用JOIN而非子查询

返回JSON格式：
{{
  "sql": "SELECT ...",
  "chart_type": "line|bar|pie|table",
  "brief": "简短描述"
}}
"""

        # 调用Claude Code
        result = await self._call_claude_code(prompt)

        # 解析结果
        return self._parse_sql_result(result)

    async def _call_claude_code(self, prompt: str) -> str:
        """
        调用Claude Code（通过子进程）

        Args:
            prompt: 提示词

        Returns:
            str: Claude Code返回结果

        Raises:
            Exception: 调用失败
        """
        # 创建临时文件存储提示词
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(prompt)
            prompt_file = f.name

        try:
            # 调用Claude Code
            cmd = [
                self.claude_path,
                "ask",
                "-f", prompt_file,
                "--output", "json",
                "--cwd", self.skill_dir  # 指定工作目录为Skill目录
            ]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.skill_dir
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                error_msg = stderr.decode('utf-8', errors='ignore')
                raise Exception(f"Claude Code执行失败: {error_msg}")

            result = stdout.decode('utf-8', errors='ignore')
            return result

        finally:
            # 删除临时文件
            import os
            if os.path.exists(prompt_file):
                os.remove(prompt_file)

    def _parse_sql_result(self, result: str) -> Dict[str, Any]:
        """解析SQL生成结果"""
        try:
            # 尝试提取JSON
            if '{' in result and '}' in result:
                start = result.find('{')
                end = result.rfind('}') + 1
                json_str = result[start:end]
                return json.loads(json_str)
            else:
                raise ValueError("无法从结果中提取JSON")
        except Exception as e:
            # 如果解析失败，返回纯文本
            return {
                "sql": result.strip(),
                "chart_type": "table",
                "brief": ""
            }

    async def sync_config(self, datasource_id: int = 1, oid: int = 1) -> bool:
        """
        同步配置到MD文件

        Args:
            datasource_id: 数据源ID
            oid: 组织ID

        Returns:
            bool: 是否成功
        """
        try:
            from apps.config_sync.sync_config_to_md import sync_all
            await asyncio.to_thread(sync_all, datasource_id, oid)
            return True
        except Exception as e:
            raise Exception(f"配置同步失败: {str(e)}")
```

---

### 8. Claude Code方案任务

```python
# backend/apps/chat/task/claude_code.py

import asyncio
import traceback
from typing import AsyncIterator, Dict, Any
from sqlmodel import Session

from apps.chat.curd.chat import (
    save_question, save_sql_answer, get_chart_data
)
from apps.chat.models.chat_model import ChatQuestion, ChatRecord
from apps.config_sync.claude_code_client import ClaudeCodeClient
from apps.system.crud.feature_flag import FeatureFlagService
from common.core.deps import CurrentUser, CurrentAssistant
from common.error import SingleMessageError
from common.utils.locale import I18n, I18nHelper


class ClaudeCodeTask:
    """
    Claude Code方案任务

    职责：
    1. 调用Claude Code生成SQL
    2. 【SQLBot后端】执行SQL（复用现有逻辑）
    3. 【SQLBot后端】生成图表配置（复用现有逻辑）

    不负责：
    - RAG检索（Claude Code会直接读取MD文件）
    """

    def __init__(self, session: Session, current_user: CurrentUser,
                 chat_question: ChatQuestion, current_assistant: CurrentAssistant = None):
        self.session = session
        self.current_user = current_user
        self.chat_question = chat_question
        self.current_assistant = current_assistant
        self.record: ChatRecord = None
        self.client: ClaudeCodeClient = None

        # 国际化
        i18n = I18n()
        self.trans: I18nHelper = i18n(lang=current_user.language)

    async def create(self):
        """初始化Claude Code客户端"""
        # 获取配置
        skill_dir = FeatureFlagService.get_string(
            self.session,
            'claude_code_skill_dir',
            '/Users/guchuan/codespace/SQLBot/skills/sqlbot-knowledge'
        )

        # 创建客户端
        self.client = ClaudeCodeClient(skill_dir=skill_dir)

        # 检查是否需要同步配置
        sync_enabled = FeatureFlagService.get_bool(self.session, 'claude_code_sync_enabled', True)
        if sync_enabled:
            # 异步同步配置（不阻塞）
            asyncio.create_task(self._sync_config_async())

    async def _sync_config_async(self):
        """异步同步配置"""
        try:
            ds_id = self.chat_question.datasource_id
            if ds_id:
                oid = self.current_user.oid if self.current_assistant is None else self.current_assistant.oid
                await self.client.sync_config(datasource_id=ds_id, oid=oid)
        except Exception as e:
            # 同步失败不影响主流程
            print(f"[ClaudeCode] 配置同步失败: {e}")

    async def init_record(self) -> ChatRecord:
        """
        初始化聊天记录

        注意：这里不做RAG检索，因为Claude Code会直接读取MD文件
        """
        self.record = save_question(
            session=self.session,
            current_user=self.current_user,
            question=self.chat_question
        )
        return self.record

    async def generate_sql(self) -> AsyncIterator[Dict[str, Any]]:
        """
        生成SQL（由Claude Code完成）

        Claude Code会自动读取MD文件获取上下文

        Yields:
            Dict: 流式返回的SQL生成结果
        """
        question = self.chat_question.question

        yield {
            'type': 'status',
            'content': self.trans('i18n_chat.generating_sql')
        }

        try:
            # 调用Claude Code生成SQL
            result = await self.client.generate_sql(question)

            sql = result.get('sql', '')
            chart_type = result.get('chart_type', 'table')
            brief = result.get('brief', '')

            if not sql:
                raise SingleMessageError(self.trans('i18n_chat.sql_generation_failed'))

            # 保存生成的SQL
            save_sql_answer(
                session=self.session,
                record_id=self.record.id,
                answer=f'{{"content": {sql}}}'
            )

            # 流式返回SQL
            yield {
                'type': 'sql',
                'content': sql,
                'chart_type': chart_type,
                'brief': brief
            }

        except Exception as e:
            traceback.print_exc()
            yield {
                'type': 'error',
                'content': str(e)
            }
            raise

    async def execute_sql(self, sql: str) -> AsyncIterator[Dict[str, Any]]:
        """
        执行SQL（由SQLBot后端完成，复用现有逻辑）

        Args:
            sql: SQL语句

        Yields:
            Dict: 流式返回的执行结果
        """
        yield {
            'type': 'status',
            'content': self.trans('i18n_chat.executing_sql')
        }

        try:
            # 获取数据源
            from apps.datasource.crud.datasource import get_ds
            ds = get_ds(self.session, self.record.datasource)
            if not ds:
                raise SingleMessageError(self.trans('i18n_chat.datasource_not_found'))

            # 执行SQL（复用现有逻辑）
            from apps.db.db import exec_sql
            data, columns = await exec_sql(ds=ds, sql=sql)

            # 返回结果
            yield {
                'type': 'data',
                'content': {
                    'data': data,
                    'columns': columns
                }
            }

        except Exception as e:
            traceback.print_exc()
            yield {
                'type': 'error',
                'content': str(e)
            }
            raise

    async def generate_chart(self, chart_type: str = '', schema: str = '') -> AsyncIterator[Dict[str, Any]]:
        """
        生成图表配置（由SQLBot后端完成，复用现有逻辑）

        Args:
            chart_type: 图表类型
            schema: 数据Schema

        Yields:
            Dict: 流式返回的图表配置
        """
        yield {
            'type': 'status',
            'content': self.trans('i18n_chat.generating_chart')
        }

        try:
            # 复用现有逻辑生成图表配置
            # 这里可以复用LLMService中的generate_chart方法
            # 或者调用现有的图表生成逻辑

            # 获取数据
            data = get_chart_data(self.session, self.record.id)

            # 生成图表配置（复用现有逻辑）
            # 这里可以调用现有的图表生成服务
            # 或者使用LLM生成图表配置

            # 暂时使用简单逻辑
            chart_config = {
                "type": chart_type or "table",
                "data": data,
                "title": self.chat_question.question
            }

            # 保存图表配置
            import json
            from apps.chat.curd.chat import save_chart_answer
            save_chart_answer(
                session=self.session,
                record_id=self.record.id,
                answer=f'{{"content": {json.dumps(chart_config)}}}'
            )

            # 流式返回图表配置
            yield {
                'type': 'chart',
                'content': chart_config
            }

        except Exception as e:
            traceback.print_exc()
            yield {
                'type': 'error',
                'content': str(e)
            }
            raise

    async def run_task(self, in_chat: bool = True, stream: bool = True,
                       finish_step: str = 'generate_chart') -> AsyncIterator[Dict[str, Any]]:
        """
        运行完整任务流程

        Args:
            in_chat: 是否在聊天中
            stream: 是否流式返回
            finish_step: 完成步骤

        Yields:
            Dict: 流式返回的结果

        流程：
        1. 【Claude Code】生成SQL
        2. 【SQLBot后端】执行SQL
        3. 【SQLBot后端】生成图表配置
        """
        # 1. 生成SQL（Claude Code自动读取MD文件）
        async for chunk in self.generate_sql():
            yield chunk

            # 如果出错，停止
            if chunk.get('type') == 'error':
                return

            sql = chunk.get('content')

        # 2. 执行SQL（SQLBot后端完成）
        async for chunk in self.execute_sql(sql):
            yield chunk

            # 如果出错，停止
            if chunk.get('type') == 'error':
                return

        # 3. 生成图表配置（SQLBot后端完成）
        if finish_step == 'generate_chart':
            async for chunk in self.generate_chart():
                yield chunk

                # 如果出错，停止
                if chunk.get('type') == 'error':
                    return
```

---

### 9. 策略工厂

```python
# backend/apps/chat/task/strategy_factory.py

from abc import ABC, abstractmethod
from typing import AsyncIterator, Dict, Any
from sqlmodel import Session

from apps.chat.models.chat_model import ChatQuestion
from apps.chat.task.llm import LLMService
from apps.chat.task.claude_code import ClaudeCodeTask
from apps.system.crud.feature_flag import FeatureFlagService
from common.core.deps import CurrentUser, CurrentAssistant


class BaseSQLGenerator(ABC):
    """SQL生成器基类（策略接口）"""

    def __init__(self, session: Session, chat_question: ChatQuestion,
                 current_user: CurrentUser, current_assistant: CurrentAssistant = None):
        self.session = session
        self.chat_question = chat_question
        self.current_user = current_user
        self.current_assistant = current_assistant
        self.record = None

    @abstractmethod
    async def create(self):
        """初始化生成器"""
        pass

    @abstractmethod
    async def init_record(self):
        """初始化记录"""
        pass

    @abstractmethod
    async def run_task(self, in_chat: bool = True, stream: bool = True,
                      finish_step: str = 'generate_chart') -> AsyncIterator[Dict[str, Any]]:
        """运行任务"""
        pass

    def get_record(self):
        """获取记录"""
        return self.record


class LLMSQLGenerator(BaseSQLGenerator):
    """
    LLM方案生成器（含RAG检索）

    职责：
    - 后端RAG检索（embedding向量）
    - 后端调用LLM API生成SQL
    - 后端执行SQL
    - 后端生成图表配置
    """

    def __init__(self, session: Session, chat_question: ChatQuestion,
                 current_user: CurrentUser, current_assistant: CurrentAssistant = None):
        super().__init__(session, chat_question, current_user, current_assistant)
        self.llm_service: LLMService = None

    async def create(self):
        """初始化LLM服务"""
        self.llm_service = await LLMService.create(
            self.session, self.current_user, self.chat_question, self.current_assistant
        )

        # LLMService内部会自动做RAG检索
        # - choose_table_schema: 使用embedding检索表结构
        # - filter_terminology_template: 使用embedding检索术语
        # - filter_training_template: 使用embedding检索示例

    async def init_record(self):
        """初始化记录"""
        self.record = self.llm_service.init_record(self.session)

    async def run_task(self, in_chat: bool = True, stream: bool = True,
                      finish_step: str = 'generate_chart') -> AsyncIterator[Dict[str, Any]]:
        """运行LLM任务（含RAG）"""
        self.llm_service.run_task_async(in_chat=in_chat, stream=stream, finish_step=finish_step)

        # 等待结果
        async for chunk in self.llm_service.await_result():
            yield chunk


class ClaudeCodeSQLGenerator(BaseSQLGenerator):
    """
    Claude Code方案生成器（无RAG检索）

    职责：
    - Claude Code生成SQL（读取MD文件）
    - SQLBot后端执行SQL（复用现有逻辑）
    - SQLBot后端生成图表配置（复用现有逻辑）

    不负责：
    - RAG检索（Claude Code会直接读取MD文件）
    """

    def __init__(self, session: Session, chat_question: ChatQuestion,
                 current_user: CurrentUser, current_assistant: CurrentAssistant = None):
        super().__init__(session, chat_question, current_user, current_assistant)
        self.cc_task: ClaudeCodeTask = None

    async def create(self):
        """初始化Claude Code任务"""
        self.cc_task = ClaudeCodeTask(
            self.session, self.current_user, self.chat_question, self.current_assistant
        )
        await self.cc_task.create()

    async def init_record(self):
        """
        初始化记录（无RAG检索）

        注意：这里不做RAG检索，因为Claude Code会直接读取MD文件
        """
        self.record = await self.cc_task.init_record()

    async def run_task(self, in_chat: bool = True, stream: bool = True,
                      finish_step: str = 'generate_chart') -> AsyncIterator[Dict[str, Any]]:
        """
        运行Claude Code任务（无RAG）

        流程：
        1. 【Claude Code】生成SQL（读取MD文件）
        2. 【SQLBot后端】执行SQL
        3. 【SQLBot后端】生成图表配置
        """
        async for chunk in self.cc_task.run_task(in_chat, stream, finish_step):
            yield chunk


class SQLGeneratorFactory:
    """SQL生成器工厂（策略工厂）"""

    @staticmethod
    async def create(session: Session, chat_question: ChatQuestion,
                    current_user: CurrentUser, current_assistant: CurrentAssistant = None) -> BaseSQLGenerator:
        """
        根据功能开关创建对应的SQL生成器

        Args:
            session: 数据库会话
            chat_question: 聊天问题
            current_user: 当前用户
            current_assistant: 当前助手

        Returns:
            BaseSQLGenerator: SQL生成器实例

        职责划分：
        - LLM方案：后端完成所有逻辑（RAG + SQL生成 + 执行 + 图表）
        - Claude Code方案：Claude Code只负责SQL生成，SQLBot负责执行和图表
        """
        # 检查功能开关
        solution_type = FeatureFlagService.get_sql_solution_type(session)

        if solution_type == 'claude_code':
            # Claude Code方案：Claude Code生成SQL，SQLBot执行和图表
            generator = ClaudeCodeSQLGenerator(session, chat_question, current_user, current_assistant)
        else:
            # LLM方案（默认）：后端完成所有逻辑
            generator = LLMSQLGenerator(session, chat_question, current_user, current_assistant)

        # 初始化生成器
        await generator.create()

        return generator
```

---

## 📊 职责划分对比

### 10. 详细职责对比

| 阶段 | LLM方案 | Claude Code方案 |
|------|---------|-----------------|
| **RAG检索** | 后端embedding向量检索 | 跳过（Claude Code读MD） |
| **读取上下文** | 后端检索表结构/术语/示例 | **Claude Code**读取MD文件 |
| **SQL生成** | 后端调用LLM API | **Claude Code**生成 |
| **SQL执行** | 后端 | **后端** |
| **图表配置** | 后端 | **后端**（复用现有逻辑） |
| **API接口** | 后端 | **后端** |

---

## 🎯 实施步骤

### Phase 1: 功能开关模块（2-3小时）

1. **实现`FeatureFlagService`**
   - 文件：`backend/apps/system/crud/feature_flag.py`
   - 功能：读写`system_variable`表
   - 测试：单元测试

2. **实现功能开关API**
   - 文件：`backend/apps/system/api/feature_flag.py`
   - 路由：`/system/feature-flags/*`
   - 功能：列表、查询、切换、更新

3. **初始化数据库**
   - 插入默认功能开关配置

### Phase 2: Claude Code客户端（3-4小时）

1. **实现`ClaudeCodeClient`**
   - 文件：`backend/apps/config_sync/claude_code_client.py`
   - 功能：调用Claude Code生成SQL
   - 测试：端到端测试

2. **配置同步**
   - 复用现有`sync_config_to_md.py`
   - 确保MD文件生成正确

### Phase 3: Claude Code方案任务（2-3小时）

1. **实现`ClaudeCodeTask`**
   - 文件：`backend/apps/chat/task/claude_code.py`
   - 功能：
     - 调用Claude Code生成SQL
     - 后端执行SQL（复用现有逻辑）
     - 后端生成图表（复用现有逻辑）
   - 测试：单元测试

2. **错误处理**
   - 降级机制：失败自动回退到LLM方案
   - 日志记录

### Phase 4: 策略工厂（2-3小时）

1. **实现策略接口和工厂**
   - 文件：`backend/apps/chat/task/strategy_factory.py`
   - 功能：工厂模式，根据开关选择方案
   - 明确职责划分
   - 测试：单元测试

2. **封装LLM方案**
   - 在`LLMSQLGenerator`中封装现有代码

### Phase 5: API改造（2-3小时）

1. **修改`chat.py`**
   - 使用工厂模式替代直接创建`LLMService`
   - 保持向后兼容

2. **测试切换逻辑**
   - 测试两种方案切换
   - 测试流式返回

### Phase 6: 前端适配（可选，4-6小时）

1. **功能开关管理页面**
   - 路由：`/admin/feature-flags`
   - 功能：查看、切换、更新功能开关

2. **配置同步页面**
   - 路由：`/admin/config-sync`
   - 功能：手动触发同步、查看同步历史

**总计**：15-22小时（不含前端）

---

## 🔒 切换方式

### 切换到Claude Code方案

```sql
-- 设置为Claude Code方案
UPDATE system_variable
SET value = ['claude_code']
WHERE name = 'sql_solution_type';
```

**效果**：
- Claude Code读取MD文件 + 生成SQL
- SQLBot后端执行SQL + 返回数据 + 生成图表

### 切换到LLM方案（默认）

```sql
-- 设置为LLM方案
UPDATE system_variable
SET value = ['llm']
WHERE name = 'sql_solution_type';
```

**效果**：
- 后端做Embedding向量检索（RAG）
- 后端调用LLM API生成SQL
- 后端执行SQL + 返回数据 + 生成图表

---

## 📝 完整流程示例

### LLM方案

```
用户问题：垂管系统数量
    ↓
【后端】RAG检索（embedding向量）
    ├── 检索表结构 → t_sys表
    ├── 检索术语库 → "垂管系统"术语
    └── 检索SQL示例 → 相似示例
    ↓
【后端】调用LLM API生成SQL
    ↓
SQL: SELECT COUNT(*) FROM t_sys WHERE type = '省垂'
    ↓
【后端】执行SQL → 返回数据
    ↓
【后端】生成图表配置
    ↓
【后端】返回结果
```

### Claude Code方案

```
用户问题：垂管系统数量
    ↓
【跳过后端RAG】
    ↓
【Claude Code】读取MD文件
    ├── SCHEMA.md → t_sys表
    ├── TERMINOLOGY.md → "垂管系统"术语
    ├── EXAMPLES.md → 相似SQL示例
    └── PROMPT.md → 自定义Prompt
    ↓
【Claude Code】生成SQL
    ↓
SQL: SELECT COUNT(*) FROM t_sys WHERE type = '省垂'
    ↓
【后端】执行SQL → 返回数据
    ↓
【后端】生成图表配置（复用现有逻辑）
    ↓
【后端】返回结果
```

---

## 🎯 核心优势

| 优势 | 说明 |
|------|------|
| ✅ **职责明确** | Claude Code只负责SQL生成，SQLBot负责执行和图表 |
| ✅ **零表结构变更** | 复用`system_variable`表 |
| ✅ **保持代码风格** | 符合SQLBot现有架构 |
| ✅ **向后兼容** | 默认使用LLM方案 |
| ✅ **平滑切换** | 修改开关立即生效 |
| ✅ **最小改动** | API层只需几行代码 |
| ✅ **自动降级** | Claude Code失败自动回退到LLM方案 |
| ✅ **复用现有逻辑** | SQL执行和图表配置复用现有代码 |

---

**文档版本**：v4.0
**创建日期**：2026-02-09
**作者**：CodeCraft
