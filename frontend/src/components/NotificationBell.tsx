/**
 * NotificationBell — in-portal notification feed.
 * Polls every 30 seconds and on window focus.
 */

import { useState } from 'react'
import { useNotifications } from '@/hooks/useNotifications'

export function NotificationBell() {
  const { notifications, unreadCount, markRead, markAllRead } = useNotifications()
  const [open, setOpen] = useState(false)

  return (
    <div className="notification-bell">
      <button
        aria-label={`Notifications — ${unreadCount} unread`}
        onClick={() => setOpen((o) => !o)}
      >
        🔔
        {unreadCount > 0 && (
          <span className="badge" aria-hidden="true">{unreadCount}</span>
        )}
      </button>

      {open && (
        <div className="notification-dropdown" role="dialog" aria-label="Notifications">
          <div className="notification-header">
            <span>Notifications</span>
            {unreadCount > 0 && (
              <button onClick={markAllRead}>Mark all read</button>
            )}
          </div>
          {notifications.length === 0 ? (
            <p className="notification-empty">No notifications.</p>
          ) : (
            <ul>
              {notifications.map((n) => (
                <li
                  key={n.id}
                  className={n.is_read ? 'read' : 'unread'}
                  onClick={() => !n.is_read && markRead(n.id)}
                >
                  <span className="notification-message">{n.message}</span>
                  <span className="notification-time">
                    {new Date(n.created_at).toLocaleString()}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  )
}
