import { useEffect, useState } from 'react'
import { Icon } from '../../components/Icon.jsx'
import { StatusBadge } from '../../components/StatusBadge.jsx'
import { getClaim } from '../../services/claims.js'

const dateFormatter = new Intl.DateTimeFormat('en-KE', { dateStyle: 'medium', timeStyle: 'short', timeZone: 'Africa/Nairobi' })
const moneyFormatter = new Intl.NumberFormat('en-KE', { style: 'currency', currency: 'KES', maximumFractionDigits: 0 })

export function ClaimDetailDrawer({ claimId, onClose }) {
  const [state, setState] = useState({ claimId: null, data: null, error: null })

  useEffect(() => {
    if (!claimId) return undefined
    const controller = new AbortController()
    getClaim(claimId, { signal: controller.signal })
      .then((data) => setState({ claimId, data, error: null }))
      .catch((error) => {
        if (error.name !== 'AbortError') setState({ claimId, data: null, error })
      })
    const closeOnEscape = (event) => {
      if (event.key === 'Escape') onClose()
    }
    const previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    window.addEventListener('keydown', closeOnEscape)
    return () => {
      controller.abort()
      document.body.style.overflow = previousOverflow
      window.removeEventListener('keydown', closeOnEscape)
    }
  }, [claimId, onClose])

  if (!claimId) return null
  const loading = state.claimId !== claimId
  const claim = loading ? null : state.data
  const error = loading ? null : state.error

  return (
    <div className="drawer-layer" role="presentation">
      <button className="drawer-backdrop" type="button" onClick={onClose} aria-label="Close claim details" />
      <aside className="claim-drawer" role="dialog" aria-modal="true" aria-labelledby="claim-drawer-title">
        <header className="drawer-header">
          <div><p className="eyebrow">Claim inspection</p><h2 id="claim-drawer-title">{claimId}</h2></div>
          <button className="icon-button" type="button" onClick={onClose} aria-label="Close claim details"><Icon name="close" /></button>
        </header>
        {loading && <DrawerState copy="Loading claim details…" />}
        {error && <DrawerState copy={error.message} error />}
        {claim && <ClaimDetails claim={claim} />}
      </aside>
    </div>
  )
}

function ClaimDetails({ claim }) {
  return (
    <div className="drawer-body">
      <div className="drawer-status-row"><StatusBadge value={claim.status} /><StatusBadge value={claim.sla_status} /><StatusBadge value={claim.documentation_status} /></div>
      <section className="detail-section">
        <h3>Claim summary</h3>
        <dl className="detail-grid">
          <Detail label="Partner" value={claim.partner} />
          <Detail label="Product" value={claim.product} />
          <Detail label="Claim type" value={claim.claim_type} />
          <Detail label="Amount" value={moneyFormatter.format(claim.amount)} />
          <Detail label="Current stage" value={claim.stage} />
          <Detail label="Owner" value={claim.assigned_agent || 'Unassigned'} />
          <Detail label="Created" value={dateFormatter.format(new Date(claim.created_at))} />
          <Detail label="SLA deadline" value={dateFormatter.format(new Date(claim.sla_deadline))} />
        </dl>
      </section>
      <section className="detail-section">
        <div className="detail-section-heading"><h3>Document readiness</h3><StatusBadge value={claim.documentation_status} /></div>
        <DocumentList title="Submitted" items={claim.submitted_documents} complete />
        <DocumentList title="Missing" items={claim.missing_documents} />
      </section>
      <section className="detail-section">
        <div className="detail-section-heading"><h3>Risk review</h3><strong className="risk-score">{claim.risk_score}/100</strong></div>
        <p className="risk-recommendation">{claim.risk_recommendation.replaceAll('_', ' ')}</p>
        {claim.risk_signals.length ? (
          <ul className="risk-list">{claim.risk_signals.map((signal) => <li key={signal.rule_id}><span>{signal.explanation}</span><strong>+{signal.points}</strong></li>)}</ul>
        ) : <p className="empty-detail">No additional risk signals identified.</p>}
      </section>
      <section className="detail-section">
        <h3>Quality and outcome</h3>
        <dl className="detail-grid">
          <Detail label="QA score" value={claim.qa_score == null ? 'Not sampled' : `${claim.qa_score}%`} />
          <Detail label="Approval status" value={claim.approval_status.replaceAll('_', ' ')} />
          <Detail label="Turnaround time" value={claim.tat_hours == null ? 'In progress' : `${claim.tat_hours} hours`} />
          <Detail label="Facility" value={claim.facility} />
        </dl>
      </section>
      <p className="drawer-disclaimer">Synthetic record. No real customer information is displayed.</p>
    </div>
  )
}

function Detail({ label, value }) {
  return <div><dt>{label}</dt><dd>{value}</dd></div>
}

function DocumentList({ title, items, complete = false }) {
  return (
    <div className="document-group">
      <p>{title} <span>{items.length}</span></p>
      {items.length ? <ul>{items.map((item) => <li key={item} className={complete ? 'document-complete' : 'document-missing'}><span aria-hidden="true">{complete ? '✓' : '!'}</span>{item}</li>)}</ul> : <span className="empty-detail">None</span>}
    </div>
  )
}

function DrawerState({ copy, error = false }) {
  return <div className={`drawer-state ${error ? 'is-error' : ''}`} role={error ? 'alert' : 'status'}>{copy}</div>
}

