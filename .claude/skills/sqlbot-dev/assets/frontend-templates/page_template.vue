<!--
/**
 * 页面组件模板
 * 文件位置: frontend/src/views/{module}/index.vue
 */
-->
<template>
  <div class="resource-page">
    <!-- 搜索栏 -->
    <el-card class="search-bar" shadow="never">
      <el-form :model="searchForm" inline>
        <el-form-item label="名称">
          <el-input
            v-model="searchForm.keyword"
            placeholder="请输入名称"
            clearable
            @clear="handleSearch"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">
            <el-icon><Search /></el-icon>
            搜索
          </el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 工具栏 -->
    <div class="toolbar">
      <el-button type="primary" @click="handleCreate">
        <el-icon><Plus /></el-icon>
        新建
      </el-button>
      <el-button @click="loadData">
        <el-icon><Refresh /></el-icon>
        刷新
      </el-button>
    </div>

    <!-- 数据表格 -->
    <el-table
      :data="tableData"
      v-loading="loading"
      border
      stripe
      @selection-change="handleSelectionChange"
    >
      <el-table-column type="selection" width="55" />
      <el-table-column prop="name" label="名称" min-width="200" />
      <el-table-column prop="description" label="描述" min-width="300" show-overflow-tooltip />
      <el-table-column prop="created_at" label="创建时间" width="180" />
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="handleEdit(row)">
            编辑
          </el-button>
          <el-button link type="primary" @click="handleView(row)">
            查看
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
      :page-sizes="[10, 20, 50, 100]"
      layout="total, sizes, prev, pager, next, jumper"
      @current-change="loadData"
      @size-change="loadData"
    />

    <!-- 表单对话框 -->
    <ResourceFormDialog
      v-model="formDialogVisible"
      :data="currentResource"
      @success="handleFormSuccess"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh, Plus } from '@element-plus/icons-vue'
import { resourceApi, type Resource } from '@/api/resource'
import ResourceFormDialog from './components/FormDialog.vue'

// ===== 状态 =====
const loading = ref(false)
const tableData = ref<Resource[]>([])
const selectedRows = ref<Resource[]>([])
const formDialogVisible = ref(false)
const currentResource = ref<Resource | undefined>()

const searchForm = reactive({
  keyword: ''
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

// ===== 数据加载 =====
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
  } catch (error) {
    ElMessage.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

// ===== 搜索操作 =====
const handleSearch = () => {
  pagination.page = 1
  loadData()
}

const handleReset = () => {
  Object.assign(searchForm, {
    keyword: ''
  })
  handleSearch()
}

// ===== CRUD 操作 =====
const handleCreate = () => {
  currentResource.value = undefined
  formDialogVisible.value = true
}

const handleEdit = (row: Resource) => {
  currentResource.value = row
  formDialogVisible.value = true
}

const handleView = (row: Resource) => {
  // 跳转到详情页
  console.log('查看:', row)
}

const handleDelete = async (row: Resource) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除 "${row.name}" 吗？`,
      '提示',
      {
        type: 'warning',
        confirmButtonText: '确定',
        cancelButtonText: '取消'
      }
    )

    await resourceApi.delete(row.id!)
    ElMessage.success('删除成功')
    loadData()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const handleSelectionChange = (rows: Resource[]) => {
  selectedRows.value = rows
}

const handleFormSuccess = () => {
  formDialogVisible.value = false
  loadData()
}

// ===== 生命周期 =====
onMounted(() => {
  loadData()
})
</script>

<style scoped lang="less">
.resource-page {
  padding: 16px;
  background-color: #f5f7fa;
  min-height: 100%;

  .search-bar {
    margin-bottom: 16px;
  }

  .toolbar {
    margin-bottom: 16px;
    display: flex;
    gap: 8px;
  }

  .el-pagination {
    margin-top: 16px;
    justify-content: flex-end;
  }
}
</style>
