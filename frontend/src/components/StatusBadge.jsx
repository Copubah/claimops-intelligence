const toneByValue = {
  HEALTHY: 'success',
  COMPLETE: 'success',
  APPROVED: 'success',
  WATCH: 'warning',
  PENDING: 'warning',
  INCOMPLETE: 'warning',
  AT_RISK: 'danger',
  BREACHED: 'danger',
  ESCALATED: 'danger',
  REJECTED: 'danger',
}

export function StatusBadge({ value }) {
  const normalized = String(value || 'Unknown').toUpperCase().replaceAll(' ', '_')
  const label = normalized.replaceAll('_', ' ')
  return <span className={`status-badge status-${toneByValue[normalized] || 'neutral'}`}>{label}</span>
}

