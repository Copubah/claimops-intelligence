import { useState } from 'react'
import { Icon } from '../components/Icon.jsx'
import { StatusBadge } from '../components/StatusBadge.jsx'
import { ActionDialog } from '../features/actions/ActionDialog.jsx'
import { useActions } from '../hooks/useActions.js'

const priorityOrder = ['ALL', 'CRITICAL', 'HIGH', 'MEDIUM']
const dateFormatter = new Intl.DateTimeFormat('en-KE', { dateStyle: 'medium', timeStyle: 'short', timeZone: 'Africa/Nairobi' })

export function ActionCenterPage() {
  const [refreshKey, setRefreshKey] = useState(0)
  const [priority, setPriority] = useState('ALL')
  const [selected, setSelected] = useState(null)
  const [notice, setNotice] = useState(null)
  const { data, error, loading } = useActions(refreshKey, priority)
  const items = data?.items || []

  function completed(result) {
    setSelected(null)
    setNotice(`${result.audit_event.action.replaceAll('_', ' ')} applied to ${result.claim.claim_id}. Audit event recorded.`)
    setRefreshKey((value) => value + 1)
  }

  return (
    <div className="page-stack action-center-page">
      <header className="page-heading"><div><p className="eyebrow">Prioritized work queue</p><h1>Action Center</h1><p className="page-description">Review operational exceptions, follow the recommendation, and explicitly authorize every state change.</p></div><span className="synthetic-badge">Recommendations are advisory</span></header>
      <section className="action-summary" aria-label="Action queue summary">
        <SummaryCard label="Requires action" value={data?.total ?? 0} tone="neutral" />
        <SummaryCard label="Critical" value={data?.critical ?? 0} tone="critical" />
        <SummaryCard label="High priority" value={data?.high ?? 0} tone="warning" />
        <SummaryCard label="Queue scope" value="Open claims" tone="positive" />
      </section>
      {notice && <div className="action-notice" role="status"><Icon name="check" size={18} /><span>{notice}</span><button type="button" onClick={() => setNotice(null)} aria-label="Dismiss"><Icon name="close" size={15} /></button></div>}
      <section className="action-queue-panel" aria-busy={loading}>
        <header className="action-queue-header"><div><h2>Prioritized queue</h2><p>{loading ? 'Evaluating operational exceptions…' : `${items.length} shown of ${data?.total ?? 0} action items`}</p></div><div className="priority-tabs" aria-label="Filter by priority">{priorityOrder.map((value) => <button key={value} type="button" className={priority === value ? 'is-active' : ''} onClick={() => setPriority(value)}>{value === 'ALL' ? 'All' : value}</button>)}</div></header>
        {error && <div className="claims-error" role="alert"><strong>Unable to load the action queue</strong><span>{error.message}</span></div>}
        {!error && loading && <div className="claims-skeleton" role="status"><span /><span /><span /><span /><span /><span /></div>}
        {!error && !loading && !items.length && <div className="claims-empty"><Icon name="check" size={24} /><strong>No matching action items</strong><span>Select another priority or refresh the queue.</span></div>}
        {!error && !loading && items.length > 0 && <div className="action-table-wrap"><table className="action-table"><thead><tr><th>Priority</th><th>Claim</th><th>Issue</th><th>Stage</th><th>Age</th><th>SLA deadline</th><th>Owner</th><th>Partner</th><th>Recommendation</th></tr></thead><tbody>{items.map((item) => <ActionRow key={item.claim_id} item={item} onAction={setSelected} />)}</tbody></table></div>}
      </section>
      {selected && <ActionDialog item={selected} onClose={() => setSelected(null)} onCompleted={completed} />}
    </div>
  )
}

function ActionRow({ item, onAction }) {
  return <tr><td data-label="Priority"><span className={`priority-pill priority-${item.priority.toLowerCase()}`}>{item.priority}</span></td><td data-label="Claim"><strong>{item.claim_id}</strong><span>{item.partner}</span></td><td data-label="Issue">{item.issue}</td><td data-label="Stage">{item.stage}</td><td data-label="Age">{formatAge(item.age_hours)}</td><td data-label="SLA deadline"><StatusBadge value={item.sla_status} /><span>{dateFormatter.format(new Date(item.sla_deadline))}</span></td><td data-label="Owner">{item.owner || <span className="unassigned-text">Unassigned</span>}</td><td data-label="Partner">{item.partner}</td><td data-label="Recommendation"><button className="recommendation-button" type="button" onClick={() => onAction(item)}>{item.recommended_action}<Icon name="chevron" size={13} /></button></td></tr>
}

function SummaryCard({ label, value, tone }) {
  return <article className={`action-summary-card action-summary-${tone}`}><span>{label}</span><strong>{typeof value === 'number' ? value.toLocaleString('en-KE') : value}</strong></article>
}

function formatAge(hours) {
  const totalHours = Math.round(hours)
  const days = Math.floor(totalHours / 24)
  const remaining = totalHours % 24
  return days ? `${days}d ${remaining}h` : `${remaining}h`
}
