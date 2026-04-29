import { describe, expect, it, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { SubmitTicketPage } from '@/pages/business/SubmitTicketPage'
import { AuthContext } from '@/context/AuthContext'
import type { AuthUser } from '@/types'

// vi.mock factories must not reference outer variables — use inline values
vi.mock('@/api/admin', () => ({
  adminApi: {
    listDepartments: vi.fn().mockResolvedValue({
      data: [{ id: 1, name: 'Engineering', is_active: true }],
    }),
    listManagers: vi.fn().mockResolvedValue({
      data: [{ id: 2, display_name: 'Jane Manager', role: 'it_manager' }],
    }),
  },
}))

vi.mock('@/api/tickets', () => ({
  ticketsApi: {
    create: vi.fn().mockResolvedValue({
      data: { id: 1, ticket_id: 'TKT-001', status: 'Pending' },
    }),
  },
}))

vi.mock('@/api/attachments', () => ({
  attachmentsApi: {
    upload: vi.fn().mockResolvedValue({ data: {} }),
  },
}))

const mockUser: AuthUser = {
  id: 1, email: 'u@e.com', display_name: 'User',
  role: 'business_user', department_id: 1, department_name: 'Engineering',
}

function renderPage() {
  return render(
    <AuthContext.Provider value={{ user: mockUser, loading: false, login: vi.fn(), logout: vi.fn() }}>
      <MemoryRouter>
        <SubmitTicketPage />
      </MemoryRouter>
    </AuthContext.Provider>
  )
}

describe('SubmitTicketPage', () => {
  beforeEach(() => { vi.clearAllMocks() })

  it('shows error when title is empty on submit', async () => {
    renderPage()
    await waitFor(() => screen.getByLabelText(/title/i))
    fireEvent.click(screen.getByRole('button', { name: /submit request/i }))
    await waitFor(() => {
      expect(screen.getByText(/title is required/i)).toBeInTheDocument()
    })
  })

  it('cost field has a hint about director approval', async () => {
    renderPage()
    await waitFor(() => screen.getByLabelText(/cost/i))
    // Use getAllByText since the hint may appear in multiple places
    const hints = screen.getAllByText(/director approval/i)
    expect(hints.length).toBeGreaterThan(0)
  })

  it('urgency field has a hint about director approval for High/Critical', async () => {
    renderPage()
    await waitFor(() => screen.getByLabelText(/urgency/i))
    // Check the hint text exists somewhere on the page
    expect(
      screen.getByText(/high or critical urgency requires director/i)
    ).toBeInTheDocument()
  })

  it('shows error when file exceeds 10MB', async () => {
    renderPage()
    await waitFor(() => screen.getByLabelText(/attachments/i))

    const bigFile = new File(['x'.repeat(100)], 'big.pdf', { type: 'application/pdf' })
    Object.defineProperty(bigFile, 'size', { value: 11 * 1024 * 1024 })

    const input = screen.getByLabelText(/attachments/i)
    fireEvent.change(input, { target: { files: [bigFile] } })
    fireEvent.click(screen.getByRole('button', { name: /submit request/i }))

    await waitFor(() => {
      expect(screen.getByText(/exceeds the 10 mb limit/i)).toBeInTheDocument()
    })
  })
})
