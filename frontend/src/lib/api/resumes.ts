import { apiClient } from './client'
import type { ResumeDTO, CreateResumeRequest } from '@/types/api'

export const resumesApi = {
  list: () => apiClient.get<ResumeDTO[]>('/api/proxy/resumes'),

  get: (id: string) => apiClient.get<ResumeDTO>(`/api/proxy/resumes/${id}`),

  create: (data: CreateResumeRequest) =>
    apiClient.post<ResumeDTO>('/api/proxy/resumes', data),

  analyze: (id: string) =>
    apiClient.post<{ resume_id: string; analysis_status: string }>(
      `/api/proxy/resumes/${id}/analyze`,
      { known_skills: [] },
    ),

  addSkill: (id: string, data: { name: string; category: string; proficiency_level: string }) =>
    apiClient.post<ResumeDTO>(`/api/proxy/resumes/${id}/skills`, data),

  uploadFile: (data: FormData) =>
    apiClient.postForm<ResumeDTO>('/api/proxy/resumes/upload', data),

  update: (id: string, data: { new_raw_text: string }) =>
    apiClient.patch<ResumeDTO>(`/api/proxy/resumes/${id}`, data),

  archive: (id: string) =>
    apiClient.post<void>(`/api/proxy/resumes/${id}/archive`, {}),
}
