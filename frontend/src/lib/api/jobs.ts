import { apiClient } from './client'
import type { JobDTO, CreateJobRequest } from '@/types/api'

export const jobsApi = {
  list: () => apiClient.get<JobDTO[]>('/api/proxy/jobs'),

  get: (id: string) => apiClient.get<JobDTO>(`/api/proxy/jobs/${id}`),

  listMine: () => apiClient.get<JobDTO[]>('/api/proxy/jobs/mine'),

  create: (data: CreateJobRequest) => apiClient.post<JobDTO>('/api/proxy/jobs', data),

  addSkill: (id: string, data: { name: string; category: string; proficiency_level: string }) =>
    apiClient.post<JobDTO>(`/api/proxy/jobs/${id}/skills`, data),

  publish: (id: string) => apiClient.post<JobDTO>(`/api/proxy/jobs/${id}/publish`, {}),

  close: (id: string) => apiClient.post<JobDTO>(`/api/proxy/jobs/${id}/close`, {}),
}
