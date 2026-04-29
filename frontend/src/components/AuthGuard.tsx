/**
 * AuthGuard — redirects unauthenticated users to /login.
 * Optionally restricts to specific roles.
 */

import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'
import type { UserRole } from '@/types'

interface Props {
  children: React.ReactNode
  allowedRoles?: UserRole[]
}

export function AuthGuard({ children, allowedRoles }: Props) {
  const { user, loading } = useAuth()
  const location = useLocation()

  // Don't redirect if already on login page
  if (location.pathname === '/login') {
    return <>{children}</>
  }

  if (loading) {
    return <div className="loading-screen">Loading…</div>
  }

  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  if (allowedRoles && !allowedRoles.includes(user.role as UserRole)) {
    return <Navigate to="/403" replace />
  }

  return <>{children}</>
}
