# Claude Code + SQLBot 整合方案 v5（替换LLM引擎版）

> 核心思路：保留SQLBot完整流程，只替换SQL生成引擎为Claude Code
> 设计时间：2026-02-08

---

## 📋 核心思路

### 方案E vs 其他方案

| 维度 | 方案B（换LLM） | 方案D（MD文件） | **方案E（替换引擎）** |
|------|---------------|---------------|---------------------|
| **SQLBot改动** | 小（修改LLM调用） | 中（新增同步） | **极小（只改LLM调用）** |
| **Claude Code角色** | 被动LLM | 主动Agent（读文件） | **被动LLM（被SQLBot调用）** |
| **用户流程** | 不变 | 不变 | **完全不变** ✅ |
| **SQLBot功能** | 100%保留 | 100%保留 | **100%保留** ✅ |
| **工作量** | 2.5-4.5小时 | 3小时 | **1-2小时** ✅ |

### 方案E优势

✅ **用户流程完全不变**：在SQLBot前端输入问题
✅ **SQLBot功能100%保留**：RAG、可视化、历史记录全部保留
✅ **工作量最小**：只修改LLM调用部分
✅ **对用户透明**：不需要知道Claude Code的存在
✅ **实时配置**：使用SQLBot的实时配置（不需要同步MD文件）

---

## 🏗️ 架构设计

```
┌─────────────────────────────────────────────────────┐
│                 SQLBot 前端                     │
│              (React - 无需修改）                  │
│                                                  │
│  用户在前端输入问题："垂管系统数量"               │
└───────────────────┬───────────────────────────────┘
                    │ HTTP/WebSocket
                    ▼
┌─────────────────────────────────────────────────────┐
│              SQLBot 后端                     │
│              (FastAPI - 只改LLM调用）          │
│                                                  │
│  ┌─────────────────────────────────────────┐   │
│  │      RAG增强层（保留）               │   │
│  ├─→ Schema (数据库表结构）                 │   │
│  ├─→ Terminology (术语库)                   │   │
│  ├─→ Data Training (SQL示例)              │   │
│  ├─→ Custom Prompt (业务规则)              │   │
│  └─────────────────────────────────────────┘   │
│                                                  │
│  ┌─────────────────────────────────────────┐   │
│  │      Prompt构建层（保留）             │   │
│  ├─→ sql_sys_question()                    │   │
│  ├─→ 注入 Schema                           │   │
│  ├─→ 注入 Terminology                      │   │
│  ├─→ 注入 Data Training                    │   │
│  ├─→ 注入 Custom Prompt                    │   │
│  └─────────────────────────────────────────┘   │
│                                                  │
│  ┌─────────────────────────────────────────┐   │
│  │      LLM调用层（只改这里！）          │   │
│  │                                          │   │
│  │  原来：                                  │   │
│  │  OpenAILLM / 通义千问 / VLLM             │   │
│  │                                          │   │
│  │  现在：                                  │   │
│  │  ClaudeLLM (调用Claude Code)             │   │
│  └─────────────────────────────────────────┘   │
│                                                  │
│  ┌─────────────────────────────────────────┐   │
│  │      数据访问层（保留）               │   │
│  ├─→ SQL 执行                              │   │
│  ├─→ 结果格式化                            │   │
│  └─→ 图表生成                              │   │
│  └─────────────────────────────────────────┘   │
└───────────────────┬───────────────────────────────┘
                    │ 调用Claude Code生成SQL
                    ▼
┌─────────────────────────────────────────────────────┐
│           Claude Code (作为LLM服务）            │
│                                                  │
│  1. 接收SQLBot的Prompt                         │
│  2. 生成SQL                                    │
│  3. 返回SQL给SQLBot                            │
└─────────────────────────────────────────────────────┘
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

## 🔧 实施步骤

### 步骤1：创建Claude Code LLM类（30分钟）

**文件**：`apps/ai_model/llm.py`

**新增代码**：

```python
# apps/ai_model/llm.py

# 在文件顶部导入
from openclaw_client import OpenClawClient

# 在 BaseLLM 类后添加 Claude Code LLM 类
class ClaudeCodeLLM(BaseLLM):
    """
    Claude Code LLM 实现
    通过OpenClaw Gateway调用Claude Code
    """
    
    def _init_llm(self) -> BaseChatModel:
        """
        初始化 Claude Code LLM 实例
        
        注意：这里不是直接调用Anthropic API，而是通过OpenClaw Gateway
        Claude Code作为Gateway的backend提供LLM服务
        """
        from langchain_openai import ChatOpenAI
        
        # 通过OpenClaw Gateway调用Claude Code
        # OpenClaw Gateway兼容OpenAI API格式
        return ChatOpenAI(
            model=self.config.model_name,  # claude-3-5-sonnet-20241022
            api_key=self.config.api_key or 'Empty',
            base_url=self.config.api_base_url,  # OpenClaw Gateway地址
            temperature=self.config.additional_params.get('temperature', 0),
            max_tokens=self.config.additional_params.get('max_tokens', 4096),
            streaming=True,
            **{k: v for k, v in self.config.additional_params.items() 
               if k not in ['temperature', 'max_tokens']}
        )
