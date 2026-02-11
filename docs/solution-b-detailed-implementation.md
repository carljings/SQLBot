# 方案B详细实施方案 - 保留SQLBot RAG + 替换Claude LLM

> 苏政源一本账智能问数 - 详细实施指南
> 方案：保留SQLBot的RAG层，替换LLM为Claude
> 设计时间：2026-02-08

---

## 📋 方案B架构图

```
┌─────────────────────────────────────────────────────┐
│                 SQLBot 前端                     │
│              (React - 无需修改）                  │
└───────────────────┬───────────────────────────────┘
                    │ HTTP/WebSocket
                    ▼
┌─────────────────────────────────────────────────────┐
│                 SQLBot 后端                     │
│              (FastAPI - 改动最小）              │
│                                                  │
│  ┌─────────────────────────────────────────┐   │
│  │         RAG 增强层（保留）               │   │
│  ├─→ Schema (数据库表结构）                 │   │
│  ├─→ Terminology (术语库)                   │   │
│  ├─→ Data Training (SQL示例)              │   │
│  ├─→ Custom Prompt (业务规则)              │   │
│  └─────────────────────────────────────────┘   │
│                                                  │
│  ┌─────────────────────────────────────────┐   │
│  │         Prompt 构建层（保留）             │   │
│  ├─→ sql_sys_question()                    │   │
│  ├─→ 注入 Schema                           │   │
│  ├─→ 注入 Terminology                      │   │
│  ├─→ 注入 Data Training                    │   │
│  ├─→ 注入 Custom Prompt                    │   │
│  └─────────────────────────────────────────┘   │
│                                                  │
│  ┌─────────────────────────────────────────┐   │
│  │         LLM 调用层（改这里！）           │   │
│  ├─→ LLMFactory.create_llm()              │   │
│  ├─→ 原来：OpenAI/通义千问/VLLM           │   │
│  └─→ 新增：Claude (ChatAnthropic)        │   │
│  └─────────────────────────────────────────┘   │
│                                                  │
│  ┌─────────────────────────────────────────┐   │
│  │         数据访问层（保留）               │   │
│  ├─→ SQL 执行                              │   │
│  ├─→ 结果格式化                            │   │
│  └─→ 图表生成                              │   │
│  └─────────────────────────────────────────┘   │
└───────────────────┬───────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────┐
│              PostgreSQL 数据库                 │
│  ├─→ 业务数据表（苏政源一本账）                │
│  ├─→ SQLBot 系统表                         │
│  ├─→ terminology (术语库)                    │
│  ├─→ data_training (SQL示例)                │
│  └─→ ai_model_detail (LLM配置)              │
└─────────────────────────────────────────────────────┘
```

---

## 🎯 核心改动点

### 只需修改3个地方！

#### 改动 1：apps/ai_model/llm.py

**新增 Claude LLM 类**

```python
# apps/ai_model/llm.py

from langchain_anthropic import ChatAnthropic

class ClaudeLLM(BaseLLM):
    """Claude LLM 实现"""
    
    def _init_llm(self) -> BaseChatModel:
        """初始化 Claude LLM 实例"""
        return ChatAnthropic(
            model=self.config.model_name,  # claude-3-5-sonnet-20241022
            api_key=self.config.api_key,
            temperature=self.config.additional_params.get('temperature', 0),
            streaming=True,
            **self.config.additional_params
        )
```

**修改 LLMFactory 注册**

```python
# apps/ai_model/llm.py

class LLMFactory:
    """大语言模型工厂类"""

    _llm_types: Dict[str, Type[BaseLLM]] = {
        "openai": OpenAILLM,        # 保留
        "tongyi": OpenAILLM,        # 保留
        "vllm": OpenAIvLLM,        # 保留
        "azure": OpenAIAzureLLM,    # 保留
        "claude": ClaudeLLM,        # 新增！
    }

    @classmethod
    @lru_cache(maxsize=32)
    def create_llm(cls, config: LLMConfig) -> BaseLLM:
        llm_class = cls._llm_types.get(config.model_type)
        if not llm_class:
            raise ValueError(f"Unsupported LLM type: {config.model_type}")
        return llm_class(config)

    @classmethod
    def register_llm(cls, model_type: str, llm_class: Type[BaseLLM]):
        """注册新模型类型"""
        cls._llm_types[model_type] = llm_class
```

