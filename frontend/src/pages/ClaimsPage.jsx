import { useCallback, useState } from 'react'
import { Icon } from '../components/Icon.jsx'
import { StatusBadge } from '../components/StatusBadge.jsx'
import { ClaimDetailDrawer } from '../features/claims/ClaimDetailDrawer.jsx'
import { useClaims } from '../hooks/useClaims.js'

const partners = ['AfriCredit', 'MobiFund', 'FarmTrust', 'QuickFinance', 'Horizon Bank']
const stages = ['Submitted', 'Document Review', 'Verification', 'Assessment', 'Approval', 'Payment', 'Closed']
const statuses = ['Pending', 'In Review', 'Escalated', 'Approved', 'Rejected']
const slaStatuses = ['HEALTHY', 'WATCH', 'AT_RISK', 'BREACHED']
const documentStatuses = ['COMPLETE', 'INCOMPLETE']
const dateFormatter = new Intl.DateTimeFormat('en-KE', { day: '2-digit', month: 'short', year: 'numeric', timeZone: 'Africa/Nairobi' })
const moneyFormatter = new Intl.NumberFormat('en-KE', { style: 'currency', currency: 'KES', maximumFractionDigits: 0 })

const initialFilters = { search: '', partner: '', status: '', stage: '', sla_status: '', documentation_status: '', limit: 25 }

export function ClaimsPage() {
  const [draft, setDraft] = useState(initialFilters)
  const [filters, setFilters] = useState(initialFilters)
  const [cursor, setCursor] = useState(null)
  const [cursorHistory, setCursorHistory] = useState([])
  const [selectedClaim, setSelectedClaim] = useState(null)
  const closeDrawer = useCallback(() => setSelectedClaim(null), [])
  const { data, error, loading } = useClaims({ ...filters, cursor })

  function applyFilters(event) {
    event.preventDefault()
    setFilters(draft)
    setCursor(null)
    setCursorHistory([])
  }

  function resetFilters() {
    setDraft(initialFilters)
    setFilters(initialFilters)
    setCursor(null)
    setCursorHistory([])
  }

  function nextPage() {
    if (!data?.next_cursor) return
    setCursorHistory((history) => [...history, cursor])
    setCursor(data.next_cursor)
  }

  function previousPage() {
    setCursorHistory((history) => {
      const previous = history.at(-1) ?? null
      setCursor(previous)
      return history.slice(0, -1)
    })
  }

  const activeFilterCount = Object.entries(filters).filter(([key, value]) => key !== 'limit' && value).length
  const firstResult = data?.total ? cursorHistory.length * filters.limit + 1 : 0
  const lastResult = data ? Math.min(firstResult + data.items.length - 1, data.total) : 0

  return (
    <div className="page-stack claims-page">
      <header className="page-heading">
        <div><p className="eyebrow">Claims workspace</p><h1>Claims</h1><p className="page-description">Filter and inspect fictional claims, document readiness, service-level status, and risk context.</p></div>
        <span className="synthetic-badge">Synthetic records only</span>
      </header>

      <form className="claim-filters" onSubmit={applyFilters}>
        <div className="claim-search"><Icon name="search" size={18} /><input value={draft.search} onChange={(event) => setDraft({ ...draft, search: event.target.value })} placeholder="Search claim, partner, agent, product…" aria-label="Search claims" minLength="2" /></div>
        <FilterSelect label="Partner" value={draft.partner} options={partners} onChange={(value) => setDraft({ ...draft, partner: value })} />
        <FilterSelect label="Status" value={draft.status} options={statuses} onChange={(value) => setDraft({ ...draft, status: value })} />
        <FilterSelect label="Stage" value={draft.stage} options={stages} onChange={(value) => setDraft({ ...draft, stage: value })} />
        <FilterSelect label="SLA" value={draft.sla_status} options={slaStatuses} onChange={(value) => setDraft({ ...draft, sla_status: value })} />
        <FilterSelect label="Documents" value={draft.documentation_status} options={documentStatuses} onChange={(value) => setDraft({ ...draft, documentation_status: value })} />
        <button className="filter-submit" type="submit">Apply filters</button>
        <button className="filter-reset" type="button" onClick={resetFilters}>Reset</button>
      </form>

      <section className="claims-panel" aria-busy={loading}>
        <header className="claims-panel-header">
          <div><h2>Claim register</h2><p>{loading ? 'Loading claims…' : `${data?.total ?? 0} matching claims`}{activeFilterCount ? ` · ${activeFilterCount} active filters` : ''}</p></div>
          <span className="result-range">{data?.total ? `${firstResult}–${lastResult} of ${data.total}` : 'No results'}</span>
        </header>
        {error && <div className="claims-error" role="alert"><strong>Unable to load claims</strong><span>{error.message}. Confirm the API is running on port 8000.</span></div>}
        {!error && loading && <ClaimsSkeleton />}
        {!error && !loading && data?.items.length === 0 && <div className="claims-empty"><Icon name="file" size={24} /><strong>No claims match these filters</strong><span>Adjust or reset the filters to widen the result set.</span></div>}
        {!error && !loading && data?.items.length > 0 && (
          <div className="claims-table-wrap">
            <table className="claims-table">
              <thead><tr><th>Claim</th><th>Partner / Product</th><th>Status</th><th>Stage</th><th>SLA</th><th>Documents</th><th>Owner</th><th>Amount</th><th>Received</th></tr></thead>
              <tbody>{data.items.map((claim) => <ClaimRow key={claim.claim_id} claim={claim} onInspect={setSelectedClaim} />)}</tbody>
            </table>
          </div>
        )}
        <footer className="claims-pagination">
          <button type="button" onClick={previousPage} disabled={!cursorHistory.length}>Previous</button>
          <span>Page {cursorHistory.length + 1}</span>
          <button type="button" onClick={nextPage} disabled={!data?.next_cursor}>Next</button>
        </footer>
      </section>
      <ClaimDetailDrawer claimId={selectedClaim} onClose={closeDrawer} />
    </div>
  )
}

