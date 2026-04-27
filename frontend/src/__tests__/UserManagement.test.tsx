import { describe, expect, it, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { UserManagement } from '@/pages/admin/UserManagement'
import { AuthContext } from '@/context/AuthContext'
import type { AuthUser } from '@/types'

const mockUpdateUser = vi.fn().mockResolvedValue({ data: {} })
const mockCreateUser = vi.fn().mockResolvedValue({
  data: { id: 99, email: 'new@e.com', display_name: 'New', role: 'business_user', department_name: 'IT', is_active: true },
})

vi.mock('@/api/admin', () => ({
  adminApi: {
    listUsers: vi.fn().mockResolvedValue({
      data: [
        { id: 1, email: 'active@e.com', display_name: 'Active User', role: 'business_user', department_name: 'IT', is_active: true },
      ],
    }),
    listDepartments: vi.fn().mockResolvedValue({
      data: [{ id: 1, name: 'IT', is_active: true }],
    }),
    createUser: mockCreateUser,
    updateUser: mockUpdateUser,
  },
}))

const adminUser: AuthUser = {
  id: 1, email: 'admin@e.com', display_name: 'Admin',
  role: 'platform_admin', department_id: 1, department_name: 'IT',
}

function renderUserMgmt() {
  return render(
    <AuthContext.Provider value={{ user: adminUser, loading: false, login: vi.fn(), logout: vi.fn() }}>
      <MemoryRouter>
        <UserManagement />
      </MemoryRouter>
    </AuthContext.Provider>
  )
}

describe('UserManagement', () => {
  beforeEach(() => vi.clearAllMocks())

  it('lists existing users', async () => {
    renderUserMgmt()
    await waitFor(() => {
      expect(screen.getByText('Active User')).toBeInTheDocument()
    })
  })

  it('deactivate button calls updateUser with is_active false', async () => {
    renderUserMgmt()
    await waitFor(() => screen.getByText('Deactivate'))
    fireEvent.click(screen.getByText('Deactivate'))
    await waitFor(() => {
      expect(mockUpdateUser).toHaveBeenCalledWith(1, { is_active: false })
    })
  })

  it('shows create user form when Add User clicked', async () => {
    renderUserMgmt()
    await waitFor(() => screen.getByText(/\+ add user/i))
    fireEvent.click(screen.getByText(/\+ add user/i))
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/display name/i)).toBeInTheDocument()
  })

  it('create user form requires email', async () => {
    renderUserMgmt()
    await waitFor(() => screen.getByText(/\+ add user/i))
    fireEvent.click(screen.getByText(/\+ add user/i))

    // Submit without filling email — HTML5 validation prevents submission
    const emailInput = screen.getByLabelText(/email/i)
    expect(emailInput).toBeRequired()
  })
})
