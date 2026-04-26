import apiClient from './client'
import type {
  CreateTicketPayload,
  PaginatedResponse,
  TicketDetail,
  TicketSummary,
  UpdateCategoryPriorityPayload,
  UpdateStatusPayload,
} from '@/types'

export interface TicketFilters {
  status?: string
  category?: string
  priority?: string
  department_id?: number
  submitter_id?: number
  page?: number
  page_size?: number
}

export const ticketsApi = {
  list: (filters: TicketFilters = {}) =>
    apiClient.get<PaginatedResponse<TicketSummary>>('/tickets', { params: filters }),

  get: (id: number) =>
    apiClient.get<TicketDetail>(`/tickets/${id}`),

  create: (payload: CreateTicketPayload) =>
    apiClient.post<TicketDetail>('/tickets', payload),

  updateStatus: (id: number, payload: UpdateStatusPayload) =>
    apiClient.patch<TicketDetail>(`/tickets/${id}/status`, payload),

  updateCategoryPriority: (id: number, payload: UpdateCategoryPriorityPayload) =>
    apiClient.patch<TicketDetail>(`/tickets/${id}/category-priority`, payload),

  remove: (id: number) =>
    apiClient.post<TicketDetail>(`/tickets/${id}/remove`),

  reopen: (id: number) =>
    apiClient.post<TicketDetail>(`/tickets/${id}/reopen`),

  softDelete: (id: number) =>
    apiClient.delete(`/tickets/${id}`),
}
