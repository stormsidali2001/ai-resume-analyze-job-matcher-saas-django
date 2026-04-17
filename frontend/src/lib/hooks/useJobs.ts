'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { jobsApi } from '@/lib/api/jobs'
import type { CreateJobRequest } from '@/types/api'

export const jobKeys = {
  all: ['jobs'] as const,
  mine: ['jobs', 'mine'] as const,
  detail: (id: string) => ['jobs', id] as const,
}

export function useJobs() {
  return useQuery({
    queryKey: jobKeys.all,
    queryFn: jobsApi.list,
  })
}

export function useJob(id: string) {
  return useQuery({
    queryKey: jobKeys.detail(id),
    queryFn: () => jobsApi.get(id),
    enabled: !!id,
  })
}

export function useMyJobs() {
  return useQuery({
    queryKey: jobKeys.mine,
    queryFn: jobsApi.listMine,
  })
}

export function useCreateJob() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: CreateJobRequest) => jobsApi.create(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: jobKeys.mine })
    },
  })
}

export function useAddJobSkill(jobId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: { name: string; category: string; proficiency_level: string }) =>
      jobsApi.addSkill(jobId, data),
    onSuccess: (updated) => {
      qc.setQueryData(jobKeys.detail(jobId), updated)
      qc.invalidateQueries({ queryKey: jobKeys.mine })
    },
  })
}

export function usePublishJob(jobId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () => jobsApi.publish(jobId),
    onSuccess: (updated) => {
      qc.setQueryData(jobKeys.detail(jobId), updated)
      qc.invalidateQueries({ queryKey: jobKeys.mine })
    },
  })
}

export function useCloseJob(jobId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () => jobsApi.close(jobId),
    onSuccess: (updated) => {
      qc.setQueryData(jobKeys.detail(jobId), updated)
      qc.invalidateQueries({ queryKey: jobKeys.mine })
    },
  })
}
