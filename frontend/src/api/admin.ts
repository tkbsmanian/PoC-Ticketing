import apiClient from './client'
import type {
  CreateUserPayload,
  Department,
  DashboardCounts,
  SyncHealth,
  UserSummary,
} from '@/types'

export const adminApi = {
  // Users
  listUsers: () =>
    apiClient.get<UserSummary[]>('/users'),

  createUser: (payload: CreateUserPayload) =>
    apiClient.post<UserSummary>('/users', payload),

  updateUser: (id: number, payload: Partial<CreateUserPayload & { is_active: boolean }>) =>
    apiClient.patch<UserSummary>(`/users/${id}`, payload),

  listManagers: () =>
    apiClient.get<UserSummary[]>('/users/managers'),

  // Departments
  listDepartments: () =>
    apiClient.get<Department[]>('/departments'),

  createDepartment: (name: string) =>
    apiClient.post<Department>('/departments', { name }),

  updateDepartment: (id: number, payload: Partial<Department>) =>
    apiClient.patch<Department>(`/departments/${id}`, payload),

  // Dashboard
  dashboard: () =>
    apiClient.get<DashboardCounts>('/dashboard'),

  // Sync health
  syncHealth: () =>
    apiClient.get<SyncHealth>('/sync/health'),

  // Audit
  auditLog: (params?: Record<string, string>) =>
    apiClient.get('/audit/log', { params }),

  ticketAudit: (ticketId: number) =>
    apiClient.get(`/audit/tickets/${ticketId}`),
}
