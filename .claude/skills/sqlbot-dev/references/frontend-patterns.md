# SQLBot 前端组件模式参考

## 目录结构

```
src/
├── api/               # API 客户端
├── stores/            # Pinia 状态管理
├── views/             # 页面组件
├── components/        # 可复用组件
├── utils/             # 工具函数
├── router/            # 路由配置
├── assets/            # 静态资源
└── i18n/              # 国际化
```

## 组件模式

### 1. 列表页组件

**文件**: `views/{module}/index.vue`

```vue
<template>
  <div class="page-container">
    <!-- 搜索栏 -->
    <el-card class="search-bar">
      <el-form :model="searchForm" inline>
        <el-form-item label="名称">
          <el-input v-model="searchForm.name" clearable />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 工具栏 -->
    <div class="toolbar">
      <el-button type="primary" @click="handleCreate">新建</el-button>
      <el-button @click="loadData">刷新</el-button>
    </div>

    <!-- 数据表格 -->
    <el-table :data="tableData" v-loading="loading" border>
      <el-table-column prop="name" label="名称" />
      <el-table-column prop="description" label="描述" />
      <el-table-column label="操作" width="200">
        <template #default="{ row }">
          <el-button link type="primary" @click="handleEdit(row)">编辑</el-button>
          <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <el-pagination
      v-model:current-page="pagination.page"
      v-model:page-size="pagination.pageSize"
      :total="pagination.total"
      @current-change="loadData"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { resourceApi } from '@/api/resource'

const loading = ref(false)
const tableData = ref([])
const searchForm = reactive({ name: '' })
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

const loadData = async () => {
  loading.value = true
  try {
    const res = await resourceApi.list({
      ...searchForm,
      skip: (pagination.page - 1) * pagination.pageSize,
      limit: pagination.pageSize
    })
    tableData.value = res?.list || []
    pagination.total = res?.total || 0
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  loadData()
}

const handleReset = () => {
  Object.assign(searchForm, { name: '' })
  handleSearch()
}

onMounted(() => loadData())
</script>
```

### 2. 对话框表单

**文件**: `views/{module}/components/FormDialog.vue`

```vue
<template>
  <el-dialog
    v-model="visible"
    :title="isEdit ? '编辑' : '新建'"
    width="600px"
    @closed="handleClosed"
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="100px"
    >
      <el-form-item label="名称" prop="name">
        <el-input v-model="form.name" placeholder="请输入名称" />
      </el-form-item>
      <el-form-item label="描述" prop="description">
        <el-input
          v-model="form.description"
          type="textarea"
          :rows="3"
        />
      </el-form-item>
      <!-- 动态表单项 -->
      <el-form-item label="类型" prop="type" v-if="isEdit">
        <el-select v-model="form.type">
          <el-option label="类型A" value="a" />
          <el-option label="类型B" value="b" />
        </el-select>
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" :loading="submitting" @click="handleSubmit">
        确定
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, watch, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'

interface Props {
  modelValue: boolean
  data?: any
}

const props = defineProps<Props>()
const emit = defineEmits(['update:modelValue', 'success'])

const visible = ref(false)
const submitting = ref(false)
const formRef = ref<FormInstance>()

const isEdit = computed(() => !!props.data?.id)

const form = reactive({
  name: '',
  description: '',
  type: 'a'
})

const rules: FormRules = {
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  description: [{ required: true, message: '请输入描述', trigger: 'blur' }]
}

watch(() => props.modelValue, (val) => {
  visible.value = val
  if (val && props.data) {
    Object.assign(form, props.data)
  }
})

watch(visible, (val) => {
  emit('update:modelValue', val)
})

const handleSubmit = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    submitting.value = true
    try {
      if (isEdit.value) {
        await resourceApi.update(props.data.id, form)
      } else {
        await resourceApi.create(form)
      }
      ElMessage.success('操作成功')
      visible.value = false
      emit('success')
    } finally {
      submitting.value = false
    }
  })
}

const handleClosed = () => {
  formRef.value?.resetFields()
}
</script>
```

### 3. 左树右表布局

```vue
<template>
  <div class="tree-table-layout">
    <el-row :gutter="16">
      <!-- 左侧树 -->
      <el-col :span="6">
        <el-card>
          <template #header>
            <span>分类</span>
          </template>
          <el-tree
            ref="treeRef"
            :data="treeData"
            :props="{ children: 'children', label: 'name' }"
            node-key="id"
            highlight-current
            @node-click="handleNodeClick"
          >
            <template #default="{ node, data }">
              <span class="tree-node">
                <el-icon><Folder /></el-icon>
                <span>{{ node.label }}</span>
              </span>
            </template>
          </el-tree>
        </el-card>
      </el-col>

      <!-- 右侧表格 -->
      <el-col :span="18">
        <el-card>
          <template #header>
            <span>{{ currentNode?.name || '全部' }}</span>
          </template>
          <el-table :data="tableData">
            <!-- 表格列 -->
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { resourceApi } from '@/api/resource'

const treeRef = ref()
const treeData = ref([])
const tableData = ref([])
const currentNode = ref(null)

const loadTree = async () => {
  treeData.value = await resourceApi.tree()
}

const handleNodeClick = (data: any) => {
  currentNode.value = data
  loadData(data.id)
}

onMounted(() => {
  loadTree()
})
</script>

<style scoped>
.tree-table-layout {
  height: 100%;
}
.tree-node {
  display: flex;
  align-items: center;
  gap: 8px;
}
</style>
```

