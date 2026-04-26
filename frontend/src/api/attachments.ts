import apiClient from './client'
import type { Attachment } from '@/types'

export const attachmentsApi = {
  upload: (ticketId: number, file: File) => {
    const form = new FormData()
    form.append('file', file)
    return apiClient.post<Attachment>(`/tickets/${ticketId}/attachments`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  download: (ticketId: number, attachmentId: number) =>
    apiClient.get(`/tickets/${ticketId}/attachments/${attachmentId}`, {
      responseType: 'blob',
    }),
}
