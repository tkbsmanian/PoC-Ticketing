/**
 * ITActionPanel — status transitions, category/priority controls for IT Triage.
 * Only rendered when the current user has canUpdateStatus permission.
 */

import { useState } from 'react'
import { ticketsApi } from '@/api/tickets'
import type { PriorityLevel, TicketDetail, TicketStatus } from '@/types'
import { domain_ticket_lifecycle_valid_next } from '@/utils/ticketLifecycle'

interface Props {
  ticket: TicketDetail
  onUpdate: () => void
}

const PRIORITY_OPTIONS: PriorityLevel[] = ['Low', 'Medium', 'High', 'Critical']

export function ITActionPanel({ ticket, onUpdate }: Props) {
  const [category, setCategory] = useState(ticket.category ?? '')
  const [priority, setPriority] = useState<PriorityLevel | ''>(ticket.priority ?? '')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const validNextStatuses = domain_ticket_lifecycle_valid_next(ticket.status)

  const handleStatusChange = async (newStatus: TicketStatus) => {
    setSaving(true)
    setError(null)
    try {
      await ticketsApi.updateStatus(ticket.id, { status: newStatus })
      onUpdate()
    } catch {
      setError('Failed to update status.')
    } finally {
      setSaving(false)
    }
  }

  const handleSaveCategoryPriority = async () => {
    setSaving(true)
    setError(null)
    try {
      await ticketsApi.updateCategoryPriority(ticket.id, {
        category: category || undefined,
        priority: (priority as PriorityLevel) || undefined,
      })
      onUpdate()
    } catch {
      setError('Failed to save changes.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <section className="it-action-panel" aria-labelledby="it-actions-heading">
      <h2 id="it-actions-heading">IT Actions</h2>

      {validNextStatuses.length > 0 && (
        <div className="status-actions">
          <span>Move to:</span>
          {validNextStatuses.map((s) => (
            <button
              key={s}
              onClick={() => handleStatusChange(s)}
              disabled={saving}
              className="btn-status"
            >
              {s}
            </button>
          ))}
        </div>
      )}

      <div className="category-priority-form">
        <div className="field">
          <label htmlFor="category">Category</label>
          <input
            id="category"
            type="text"
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            placeholder="e.g. Hardware, Software, Access"
          />
        </div>
        <div className="field">
          <label htmlFor="priority">Priority</label>
          <select
            id="priority"
            value={priority}
            onChange={(e) => setPriority(e.target.value as PriorityLevel)}
          >
            <option value="">Not set</option>
            {PRIORITY_OPTIONS.map((p) => (
              <option key={p} value={p}>{p}</option>
            ))}
          </select>
        </div>
        <button onClick={handleSaveCategoryPriority} disabled={saving}>
          {saving ? 'Saving…' : 'Save'}
        </button>
      </div>

      {error && <p className="field-error" role="alert">{error}</p>}
    </section>
  )
}
