import { describe, expect, it, vi } from 'vitest'
import { renderHook } from '@testing-library/react'
import { usePermissions } from '@/hooks/usePermissions'
import type { AuthUser } from '@/types'

// Mock useAuth to inject a specific user
vi.mock('@/hooks/useAuth', () => ({
  useAuth: vi.fn(),
}))

import { useAuth } from '@/hooks/useAuth'

function mockUser(role: AuthUser['role']): AuthUser {
  return { id: 1, email: 'test@example.com', display_name: 'Test', role, department_id: null, department_name: null }
}

describe('usePermissions', () => {
  it('business_user cannot update status', () => {
    vi.mocked(useAuth).mockReturnValue({ user: mockUser('business_user'), loading: false, login: vi.fn(), logout: vi.fn() })
    const { result } = renderHook(() => usePermissions())
    expect(result.current.canUpdateStatus).toBe(false)
  })

  it('it_triage can update status', () => {
    vi.mocked(useAuth).mockReturnValue({ user: mockUser('it_triage'), loading: false, login: vi.fn(), logout: vi.fn() })
    const { result } = renderHook(() => usePermissions())
    expect(result.current.canUpdateStatus).toBe(true)
  })

  it('auditor cannot submit tickets', () => {
    vi.mocked(useAuth).mockReturnValue({ user: mockUser('auditor'), loading: false, login: vi.fn(), logout: vi.fn() })
    const { result } = renderHook(() => usePermissions())
    expect(result.current.canSubmitTicket).toBe(false)
  })

  it('platform_admin can soft delete', () => {
    vi.mocked(useAuth).mockReturnValue({ user: mockUser('platform_admin'), loading: false, login: vi.fn(), logout: vi.fn() })
    const { result } = renderHook(() => usePermissions())
    expect(result.current.canSoftDelete).toBe(true)
  })

  it('business_user cannot view internal comments', () => {
    vi.mocked(useAuth).mockReturnValue({ user: mockUser('business_user'), loading: false, login: vi.fn(), logout: vi.fn() })
    const { result } = renderHook(() => usePermissions())
    expect(result.current.canViewInternalComments).toBe(false)
  })
})
