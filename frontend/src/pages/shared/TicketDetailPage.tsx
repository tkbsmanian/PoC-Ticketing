/**
 * Ticket detail page — shared between Business and IT portals.
 * Renders different action panels based on role via usePermissions().
 */

import { useEffect, useState } from 'react'
import { useLocation, useParams } from 'react-router-dom'
import { ticketsApi } from '@/api/tickets'
import { StatusBadge } from '@/components/StatusBadge'
import { SyncFailedBadge } from '@/components/SyncFailedBadge'
import { usePermissions } from '@/hooks/usePermissions'
import type { TicketDetail } from '@/types'
import { CommentThread } from './CommentThread'
import { StatusTimeline } from './StatusTimeline'
import { ITActionPanel } from './ITActionPanel'

export function TicketDetailPage() {
  const { id } = useParams<{ id: string }>()
  const location = useLocation()
  const perms = usePermissions()

  const [ticket, setTicket] = useState<TicketDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const successMessage = (location.state as { successMessage?: string })?.successMessage

  const load = () => {
    if (!id) return
    setLoading(true)
    ticketsApi.get(Number(id))
      .then(({ data }) => setTicket(data))
      .catch(() => setError('Failed to load ticket.'))
      .finally(() => setLoading(false))
  }

  useEffect(load, [id])

  if (loading) return <p aria-live="polite">Loading ticket…</p>
  if (error) return <p className="error-message" role="alert">{error}</p>
  if (!ticket) return null

  return (
    <div className="ticket-detail-page">
      {successMessage && (
        <div className="success-banner" role="status">{successMessage}</div>
      )}

      <div className="ticket-header">
        <h1>
          <span className="ticket-id">{ticket.ticket_id}</span>
          {ticket.title}
        </h1>
        <StatusBadge status={ticket.status} />
        <SyncFailedBadge visible={ticket.sync_failed} />
        {ticket.jira_task_url && (
          <a
            href={ticket.jira_task_url}
            target="_blank"
            rel="noopener noreferrer"
            className="jira-link"
            aria-label={`View in JIRA: ${ticket.jira_task_id}`}
          >
            JIRA: {ticket.jira_task_id}
          </a>
        )}
      </div>

      <div className="ticket-meta">
        <dl>
          <dt>Department</dt><dd>{ticket.department_name ?? '—'}</dd>
          <dt>Urgency</dt><dd>{ticket.urgency}</dd>
          <dt>Priority</dt><dd>{ticket.priority ?? 'Not set'}</dd>
          <dt>Category</dt><dd>{ticket.category ?? 'Not set'}</dd>
          {ticket.cost != null && <><dt>Cost</dt><dd>${ticket.cost.toFixed(2)}</dd></>}
          <dt>Submitted by</dt><dd>{ticket.submitter_name}</dd>
          <dt>Created</dt><dd>{new Date(ticket.created_at).toLocaleString()}</dd>
          <dt>Last updated</dt><dd>{new Date(ticket.updated_at).toLocaleString()}</dd>
        </dl>
      </div>

      <section aria-labelledby="description-heading">
        <h2 id="description-heading">Description</h2>
        <p className="ticket-description">{ticket.description}</p>
      </section>

      {perms.canUpdateStatus && (
        <ITActionPanel ticket={ticket} onUpdate={load} />
      )}

      <StatusTimeline history={ticket.history} />

      <CommentThread
        ticketId={ticket.id}
        comments={ticket.comments}
        ticketStatus={ticket.status}
        onCommentAdded={load}
      />
    </div>
  )
}
