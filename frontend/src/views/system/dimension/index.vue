<script lang="ts" setup>
import { onMounted, reactive, ref } from 'vue'
import icon_add_outlined from '@/assets/svg/icon_add_outlined.svg'
import IconOpeEdit from '@/assets/svg/icon_edit_outlined.svg'
import IconOpeDelete from '@/assets/svg/icon_delete.svg'
import icon_searchOutline_outlined from '@/assets/svg/icon_search-outline_outlined.svg'
import EmptyBackground from '@/views/dashboard/common/EmptyBackground.vue'
import { useI18n } from 'vue-i18n'
import { cloneDeep } from 'lodash-es'
import { ElMessage, ElMessageBox } from 'element-plus'
import { dimensionApi } from '@/api/dimension'

interface DimensionValue {
  id?: number | null
  name: string
  code: string
  description?: string
  values: string[]
  value_labels?: Record<string, string>
  is_system?: boolean
  enabled: boolean
}

const { t } = useI18n()
const keywords = ref('')
const searchLoading = ref(false)

onMounted(() => {
  search()
})

const dialogFormVisible = ref<boolean>(false)
const pageInfo = reactive({
  currentPage: 1,
  pageSize: 10,
  total: 0,
})

const dialogTitle = ref('')
const updateLoading = ref(false)
const defaultForm: DimensionValue = {
  id: null,
  name: '',
  code: '',
  description: '',
  values: [],
  value_labels: {},
  enabled: true,
}
const pageForm = ref<DimensionValue>(cloneDeep(defaultForm))
const tableData = ref<any[]>([])

// 新增
const handleAdd = () => {
  pageForm.value = cloneDeep(defaultForm)
  dialogTitle.value = t('dimension.add_dimension')
  dialogFormVisible.value = true
}

// 编辑
const handleEdit = (row: any) => {
  pageForm.value = cloneDeep({
    id: row.id,
    name: row.name,
    code: row.code,
    description: row.description,
    values: row.values || [],
    value_labels: row.value_labels || {},
    enabled: row.enabled,
  })
  dialogTitle.value = t('dimension.edit_dimension')
  dialogFormVisible.value = true
}

// 删除
const handleDelete = (row: any) => {
  ElMessageBox.confirm(t('dimension.delete_confirm'), {
    confirmButtonType: 'danger',
    confirmButtonText: t('common.confirm'),
    cancelButtonText: t('common.cancel'),
    customClass: 'confirm-no_icon',
    autofocus: false,
  }).then(() => {
    dimensionApi.delete(row.id).then(() => {
      ElMessage.success(t('common.delete_success'))
      search()
    })
  })
}

// 启用/禁用
const handleToggleEnabled = (row: any) => {
  dimensionApi.enable(row.id, row.enabled).then(() => {
    ElMessage.success(row.enabled ? t('common.enable_success') : t('common.disable_success'))
  })
}

// 搜索
const search = async () => {
  searchLoading.value = true
  try {
    const params: any = {
      page: pageInfo.currentPage,
      page_size: pageInfo.pageSize,
    }
    if (keywords.value) {
      params.name = keywords.value
    }
    const res = await dimensionApi.list(params)
    tableData.value = res.items || []
    pageInfo.total = res.total_count || 0
  } finally {
    searchLoading.value = false
  }
}

// 重置搜索
const resetSearch = () => {
  keywords.value = ''
  pageInfo.currentPage = 1
  search()
}

// 分页变化
const handlePageChange = (page: number) => {
  pageInfo.currentPage = page
  search()
}

const handleSizeChange = (size: number) => {
  pageInfo.pageSize = size
  pageInfo.currentPage = 1
  search()
}