### 4. 手风琴布局

```vue
<template>
  <div class="accordion-layout">
    <el-collapse v-model="activeNames">
      <el-collapse-item
        v-for="item in items"
        :key="item.id"
        :name="item.id"
      >
        <template #title>
          <div class="collapse-title">
            <span>{{ item.name }}</span>
            <el-button
              size="small"
              link
              @click.stop="handleEdit(item)"
            >
              编辑
            </el-button>
          </div>
        </template>

        <div class="collapse-content">
          <!-- 内容区域 -->
          <p>{{ item.description }}</p>
        </div>
      </el-collapse-item>
    </el-collapse>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const activeNames = ref<string[]>([])

const items = ref([
  { id: '1', name: '项目A', description: '描述A' },
  { id: '2', name: '项目B', description: '描述B' }
])
</script>

<style scoped>
.collapse-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  padding-right: 20px;
}
</style>
```

## 状态管理模式

### Store 模板

```typescript
// stores/resource.ts
import { defineStore } from 'pinia'
import { resourceApi } from '@/api/resource'

interface ResourceState {
  list: any[]
  current: any | null
  loading: boolean
}

export const useResourceStore = defineStore('resource', {
  state: (): ResourceState => ({
    list: [],
    current: null,
    loading: false
  }),

  getters: {
    isEmpty: (state) => state.list.length === 0,
    findById: (state) => (id: number) => {
      return state.list.find(item => item.id === id)
    }
  },

  actions: {
    async fetchList(params?: any) {
      this.loading = true
      try {
        const res = await resourceApi.list(params)
        this.list = res || []
        return res
      } finally {
        this.loading = false
      }
    },

    async getById(id: number) {
      const res = await resourceApi.get(id)
      this.current = res
      return res
    },

    setCurrent(item: any) {
      this.current = item
    },

    clear() {
      this.list = []
      this.current = null
    }
  }
})
```

## 路由模式

### 路由配置

```typescript
// router/index.ts
import { createRouter, createWebHistory } from 'vue-router'
import Layout from '@/layout/index.vue'

const routes = [
  {
    path: '/',
    component: Layout,
    redirect: '/chat',
    children: [
      {
        path: 'chat',
        name: 'Chat',
        component: () => import('@/views/chat/index.vue'),
        meta: { title: '对话', icon: 'chat' }
      },
      {
        path: 'datasource',
        name: 'DataSource',
        component: () => import('@/views/ds/index.vue'),
        meta: { title: '数据源', icon: 'database' }
      }
    ]
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/login/index.vue'),
    meta: { hidden: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('user.token')
  if (!token && to.path !== '/login') {
    next('/login')
  } else {
    next()
  }
})

export default router
```

### 编程式导航

```typescript
import { useRouter } from 'vue-router'

const router = useRouter()

// 简单跳转
router.push('/chat')

// 带参数
router.push({
  path: '/datasource',
  query: { id: '123' }
})

// 命名路由
router.push({
  name: 'Chat',
  params: { id: '123' }
})

// 替换（不保留历史记录）
router.replace('/login')

// 后退
router.back()
```

## 国际化

### 使用翻译

```vue
<script setup>
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
</script>

<template>
  <h1>{{ t('common.welcome') }}</h1>
  <el-button>{{ t('common.login') }}</el-button>
</template>
```

### 定义翻译

```typescript
// i18n/locales/zh-CN.ts
export default {
  common: {
    welcome: '欢迎使用',
    login: '登录',
    logout: '退出登录'
  }
}
```

## 工具函数

### 缓存使用

```typescript
import { useCache } from '@/utils/useCache'

const { wsCache } = useCache()

// 设置缓存
wsCache.set('user.token', 'xxx')

// 获取缓存
const token = wsCache.get('user.token')

// 删除缓存
wsCache.delete('user.token')
```

### 格式化

```typescript
// utils/format.ts

// 日期格式化
export const formatDate = (date: string | Date) => {
  return dayjs(date).format('YYYY-MM-DD HH:mm:ss')
}

// 文件大小格式化
export const formatFileSize = (bytes: number) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return (bytes / Math.pow(k, i)).toFixed(2) + ' ' + sizes[i]
}
```
