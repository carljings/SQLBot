<!--
/**
 * 表单对话框模板
 * 文件位置: frontend/src/views/{module}/components/FormDialog.vue
 */
-->
<template>
  <el-dialog
    v-model="visible"
    :title="isEdit ? '编辑资源' : '新建资源'"
    width="600px"
    :close-on-click-modal="false"
    @closed="handleClosed"
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="100px"
    >
      <el-form-item label="名称" prop="name">
        <el-input
          v-model="form.name"
          placeholder="请输入资源名称"
          maxlength="100"
          show-word-limit
        />
      </el-form-item>

      <el-form-item label="描述" prop="description">
        <el-input
          v-model="form.description"
          type="textarea"
          :rows="4"
          placeholder="请输入资源描述"
          maxlength="500"
          show-word-limit
        />
      </el-form-item>

      <!-- 动态表单项示例 -->
      <el-form-item label="状态" prop="status" v-if="isEdit">
        <el-radio-group v-model="form.status">
          <el-radio :label="1">启用</el-radio>
          <el-radio :label="0">禁用</el-radio>
        </el-radio-group>
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button
        type="primary"
        :loading="submitting"
        @click="handleSubmit"
      >
        确定
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, watch, computed, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { resourceApi, type Resource, type ResourceCreate, type ResourceUpdate } from '@/api/resource'

// ===== Props & Emits =====
interface Props {
  modelValue: boolean
  data?: Resource
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'success': []
}>()

// ===== 状态 =====
const visible = ref(false)
const submitting = ref(false)
const formRef = ref<FormInstance>()

const isEdit = computed(() => !!props.data?.id)

const form = reactive<ResourceCreate & { status?: number }>({
  name: '',
  description: '',
  status: 1
})

// ===== 表单验证规则 =====
const rules: FormRules = {
  name: [
    { required: true, message: '请输入资源名称', trigger: 'blur' },
    { min: 2, max: 100, message: '长度在 2 到 100 个字符', trigger: 'blur' }
  ],
  description: [
    { required: true, message: '请输入资源描述', trigger: 'blur' },
    { max: 500, message: '最多 500 个字符', trigger: 'blur' }
  ]
}

// ===== 监听 props 变化 =====
watch(() => props.modelValue, (val) => {
  visible.value = val
  if (val && props.data) {
    // 编辑模式：填充表单
    nextTick(() => {
      Object.assign(form, {
        name: props.data?.name || '',
        description: props.data?.description || '',
        status: props.data?.status ?? 1
      })
    })
  }
})

watch(visible, (val) => {
  emit('update:modelValue', val)
})

// ===== 表单操作 =====
const handleSubmit = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
  } catch {
    return
  }

  submitting.value = true
  try {
    if (isEdit.value) {
      // 更新
      const updateData: ResourceUpdate = {
        name: form.name,
        description: form.description,
        status: form.status
      }
      await resourceApi.update(props.data!.id!, updateData)
      ElMessage.success('更新成功')
    } else {
      // 创建
      const createData: ResourceCreate = {
        name: form.name,
        description: form.description
      }
      await resourceApi.create(createData)
      ElMessage.success('创建成功')
    }

    visible.value = false
    emit('success')
  } catch (error: any) {
    ElMessage.error(error?.message || '操作失败')
  } finally {
    submitting.value = false
  }
}

const handleClosed = () => {
  formRef.value?.resetFields()
  Object.assign(form, {
    name: '',
    description: '',
    status: 1
  })
}
</script>

<style scoped lang="less">
:deep(.el-dialog__body) {
  padding-top: 20px;
}
</style>