---

#### 改动 2：apps/ai_model/model_factory.py

**修改 get_default_config() 方法**

```python
# apps/ai_model/model_factory.py

async def get_default_config() -> LLMConfig:
    """获取默认 LLM 配置"""
    
    with Session(engine) as session:
        # 查询 default_model=True 的配置
        db_model = session.exec(
            select(AiModelDetail).where(AiModelDetail.default_model == True)
        ).first()
        
        if not db_model:
            raise Exception("The system default model has not been set")

        # 解析 additional_params
        additional_params = {}
        if db_model.config:
            try:
                config_raw = json.loads(db_model.config)
                additional_params = {
                    item["key"]: prepare_model_arg(item.get('val'))
                    for item in config_raw
                    if "key" in item and "val" in item
                }
            except Exception:
                pass
        
        # 解密 API Key 和 Endpoint（如果加密）
        if not db_model.api_domain.startswith("http"):
            db_model.api_domain = await sqlbot_decrypt(db_model.api_domain)
            if db_model.api_key:
                db_model.api_key = await sqlbot_decrypt(db_model.api_key)
        
        # 构造 LLMConfig（支持 Claude）
        # protocol: 1=OpenAI兼容, 2=VLLM
        # 对于 Claude，使用 protocol=1 (OpenAI兼容)
        return LLMConfig(
            model_id=db_model.id,
            model_type="claude" if "claude" in db_model.base_model.lower() 
                          else "openai" if db_model.protocol == 1 
                          else "vllm",
            model_name=db_model.base_model,
            api_key=db_model.api_key,
            api_base_url=db_model.api_domain,
            additional_params=additional_params,
        )
```

---

#### 改动 3：数据库配置（添加 Claude 模型）

**SQL 插入语句**

```sql
-- 添加 Claude 3.5 Sonnet 模型配置
INSERT INTO ai_model_detail (
    name,                    -- 模型名称
    base_model,              -- 基础模型（Claude 模型名）
    protocol,                -- 协议类型（1=OpenAI兼容）
    api_domain,             -- API 地址
    api_key,                -- API Key（加密存储）
    type_name,               -- 类型名称（用于 LLMFactory）
    default_model,           -- 是否为默认模型
    temperature,            -- 温度参数
    config,                 -- 额外配置（JSON）
    oid,                    -- 所属组织
    created_at,
    updated_at
) VALUES (
    'Claude 3.5 Sonnet',                           -- name
    'claude-3-5-sonnet-20241022',                 -- base_model
    1,                                                -- protocol (OpenAI兼容)
    'https://api.anthropic.com',                    -- api_domain
    'your-claude-api-key-here',                   -- api_key
    'claude',                                        -- type_name
    true,                                            -- default_model
    0.0,                                             -- temperature
    '[]',                                            -- config (JSON字符串)
    1,                                                -- oid (组织ID)
    NOW(),                                           -- created_at
    NOW()                                            -- updated_at
);
```

**SQL 更新为默认模型**

```sql
-- 将所有模型设为非默认
UPDATE ai_model_detail SET default_model = false;

-- 将 Claude 设为默认
UPDATE ai_model_detail 
SET default_model = true 
WHERE base_model = 'claude-3-5-sonnet-20241022';
```

---

## 🔧 详细实施步骤

### 步骤 1：安装依赖（10分钟）

```bash
cd /Users/guchuan/codespace/SQLBot/backend

# 安装 LangChain Anthropic 集成
pip install langchain-anthropic

# 验证安装
python -c "from langchain_anthropic import ChatAnthropic; print('OK')"
```

---

### 步骤 2：创建 Claude LLM 类（30分钟）

**文件**：`apps/ai_model/llm.py`

**代码**：

