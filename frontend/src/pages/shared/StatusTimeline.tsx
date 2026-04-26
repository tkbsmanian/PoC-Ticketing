/**
 * StatusTimeline — chronological audit trail of status changes and field updates.
 */

import type { StatusHistoryEntry } from '@/types'

interface Props {
  history: StatusHistoryEntry[]
}

export function StatusTimeline({ history }: Props) {
  if (history.length === 0) {
    return (
      <section aria-labelledby="timeline-heading">
        <h2 id="timeline-heading">History</h2>
        <p className="empty-state">No history yet.</p>
      </section>
    )
  }

  return (
    <section aria-labelledby="timeline-heading">
      <h2 id="timeline-heading">History</h2>
      <ol className="status-timeline" aria-label="Ticket history">
        {history.map((entry) => (
          <li key={entry.id} className="timeline-entry">
            <div className="timeline-dot" aria-hidden="true" />
            <div className="timeline-content">
              <span className="timeline-event">{formatEvent(entry)}</span>
              <span className="timeline-meta">
                {entry.actor_name} · {new Date(entry.created_at).toLocaleString()}
              </span>
            </div>
          </li>
        ))}
      </ol>
    </section>
  )
}

function formatEvent(entry: StatusHistoryEntry): string {
  if (entry.event_type === 'status_changed') {
    return `Status changed: ${entry.old_value} → ${entry.new_value}`
  }
  if (entry.event_type === 'field_changed' && entry.field_name) {
    const field = entry.field_name.charAt(0).toUpperCase() + entry.field_name.slice(1)
    return `${field} changed: ${entry.old_value ?? '—'} → ${entry.new_value ?? '—'}`
  }
  if (entry.event_type === 'approval_decision') {
    return `Approval: ${entry.new_value}`
  }
  if (entry.event_type === 'ticket_created') {
    return 'Ticket submitted'
  }
  return entry.event_type.replace(/_/g, ' ')
}
