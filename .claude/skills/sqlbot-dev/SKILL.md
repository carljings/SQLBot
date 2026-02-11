---
name: sqlbot-dev
description: SQLBot 全栈开发助手 - FastAPI 后端 + Vue 3 前端一体化开发。用于创建新功能、API 端点、前端组件，以及前后端集成。支持 CRUD 操作、数据库模型、认证授权、状态管理等。当用户请求创建新功能、添加 API、开发前端组件或修改 SQLBot 项目代码时触发。
---

# SQLBot 全栈开发助手

## 快速开始

### 添加新功能的标准流程

1. **后端 API** - 在 `backend/apps/` 下创建路由和 CRUD
2. **前端 API** - 在 `frontend/src/api/` 下添加 API 客户端
3. **前端组件** - 在 `frontend/src/views/` 下创建 Vue 组件
4. **状态管理** - 如需全局状态，在 `frontend/src/stores/` 添加 Pinia store

## 后端开发 (FastAPI)

### 项目结构

```
backend/
├── apps/
│   ├── {module}/
│   │   ├── api/          # 路由定义
│   │   ├── crud/         # 数据库操作
│   │   ├── schemas/      # Pydantic 模型
│   │   └── models.py     # SQLAlchemy 模型
│   └── api.py            # 路由注册
├── common/
│   ├── core/
│   │   ├── config.py     # 配置管理
│   │   ├── deps.py       # 依赖注入 (CurrentUser, SessionDep)
│   │   └── security.py   # 认证相关
│   └── utils/
└── main.py
```

### 创建新 API 端点

**路由定义** (`apps/{module}/api/{resource}.py`):

```python
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from common.core.deps import SessionDep, CurrentUser

router = APIRouter(tags=["Resource"], prefix="/resource")

class ResourceCreate(BaseModel):
    name: str
    description: str

class ResourceUpdate(BaseModel):
    name: str | None = None
    description: str | None = None

@router.get("/", response_model=list[Resource])
async def list_resources(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100
):
    """获取资源列表"""
    from .crud import list_resources
    return list_resources(session, skip=skip, limit=limit)

@router.get("/{id}", response_model=Resource)
async def get_resource(
    id: int,
    session: SessionDep,
    current_user: CurrentUser
):
    """获取单个资源"""
    from .crud import get_resource
    return get_resource(session, id)

@router.post("/", response_model=Resource)
async def create_resource(
    data: ResourceCreate,
    session: SessionDep,
    current_user: CurrentUser
):
    """创建资源"""
    from .crud import create_resource
    return create_resource(session, data, current_user.uid)

@router.put("/{id}", response_model=Resource)
async def update_resource(
    id: int,
    data: ResourceUpdate,
    session: SessionDep,
    current_user: CurrentUser
):
    """更新资源"""
    from .crud import update_resource
    return update_resource(session, id, data)

@router.delete("/{id}")
async def delete_resource(
    id: int,
    session: SessionDep,
    current_user: CurrentUser
):
    """删除资源"""
    from .crud import delete_resource
    delete_resource(session, id)
    return {"message": "删除成功"}
```

**CRUD 操作** (`apps/{module}/crud/{resource}.py`):

```python
from sqlalchemy import select
from sqlalchemy.orm import Session

def list_resources(session: Session, skip: int = 0, limit: int = 100):
    stmt = select(Resource).offset(skip).limit(limit)
    return session.scalars(stmt).all()

def get_resource(session: Session, id: int):
    return session.get(Resource, id)

def create_resource(session: Session, data: ResourceCreate, user_id: str):
    db_obj = Resource(**data.model_dump(), created_by=user_id)
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj

def update_resource(session: Session, id: int, data: ResourceUpdate):
    db_obj = session.get(Resource, id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(db_obj, field, value)
    session.commit()
    session.refresh(db_obj)
    return db_obj

def delete_resource(session: Session, id: int):
    db_obj = session.get(Resource, id)
    session.delete(db_obj)
    session.commit()
```

**注册路由** (`apps/api.py`):

```python
from apps.{module}.api import {resource}

api_router.include_router({resource}.router)
```

