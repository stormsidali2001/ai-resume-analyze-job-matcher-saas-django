'use client'

import { useMutation } from '@tanstack/react-query'
import { matchApi } from '@/lib/api/match'
import type { MatchRequest } from '@/types/api'

export function useRunMatch() {
  return useMutation({
    mutationFn: (data: MatchRequest) => matchApi.run(data),
  })
}
