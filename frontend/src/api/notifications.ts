import apiClient from './client'
import type { Notification } from '@/types'

export const notificationsApi = {
  list: () =>
    apiClient.get<Notification[]>('/notifications'),

  markRead: (id: number) =>
    apiClient.post(`/notifications/${id}/read`),

  markAllRead: () =>
    apiClient.post('/notifications/read-all'),
}
