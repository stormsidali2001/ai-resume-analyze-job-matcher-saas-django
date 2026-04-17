'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { resumesApi } from '@/lib/api/resumes'
import type { CreateResumeRequest, ResumeDTO } from '@/types/api'

export const resumeKeys = {
  all: ['resumes'] as const,
  detail: (id: string) => ['resumes', id] as const,
}

export function useResumes() {
  return useQuery({
    queryKey: resumeKeys.all,
    queryFn: resumesApi.list,
  })
}

export function useResume(id: string) {
  return useQuery({
    queryKey: resumeKeys.detail(id),
    queryFn: () => resumesApi.get(id),
    enabled: !!id,
  })
}

export function useCreateResume() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: CreateResumeRequest) => resumesApi.create(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: resumeKeys.all })
    },
  })
}

export function useAnalyzeResume(id: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () => resumesApi.analyze(id),
    onSuccess: (updated) => {
      qc.setQueryData(resumeKeys.detail(id), updated)
    },
  })
}

export function useAddSkill(resumeId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: { name: string; category: string; proficiency_level: string }) =>
      resumesApi.addSkill(resumeId, data),
    onSuccess: (updated) => {
      qc.setQueryData(resumeKeys.detail(resumeId), updated)
    },
  })
}

export function useUpdateResume(id: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: { new_raw_text: string }) => resumesApi.update(id, data),
    onSuccess: (updated) => {
      qc.setQueryData(resumeKeys.detail(id), updated)
    },
  })
}

export function useArchiveResume(id: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () => resumesApi.archive(id),
    onSuccess: () => {
      qc.setQueryData<ResumeDTO[]>(resumeKeys.all, (old) =>
        old?.filter((r) => r.resume_id !== id) ?? []
      )
      qc.removeQueries({ queryKey: resumeKeys.detail(id) })
    },
  })
}
