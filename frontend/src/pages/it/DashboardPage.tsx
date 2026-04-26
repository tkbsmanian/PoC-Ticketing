/**
 * IT Operations portal — role-scoped dashboard with ticket counts by status.
 */

import { useEffect, useState } from 'react'
import { adminApi } from '@/api/admin'
import type { DashboardCounts, SyncHealth } from '@/types'
import { usePermissions } from '@/hooks/usePermissions'

export function DashboardPage() {
  const perms = usePermissions()
  const [counts, setCounts] = useState<DashboardCounts | null>(null)
  const [health, setHealth] = useState<SyncHealth | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const promises: Promise<void>[] = [
      adminApi.dashboard().then(({ data }) => setCounts(data)),
    ]
    if (perms.canViewSyncHealth) {
      promises.push(adminApi.syncHealth().then(({ data }) => setHealth(data)))
    }
    Promise.all(promises).finally(() => setLoading(false))
  }, [perms.canViewSyncHealth])

  if (loading) return <p aria-live="polite">Loading dashboard…</p>

  return (
    <div className="dashboard-page">
      <h1>Dashboard</h1>

      {counts && (
        <section aria-labelledby="status-counts-heading">
          <h2 id="status-counts-heading">Tickets by Status</h2>
          <div className="status-counts-grid">
            {Object.entries(counts.by_status).map(([status, count]) => (
              <div key={status} className="count-card">
                <span className="count-label">{status}</span>
                <span className="count-value">{count}</span>
              </div>
            ))}
          </div>
          <p className="total-open">Total open: <strong>{counts.total_open}</strong></p>
        </section>
      )}

      {health && (
        <section aria-labelledby="sync-health-heading">
          <h2 id="sync-health-heading">JIRA Sync Health</h2>
          <dl className="sync-health">
            <dt>Adapter</dt><dd>{health.adapter}</dd>
            <dt>Last successful sync</dt>
            <dd>{health.last_success_at
              ? new Date(health.last_success_at).toLocaleString()
              : 'Never'}</dd>
            <dt>Pending events</dt><dd>{health.pending_count}</dd>
            <dt>Failed events</dt>
            <dd className={health.failed_count > 0 ? 'sync-failed-count' : ''}>
              {health.failed_count}
            </dd>
          </dl>
        </section>
      )}
    </div>
  )
}