```python
# apps/ai_model/llm.py

# 在文件顶部导入
from langchain_anthropic import ChatAnthropic

# 在 BaseLLM 类后添加 Claude LLM 类
class ClaudeLLM(BaseLLM):
    """
    Claude LLM 实现
    基于 Anthropic Claude 3.5 Sonnet
    """
    
    def _init_llm(self) -> BaseChatModel:
        """
        初始化 Claude LLM 实例
        
        Returns:
            ChatAnthropic: LangChain Claude 实例
        """
        return ChatAnthropic(
            # 模型名称（必填）
            model=self.config.model_name,
            # Claude API Key（必填）
            api_key=self.config.api_key or 'Empty',
            # API Base URL（默认：https://api.anthropic.com）
            base_url=self.config.api_base_url,
            # 温度参数（0-1，默认0）
            temperature=self.config.additional_params.get('temperature', 0),
            # 最大 Token 数（默认4096）
            max_tokens=self.config.additional_params.get('max_tokens', 4096),
            # 启用流式响应
            streaming=True,
            # 其他额外参数
            **{k: v for k, v in self.config.additional_params.items() 
               if k not in ['temperature', 'max_tokens']}
        )
```

---

### 步骤 3：注册 Claude LLM（20分钟）

**文件**：`apps/ai_model/llm.py`

**代码**：修改 `LLMFactory` 类

```python
# apps/ai_model/llm.py

class LLMFactory:
    """大语言模型工厂类"""

    # LLM 类型注册表
    _llm_types: Dict[str, Type[BaseLLM]] = {
        "openai": OpenAILLM,        # OpenAI GPT
        "tongyi": OpenAILLM,        # 阿里云通义千问
        "vllm": OpenAIvLLM,        # VLLM (本地部署）
        "azure": OpenAIAzureLLM,    # Azure OpenAI
        "claude": ClaudeLLM,        # Claude Anthropic（新增！）
    }

    @classmethod
    @lru_cache(maxsize=32)
    def create_llm(cls, config: LLMConfig) -> BaseLLM:
        """
        创建 LLM 实例（工厂方法）
        
        Args:
            config (LLMConfig): LLM 配置对象
            
        Returns:
            BaseLLM: LLM 实例
            
        Raises:
            ValueError: 不支持的 LLM 类型
        """
        llm_class = cls._llm_types.get(config.model_type)
        if not llm_class:
            raise ValueError(f"Unsupported LLM type: {config.model_type}")
        return llm_class(config)

    @classmethod
    def register_llm(cls, model_type: str, llm_class: Type[BaseLLM]):
        """
        注册新模型类型（用于扩展）
        
        Args:
            model_type (str): 模型类型标识
            llm_class (Type[BaseLLM]): LLM 类
        """
        cls._llm_types[model_type] = llm_class
```

---

### 步骤 4：修改 get_default_config()（30分钟）

**文件**：`apps/ai_model/model_factory.py`

**代码**：修改 `get_default_config()` 函数

```python
# apps/ai_model/model_factory.py

async def get_default_config() -> LLMConfig:
    """
    获取默认 LLM 配置
    从数据库中读取 default_model=True 的配置
    
    Returns:
        LLMConfig: LLM 配置对象
        
    Raises:
        Exception: 未设置默认模型
    """
    with Session(engine) as session:
        # 查询默认模型
        db_model = session.exec(
            select(AiModelDetail).where(AiModelDetail.default_model == True)
        ).first()
        
        if not db_model:
            raise Exception("The system default model has not been set")

        # 解析配置（config 字段是 JSON 字符串）
        additional_params = {}
        if db_model.config:
            try:
                config_raw = json.loads(db_model.config)
                # 转换为字典
                additional_params = {
                    item["key"]: prepare_model_arg(item.get('val'))
                    for item in config_raw
                    if "key" in item and "val" in item
                }
            except Exception as e:
                print(f"Warning: Failed to parse config: {e}")
                pass
        
        # 解密 API Key 和 Endpoint
        # 注意：如果你的系统有加密，需要解密
        if not db_model.api_domain.startswith("http"):
            # 假设有 sqlbot_decrypt 函数
            db_model.api_domain = await sqlbot_decrypt(db_model.api_domain)
            if db_model.api_key:
                db_model.api_key = await sqlbot_decrypt(db_model.api_key)
        
        # 确定 model_type
        # protocol: 1=OpenAI兼容, 2=VLLM
        # Claude 使用 OpenAI 兼容协议，所以 model_type="claude"
        if "claude" in db_model.base_model.lower():
            model_type = "claude"
        elif db_model.protocol == 1:
            model_type = "openai"
        elif db_model.protocol == 2:
            model_type = "vllm"
        else:
            model_type = "openai"
        
        # 构造 LLMConfig
        return LLMConfig(
            model_id=db_model.id,
            model_type=model_type,
            model_name=db_model.base_model,
            api_key=db_model.api_key,
            api_base_url=db_model.api_domain,
            additional_params=additional_params,
        )
```

