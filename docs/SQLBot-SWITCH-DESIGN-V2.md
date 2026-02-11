# SQLBot 双方案切换设计（V2 - 按SQLBot现有架构）

## 📋 概要设计

### 1. 设计原则

按照SQLBot现有架构模式设计：
- 使用`system_variable`表存储功能开关
- 保持现有分层结构（api/crud/models/task）
- 使用FastAPI依赖注入和sqlmodel/SQLAlchemy ORM
- 异步编程，保持代码风格一致
- 最小化现有代码改动

---

## 🏗️ 架构设计

### 2. 目录结构

```
backend/apps/chat/
├── api/
│   └── chat.py              # 现有API（添加切换逻辑）
├── task/
│   ├── __init__.py
│   ├── llm.py               # 现有LLM方案（保持不变）
│   ├── claude_code.py       # 新增：Claude Code方案
│   └── strategy_factory.py  # 新增：方案工厂（策略模式）
├── models/
│   └── chat_model.py        # 现有模型
└── curd/
    └── chat.py              # 现有CRUD

backend/apps/system/
├── crud/
│   └── feature_flag.py      # 新增：功能开关CRUD
├── api/
│   └── feature_flag.py      # 新增：功能开关API
└── models/
    └── system_variable_model.py  # 现有（复用）

backend/apps/config_sync/
├── sync_config_to_md.py     # 现有配置同步
└── claude_code_client.py    # 新增：Claude Code客户端
```

---

## 🗄️ 数据库设计

### 3. 使用现有`system_variable`表

**存储功能开关配置**：

```sql
-- 插入功能开关配置
INSERT INTO system_variable (name, var_type, type, value, create_time, create_by)
VALUES
('use_claude_code', 'boolean', 'system', [false], NOW(), 1),
('claude_code_skill_dir', 'string', 'custom', ['/Users/guchuan/codespace/SQLBot/skills/sqlbot-knowledge'], NOW(), 1),
('claude_code_sync_enabled', 'boolean', 'custom', [true], NOW(), 1);
```

**字段说明**：
- `name`: 变量名（功能开关键）
- `var_type`: 变量类型（boolean/string）
- `type`: 类型（system=系统级，custom=自定义）
- `value`: 值（JSONB数组，存储开关值）
- `create_time`: 创建时间
- `create_by`: 创建人

---

## 🔧 核心代码设计

### 4. 功能开关CRUD

```python
# backend/apps/system/crud/feature_flag.py

from typing import List, Optional
from sqlmodel import select
from apps.system.models.system_variable_model import SystemVariable
from common.core.deps import SessionDep, CurrentUser, Trans


class FeatureFlagService:
    """功能开关服务"""

    @staticmethod
    def get_bool(session: SessionDep, name: str, default: bool = False) -> bool:
        """
        获取布尔类型的功能开关

        Args:
            session: 数据库会话
            name: 变量名
            default: 默认值

        Returns:
            bool: 开关值
        """
        stmt = select(SystemVariable).where(SystemVariable.name == name)
        result = session.exec(stmt).first()

        if not result or not result.value:
            return default

        if result.var_type == 'boolean':
            return bool(result.value[0]) if result.value else default

        return default

    @staticmethod
    def get_string(session: SessionDep, name: str, default: str = '') -> str:
        """
        获取字符串类型的功能开关

        Args:
            session: 数据库会话
            name: 变量名
            default: 默认值

        Returns:
            str: 开关值
        """
        stmt = select(SystemVariable).where(SystemVariable.name == name)
        result = session.exec(stmt).first()

        if not result or not result.value:
            return default

        if result.var_type == 'string':
            return str(result.value[0]) if result.value else default

        return default

    @staticmethod
    def set_bool(session: SessionDep, name: str, value: bool, user_id: int = 1) -> bool:
        """
        设置布尔类型的功能开关

        Args:
            session: 数据库会话
            name: 变量名
            value: 开关值
            user_id: 用户ID

        Returns:
            bool: 是否成功
        """
        import datetime

        stmt = select(SystemVariable).where(SystemVariable.name == name)
        result = session.exec(stmt).first()

        if result:
            result.value = [value]
            result.create_by = user_id
            session.add(result)
        else:
            variable = SystemVariable(
                name=name,
                var_type='boolean',
                type='custom',
                value=[value],
                create_time=datetime.datetime.now(),
                create_by=user_id
            )
            session.add(variable)

        session.commit()
        return True

    @staticmethod
    def set_string(session: SessionDep, name: str, value: str, user_id: int = 1) -> bool:
        """
        设置字符串类型的功能开关

        Args:
            session: 数据库会话
            name: 变量名
            value: 值
            user_id: 用户ID

        Returns:
            bool: 是否成功
        """
        import datetime

        stmt = select(SystemVariable).where(SystemVariable.name == name)
        result = session.exec(stmt).first()

        if result:
            result.value = [value]
            result.create_by = user_id
            session.add(result)
        else:
            variable = SystemVariable(
                name=name,
                var_type='string',
                type='custom',
                value=[value],
                create_time=datetime.datetime.now(),
                create_by=user_id
            )
            session.add(variable)

        session.commit()
        return True

    @staticmethod
    def get_all(session: SessionDep, trans: Trans, keyword: str = None) -> List[SystemVariable]:
        """
        获取所有功能开关

        Args:
            session: 数据库会话
            trans: 国际化
            keyword: 搜索关键词

        Returns:
            List[SystemVariable]: 功能开关列表
        """
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

### 5. 功能开关API

```python
# backend/apps/system/api/feature_flag.py

