import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { CommentThread } from '@/pages/shared/CommentThread'
import { AuthContext } from '@/context/AuthContext'
import type { AuthUser, Comment } from '@/types'

// No outer variables in mock factory
vi.mock('@/api/comments', () => ({
  commentsApi: { create: vi.fn() },
}))

function renderThread(
  role: AuthUser['role'],
  comments: Comment[],
  status = 'In Progress'
) {
  const user: AuthUser = {
    id: 1, email: 'u@e.com', display_name: 'User',
    role, department_id: 1, department_name: 'IT',
  }
  return render(
    <AuthContext.Provider value={{ user, loading: false, login: vi.fn(), logout: vi.fn() }}>
      <CommentThread
        ticketId={1}
        comments={comments}
        ticketStatus={status as any}
        onCommentAdded={vi.fn()}
      />
    </AuthContext.Provider>
  )
}

const publicComment: Comment = {
  id: 1, author_name: 'IT User', author_role: 'it_triage',
  body: 'Working on it', is_internal: false,
  created_at: new Date().toISOString(),
}

const internalComment: Comment = {
  id: 2, author_name: 'IT User', author_role: 'it_triage',
  body: 'Internal note only', is_internal: true,
  created_at: new Date().toISOString(),
}

describe('CommentThread', () => {
  it('shows public comments to business_user', () => {
    renderThread('business_user', [publicComment])
    expect(screen.getByText('Working on it')).toBeInTheDocument()
  })

  it('hides internal comments from business_user', () => {
    renderThread('business_user', [internalComment])
    expect(screen.queryByText('Internal note only')).not.toBeInTheDocument()
  })

  it('shows internal comments to it_triage', () => {
    renderThread('it_triage', [internalComment])
    expect(screen.getByText('Internal note only')).toBeInTheDocument()
  })

  it('shows internal badge on internal comments for IT', () => {
    renderThread('it_triage', [internalComment])
    // Use aria-label which is unique
    expect(screen.getByLabelText('Internal note')).toBeInTheDocument()
  })

  it('disables comment form on closed ticket', () => {
    renderThread('business_user', [], 'Closed')
    expect(screen.queryByRole('textbox')).not.toBeInTheDocument()
    expect(screen.getByText(/comments are disabled/i)).toBeInTheDocument()
  })

  it('shows comment form on non-closed ticket', () => {
    renderThread('business_user', [], 'In Progress')
    expect(screen.getByRole('textbox')).toBeInTheDocument()
  })

  it('shows internal toggle for it_triage', () => {
    renderThread('it_triage', [])
    expect(screen.getByText(/internal note \(hidden from requester\)/i)).toBeInTheDocument()
  })

  it('does not show internal toggle for business_user', () => {
    renderThread('business_user', [])
    expect(screen.queryByText(/internal note \(hidden from requester\)/i)).not.toBeInTheDocument()
  })
})
