import { describe, expect, it, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { TicketDetailPage } from '@/pages/shared/TicketDetailPage'
import { AuthContext } from '@/context/AuthContext'
import type { AuthUser } from '@/types'

// All values must be INSIDE the factory — no top-level variable references
vi.mock('@/api/tickets', () => ({
  ticketsApi: {
    get: vi.fn().mockResolvedValue({
      data: {
        id: 1,
        ticket_id: 'TKT-001',
        title: 'Test ticket',
        description: 'Need help',
        status: 'In Progress',
        urgency: 'Medium',
        priority: 'High',
        category: 'Hardware',
        department_name: 'IT',
        submitter_name: 'Jane',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
        sync_failed: false,
        jira_task_id: 'BB-42',
        jira_task_url: 'https://mock.atlassian.net/browse/BB-42',
        cost: null,
        director_approval_required: false,
        comments: [],
        attachments: [],
        history: [],
        approvals: [],
      },
    }),
    updateStatus: vi.fn(),
    updateCategoryPriority: vi.fn(),
  },
}))

function renderDetail(role: AuthUser['role'] = 'business_user') {
  const user: AuthUser = {
    id: 1, email: 'u@e.com', display_name: 'User',
    role, department_id: 1, department_name: 'IT',
  }
  return render(
    <AuthContext.Provider value={{ user, loading: false, login: vi.fn(), logout: vi.fn() }}>
      <MemoryRouter initialEntries={['/tickets/1']}>
        <Routes>
          <Route path="/tickets/:id" element={<TicketDetailPage />} />
        </Routes>
      </MemoryRouter>
    </AuthContext.Provider>
  )
}

describe('TicketDetailPage', () => {
  it('renders ticket title', async () => {
    renderDetail()
    await waitFor(() => expect(screen.getByText('Test ticket')).toBeInTheDocument())
  })

  it('renders JIRA link when jira_task_url is present', async () => {
    renderDetail()
    await waitFor(() => {
      const link = screen.getByRole('link', { name: /jira/i })
      expect(link).toHaveAttribute('href', 'https://mock.atlassian.net/browse/BB-42')
    })
  })

  it('shows IT action panel for it_triage role', async () => {
    renderDetail('it_triage')
    await waitFor(() => {
      expect(screen.getByText(/it actions/i)).toBeInTheDocument()
    })
  })

  it('does not show IT action panel for business_user', async () => {
    renderDetail('business_user')
    await waitFor(() => {
      expect(screen.queryByText(/it actions/i)).not.toBeInTheDocument()
    })
  })
})
