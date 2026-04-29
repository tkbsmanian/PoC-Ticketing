import { describe, expect, it, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { DashboardPage } from '@/pages/it/DashboardPage'
import { AuthContext } from '@/context/AuthContext'
import type { AuthUser } from '@/types'

// No outer variables in mock factory
vi.mock('@/api/admin', () => ({
  adminApi: {
    dashboard: vi.fn().mockResolvedValue({
      data: {
        by_status: { Pending: 3, 'In Progress': 2, Resolved: 1 },
        total_open: 5,
      },
    }),
    syncHealth: vi.fn().mockResolvedValue({
      data: {
        adapter: 'mock',
        last_success_at: null,
        pending_count: 0,
        failed_count: 2,
      },
    }),
  },
}))

function renderDashboard(role: AuthUser['role'] = 'it_triage') {
  const user: AuthUser = {
    id: 1, email: 'it@e.com', display_name: 'IT',
    role, department_id: 1, department_name: 'IT',
  }
  return render(
    <AuthContext.Provider value={{ user, loading: false, login: vi.fn(), logout: vi.fn() }}>
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>
    </AuthContext.Provider>
  )
}

describe('DashboardPage', () => {
  it('shows ticket counts by status', async () => {
    renderDashboard()
    await waitFor(() => {
      expect(screen.getByText('Pending')).toBeInTheDocument()
    })
    // Count value for Pending is 3
    const countCards = screen.getAllByText('3')
    expect(countCards.length).toBeGreaterThan(0)
  })

  it('shows total open count', async () => {
    renderDashboard()
    await waitFor(() => {
      expect(screen.getByText(/total open/i)).toBeInTheDocument()
    })
    expect(screen.getByText('5')).toBeInTheDocument()
  })

  it('shows sync health for it_triage', async () => {
    renderDashboard('it_triage')
    await waitFor(() => {
      expect(screen.getByText(/jira sync health/i)).toBeInTheDocument()
    })
  })

  it('shows failed count with error styling when > 0', async () => {
    renderDashboard()
    await waitFor(() => {
      expect(screen.getByText(/jira sync health/i)).toBeInTheDocument()
    })
    // Multiple elements may show "2" (e.g. In Progress count) — find the one in a dd.sync-failed-count
    const allTwos = screen.getAllByText('2')
    const failedDd = allTwos.find(el => el.closest('dd')?.classList.contains('sync-failed-count'))
    expect(failedDd).toBeDefined()
  })
})
