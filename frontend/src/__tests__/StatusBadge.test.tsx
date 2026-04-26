import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import { StatusBadge } from '@/components/StatusBadge'

describe('StatusBadge', () => {
  it('renders the status text', () => {
    render(<StatusBadge status="In Progress" />)
    expect(screen.getByText('In Progress')).toBeInTheDocument()
  })

  it('has accessible aria-label', () => {
    render(<StatusBadge status="Resolved" />)
    expect(screen.getByLabelText('Status: Resolved')).toBeInTheDocument()
  })
})
