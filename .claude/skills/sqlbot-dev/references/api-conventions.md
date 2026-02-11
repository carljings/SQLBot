# SQLBot API 命名规范

## RESTful API 规范

### URL 命名

```
{base_url}/api/v1/{resource}/{action}

base_url:     http://localhost:8000
resource:     资源名称 (复数形式)
action:       操作类型
```

### 标准端点

| 操作 | HTTP 方法 | 端点 | 说明 |
|------|-----------|------|------|
| 列表 | GET | `/api/v1/{resource}/list` | 获取列表 |
| 详情 | GET | `/api/v1/{resource}/{id}` | 获取单个资源 |
| 创建 | POST | `/api/v1/{resource}/` | 创建新资源 |
| 更新 | PUT | `/api/v1/{resource}/{id}` | 更新资源 |
| 删除 | DELETE | `/api/v1/{resource}/{id}` | 删除资源 |

### 示例

```
GET    /api/v1/chat/list           # 获取聊天列表
GET    /api/v1/chat/123            # 获取聊天详情
POST   /api/v1/chat/               # 创建新聊天
PUT    /api/v1/chat/123            # 更新聊天
DELETE /api/v1/chat/123            # 删除聊天
```

## 后端命名规范

### 路由定义

```python
# apps/{module}/api/{resource}.py

router = APIRouter(
    tags=["Resource"],           # API 文档分组名称
    prefix="/resource"            # URL 前缀
)

@router.get("/list", summary="get_resource_list")
async def list_resources(...):
    """获取资源列表"""
    pass

@router.post("/", summary="create_resource")
async def create_resource(...):
    """创建资源"""
    pass
```

### CRUD 函数命名

```python
# apps/{module}/crud/{resource}.py

def list_{resource}s(session, skip=0, limit=100):
    """列表查询"""
    pass

def get_{resource}(session, id):
    """单条查询"""
    pass

def create_{resource}(session, data, user_id):
    """创建"""
    pass

def update_{resource}(session, id, data):
    """更新"""
    pass

def delete_{resource}(session, id):
    """删除"""
    pass
```

### Pydantic Schema 命名

```python
# apps/{module}/schemas/{resource}.py

class {Resource}Base(BaseModel):
    """基础模型"""
    pass

class {Resource}Create({Resource}Base):
    """创建模型"""
    pass

class {Resource}Update({Resource}Base):
    """更新模型 (所有字段可选)"""
    pass

class {Resource}({Resource}Base):
    """完整模型"""
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
```

## 前端命名规范

### API 客户端

```typescript
// src/api/{resource}.ts

export interface {Resource} {
  id?: number
  name: string
  // ...
}

export interface {Resource}Create {
  name: string
  // ...
}

export interface {Resource}Update {
  name?: string
  // ...
}

export const {resource}Api = {
  list: (params?: any) => request.get<{Resource}[]>('/resource/list', { params }),
  get: (id: number) => request.get<{Resource}>(`/resource/${id}`),
  create: (data: {Resource}Create) => request.post<{Resource}>('/resource', data),
  update: (id: number, data: {Resource}Update) => request.put<{Resource}>(`/resource/${id}`, data),
  delete: (id: number) => request.delete(`/resource/${id}`)
}
```

### Store 命名

```typescript
// src/stores/{resource}.ts

export const use{Resource}Store = defineStore('{resource}', {
  state: () => ({
    {resource}List: [],
    current{Resource}: null
  }),
  // ...
})
```

### 组件命名

```
views/
├── {module}/
│   ├── index.vue              # 列表页
│   ├── components/
│   │   ├── FormDialog.vue     # 表单对话框
│   │   ├── Card.vue           # 卡片组件
│   │   └── {Feature}Item.vue  # 功能项组件
```

## 通用命名约定

### 文件命名

- **后端**: 小写，下划线分隔 `chat_record.py`
- **前端**: 小写，短横线分隔 `chat-record.vue` (组件), `chat.ts` (非组件)

### 变量命名

- **Python**: 小写，下划线分隔 `user_id`, `chat_list`
- **TypeScript**: 小驼峰 `userId`, `chatList`

### 常量命名

- **Python**: 大写，下划线分隔 `MAX_LIMIT`, `DEFAULT_PAGE_SIZE`
- **TypeScript**: 大驼峰或全大写 `MAX_LIMIT`, `DefaultPageSize`

### 类型命名

- **Python**: 大驼峰 `ChatRecord`, `UserCreate`
- **TypeScript**: 大驼峰 `ChatRecord`, `UserCreate`, 接口加 `I` 前缀 `IUser`

### 函数命名

- **后端**: 动词开头 `get_user`, `create_chat`, `list_records`
- **前端**: 动词开头或 handle 前缀 `getUser`, `handleCreate`, `onSubmit`

## 特殊端点

### 认证相关

```
POST   /api/v1/login/access-token      # 登录获取 Token
POST   /api/v1/login/logout           # 登出
GET    /api/v1/login/info             # 获取当前用户信息
```

### 上传相关

```
POST   /api/v1/{resource}/upload       # 上传文件
```

### 批量操作

```
POST   /api/v1/{resource}/batch       # 批量创建
PUT    /api/v1/{resource}/batch       # 批量更新
DELETE /api/v1/{resource}/batch       # 批量删除
```

### 状态变更

```
POST   /api/v1/{resource}/{id}/enable   # 启用
POST   /api/v1/{resource}/{id}/disable  # 禁用
POST   /api/v1/{resource}/{id}/archive  # 归档
```

## 查询参数规范

### 分页

```
GET /api/v1/resource/list?skip=0&limit=20
```

### 排序

```
GET /api/v1/resource/list?sort_by=created_at&order=desc
```

### 过滤

```
GET /api/v1/resource/list?status=active&type=a
```

### 搜索

```
GET /api/v1/resource/list?keyword=test
```

## 响应格式规范

### 成功响应

```json
{
  "code": 200,
  "data": {
    "id": 123,
    "name": "资源名称"
  },
  "message": "success"
}
```

### 列表响应

```json
{
  "code": 200,
  "data": {
    "list": [...],
    "total": 100
  },
  "message": "success"
}
```

### 错误响应

```json
{
  "code": 400,
  "data": null,
  "message": "参数验证失败"
}
```
