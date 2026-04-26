/**
 * Frontend mirror of the ticket lifecycle transition table.
 * Used to compute valid next-status buttons in the UI.
 * Source of truth remains the backend domain/ticket_lifecycle.py.
 */

import type { TicketStatus } from '@/types'

const VALID_TRANSITIONS: Record<TicketStatus, TicketStatus[]> = {
  Pending: ['Approved', 'Rejected', 'Removed'],
  Approved: ['In Review', 'Rejected'],
  'In Review': ['In Progress', 'Removed'],
  'In Progress': ['Resolved', 'In Review'],
  Resolved: ['Closed', 'In Progress'],
  Closed: [],
  Rejected: [],
  Removed: [],
}

export function domain_ticket_lifecycle_valid_next(current: TicketStatus): TicketStatus[] {
  return VALID_TRANSITIONS[current] ?? []
}

export function isTerminal(status: TicketStatus): boolean {
  return VALID_TRANSITIONS[status]?.length === 0
}
