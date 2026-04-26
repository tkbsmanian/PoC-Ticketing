import type { TicketStatus } from '@/types'

const STATUS_COLOURS: Record<TicketStatus, string> = {
  Pending: '#f59e0b',
  Approved: '#3b82f6',
  'In Review': '#8b5cf6',
  'In Progress': '#0ea5e9',
  Resolved: '#10b981',
  Closed: '#6b7280',
  Rejected: '#ef4444',
  Removed: '#9ca3af',
}

interface Props {
  status: TicketStatus
}

export function StatusBadge({ status }: Props) {
  return (
    <span
      className="status-badge"
      style={{ backgroundColor: STATUS_COLOURS[status] }}
      aria-label={`Status: ${status}`}
    >
      {status}
    </span>
  )
}
