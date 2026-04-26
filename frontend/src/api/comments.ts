import apiClient from './client'
import type { Comment, CreateCommentPayload } from '@/types'

export const commentsApi = {
  list: (ticketId: number) =>
    apiClient.get<Comment[]>(`/tickets/${ticketId}/comments`),

  create: (ticketId: number, payload: CreateCommentPayload) =>
    apiClient.post<Comment>(`/tickets/${ticketId}/comments`, payload),
}
