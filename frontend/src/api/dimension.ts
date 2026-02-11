import { request } from '@/utils/request'

export const dimensionApi = {
  list: (params: any) => request.get('/dimension/list', { params }),
  all: (enabledOnly = true) => request.get('/dimension/all', { params: { enabled_only: enabledOnly } }),
  get: (id: number) => request.get(`/dimension/${id}`),
  create: (data: any) => request.post('/dimension/', data),
  update: (id: number, data: any) => request.put(`/dimension/${id}`, data),
  delete: (id: number) => request.delete(`/dimension/${id}`),
  enable: (id: number, enabled: boolean) => request.patch(`/dimension/${id}/enable`, null, { params: { enabled } }),
}
