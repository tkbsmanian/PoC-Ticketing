/**
 * useNotifications — polls for unread notifications every 30 seconds.
 */

import { useCallback, useEffect, useState } from 'react'
import { notificationsApi } from '@/api/notifications'
import type { Notification } from '@/types'

const POLL_INTERVAL_MS = 30_000

export function useNotifications() {
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [unreadCount, setUnreadCount] = useState(0)

  const fetch = useCallback(async () => {
    try {
      const { data } = await notificationsApi.list()
      setNotifications(data)
      setUnreadCount(data.filter((n) => !n.is_read).length)
    } catch {
      // silent — notification failures must not disrupt the UI
    }
  }, [])

  useEffect(() => {
    fetch()
    const interval = setInterval(fetch, POLL_INTERVAL_MS)
    const onFocus = () => fetch()
    window.addEventListener('focus', onFocus)
    return () => {
      clearInterval(interval)
      window.removeEventListener('focus', onFocus)
    }
  }, [fetch])

  const markRead = async (id: number) => {
    await notificationsApi.markRead(id)
    setNotifications((prev) =>
      prev.map((n) => (n.id === id ? { ...n, is_read: true } : n))
    )
    setUnreadCount((c) => Math.max(0, c - 1))
  }

  const markAllRead = async () => {
    await notificationsApi.markAllRead()
    setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })))
    setUnreadCount(0)
  }

  return { notifications, unreadCount, markRead, markAllRead, refresh: fetch }
}
