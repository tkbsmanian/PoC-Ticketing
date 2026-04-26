/**
 * ITLayout — shell for the IT Operations portal.
 * Navigation: Queue | Dashboard | Admin (platform_admin only)
 */

import { Link, NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'
import { usePermissions } from '@/hooks/usePermissions'
import { NotificationBell } from '@/components/NotificationBell'

export function ITLayout() {
  const { user, logout } = useAuth()
  const perms = usePermissions()

  return (
    <div className="layout it-layout">
      <header className="layout-header it-header">
        <Link to="/it" className="logo">
          IT Operations Portal
        </Link>
        <nav aria-label="IT portal navigation">
          <NavLink to="/it/tickets">Ticket Queue</NavLink>
          <NavLink to="/it/dashboard">Dashboard</NavLink>
          {perms.canViewAuditLog && (
            <NavLink to="/it/audit">Audit Log</NavLink>
          )}
          {perms.isAdmin && (
            <NavLink to="/it/admin">Admin</NavLink>
          )}
        </nav>
        <div className="header-actions">
          <NotificationBell />
          <span className="user-name">{user?.display_name}</span>
          <span className="role-badge">{user?.role}</span>
          <button onClick={logout}>Sign out</button>
        </div>
      </header>

      <main className="layout-main">
        <Outlet />
      </main>

      <footer className="layout-footer">
        IT Operations Portal — PoC
      </footer>
    </div>
  )
}
