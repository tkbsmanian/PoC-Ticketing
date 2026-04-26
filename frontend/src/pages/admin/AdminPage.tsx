/**
 * Platform Admin configuration screen.
 * Tabs: Users | Departments | Audit Log | System Health
 */

import { useState } from 'react'
import { UserManagement } from './UserManagement'
import { DepartmentManagement } from './DepartmentManagement'
import { AuditLogView } from './AuditLogView'

type Tab = 'users' | 'departments' | 'audit'

export function AdminPage() {
  const [tab, setTab] = useState<Tab>('users')

  return (
    <div className="admin-page">
      <h1>Platform Administration</h1>

      <div className="tab-bar" role="tablist" aria-label="Admin sections">
        {(['users', 'departments', 'audit'] as Tab[]).map((t) => (
          <button
            key={t}
            role="tab"
            aria-selected={tab === t}
            aria-controls={`tab-panel-${t}`}
            onClick={() => setTab(t)}
            className={tab === t ? 'tab-active' : ''}
          >
            {t.charAt(0).toUpperCase() + t.slice(1)}
          </button>
        ))}
      </div>

      <div id={`tab-panel-${tab}`} role="tabpanel">
        {tab === 'users' && <UserManagement />}
        {tab === 'departments' && <DepartmentManagement />}
        {tab === 'audit' && <AuditLogView />}
      </div>
    </div>
  )
}