from typing import List, Optional
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from apps.system.models.system_variable_model import SystemVariable
from apps.system.crud.feature_flag import FeatureFlagService
from apps.swagger.i18n import PLACEHOLDER_PREFIX
from common.core.deps import SessionDep, CurrentUser, Trans

router = APIRouter(tags=["Feature Flags"], prefix="/system/feature-flags")


class ToggleFlagRequest(BaseModel):
    """切换开关请求"""
    name: str
    value: bool


class UpdateFlagRequest(BaseModel):
    """更新开关请求"""
    name: str
    value: str  # JSON字符串


@router.get("/list", summary=f"{PLACEHOLDER_PREFIX}get_feature_flags")
async def list_flags(
    session: SessionDep,
    trans: Trans,
    keyword: Optional[str] = Query(None, description="搜索关键词")
) -> List[SystemVariable]:
    """
    获取功能开关列表

    Args:
        session: 数据库会话
        trans: 国际化
        keyword: 搜索关键词

    Returns:
        List[SystemVariable]: 功能开关列表
    """
    return FeatureFlagService.get_all(session, trans, keyword)


@router.get("/{name}", summary=f"{PLACEHOLDER_PREFIX}get_feature_flag")
async def get_flag(
    session: SessionDep,
    name: str
) -> dict:
    """
    获取功能开关值

    Args:
        session: 数据库会话
        name: 变量名

    Returns:
        dict: 开关值
    """
    # 先尝试获取boolean
    try:
        value = FeatureFlagService.get_bool(session, name)
        return {"name": name, "value": value, "type": "boolean"}
    except:
        pass

    # 再尝试获取string
    value = FeatureFlagService.get_string(session, name)
    return {"name": name, "value": value, "type": "string"}


@router.post("/toggle", summary=f"{PLACEHOLDER_PREFIX}toggle_feature_flag")
async def toggle_flag(
    session: SessionDep,
    current_user: CurrentUser,
    request: ToggleFlagRequest
) -> dict:
    """
    切换功能开关

    Args:
        session: 数据库会话
        current_user: 当前用户
        request: 切换请求

    Returns:
        dict: 切换结果
    """
    success = FeatureFlagService.set_bool(
        session,
        request.name,
        request.value,
        current_user.id
    )

    if not success:
        raise HTTPException(status_code=500, detail="切换失败")

    return {"name": request.name, "value": request.value, "success": True}


@router.post("/update", summary=f"{PLACEHOLDER_PREFIX}update_feature_flag")
async def update_flag(
    session: SessionDep,
    current_user: CurrentUser,
    request: UpdateFlagRequest
) -> dict:
    """
    更新功能开关

    Args:
        session: 数据库会话
        current_user: 当前用户
        request: 更新请求

    Returns:
        dict: 更新结果
    """
    success = FeatureFlagService.set_string(
        session,
        request.name,
        request.value,
        current_user.id
    )

    if not success:
        raise HTTPException(status_code=500, detail="更新失败")

    return {"name": request.name, "value": request.value, "success": True}
