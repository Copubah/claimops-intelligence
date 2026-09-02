import { useMemo, useState } from 'react'
import { Icon } from '../components/Icon.jsx'
import { StatusBadge } from '../components/StatusBadge.jsx'
import { useSla } from '../hooks/useSla.js'

const states = ['ALL', 'BREACHED', 'AT_RISK', 'WATCH', 'HEALTHY']
const formatter = new Intl.DateTimeFormat('en-KE', { dateStyle: 'medium', timeStyle: 'short', timeZone: 'Africa/Nairobi' })

export function SlaControlTowerPage() {
  const [status, setStatus] = useState('ALL')
  const [partner, setPartner] = useState('')
  const filters = useMemo(() => ({ status, partner, limit: 100 }), [status, partner])
  const { data, error, loading } = useSla(filters)
  const summary = data?.summary || {}

  return <div className="page-stack sla-page">
    <header className="page-heading"><div><p className="eyebrow">Service-level monitoring</p><h1>SLA Control Tower</h1><p className="page-description">See current exposure, approaching deadlines, and the operational stage responsible for every delay.</p></div>{data && <div className="sla-evaluated"><span>Live evaluation</span><strong>{formatter.format(new Date(data.evaluated_at))}</strong></div>}</header>
    <section className="sla-summary" aria-label="SLA summary">
      <SlaCard label="Open claims" value={data?.total_open} tone="neutral" />
      <SlaCard label="Healthy" value={summary.healthy} tone="healthy" />
      <SlaCard label="Watch" value={summary.watch} tone="watch" />
      <SlaCard label="At risk" value={summary.at_risk} tone="risk" />
      <SlaCard label="Breached" value={summary.breached} tone="breached" />
    </section>
    <section className="sla-panel" aria-busy={loading}>
      <header className="sla-panel-header"><div><h2>Deadline exposure</h2><p>{data ? `${data.total_matching} matching claims · at risk below ${data.thresholds.at_risk_minutes}m · watch through ${data.thresholds.watch_minutes}m` : 'Evaluating open claims…'}</p></div><div className="sla-controls"><label><span>Partner</span><input value={partner} onChange={(event) => setPartner(event.target.value)} placeholder="All partners" /></label><div className="priority-tabs" aria-label="Filter SLA status">{states.map((value) => <button key={value} type="button" className={status === value ? 'is-active' : ''} onClick={() => setStatus(value)}>{value.replace('_', ' ')}</button>)}</div></div></header>
      {error && <div className="claims-error" role="alert"><strong>Unable to load SLA exposure</strong><span>{error.message}</span></div>}
      {!error && loading && <div className="claims-skeleton" role="status"><span /><span /><span /><span /><span /></div>}
      {!error && !loading && !data?.items.length && <div className="claims-empty"><Icon name="check" size={24} /><strong>No matching open claims</strong><span>Change the status or partner filter.</span></div>}
      {!error && !loading && data?.items.length > 0 && <div className="sla-table-wrap"><table className="sla-table"><thead><tr><th>Status</th><th>Claim</th><th>Time position</th><th>Deadline</th><th>Delay stage</th><th>Assigned agent</th><th>Partner</th></tr></thead><tbody>{data.items.map((item) => <tr key={item.claim_id}><td data-label="Status"><StatusBadge value={item.status} /></td><td data-label="Claim"><strong>{item.claim_id}</strong></td><td data-label="Time position"><strong className={item.status === 'BREACHED' ? 'sla-time-breached' : ''}>{item.status === 'BREACHED' ? `${duration(item.breached_by_seconds)} overdue` : `${duration(item.remaining_seconds)} remaining`}</strong></td><td data-label="Deadline">{item.deadline ? formatter.format(new Date(item.deadline)) : 'Not set'}</td><td data-label="Delay stage"><span className="sla-stage">{item.stage}</span></td><td data-label="Assigned agent">{item.assigned_agent || <span className="unassigned-text">Unassigned</span>}</td><td data-label="Partner">{item.partner}</td></tr>)}</tbody></table></div>}
    </section>
  </div>
}

function SlaCard({ label, value, tone }) { return <article className={`sla-card sla-card-${tone}`}><span>{label}</span><strong>{value === undefined ? '—' : value.toLocaleString('en-KE')}</strong></article> }
function duration(seconds) { const minutes = Math.floor(seconds / 60); const days = Math.floor(minutes / 1440); const hours = Math.floor((minutes % 1440) / 60); const mins = minutes % 60; return days ? `${days}d ${hours}h` : hours ? `${hours}h ${mins}m` : `${mins}m` }
