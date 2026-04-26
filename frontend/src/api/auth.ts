import apiClient from './client'
import type { AuthUser } from '@/types'

export const authApi = {
  login: (email: string, password: string) =>
    apiClient.post<AuthUser>('/auth/login', { email, password }),

  logout: () =>
    apiClient.post('/auth/logout'),

  me: () =>
    apiClient.get<AuthUser>('/auth/me'),

  requestPasswordReset: (email: string) =>
    apiClient.post('/auth/password-reset/request', { email }),

  confirmPasswordReset: (token: string, new_password: string) =>
    apiClient.post('/auth/password-reset/confirm', { token, new_password }),
}