// 提交表单
const submitForm = async () => {
  // 验证必填字段
  if (!pageForm.value.name?.trim()) {
    ElMessage.warning(t('dimension.name_required'))
    return
  }
  if (!pageForm.value.code?.trim()) {
    ElMessage.warning(t('dimension.code_required'))
    return
  }
  if (!pageForm.value.values || pageForm.value.values.length === 0) {
    ElMessage.warning(t('dimension.values_required'))
    return
  }

  updateLoading.value = true
  try {
    const data = {
      ...pageForm.value,
      name: pageForm.value.name.trim(),
      code: pageForm.value.code.trim(),
      description: pageForm.value.description?.trim() || '',
    }
    if (pageForm.value.id) {
      await dimensionApi.update(pageForm.value.id, data)
      ElMessage.success(t('common.update_success'))
    } else {
      await dimensionApi.create(data)
      ElMessage.success(t('common.create_success'))
    }
    dialogFormVisible.value = false
    search()
  } finally {
    updateLoading.value = false
  }
}

// 添加值
const addValue = () => {
  if (!pageForm.value.values) {
    pageForm.value.values = []
  }
  pageForm.value.values.push('')
}

// 删除值
const removeValue = (index: number) => {
  pageForm.value.values?.splice(index, 1)
}

// 暴露给外部使用
defineExpose({
  dimensionApi,
})
</script>