---

### 步骤 5：添加 Claude 模型到数据库（10分钟）

**方式 1：通过 SQL 插入**

```sql
-- 添加 Claude 3.5 Sonnet
INSERT INTO ai_model_detail (
    name,
    base_model,
    protocol,
    api_domain,
    api_key,
    type_name,
    default_model,
    temperature,
    config,
    oid,
    created_at,
    updated_at
) VALUES (
    'Claude 3.5 Sonnet',
    'claude-3-5-sonnet-20241022',
    1,
    'https://api.anthropic.com',
    'sk-ant-api03-your-api-key-here',
    'claude',
    true,
    0.0,
    '[]',
    1,
    NOW(),
    NOW()
);

-- 设置为默认模型
UPDATE ai_model_detail 
SET default_model = true 
WHERE base_model = 'claude-3-5-sonnet-20241022';
```

**方式 2：通过前端添加**

1. 启动 SQLBot
2. 访问：http://localhost:8000
3. 进入：系统设置 → AI 模型管理
4. 点击"添加模型"
5. 填写配置：
   - 名称：`Claude 3.5 Sonnet`
   - 基础模型：`claude-3-5-sonnet-20241022`
   - 协议类型：`OpenAI`
   - API 地址：`https://api.anthropic.com`
   - API Key：你的 Claude API Key
   - 类型名称：`claude`
   - 温度：`0`
6. 点击"设为默认"

---

### 步骤 6：验证配置（10分钟）

```bash
# 启动 SQLBot 后端
cd /Users/guchuan/codespace/SQLBot/backend
python main.py

# 访问前端测试
# http://localhost:8000

# 测试查询
# 输入："系统数量"
# 预期：应该使用 Claude 生成 SQL
```

**验证点**：
- [ ] Claude 模型已添加到数据库
- [ ] Claude 已设置为默认模型
- [ ] SQLBot 后端启动成功
- [ ] 前端可以正常访问
- [ ] 测试查询，SQL 正确生成
- [ ] 查看日志，确认使用的是 Claude

---

### 步骤 7：测试和调优（1-2小时）

#### 测试场景 1：简单查询

```sql
-- 测试 SQL
-- 输入："系统数量"
-- 预期 SQL：
SELECT COUNT(*) FROM t_sys;

-- 验证点：
- [ ] SQL 语法正确
- [ ] 结果准确
- [ ] 响应时间可接受（<3秒）
```

#### 测试场景 2：复杂查询

```sql
-- 测试 SQL
-- 输入："2025年南京市省垂系统数量"
-- 预期 SQL：
SELECT COUNT(*) 
FROM t_sys 
WHERE year = 2025 
  AND city = '南京市' 
  AND type = '省垂';

-- 验证点：
- [ ] SQL 语法正确
- [ ] 多个条件正确组合
- [ ] 术语"省垂"正确匹配
- [ ] 结果准确
```

#### 测试场景 3：术语匹配

```sql
-- 测试术语
-- 输入："垂管系统数量"
-- 预期：通过术语库匹配，生成 WHERE type = '省垂'

-- 验证点：
- [ ] 术语库正确匹配
- [ ] SQL 正确注入术语条件
```

#### 测试场景 4：SQL 示例

```sql
-- 测试 SQL 示例（Few-shot）
-- 输入："系统总数量"
-- 预期：参考 SQL 示例生成

-- 验证点：
- [ ] SQL 示例正确引用
- [ ] 生成的 SQL 与示例风格一致
```

---

## 🔍 日志和调试

### 查看 LLM 调用日志

```python
# 在 apps/chat/task/llm.py 中添加日志

class LLMService:
    def __init__(self, session, current_user, chat_question, ...):
        # ...
        
        # 添加日志：显示使用的模型
        SQLBotLogUtil.info(f"Using LLM: {self.config.model_name} (type: {self.config.model_type})")
```

