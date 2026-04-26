import apiClient from './client'
import type { Approval, ApprovalActionPayload } from '@/types'

export const approvalsApi = {
  pending: () =>
    apiClient.get<Approval[]>('/approvals/pending'),

  approve: (approvalId: number, payload: ApprovalActionPayload = {}) =>
    apiClient.post<Approval>(`/approvals/${approvalId}/approve`, payload),

  reject: (approvalId: number, payload: ApprovalActionPayload) =>
    apiClient.post<Approval>(`/approvals/${approvalId}/reject`, payload),
}
