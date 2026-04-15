import { apiClient } from './client'
import type { ResumeDTO, CreateResumeRequest } from '@/types/api'

export const resumesApi = {
  list: () => apiClient.get<ResumeDTO[]>('/api/proxy/resumes'),

  get: (id: string) => apiClient.get<ResumeDTO>(`/api/proxy/resumes/${id}`),

  create: (data: CreateResumeRequest) =>
    apiClient.post<ResumeDTO>('/api/proxy/resumes', data),
}