<template>
  <div v-loading="searchLoading" class="dimension">
    <!-- 顶部工具栏 -->
    <div class="tool-left">
      <span class="page-title">{{ t('dimension.dimension_management') }}</span>
      <div class="search-bar">
        <el-input
          v-model="keywords"
          style="width: 240px; margin-right: 12px"
          :placeholder="t('dimension.search_placeholder')"
          clearable
          @clear="search"
          @keydown.enter.exact.prevent="search"
        >
          <template #prefix>
            <el-icon>
              <icon_searchOutline_outlined />
            </el-icon>
          </template>
        </el-input>
        <el-button type="primary" @click="handleAdd">
          <template #icon>
            <icon_add_outlined></icon_add_outlined>
          </template>
          {{ t('dimension.add_dimension') }}
        </el-button>
      </div>
    </div>

    <!-- 表格内容 -->
    <div class="table-content">
      <div class="preview-or-schema">
        <el-table :data="tableData" stripe style="width: 100%" v-if="tableData.length > 0">
          <el-table-column prop="name" :label="t('dimension.dimension_name')" min-width="150" />
          <el-table-column prop="code" :label="t('dimension.dimension_code')" min-width="120" />
          <el-table-column prop="description" :label="t('dimension.description')" min-width="200" show-overflow-tooltip />
          <el-table-column :label="t('dimension.values')" min-width="250">
            <template #default="{ row }">
              <el-tag
                v-for="(value, index) in (row.values || []).slice(0, 4)"
                :key="index"
                size="small"
                style="margin-right: 6px; margin-bottom: 6px"
              >
                {{ value }}
              </el-tag>
              <span v-if="row.values && row.values.length > 4" class="more-hint">
                +{{ row.values.length - 4 }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="value_count" :label="t('dimension.value_count')" width="100" align="center" />
          <el-table-column :label="t('common.status')" width="100" align="center">
            <template #default="{ row }">
              <el-switch
                v-model="row.enabled"
                @change="handleToggleEnabled(row)"
                :disabled="row.is_system"
              />
            </template>
          </el-table-column>
          <el-table-column fixed="right" width="120" :label="t('ds.actions')">
            <template #default="{ row }">
              <div class="field-comment">
                <el-tooltip :offset="14" effect="dark" :content="t('common.edit')" placement="top">
                  <el-icon class="action-btn" size="16" @click="handleEdit(row)">
                    <IconOpeEdit />
                  </el-icon>
                </el-tooltip>
                <el-tooltip
                  v-if="!row.is_system"
                  :offset="14"
                  effect="dark"
                  :content="t('common.delete')"
                  placement="top"
                >
                  <el-icon class="action-btn danger" size="16" @click="handleDelete(row)">
                    <IconOpeDelete />
                  </el-icon>
                </el-tooltip>
              </div>
            </template>
          </el-table-column>
        </el-table>

        <!-- 空状态 -->
        <EmptyBackground
          v-else-if="!keywords && !tableData.length"
          :description="t('dimension.empty_description')"
          img-type="noneWhite"
        />
        <EmptyBackground
          v-else-if="!!keywords && !tableData.length"
          :description="t('datasource.relevant_content_found')"
          img-type="tree"
        />
      </div>
    </div>

    <!-- 分页 -->
    <div v-if="tableData.length" class="pagination-container">
      <el-pagination
        v-model:current-page="pageInfo.currentPage"
        v-model:page-size="pageInfo.pageSize"
        :page-sizes="[10, 20, 30]"
        :background="true"
        layout="total, sizes, prev, pager, next, jumper"
        :total="pageInfo.total"
        @current-change="handlePageChange"
        @size-change="handleSizeChange"
      />
    </div>

    <!-- 编辑对话框 -->
    <el-dialog
      v-model="dialogFormVisible"
      :title="dialogTitle"
      width="600px"
      :close-on-click-modal="false"
      destroy-on-close
    >
      <el-form :model="pageForm" label-width="120px">
        <el-form-item :label="t('dimension.dimension_name')" required>
          <el-input v-model="pageForm.name" :placeholder="t('dimension.name_placeholder')" />
        </el-form-item>
        <el-form-item :label="t('dimension.dimension_code')" required>
          <el-input
            v-model="pageForm.code"
            :placeholder="t('dimension.code_placeholder')"
            :disabled="pageForm.id && pageForm.is_system"
          />
          <div class="form-hint">{{ t('dimension.code_hint') }}</div>
        </el-form-item>
        <el-form-item :label="t('dimension.description')">
          <el-input
            v-model="pageForm.description"
            type="textarea"
            :rows="3"
            :placeholder="t('dimension.description_placeholder')"
          />
        </el-form-item>
        <el-form-item :label="t('dimension.values')" required>
          <div class="values-container">
            <div v-for="(_, index) in pageForm.values" :key="index" class="value-item">
              <el-input v-model="pageForm.values[index]" :placeholder="`${t('dimension.value')} ${index + 1}`" />
              <el-tooltip
                v-if="pageForm.values.length > 1"
                :offset="14"
                effect="dark"
                :content="t('common.remove')"
                placement="top"
              >
                <el-icon class="action-btn danger" size="16" @click="removeValue(index)">
                  <IconOpeDelete />
                </el-icon>
              </el-tooltip>
            </div>
            <el-button text type="primary" :icon="icon_add_outlined" @click="addValue">
              {{ t('dimension.add_value') }}
            </el-button>
          </div>
        </el-form-item>
        <el-form-item :label="t('common.status')">
          <el-switch v-model="pageForm.enabled" :active-text="t('common.enabled')" :inactive-text="t('common.disabled')" />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="dialogFormVisible = false">{{ t('common.cancel') }}</el-button>
          <el-button type="primary" @click="submitForm" :loading="updateLoading">
            {{ t('common.confirm') }}
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<style lang="less" scoped>
.dimension {
  height: 100%;
  position: relative;

  .tool-left {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 16px;

    .page-title {
      font-weight: 500;
      font-size: 20px;
      line-height: 28px;
    }
  }

  .pagination-container {
    display: flex;
    justify-content: end;
    align-items: center;
    margin-top: 16px;
  }

  .table-content {
    max-height: calc(100% - 80px);
    overflow-y: auto;

    .preview-or-schema {
      .more-hint {
        color: #909399;
        font-size: 12px;
      }

      .field-comment {
        display: flex;
        gap: 16px;
        height: 24px;

        .action-btn {
          position: relative;
          cursor: pointer;
          margin-top: 4px;
          color: #646a73;

          &::after {
            content: '';
            background-color: #1f23291a;
            position: absolute;
            border-radius: 6px;
            width: 24px;
            height: 24px;
            transform: translate(-50%, -50%);
            top: 50%;
            left: 50%;
            display: none;
          }

          &:hover {
            &::after {
              display: block;
            }
          }

          &.danger {
            color: var(--ed-color-danger);
          }
        }
      }
    }
  }

  .form-hint {
    color: #8f959e;
    font-size: 12px;
    line-height: 20px;
    margin-top: 4px;
  }

  .values-container {
    width: 100%;

    .value-item {
      display: flex;
      gap: 12px;
      margin-bottom: 12px;
      align-items: center;

      .el-input {
        flex: 1;
      }
    }
  }

  .dialog-footer {
    display: flex;
    justify-content: flex-end;
    gap: 12px;
  }
}
</style>