function ClaimRow({ claim, onInspect }) {
  return (
    <tr>
      <td data-label="Claim"><button className="claim-id-button" type="button" onClick={() => onInspect(claim.claim_id)}>{claim.claim_id}</button><span className="mobile-claim-type">{claim.claim_type}</span></td>
      <td data-label="Partner / Product"><strong>{claim.partner}</strong><span>{claim.product}</span></td>
      <td data-label="Status"><StatusBadge value={claim.status} /></td>
      <td data-label="Stage">{claim.stage}</td>
      <td data-label="SLA"><StatusBadge value={claim.sla_status} /></td>
      <td data-label="Documents"><StatusBadge value={claim.documentation_status} /><span className="document-count">{claim.documentation_status === 'COMPLETE' ? `${claim.submitted_documents.length}/${claim.required_documents.length} submitted` : `${claim.missing_documents.length} missing`}</span></td>
      <td data-label="Owner">{claim.assigned_agent || <span className="unassigned-text">Unassigned</span>}</td>
      <td data-label="Amount" className="amount-cell">{moneyFormatter.format(claim.amount)}</td>
      <td data-label="Received">{dateFormatter.format(new Date(claim.created_at))}</td>
    </tr>
  )
}

function FilterSelect({ label, value, options, onChange }) {
  return <label className="filter-select"><span>{label}</span><select value={value} onChange={(event) => onChange(event.target.value)}><option value="">All</option>{options.map((option) => <option key={option} value={option}>{option.replaceAll('_', ' ')}</option>)}</select></label>
}

function ClaimsSkeleton() {
  return <div className="claims-skeleton" role="status"><span /><span /><span /><span /><span /><span /><span /><span /></div>
}