### 查看生成的 Prompt

```python
# 在 apps/chat/task/llm.py 中添加日志

class LLMService:
    def generate_sql(self, question: str) -> str:
        # 构建系统 Prompt
        sys_prompt = self.chat_question.sql_sys_question(self.ds.type)
        
        # 添加日志：显示 Prompt 片段
        SQLBotLogUtil.info(f"Schema length: {len(self.ds.schema)}")
        SQLBotLogUtil.info(f"Terminologies count: {len(self.chat_question.terminologies)}")
        SQLBotLogUtil.info(f"Data training count: {len(self.chat_question.data_training)}")
```

---

## 📊 性能对比

### Claude vs 通义千问

| 指标 | 通义千问 | Claude 3.5 Sonnet |
|------|---------|------------------|
| **准确性** | 中等 | 高 |
| **响应时间** | 快（~2秒） | 中等（~3秒） |
| **成本** | 低（¥0.008/1K tokens） | 中等（$3.00/1M tokens） |
| **理解能力** | 中等 | 高 |
| **中文支持** | 优秀 | 优秀 |

### 成本估算（假设）

| 操作 | 通义千问 | Claude 3.5 Sonnet | 差异 |
|------|---------|------------------|------|
| **1K tokens** | ¥0.008 | $0.003 (约¥0.022) | +175% |
| **日均查询100次** | ¥32/天 | ¥88/天 | +175% |
| **月均查询3000次** | ¥960/月 | ¥2640/月 | +175% |

**建议**：
- 开发/测试阶段：使用通义千问（成本低）
- 生产环境：使用 Claude 3.5 Sonnet（准确性高）

---

## 🎨 配置示例

### Claude 3.5 Sonnet 配置

```json
{
  "model_id": 100,
  "model_type": "claude",
  "model_name": "claude-3-5-sonnet-20241022",
  "api_key": "sk-ant-api03-your-key",
  "api_base_url": "https://api.anthropic.com",
  "additional_params": {
    "temperature": 0,
    "max_tokens": 4096,
    "top_p": 1.0
  }
}
```

### 通义千问配置（对比）

```json
{
  "model_id": 99,
  "model_type": "openai",
  "model_name": "qwen-max",
  "api_key": "your-dashscope-key",
  "api_base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
  "additional_params": {
    "temperature": 0,
    "max_tokens": 4096
  }
}
```

---

## 🐛 常见问题和解决

### 问题 1：LangChain Anthropic 导入失败

**错误信息**：
```
ModuleNotFoundError: No module named 'langchain_anthropic'
```

**解决方案**：
```bash
pip install langchain-anthropic
```

---

### 问题 2：Claude API Key 无效

**错误信息**：
```
Error: Invalid API Key
```

**解决方案**：
1. 检查 API Key 是否正确
2. 检查 API Key 是否有权限访问 Claude 3.5 Sonnet
3. 登录 Anthropic 控制台确认

---

### 问题 3：模型类型识别错误

**错误信息**：
```
ValueError: Unsupported LLM type: claude
```

**解决方案**：
1. 检查 `LLMFactory._llm_types` 是否包含 "claude"
2. 检查 `type_name` 字段是否为 "claude"
3. 重启 SQLBot 后端

---

### 问题 4：SQL 生成不准确

**可能原因**：
1. 温度参数太高（建议 0）
2. Prompt 缺少上下文（检查术语库、SQL 示例）
3. RAG 检索不准确（检查向量存储）

**解决方案**：
```sql
-- 1. 降低温度
UPDATE ai_model_detail 
SET temperature = 0 
WHERE base_model = 'claude-3-5-sonnet-20241022';

-- 2. 检查术语库
SELECT * FROM terminology LIMIT 10;

-- 3. 检查 SQL 示例
SELECT * FROM data_training LIMIT 10;

-- 4. 检查 Prompt 配置
SELECT * FROM custom_prompt WHERE enabled = true;
```

---

## 📝 回退方案

如果 Claude 不满足需求，可以快速切换回通义千问：

```sql
-- 切换回通义千问
UPDATE ai_model_detail 
SET default_model = true 
WHERE base_model LIKE 'qwen%';
```

