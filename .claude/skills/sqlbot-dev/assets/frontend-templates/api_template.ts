/**
 * API 客户端模板
 * 文件位置: frontend/src/api/{resource}.ts
 */
import { request } from '@/utils/request'

// ===== 类型定义 =====
export interface Resource {
  id?: number
  name: string
  description: string
  status?: number
  created_by?: string
  created_at?: string
  updated_at?: string
}

export interface ResourceCreate {
  name: string
  description: string
}

export interface ResourceUpdate {
  name?: string
  description?: string
  status?: number
}

export interface ResourceListParams {
  skip?: number
  limit?: number
  keyword?: string
}

export interface ResourceListResponse {
  list: Resource[]
  total: number
}

// ===== API 客户端 =====
export const resourceApi = {
  /**
   * 获取资源列表
   */
  list: (params?: ResourceListParams) => {
    return request.get<ResourceListResponse>('/resource/list', { params })
  },

  /**
   * 获取单个资源
   */
  get: (id: number) => {
    return request.get<Resource>(`/resource/${id}`)
  },

  /**
   * 创建资源
   */
  create: (data: ResourceCreate) => {
    return request.post<Resource>('/resource', data)
  },

  /**
   * 更新资源
   */
  update: (id: number, data: ResourceUpdate) => {
    return request.put<Resource>(`/resource/${id}`, data)
  },

  /**
   * 删除资源
   */
  delete: (id: number) => {
    return request.delete(`/resource/${id}`)
  },

  /**
   * 批量删除
   */
  batchDelete: (ids: number[]) => {
    return request.post('/resource/batch-delete', { ids })
  }
}
