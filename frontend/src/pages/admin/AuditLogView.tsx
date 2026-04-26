import { useEffect, useState } from 'react'
import { adminApi } from '@/api/admin'

interface AuditEntry {
  id: number
  ticket_id: number | null
  actor_name: string | null
  event_type: string
  field_name: string | null
  old_value: string | null
  new_value: string | null
  notes: string | null
  created_at: string
}

export function AuditLogView() {
  const [entries, setEntries] = useState<AuditEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [eventFilter, setEventFilter] = useState('')

  useEffect(() => {
    const params = eventFilter ? { event_type: eventFilter } : undefined
    adminApi.auditLog(params)
      .then(({ data }) => setEntries(data))
      .finally(() => setLoading(false))
  }, [eventFilter])

  return (
    <div className="audit-log-view">
      <h2>Audit Log</h2>
      <div className="filter-bar">
        <input
          type="text"
          placeholder="Filter by event type…"
          value={eventFilter}
          onChange={(e) => setEventFilter(e.target.value)}
          aria-label="Filter audit log by event type"
        />
      </div>

      {loading ? (
        <p aria-live="polite">Loading audit log…</p>
      ) : (
        <table className="admin-table audit-table" aria-label="Audit log">
          <thead>
            <tr>
              <th>Time</th><th>Event</th><th>Actor</th>
              <th>Ticket</th><th>Field</th><th>Old</th><th>New</th>
            </tr>
          </thead>
          <tbody>
            {entries.length === 0 ? (
              <tr><td colSpan={7} className="empty-state">No audit entries found.</td></tr>
            ) : entries.map((e) => (
              <tr key={e.id}>
                <td>{new Date(e.created_at).toLocaleString()}</td>
                <td>{e.event_type}</td>
                <td>{e.actor_name ?? '—'}</td>
                <td>{e.ticket_id ?? '—'}</td>
                <td>{e.field_name ?? '—'}</td>
                <td>{e.old_value ?? '—'}</td>
                <td>{e.new_value ?? '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}