或者通过前端：
1. 系统设置 → AI 模型管理
2. 选择通义千问
3. 点击"设为默认"

---

## 📋 检查清单

### 实施前检查

- [ ] 已安装 `langchain-anthropic`
- [ ] 已获取 Claude API Key
- [ ] 已备份 SQLBot 数据库
- [ ] 已阅读 SQLBot 文档

### 实施后检查

- [ ] Claude LLM 类已创建
- [ ] LLMFactory 已注册 Claude
- [ ] get_default_config 已修改
- [ ] Claude 模型已添加到数据库
- [ ] Claude 已设置为默认模型
- [ ] SQLBot 后端启动成功
- [ ] 前端可以正常访问
- [ ] 测试查询正常
- [ ] 日志显示使用的是 Claude

---

## 🚀 完整代码示例

### 文件：apps/ai_model/llm.py（完整修改）

```python
from functools import lru_cache
import json
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Type

from langchain.chat_models.base import BaseChatModel
from pydantic import BaseModel
from sqlmodel import Session, select

# 新增导入
from langchain_anthropic import ChatAnthropic

from apps.ai_model.openai.llm import BaseChatOpenAI
from apps.system.models.system_model import AiModelDetail
from common.core.db import engine
from common.utils.crypto import sqlbot_decrypt
from common.utils.utils import prepare_model_arg
from langchain_community.llms import VLLMOpenAI
from langchain_openai import AzureChatOpenAI

class LLMConfig(BaseModel):
    """Base configuration class for large language models"""
    model_id: Optional[int] = None
    model_type: str  # Model type: openai/tongyi/vllm/claude etc.
    model_name: str  # Specific model name
    api_key: Optional[str] = None
    api_base_url: Optional[str] = None
    additional_params: Dict[str, Any] = {}
    class Config:
        frozen = True

    def __hash__(self):
        if hasattr(self, 'additional_params') and isinstance(self.additional_params, dict):
            hashable_params = frozenset((k, tuple(v) if isinstance(v, (list, dict)) else v) 
                            for k, v in self.additional_params.items())
        else:
            hashable_params = None
        
        return hash((
            self.model_id,
            self.model_type,
            self.model_name,
            self.api_key,
            self.api_base_url,
            hashable_params
        ))

class BaseLLM(ABC):
    """Abstract base class for large language models"""

    def __init__(self, config: LLMConfig):
        self.config = config
        self._llm = self._init_llm()

    @abstractmethod
    def _init_llm(self) -> BaseChatModel:
        """Initialize specific large language model instance"""
        pass

    @property
    def llm(self) -> BaseChatModel:
        """Return the langchain LLM instance"""
        return self._llm

class OpenAIvLLM(BaseLLM):
    def _init_llm(self) -> VLLMOpenAI:
        return VLLMOpenAI(
            openai_api_key=self.config.api_key or 'Empty',
            openai_api_base=self.config.api_base_url,
            model_name=self.config.model_name,
            streaming=True,
            **self.config.additional_params,
        )

class OpenAIAzureLLM(BaseLLM):
    def _init_llm(self) -> AzureChatOpenAI:
        api_version = self.config.additional_params.get("api_version")
        deployment_name = self.config.additional_params.get("deployment_name")
        if api_version:
            self.config.additional_params.pop("api_version")
        if deployment_name:
            self.config.additional_params.pop("deployment_name")
        return AzureChatOpenAI(
            azure_endpoint=self.config.api_base_url,
            api_key=self.config.api_key or 'Empty',
            model_name=self.config.model_name,
            api_version=api_version,
            deployment_name=deployment_name,
            streaming=True,
            **self.config.additional_params,
        )
    
class OpenAILLM(BaseLLM):
    def _init_llm(self) -> BaseChatModel:
        return BaseChatOpenAI(
            model=self.config.model_name,
            api_key=self.config.api_key or 'Empty',
            base_url=self.config.api_base_url,
            stream_usage=True,
            **self.config.additional_params,
        )

    def generate(self, prompt: str) -> str:
        return self.llm.invoke(prompt)

# 新增：Claude LLM
class ClaudeLLM(BaseLLM):
    """
    Claude LLM 实现
    基于 Anthropic Claude 3.5 Sonnet
    """
    
    def _init_llm(self) -> BaseChatModel:
        """
        初始化 Claude LLM 实例
        
        Returns:
            ChatAnthropic: LangChain Claude 实例
        """
        return ChatAnthropic(
            model=self.config.model_name,
            api_key=self.config.api_key or 'Empty',
            base_url=self.config.api_base_url,
            temperature=self.config.additional_params.get('temperature', 0),
            max_tokens=self.config.additional_params.get('max_tokens', 4096),
            streaming=True,
            **{k: v for k, v in self.config.additional_params.items() 
               if k not in ['temperature', 'max_tokens']}
        )

class LLMFactory:
    """Large Language Model Factory Class"""

    _llm_types: Dict[str, Type[BaseLLM]] = {
        "openai": OpenAILLM,
        "tongyi": OpenAILLM,
        "vllm": OpenAIvLLM,
        "azure": OpenAIAzureLLM,
        "claude": ClaudeLLM,  # 新增
    }

    @classmethod
    @lru_cache(maxsize=32)
    def create_llm(cls, config: LLMConfig) -> BaseLLM:
        llm_class = cls._llm_types.get(config.model_type)
        if not llm_class:
            raise ValueError(f"Unsupported LLM type: {config.model_type}")
        return llm_class(config)

    @classmethod
    def register_llm(cls, model_type: str, llm_class: Type[BaseLLM]):
        """Register new model type"""
        cls._llm_types[model_type] = llm_class

async def get_default_config() -> LLMConfig:
    """
    获取默认 LLM 配置
    支持 Claude 模型
    """
    with Session(engine) as session:
        db_model = session.exec(
            select(AiModelDetail).where(AiModelDetail.default_model == True)
        ).first()
        if not db_model:
            raise Exception("The system default model has not been set")

        additional_params = {}
        if db_model.config:
            try:
                config_raw = json.loads(db_model.config)
                additional_params = {
                    item["key"]: prepare_model_arg(item.get('val'))
                    for item in config_raw
                    if "key" in item and "val" in item
                }
            except Exception:
                pass
        
        if not db_model.api_domain.startswith("http"):
            db_model.api_domain = await sqlbot_decrypt(db_model.api_domain)
            if db_model.api_key:
                db_model.api_key = await sqlbot_decrypt(db_model.api_key)
        
        # 确定 model_type（支持 Claude）
        if "claude" in db_model.base_model.lower():
            model_type = "claude"
        elif db_model.protocol == 1:
            model_type = "openai"
        elif db_model.protocol == 2:
            model_type = "vllm"
        else:
            model_type = "openai"
        
        return LLMConfig(
            model_id=db_model.id,
            model_type=model_type,
            model_name=db_model.base_model,
            api_key=db_model.api_key,
            api_base_url=db_model.api_domain,
            additional_params=additional_params,
        )
```

