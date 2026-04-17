import { apiClient } from './client'
import type { MatchResultDTO, MatchRequest } from '@/types/api'

export const matchApi = {
  run: (data: MatchRequest) => apiClient.post<MatchResultDTO>('/api/proxy/match', data),
}