### 数据库模型

```python
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from common.db.base_class import Base

class Resource(Base):
    __tablename__ = "resource"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(String(1000))
    created_by = Column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

### 认证与授权

```python
from common.core.deps import CurrentUser, SessionDep

@router.get("/protected")
async def protected_endpoint(
    current_user: CurrentUser,  # 自动注入当前用户
    session: SessionDep          # 自动注入数据库会话
):
    return {
        "user_id": current_user.uid,
        "user_name": current_user.name,
        "is_admin": current_user.uid == "1"
    }
```

### 行级权限过滤

```python
from apps.system.crud.user import get_visible_users_stmt

def list_resources(session: Session, current_user: CurrentUser):
    # 获取有权限的用户列表
    user_stmt = get_visible_users_stmt(current_user)
    stmt = select(Resource).where(
        Resource.created_by.in_(user_stmt)
    )
    return session.scalars(stmt).all()
```

## 前端开发 (Vue 3)

### 项目结构

```
frontend/
├── src/
│   ├── api/           # API 客户端
│   ├── stores/        # Pinia 状态管理
│   ├── views/         # 页面组件
│   ├── components/    # 可复用组件
│   ├── utils/         # 工具函数
│   └── router/        # 路由配置
```

### API 客户端

**创建 API 文件** (`src/api/{resource}.ts`):

```typescript
import { request } from '@/utils/request'

export interface Resource {
  id?: number
  name: string
  description: string
  created_by?: string
  created_at?: string
}

export interface ResourceCreate {
  name: string
  description: string
}

export interface ResourceUpdate {
  name?: string
  description?: string
}

export const resourceApi = {
  list: (params?: { skip?: number; limit?: number }) => {
    return request.get<Resource[]>('/resource/list', { params })
  },

  get: (id: number) => {
    return request.get<Resource>(`/resource/${id}`)
  },

  create: (data: ResourceCreate) => {
    return request.post<Resource>('/resource', data)
  },

  update: (id: number, data: ResourceUpdate) => {
    return request.put<Resource>(`/resource/${id}`, data)
  },

  delete: (id: number) => {
    return request.delete(`/resource/${id}`)
  }
}
```

### Vue 组件

**基础组件模板** (`src/views/{module}/index.vue`):

```vue
<template>
  <div class="resource-container">
    <!-- 操作栏 -->
    <el-row :gutter="16" class="mb-16">
      <el-col :span="12">
        <el-input
          v-model="searchText"
          placeholder="搜索资源..."
          clearable
          @input="handleSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
      </el-col>
      <el-col :span="12" class="text-right">
        <el-button type="primary" @click="handleCreate">
          新建资源
        </el-button>
      </el-col>
    </el-row>

    <!-- 数据表格 -->
    <el-table :data="tableData" v-loading="loading" border>
      <el-table-column prop="name" label="名称" />
      <el-table-column prop="description" label="描述" />
      <el-table-column prop="created_at" label="创建时间" width="180" />
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="handleEdit(row)">
            编辑
          </el-button>
          <el-button link type="danger" @click="handleDelete(row)">
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <el-pagination
      v-model:current-page="pagination.page"
      v-model:page-size="pagination.pageSize"
      :total="pagination.total"
      @current-change="loadData"
      @size-change="loadData"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { resourceApi, type Resource } from '@/api/resource'

const loading = ref(false)
const searchText = ref('')
const tableData = ref<Resource[]>([])
const pagination = ref({
  page: 1,
  pageSize: 20,
  total: 0
})

