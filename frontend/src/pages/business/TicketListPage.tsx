/**
 * Business portal — My Requests list.
 * Shows only tickets submitted by the current user.
 */

import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { ticketsApi } from '@/api/tickets'
import { StatusBadge } from '@/components/StatusBadge'
import { SyncFailedBadge } from '@/components/SyncFailedBadge'
import type { TicketSummary } from '@/types'

export function BusinessTicketListPage() {
  const [tickets, setTickets] = useState<TicketSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    ticketsApi.list()
      .then(({ data }) => setTickets(data.items))
      .catch(() => setError('Failed to load your requests. Please try again.'))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <p aria-live="polite">Loading your requests…</p>
  if (error) return <p className="error-message" role="alert">{error}</p>

  return (
    <div className="ticket-list-page">
      <div className="page-header">
        <h1>My Requests</h1>
        <Link to="/portal/tickets/new" className="btn-primary">
          + New Request
        </Link>
      </div>

      {tickets.length === 0 ? (
        <div className="empty-state">
          <p>You haven't submitted any requests yet.</p>
          <Link to="/portal/tickets/new">Submit your first request</Link>
        </div>
      ) : (
        <table className="ticket-table" aria-label="My requests">
          <thead>
            <tr>
              <th scope="col">ID</th>
              <th scope="col">Title</th>
              <th scope="col">Status</th>
              <th scope="col">Urgency</th>
              <th scope="col">Submitted</th>
              <th scope="col">Updated</th>
              <th scope="col"><span className="sr-only">Actions</span></th>
            </tr>
          </thead>
          <tbody>
            {tickets.map((t) => (
              <tr key={t.id}>
                <td>{t.ticket_id}</td>
                <td>
                  {t.title}
                  <SyncFailedBadge visible={t.sync_failed} />
                </td>
                <td><StatusBadge status={t.status} /></td>
                <td>{t.urgency}</td>
                <td>{new Date(t.created_at).toLocaleDateString()}</td>
                <td>{new Date(t.updated_at).toLocaleDateString()}</td>
                <td>
                  <Link to={`/portal/tickets/${t.id}`}>View</Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}
