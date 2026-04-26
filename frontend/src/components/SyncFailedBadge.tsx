interface Props {
  visible: boolean
}

export function SyncFailedBadge({ visible }: Props) {
  if (!visible) return null
  return (
    <span
      className="sync-failed-badge"
      title="JIRA sync failed — contact Platform Admin"
      aria-label="JIRA sync failed"
    >
      ⚠ JIRA Sync Failed
    </span>
  )
}