```

**说明**：
- **关键点**：通过OpenClaw Gateway调用Claude Code
- **OpenClaw Gateway兼容OpenAI API**：所以可以直接用`ChatOpenAI`
- **不需要Claude API Key**：只需要OpenClaw Gateway地址

---

### 步骤2：注册Claude Code LLM（15分钟）

**文件**：`apps/ai_model/llm.py`

**修改**：`LLMFactory`类

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
        "claude": ClaudeLLM,        # Claude Anthropic
        "claude_code": ClaudeCodeLLM,  # Claude Code（新增！）
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

### 步骤3：修改 get_default_config()（30分钟）

**文件**：`apps/ai_model/model_factory.py`

**修改**：`get_default_config()` 函数

```python
# apps/ai_model/model_factory.py

async def get_default_config() -> LLMConfig:
    """
    获取默认 LLM 配置
    从数据库中读取 default_model=True 的配置
    支持 Claude Code
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
        # 注意：如果是OpenClaw Gateway，通常不需要解密
        if not db_model.api_domain.startswith("http"):
            # 假设有 sqlbot_decrypt 函数
            db_model.api_domain = await sqlbot_decrypt(db_model.api_domain)
            if db_model.api_key:
                db_model.api_key = await sqlbot_decrypt(db_model.api_key)
        
        # 确定 model_type
        # protocol: 1=OpenAI兼容, 2=VLLM
        # Claude Code 使用 OpenAI 兼容协议（通过OpenClaw Gateway）
        if "claude_code" in db_model.base_model.lower():
            model_type = "claude_code"
        elif "claude" in db_model.base_model.lower():
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

### 步骤4：添加Claude Code模型到数据库（10分钟）

**SQL 插入语句**：

```sql
-- 添加 Claude Code 模型配置（通过OpenClaw Gateway）
INSERT INTO ai_model_detail (
    name,                    -- 模型名称
    base_model,              -- 基础模型
    protocol,                -- 协议类型（1=OpenAI兼容）
    api_domain,             -- API 地址（OpenClaw Gateway）
    api_key,                -- API Key（如果Gateway需要）
    type_name,               -- 类型名称（用于 LLMFactory）
    default_model,           -- 是否为默认模型
    temperature,            -- 温度参数
    config,                 -- 额外配置（JSON）
    oid,                    -- 所属组织
    created_at,
    updated_at
) VALUES (
    'Claude Code (OpenClaw Gateway)',           -- name
    'claude-code',                               -- base_model
    1,                                           -- protocol (OpenAI兼容)
    'http://localhost:6800',                     -- api_domain (OpenClaw Gateway地址)
    'your-openclaw-token-here',                   -- api_key (如果Gateway需要认证)
    'claude_code',                                -- type_name
    true,                                        -- default_model
    0.0,                                         -- temperature
    '[]',                                        -- config (JSON字符串)
    1,                                           -- oid (组织ID)
    NOW(),                                       -- created_at
    NOW()                                        -- updated_at
);

-- 设置为默认模型
UPDATE ai_model_detail 
SET default_model = true 
WHERE base_model = 'claude-code';
```

**或者通过SQLBot前端添加**：

1. 启动SQLBot
2. 访问：http://localhost:8000
3. 进入：系统设置 → AI 模型管理
4. 点击"添加模型"
5. 填写配置：
   - 名称：`Claude Code (OpenClaw Gateway)`
   - 基础模型：`claude-code`
   - 协议类型：`OpenAI`
   - API 地址：`http://localhost:6800`（或你的OpenClaw Gateway地址）
   - API Key：你的OpenClaw Token（如果需要）
   - 类型名称：`claude_code`
   - 温度：`0`
6. 点击"设为默认"

---

## 🎯 完整工作流程

### 用户操作

1. **在SQLBot前端输入问题**
   ```
   垂管系统数量
   ```

2. **SQLBot后端处理**
   - 接收问题
   - 从数据库获取Schema/Terminology/Examples
   - 构建Prompt

3. **SQLBot调用Claude Code生成SQL**
   ```
   Prompt:
   你是SQL生成专家。
   
   表结构：
   # Table: t_sys, 系统表
   [(id:BIGINT, ID), (name:VARCHAR, 系统名称), (type:VARCHAR, 系统类型), ...]
   
   术语：
   ## 垂管系统
   **描述**: 由省级部门直接管理的系统
   **同义词**: 省垂, 垂直管理
   
   参考示例：
   ## 示例 1
   **问题**: 系统数量
   **SQL**: SELECT COUNT(*) FROM t_sys
   
   用户问题：垂管系统数量
   
   生成SQL：
   ```

4. **Claude Code返回SQL**
   ```sql
   SELECT COUNT(*) FROM t_sys WHERE type = '省垂'
   ```

5. **SQLBot执行SQL并生成图表**
   - 执行SQL
   - 生成图表（ECharts/G2）
   - 返回结果和图表

6. **前端显示结果**
   ```
   垂管系统数量为5个
   
   📊 [柱状图]
   ```

---

## 🔧 OpenClaw Gateway配置

### 启动OpenClaw Gateway

如果还没启动Gateway，先启动：

```bash
# 启动OpenClaw Gateway
openclaw gateway start

# 查看Gateway状态
openclaw gateway status

# 查看Gateway地址
openclaw gateway probe
```

**默认地址**：`ws://localhost:6800`

**HTTP API地址**：`http://localhost:6800`（兼容OpenAI API）

---

## 📊 配置示例

### Claude Code 配置（通过OpenClaw Gateway）

```json
{
  "model_id": 100,
  "model_type": "claude_code",
  "model_name": "claude-code",
  "api_key": "your-openclaw-token-here",
  "api_base_url": "http://localhost:6800",
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

## 🚀 实施步骤总结

| 步骤 | 任务 | 时间 |
|------|------|------|
| 第1步 | 创建Claude Code LLM类 | 30 分钟 |
| 第2步 | 注册Claude Code LLM | 15 分钟 |
| 第3步 | 修改 get_default_config() | 30 分钟 |
| 第4步 | 添加Claude Code模型配置 | 10 分钟 |
| 第5步 | 启动OpenClaw Gateway | 5 分钟 |
| 第6步 | 测试验证 | 30 分钟 |
| **总计** | | **2 小时** |

---

## 🎯 核心优势

### 相比其他方案

| 维度 | 方案B | 方案D | **方案E（替换引擎）** |
|------|-------|-------|---------------------|
| **SQLBot改动** | 小 | 中 | **极小** ✅ |
| **用户流程** | 不变 | 不变 | **完全不变** ✅ |
| **SQLBot功能** | 100% | 100% | **100%** ✅ |
| **配置同步** | 不需要 | 需要 | **不需要** ✅ |
| **实时配置** | 是 | 有延迟 | **是** ✅ |
| **工作量** | 2.5-4.5小时 | 3小时 | **2小时** ✅ |
| **对用户透明** | 是 | 是 | **完全透明** ✅ |

### 方案E最佳适用场景

✅ **最适合**：
- 保留SQLBot的完整流程
- 只想替换LLM为Claude Code
- 希望工作量最小
- 对用户透明（不需要知道Claude Code）

---

## ⚠️ 注意事项

### OpenClaw Gateway依赖

- **必须启动OpenClaw Gateway**：SQLBot需要通过Gateway调用Claude Code
- **Gateway地址**：确保SQLBot可以访问Gateway地址（默认`http://localhost:6800`）
- **认证**：如果Gateway设置了认证，SQLBot需要提供token

### 性能考虑

- **网络调用**：SQLBot → OpenClaw Gateway → Claude Code
- **延迟**：比直接调用LLM略高（增加了Gateway一层）
- **并发**：Gateway支持并发，多个SQLBot实例可以同时调用

### 回退方案

如果Claude Code不可用，可以快速切换回通义千问：

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

- [ ] 已启动OpenClaw Gateway
- [ ] 已获取Gateway地址（默认：http://localhost:6800）
- [ ] 已获取Gateway Token（如果需要）
- [ ] 已备份SQLBot数据库

### 实施后检查

- [ ] Claude Code LLM类已创建
- [ ] LLMFactory已注册"claude_code"
- [ ] get_default_config已修改
- [ ] Claude Code模型已添加到数据库
- [ ] Claude Code已设置为默认模型
- [ ] OpenClaw Gateway正在运行
- [ ] SQLBot后端启动成功
- [ ] 前端可以正常访问
- [ ] 测试查询正常
- [ ] 图表正常生成

---

## 🚀 下一步

**实施建议**：
1. 先在测试环境完成步骤1-5
2. 验证基本功能正常
3. 进行步骤6的详细测试
4. 部署到生产环境

---

**最后更新**：2026-02-08
