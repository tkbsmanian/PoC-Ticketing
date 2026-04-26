/**
 * usePermissions — single source of truth for role-based UI rendering.
 * Never compare role strings inline in components — use this hook.
 */

import { useAuth } from './useAuth'
import type { UserRole } from '@/types'

export function usePermissions() {
  const { user } = useAuth()
  const role = user?.role as UserRole | undefined

  return {
    // Ticket actions
    canSubmitTicket: role !== 'auditor',
    canViewAllTickets: role === 'it_triage' || role === 'platform_admin' || role === 'auditor',
    canViewDeptTickets: role === 'it_manager' || role === 'it_triage' || role === 'platform_admin' || role === 'auditor',
    canUpdateStatus: role === 'it_triage' || role === 'platform_admin',
    canUpdateCategoryPriority: role === 'it_triage' || role === 'platform_admin',
    canSoftDelete: role === 'platform_admin',
    canApprove: role === 'it_manager',

    // Comments
    canAddInternalComment: role === 'it_triage' || role === 'platform_admin',
    canViewInternalComments: role === 'it_triage' || role === 'platform_admin' || role === 'auditor',

    // Admin
    canManageUsers: role === 'platform_admin',
    canManageDepartments: role === 'platform_admin',
    canViewAuditLog: role === 'platform_admin' || role === 'auditor',
    canViewSyncHealth: role === 'it_triage' || role === 'platform_admin' || role === 'auditor',
    canViewSystemHealth: role === 'platform_admin',

    // Portal routing
    isBusinessUser: role === 'business_user',
    isITRole: role === 'it_triage' || role === 'it_manager' || role === 'platform_admin' || role === 'auditor',
    isAdmin: role === 'platform_admin',
  }
}
