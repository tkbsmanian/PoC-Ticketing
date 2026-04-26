/**
 * App — root router.
 *
 * Route structure:
 *   /login                          → LoginPage (public)
 *   /forgot-password                → PasswordResetPage (public)
 *   /portal/*                       → BusinessLayout (business_user, it_manager)
 *     /portal/tickets               → BusinessTicketListPage
 *     /portal/tickets/new           → SubmitTicketPage
 *     /portal/tickets/:id           → TicketDetailPage
 *     /portal/approvals             → ApprovalQueuePage (it_manager only)
 *   /it/*                           → ITLayout (it_triage, it_manager, platform_admin, auditor)
 *     /it/tickets                   → ITTicketListPage
 *     /it/tickets/:id               → TicketDetailPage
 *     /it/dashboard                 → DashboardPage
 *     /it/audit                     → AuditLogView (platform_admin, auditor)
 *     /it/admin                     → AdminPage (platform_admin only)
 *   /403                            → ForbiddenPage
 *   /                               → redirect based on role
 */

import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { AuthProvider } from '@/context/AuthContext'
import { AuthGuard } from '@/components/AuthGuard'

import { LoginPage } from '@/pages/LoginPage'
import { BusinessLayout } from '@/layouts/BusinessLayout'
import { ITLayout } from '@/layouts/ITLayout'
import { BusinessTicketListPage } from '@/pages/business/TicketListPage'
import { SubmitTicketPage } from '@/pages/business/SubmitTicketPage'
import { TicketDetailPage } from '@/pages/shared/TicketDetailPage'
import { ITTicketListPage } from '@/pages/it/ITTicketListPage'
import { DashboardPage } from '@/pages/it/DashboardPage'
import { AdminPage } from '@/pages/admin/AdminPage'
import { AuditLogView } from '@/pages/admin/AuditLogView'
import { ForbiddenPage } from '@/pages/shared/ForbiddenPage'

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* Public */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/403" element={<ForbiddenPage />} />

          {/* Business portal */}
          <Route
            path="/portal"
            element={
              <AuthGuard allowedRoles={['business_user', 'it_manager']}>
                <BusinessLayout />
              </AuthGuard>
            }
          >
            <Route index element={<Navigate to="tickets" replace />} />
            <Route path="tickets" element={<BusinessTicketListPage />} />
            <Route path="tickets/new" element={<SubmitTicketPage />} />
            <Route path="tickets/:id" element={<TicketDetailPage />} />
          </Route>

          {/* IT Operations portal */}
          <Route
            path="/it"
            element={
              <AuthGuard allowedRoles={['it_triage', 'it_manager', 'platform_admin', 'auditor']}>
                <ITLayout />
              </AuthGuard>
            }
          >
            <Route index element={<Navigate to="tickets" replace />} />
            <Route path="tickets" element={<ITTicketListPage />} />
            <Route path="tickets/:id" element={<TicketDetailPage />} />
            <Route path="dashboard" element={<DashboardPage />} />
            <Route
              path="audit"
              element={
                <AuthGuard allowedRoles={['platform_admin', 'auditor']}>
                  <AuditLogView />
                </AuthGuard>
              }
            />
            <Route
              path="admin"
              element={
                <AuthGuard allowedRoles={['platform_admin']}>
                  <AdminPage />
                </AuthGuard>
              }
            />
          </Route>

          {/* Root redirect */}
          <Route path="/" element={<Navigate to="/login" replace />} />
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}
