/**
 * IT Operations portal — full ticket queue with filters.
 */

import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { ticketsApi, type TicketFilters } from '@/api/tickets'
import { adminApi } from '@/api/admin'
import { StatusBadge } from '@/components/StatusBadge'
import { SyncFailedBadge } from '@/components/SyncFailedBadge'
import type { Department, TicketStatus, TicketSummary } from '@/types'

const STATUS_OPTIONS: TicketStatus[] = [
  'Pending', 'Approved', 'In Review', 'In Progress', 'Resolved', 'Closed', 'Rejected', 'Removed',
]

export function ITTicketListPage() {
  const [tickets, setTickets] = useState<TicketSummary[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [departments, setDepartments] = useState<Department[]>([])

  const [filters, setFilters] = useState<TicketFilters>({ page: 1, page_size: 25 })

  useEffect(() => {
    adminApi.listDepartments().then(({ data }) => setDepartments(data))
  }, [])

  useEffect(() => {
    setLoading(true)
    ticketsApi.list(filters)
      .then(({ data }) => { setTickets(data.items); setTotal(data.total) })
      .catch(() => setError('Failed to load tickets.'))
      .finally(() => setLoading(false))
  }, [filters])

  const setFilter = (key: keyof TicketFilters, value: string | number | undefined) =>
    setFilters((f) => ({ ...f, [key]: value || undefined, page: 1 }))

  return (
    <div className="it-ticket-list-page">
      <div className="page-header">
        <h1>Ticket Queue</h1>
        <span className="total-count">{total} tickets</span>
      </div>

      <div className="filter-bar" role="search" aria-label="Filter tickets">
        <select
          aria-label="Filter by status"
          onChange={(e) => setFilter('status', e.target.value)}
        >
          <option value="">All statuses</option>
          {STATUS_OPTIONS.map((s) => <option key={s} value={s}>{s}</option>)}
        </select>

        <select
          aria-label="Filter by department"
          onChange={(e) => setFilter('department_id', Number(e.target.value))}
        >
          <option value="">All departments</option>
          {departments.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
        </select>

        <select
          aria-label="Filter by priority"
          onChange={(e) => setFilter('priority', e.target.value)}
        >
          <option value="">All priorities</option>
          {['Low', 'Medium', 'High', 'Critical'].map((p) => (
            <option key={p} value={p}>{p}</option>
          ))}
        </select>
      </div>

      {loading && <p aria-live="polite">Loading tickets…</p>}
      {error && <p className="error-message" role="alert">{error}</p>}

      {!loading && !error && (
        <table className="ticket-table" aria-label="Ticket queue">
          <thead>
            <tr>
              <th scope="col">ID</th>
              <th scope="col">Title</th>
              <th scope="col">Status</th>
              <th scope="col">Priority</th>
              <th scope="col">Department</th>
              <th scope="col">Submitted by</th>
              <th scope="col">Updated</th>
              <th scope="col"><span className="sr-only">Actions</span></th>
            </tr>
          </thead>
          <tbody>
            {tickets.length === 0 ? (
              <tr><td colSpan={8} className="empty-state">No tickets match the current filters.</td></tr>
            ) : tickets.map((t) => (
              <tr key={t.id} className={t.sync_failed ? 'row-sync-failed' : ''}>
                <td>{t.ticket_id}</td>
                <td>
                  {t.title}
                  <SyncFailedBadge visible={t.sync_failed} />
                </td>
                <td><StatusBadge status={t.status} /></td>
                <td>{t.priority ?? '—'}</td>
                <td>{t.department_name ?? '—'}</td>
                <td>{t.submitter_name}</td>
                <td>{new Date(t.updated_at).toLocaleDateString()}</td>
                <td><Link to={`/it/tickets/${t.id}`}>View</Link></td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}
