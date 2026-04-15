'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { resumesApi } from '@/lib/api/resumes'
import type { CreateResumeRequest } from '@/types/api'

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
