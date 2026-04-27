import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { AuthGuard } from '@/components/AuthGuard'
import { AuthContext } from '@/context/AuthContext'
import type { AuthUser } from '@/types'

function renderWithAuth(user: AuthUser | null, loading = false) {
  return render(
    <AuthContext.Provider value={{ user, loading, login: vi.fn(), logout: vi.fn() }}>
      <MemoryRouter initialEntries={['/protected']}>
        <Routes>
          <Route path="/login" element={<div>Login Page</div>} />
          <Route path="/403" element={<div>Forbidden</div>} />
          <Route
            path="/protected"
            element={
              <AuthGuard>
                <div>Protected Content</div>
              </AuthGuard>
            }
          />
        </Routes>
      </MemoryRouter>
    </AuthContext.Provider>
  )
}

const mockUser: AuthUser = {
  id: 1,
  email: 'user@example.com',
  display_name: 'User',
  role: 'business_user',
  department_id: 1,
  department_name: 'IT',
}

describe('AuthGuard', () => {
  it('redirects unauthenticated user to /login', () => {
    renderWithAuth(null)
    expect(screen.getByText('Login Page')).toBeInTheDocument()
  })

  it('shows loading state while auth is resolving', () => {
    renderWithAuth(null, true)
    expect(screen.getByText(/loading/i)).toBeInTheDocument()
  })

  it('renders children for authenticated user', () => {
    renderWithAuth(mockUser)
    expect(screen.getByText('Protected Content')).toBeInTheDocument()
  })

  it('redirects to /403 when role not allowed', () => {
    render(
      <AuthContext.Provider value={{ user: mockUser, loading: false, login: vi.fn(), logout: vi.fn() }}>
        <MemoryRouter initialEntries={['/admin']}>
          <Routes>
            <Route path="/403" element={<div>Forbidden</div>} />
            <Route
              path="/admin"
              element={
                <AuthGuard allowedRoles={['platform_admin']}>
                  <div>Admin Content</div>
                </AuthGuard>
              }
            />
          </Routes>
        </MemoryRouter>
      </AuthContext.Provider>
    )
    expect(screen.getByText('Forbidden')).toBeInTheDocument()
  })
})