```

---

### 6. Claude Code客户端

```python
# backend/apps/config_sync/claude_code_client.py

import asyncio
import subprocess
import json
from typing import Dict, Any, Optional
from pathlib import Path


class ClaudeCodeClient:
    """Claude Code客户端"""

    def __init__(self, skill_dir: str = None, claude_path: str = "claude"):
        self.skill_dir = skill_dir or "/Users/guchuan/codespace/SQLBot/skills/sqlbot-knowledge"
        self.claude_path = claude_path

    async def generate_sql(self, question: str, **kwargs) -> Dict[str, Any]:
        """
        调用Claude Code生成SQL

        Args:
            question: 用户问题
            **kwargs: 其他参数

        Returns:
            Dict: {'sql': str, 'chart_type': Optional[str], 'brief': Optional[str]}

        Raises:
            Exception: Claude Code调用失败
        """
        # 构建提示词
        prompt = self._build_sql_prompt(question, **kwargs)

        # 调用Claude Code
        result = await self._call_claude_code(prompt)

        # 解析结果
        return self._parse_sql_result(result)

    async def generate_chart(self, question: str, data: dict, chart_type: str = '', **kwargs) -> Dict[str, Any]:
        """
        调用Claude Code生成图表配置

        Args:
            question: 用户问题
            data: 数据
            chart_type: 图表类型
            **kwargs: 其他参数

        Returns:
            Dict: 图表配置

        Raises:
            Exception: Claude Code调用失败
        """
        # 构建提示词
        prompt = self._build_chart_prompt(question, data, chart_type, **kwargs)

        # 调用Claude Code
        result = await self._call_claude_code(prompt)

        # 解析结果
        return self._parse_chart_result(result)

    def _build_sql_prompt(self, question: str, **kwargs) -> str:
        """构建SQL生成提示词"""
        return f"""
你是SQLBot的智能问数Agent。请根据以下信息生成SQL：

用户问题：{question}

请读取以下配置文件：
- {self.skill_dir}/SCHEMA.md
- {self.skill_dir}/TERMINOLOGY.md
- {self.skill_dir}/EXAMPLES.md
- {self.skill_dir}/PROMPT.md

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

    def _build_chart_prompt(self, question: str, data: dict, chart_type: str = '', **kwargs) -> str:
        """构建图表配置提示词"""
        data_str = json.dumps(data, ensure_ascii=False, indent=2)

        return f"""
请为以下数据生成图表配置：

用户问题：{question}
推荐图表类型：{chart_type or '自动推荐'}
数据结构：
{data_str}

