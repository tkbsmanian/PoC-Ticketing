import { describe, expect, it } from 'vitest'
import { domain_ticket_lifecycle_valid_next, isTerminal } from '@/utils/ticketLifecycle'
import type { TicketStatus } from '@/types'

describe('ticketLifecycle', () => {
  it('Pending has valid next statuses', () => {
    const next = domain_ticket_lifecycle_valid_next('Pending')
    expect(next).toContain('Approved')
    expect(next).toContain('Rejected')
    expect(next).toContain('Removed')
  })

  it('Closed is terminal', () => {
    expect(isTerminal('Closed')).toBe(true)
    expect(domain_ticket_lifecycle_valid_next('Closed')).toHaveLength(0)
  })

  it('Rejected is terminal', () => {
    expect(isTerminal('Rejected')).toBe(true)
  })

  it('Removed is terminal', () => {
    expect(isTerminal('Removed')).toBe(true)
  })

  it('Resolved can go to Closed or In Progress (re-open)', () => {
    const next = domain_ticket_lifecycle_valid_next('Resolved')
    expect(next).toContain('Closed')
    expect(next).toContain('In Progress')
  })

  const nonTerminal: TicketStatus[] = ['Pending', 'Approved', 'In Review', 'In Progress', 'Resolved']
  nonTerminal.forEach((s) => {
    it(`${s} is not terminal`, () => {
      expect(isTerminal(s)).toBe(false)
    })
  })
})
