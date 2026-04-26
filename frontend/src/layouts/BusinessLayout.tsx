/**
 * BusinessLayout — shell for the Business Requester portal.
 * Navigation: My Requests | Submit Request | Approvals (if manager)
 */

import { Link, NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'
import { usePermissions } from '@/hooks/usePermissions'
import { NotificationBell } from '@/components/NotificationBell'

export function BusinessLayout() {
  const { user, logout } = useAuth()
  const perms = usePermissions()

  return (
    <div className="layout business-layout">
      <header className="layout-header">
        <Link to="/portal" className="logo">
          IT Request Portal
        </Link>
        <nav aria-label="Business portal navigation">
          <NavLink to="/portal/tickets">My Requests</NavLink>
          <NavLink to="/portal/tickets/new">Submit Request</NavLink>
          {perms.canApprove && (
            <NavLink to="/portal/approvals">Approvals</NavLink>
          )}
        </nav>
        <div className="header-actions">
          <NotificationBell />
          <span className="user-name">{user?.display_name}</span>
          <button onClick={logout}>Sign out</button>
        </div>
      </header>

      <main className="layout-main">
        <Outlet />
      </main>

      <footer className="layout-footer">
        Internal Ticketing Portal — PoC
      </footer>
    </div>
  )
}