返回JSON格式：
{{
  "type": "line|bar|pie|table",
  "x": "x轴字段名",
  "y": "y轴字段名",
  "series": [...],
  "title": "图表标题"
}}
"""

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
                "--output", "json"
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

    def _parse_chart_result(self, result: str) -> Dict[str, Any]:
        """解析图表配置结果"""
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
            # 如果解析失败，返回默认配置
            return {
                "type": "table",
                "x": "",
                "y": "",
                "series": [],
                "title": ""
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

### 7. Claude Code方案任务

```python
# backend/apps/chat/task/claude_code.py

import asyncio
import traceback
from typing import AsyncIterator, Dict, Any, List, Union
from sqlmodel import Session

from apps.chat.curd.chat import (
    save_question, save_sql_answer, save_chart_answer,
    get_chart_data, get_chat_record_by_id
)
from apps.chat.models.chat_model import ChatQuestion, ChatRecord, OperationEnum
from apps.config_sync.claude_code_client import ClaudeCodeClient
from apps.db.db import exec_sql
from apps.system.crud.feature_flag import FeatureFlagService
from common.core.deps import CurrentUser, CurrentAssistant
from common.error import SingleMessageError
from common.utils.locale import I18n, I18nHelper


class ClaudeCodeTask:
    """Claude Code方案任务"""

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
        """初始化聊天记录"""
        self.record = save_question(
            session=self.session,
            current_user=self.current_user,
            question=self.chat_question
        )
        return self.record

    async def generate_sql(self) -> AsyncIterator[Dict[str, Any]]:
        """
        生成SQL

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
        执行SQL

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

            # 执行SQL
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
        生成图表配置

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
            # 获取数据
            data = get_chart_data(self.session, self.record.id)

            # 调用Claude Code生成图表配置
            result = await self.client.generate_chart(
                question=self.chat_question.question,
                data=data,
                chart_type=chart_type
            )

            # 保存图表配置
            save_chart_answer(
                session=self.session,
                record_id=self.record.id,
                answer=f'{{"content": {json.dumps(result)}}}'
            )

            # 流式返回图表配置
            yield {
                'type': 'chart',
                'content': result
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
        """
        # 1. 生成SQL
        async for chunk in self.generate_sql():
            yield chunk

            # 如果出错，停止
            if chunk.get('type') == 'error':
                return

            sql = chunk.get('content')

        # 2. 执行SQL
        async for chunk in self.execute_sql(sql):
            yield chunk

            # 如果出错，停止
            if chunk.get('type') == 'error':
                return

        # 3. 生成图表配置
        if finish_step == 'generate_chart':
            async for chunk in self.generate_chart():
                yield chunk

                # 如果出错，停止
                if chunk.get('type') == 'error':
                    return
```

---

### 8. 策略工厂

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
    """LLM方案生成器"""

    def __init__(self, session: Session, chat_question: ChatQuestion,
                 current_user: CurrentUser, current_assistant: CurrentAssistant = None):
        super().__init__(session, chat_question, current_user, current_assistant)
        self.llm_service: LLMService = None

    async def create(self):
        """初始化LLM服务"""
        self.llm_service = await LLMService.create(
            self.session, self.current_user, self.chat_question, self.current_assistant
        )

    async def init_record(self):
        """初始化记录"""
        self.record = self.llm_service.init_record(self.session)

    async def run_task(self, in_chat: bool = True, stream: bool = True,
                      finish_step: str = 'generate_chart') -> AsyncIterator[Dict[str, Any]]:
        """运行LLM任务"""
        self.llm_service.run_task_async(in_chat=in_chat, stream=stream, finish_step=finish_step)

        # 等待结果
        from fastapi.responses import StreamingResponse
        async for chunk in self.llm_service.await_result():
            yield chunk


class ClaudeCodeSQLGenerator(BaseSQLGenerator):
    """Claude Code方案生成器"""

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
        """初始化记录"""
        self.record = await self.cc_task.init_record()

    async def run_task(self, in_chat: bool = True, stream: bool = True,
                      finish_step: str = 'generate_chart') -> AsyncIterator[Dict[str, Any]]:
        """运行Claude Code任务"""
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
        """
        # 检查功能开关
        use_claude_code = FeatureFlagService.get_bool(
            session,
            'use_claude_code',
            default=False  # 默认使用LLM方案
        )

        if use_claude_code:
            # 使用Claude Code方案
            generator = ClaudeCodeSQLGenerator(session, chat_question, current_user, current_assistant)
        else:
            # 使用LLM方案（默认）
            generator = LLMSQLGenerator(session, chat_question, current_user, current_assistant)

        # 初始化生成器
        await generator.create()

        return generator
```

---

### 9. API修改

```python
# backend/apps/chat/api/chat.py 修改部分

async def stream_sql(session: SessionDep, current_user: CurrentUser, request_question: ChatQuestion,
                     current_assistant: Optional[CurrentAssistant] = None, in_chat: bool = True,
                     stream: bool = True, finish_step: ChatFinishStep = ChatFinishStep.GENERATE_CHART,
                     embedding: bool = False):
    """
    流式生成SQL（修改版）

    使用工厂模式，根据功能开关选择方案
    """
    try:
        # 原代码：
        # llm_service = await LLMService.create(...)

        # 新代码：使用工厂创建SQL生成器
        from apps.chat.task.strategy_factory import SQLGeneratorFactory

        sql_generator = await SQLGeneratorFactory.create(
            session, current_user, request_question, current_assistant
        )

        # 初始化记录
        await sql_generator.init_record()

        # 运行任务
        sql_generator.run_task_async(in_chat=in_chat, stream=stream, finish_step=finish_step)

    except Exception as e:
        traceback.print_exc()

        if stream:
            def _err(_e: Exception):
                yield 'data:' + orjson.dumps({'content': str(_e), 'type': 'error'}).decode() + '\n\n'

            return StreamingResponse(_err(e), media_type="text/event-stream")
        else:
            return JSONResponse(
                content={'message': str(e)},
                status_code=500,
            )

    if stream:
        return StreamingResponse(sql_generator.await_result(), media_type="text/event-stream")
    else:
        res = sql_generator.await_result()
        raw_data = {}
        for chunk in res:
            if chunk:
                raw_data = chunk
        status_code = 200
        if not raw_data.get('success'):
            status_code = 500

        return JSONResponse(
            content=raw_data,
            status_code=status_code,
        )
```

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
   - 功能：调用Claude Code生成SQL/图表
   - 测试：端到端测试

2. **配置同步**
   - 复用现有`sync_config_to_md.py`
   - 确保MD文件生成正确

### Phase 3: Claude Code方案任务（2-3小时）

1. **实现`ClaudeCodeTask`**
   - 文件：`backend/apps/chat/task/claude_code.py`
   - 功能：生成SQL、执行SQL、生成图表
   - 测试：单元测试

2. **错误处理**
   - 降级机制：失败自动回退到LLM方案
   - 日志记录

### Phase 4: 策略工厂（2-3小时）

1. **实现策略接口和工厂**
   - 文件：`backend/apps/chat/task/strategy_factory.py`
   - 功能：工厂模式，根据开关选择方案
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

## 📊 技术要点

### 10. 兼容性

- **向后兼容**：默认使用LLM方案，`use_claude_code=false`
- **平滑切换**：修改功能开关后立即生效，无需重启
- **数据隔离**：两种方案共享数据库，结果格式一致

### 11. 性能

| 方案 | 优势 | 劣势 |
|------|------|------|
| LLM方案 | 响应稳定，可控 | API成本 |
| Claude Code | 免API成本，理解能力强 | 依赖本地进程，配置同步开销 |

**建议**：
- 高并发场景：优先LLM方案
- 复杂查询：优先Claude Code方案
- 支持：按数据源级别配置

### 12. 监控和日志

- 记录每次使用的方案（在`ChatRecord`中添加`solution_type`字段）
- 统计两种方案的成功率、响应时间
- 异常情况自动降级并记录日志

### 13. 安全性

- Claude Code调用需要权限验证
- 敏感信息（API Key）不存储在Skill文件中
- 配置同步使用内部API，不对外暴露

---

## 🔒 风险和应对

| 风险 | 应对措施 |
|------|----------|
| Claude Code调用失败 | 自动降级到LLM方案，记录日志 |
| 配置同步失败 | 提供手动同步按钮，发送告警 |
| 性能下降 | 添加缓存，监控响应时间，支持回退 |
| 切换不可控 | 保留LLM方案作为后备，提供一键回滚 |

---

## 🚀 后续优化

1. **A/B测试**：支持对部分用户使用Claude Code方案
2. **多模型支持**：同时支持多种LLM方案，动态选择最优
3. **智能切换**：根据问题类型自动选择最合适的方案
4. **缓存机制**：缓存常见问题的SQL，减少重复调用
5. **性能优化**：配置同步增量更新，减少全量同步

---

## 📝 使用示例

### 开启Claude Code方案

```bash
# 方法1：通过API
curl -X POST "http://localhost:8000/api/system/feature-flags/toggle" \
  -H "Content-Type: application/json" \
  -d '{"name": "use_claude_code", "value": true}'

# 方法2：通过数据库
UPDATE system_variable
SET value = [true]
WHERE name = 'use_claude_code';
```

### 手动同步配置

```bash
# 方法1：通过API（待实现）
curl -X POST "http://localhost:8000/api/system/config-sync/sync" \
  -H "Content-Type: application/json" \
  -d '{"datasource_id": 1, "oid": 1}'

# 方法2：通过Python脚本
cd /Users/guchuan/codespace/SQLBot/backend
python apps/config_sync/sync_config_to_md.py
```

---

**文档版本**：v2.0
**创建日期**：2026-02-09
**作者**：CodeCraft
