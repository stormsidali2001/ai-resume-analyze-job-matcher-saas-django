import { apiClient } from './client'
import type { AuthUser } from '@/types/api'

export const authApi = {
  login: (username: string, password: string) =>
    apiClient.post<{ ok: boolean }>('/api/auth/login', { username, password }),

  register: (data: {
    username: string
    email: string
    password: string
    role: string
  }) => apiClient.post<{ user: AuthUser }>('/api/auth/register', data),

  logout: () => apiClient.post<{ ok: boolean }>('/api/auth/logout'),
}