---

## 📝 总结

### 方案B 核心优势

1. ✅ **保留 SQLBot 的 RAG**：Schema、术语库、SQL 示例
2. ✅ **最小化代码改动**：只需修改 3 个地方
3. ✅ **风险最低**：保留 SQLBot 的所有优化经验
4. ✅ **工作量最小**：2.5-4.5 天完成
5. ✅ **可快速切换**：随时可以切换回通义千问

### 实施时间表

| 阶段 | 任务 | 时间 |
|------|------|------|
| **阶段 1** | 安装依赖 | 10 分钟 |
| **阶段 2** | 创建 Claude LLM 类 | 30 分钟 |
| **阶段 3** | 注册 Claude LLM | 20 分钟 |
| **阶段 4** | 修改 get_default_config() | 30 分钟 |
| **阶段 5** | 添加 Claude 模型配置 | 10 分钟 |
| **阶段 6** | 验证配置 | 10 分钟 |
| **阶段 7** | 测试和调优 | 1-2 小时 |
| **总计** | | **2.5-4.5 小时** |

### 下一步

**实施建议**：
1. 先在测试环境完成步骤 1-6
2. 验证基本功能正常
3. 进行阶段 7 的详细测试
4. 部署到生产环境

**你的选择**：
1. 现在开始实施？
2. 还有疑问需要解答？

---

*文档生成时间：2026-02-08*
*最后更新：2026-02-08*