const loadData = async () => {
  loading.value = true
  try {
    const res = await resourceApi.list({
      skip: (pagination.value.page - 1) * pagination.value.pageSize,
      limit: pagination.value.pageSize
    })
    tableData.value = res || []
  } catch (error) {
    ElMessage.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

const handleCreate = () => {
  // 打开创建对话框
}

const handleEdit = (row: Resource) => {
  // 打开编辑对话框
}

const handleDelete = async (row: Resource) => {
  try {
    await ElMessageBox.confirm('确定要删除吗?', '提示', {
      type: 'warning'
    })
    await resourceApi.delete(row.id!)
    ElMessage.success('删除成功')
    loadData()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const handleSearch = () => {
  pagination.value.page = 1
  loadData()
}

onMounted(() => {
  loadData()
})
</script>

<style scoped lang="less">
.resource-container {
  padding: 16px;
}
</style>
```

### Pinia Store

**创建 Store** (`src/stores/{resource}.ts`):

```typescript
import { defineStore } from 'pinia'
import { resourceApi, type Resource, type ResourceCreate } from '@/api/resource'

interface ResourceState {
  currentResource: Resource | null
  list: Resource[]
}

export const useResourceStore = defineStore('resource', {
  state: (): ResourceState => ({
    currentResource: null,
    list: []
  }),

  getters: {
    getResourceById: (state) => (id: number) => {
      return state.list.find(r => r.id === id)
    }
  },

  actions: {
    async fetchList() {
      const res = await resourceApi.list()
      this.list = res || []
    },

    async create(data: ResourceCreate) {
      const res = await resourceApi.create(data)
      this.list.push(res)
      return res
    },

    setCurrent(resource: Resource) {
      this.currentResource = resource
    },

    clear() {
      this.currentResource = null
      this.list = []
    }
  }
})
```

## 前后端集成

### HTTP 请求配置

**请求拦截器** (`src/utils/request.ts`):

```typescript
// 自动添加 Token
instance.interceptors.request.use((config) => {
  const token = wsCache.get('user.token')
  if (token) {
    config.headers['X-SQLBOT-TOKEN'] = `Bearer ${token}`
  }
  return config
})

// 统一错误处理
instance.interceptors.response.use(
  (response) => response.data.data,
  (error) => {
    if (error.response?.status === 401) {
      // Token 过期，跳转登录
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)
```

### 流式响应 (SSE)

**后端** (FastAPI):

```python
from fastapi.responses import StreamingResponse

@router.post("/question")
async def chat_question(data: ChatQuestion):
    async def generate():
        async for chunk in llm_service.stream_chat(data):
            yield f"data: {chunk}\n\n"
    return StreamingResponse(generate(), media_type="text/event-stream")
```

**前端**:

```typescript
const sendQuestion = async (data: any, controller?: AbortController) => {
  return request.fetchStream('/chat/question', data, controller, {
    onMessage: (chunk: string) => {
      // 处理流式消息
      console.log(chunk)
    }
  })
}
```

## 常见模式

### 左树右表布局

```vue
<template>
  <div class="layout-container">
    <el-row :gutter="16">
      <!-- 左侧树 -->
      <el-col :span="6">
        <el-tree :data="treeData" @node-click="handleNodeClick" />
      </el-col>
      <!-- 右侧表格 -->
      <el-col :span="18">
        <el-table :data="tableData">...</el-table>
      </el-col>
    </el-row>
  </div>
</template>
```

### 对话框表单

```vue
<el-dialog v-model="visible" title="编辑资源">
  <el-form :model="form" :rules="rules" ref="formRef">
    <el-form-item label="名称" prop="name">
      <el-input v-model="form.name" />
    </el-form-item>
    <el-form-item label="描述" prop="description">
      <el-input v-model="form.description" type="textarea" />
    </el-form-item>
  </el-form>
  <template #footer>
    <el-button @click="visible = false">取消</el-button>
    <el-button type="primary" @click="handleSubmit">确定</el-button>
  </template>
</el-dialog>
```

### 权限控制

```vue
<script setup>
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()

// 检查管理员权限
const isAdmin = computed(() => userStore.isAdmin)

// 检查空间管理员权限
const isSpaceAdmin = computed(() => userStore.isSpaceAdmin)
</script>

<template>
  <el-button v-if="isAdmin" type="danger">删除</el-button>
</template>
```

## 参考文档

- **后端架构详情**: [references/backend-architecture.md](references/backend-architecture.md)
- **前端组件模式**: [references/frontend-patterns.md](references/frontend-patterns.md)
- **API 命名规范**: [references/api-conventions.md](references/api-conventions.md)
- **数据库迁移**: [references/database-migrations.md](references/database-migrations.md)
