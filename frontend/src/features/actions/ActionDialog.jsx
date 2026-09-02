import { useState } from 'react'
import { Icon } from '../../components/Icon.jsx'
import { executeClaimAction } from '../../services/claims.js'

const actions = [
  ['ASSIGN', 'Assign'], ['REASSIGN', 'Reassign'], ['ESCALATE', 'Escalate'],
  ['REQUEST_DOCUMENTS', 'Request documents'], ['ADD_FOLLOW_UP', 'Add follow-up'],
  ['ADD_NOTE', 'Add note'], ['RESOLVE', 'Resolve'], ['MARK_REVIEWED', 'Mark reviewed'],
]
const agents = ['Agent Amina', 'Agent Baraka', 'Agent Chao', 'Agent Deka', 'Agent Eshe', 'Agent Femi', 'Agent Gita', 'Agent Hamisi']

const suggestedAction = {
  Assign: 'ASSIGN',
  Escalate: 'ESCALATE',
  'Request documents': 'REQUEST_DOCUMENTS',
  'Add follow-up': 'ADD_FOLLOW_UP',
  'Mark reviewed': 'MARK_REVIEWED',
}

export function ActionDialog({ item, onClose, onCompleted }) {
  const [action, setAction] = useState(suggestedAction[item.recommended_action] || 'ADD_NOTE')
  const [owner, setOwner] = useState(item.owner || agents[0])
  const [note, setNote] = useState('')
  const [documents, setDocuments] = useState(item.issue.startsWith('Missing ') ? item.issue.replace('Missing ', '') : '')
  const [resolution, setResolution] = useState('Approved')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)

  async function submit(event) {
    event.preventDefault()
    setSubmitting(true)
    setError(null)
    const command = { action, expected_version: item.version }
    if (['ASSIGN', 'REASSIGN'].includes(action)) command.owner = owner
    if (action === 'REQUEST_DOCUMENTS') command.documents = documents.split(',').map((value) => value.trim()).filter(Boolean)
    if (['ADD_NOTE', 'ADD_FOLLOW_UP'].includes(action)) command.note = note
    if (action === 'RESOLVE') command.resolution = resolution
    try {
      const result = await executeClaimAction(item.claim_id, command)
      onCompleted(result)
    } catch (requestError) {
      setError(requestError.message)
      setSubmitting(false)
    }
  }

  return (
    <div className="action-dialog-layer">
      <button className="drawer-backdrop" type="button" onClick={onClose} aria-label="Close action dialog" />
      <section className="action-dialog" role="dialog" aria-modal="true" aria-labelledby="action-dialog-title">
        <header><div><p className="eyebrow">Authorized claim action</p><h2 id="action-dialog-title">{item.claim_id}</h2></div><button className="icon-button" type="button" onClick={onClose} aria-label="Close"><Icon name="close" /></button></header>
        <form onSubmit={submit}>
          <div className="action-context"><span>{item.issue}</span><strong>Version {item.version}</strong></div>
          <label className="action-field"><span>Action</span><select value={action} onChange={(event) => setAction(event.target.value)}>{actions.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
          {['ASSIGN', 'REASSIGN'].includes(action) && <label className="action-field"><span>New owner</span><select value={owner} onChange={(event) => setOwner(event.target.value)}>{agents.map((agent) => <option key={agent}>{agent}</option>)}</select></label>}
          {action === 'REQUEST_DOCUMENTS' && <label className="action-field"><span>Required documents</span><input value={documents} onChange={(event) => setDocuments(event.target.value)} placeholder="Invoice, Claim form" required /></label>}
          {['ADD_NOTE', 'ADD_FOLLOW_UP'].includes(action) && <label className="action-field"><span>{action === 'ADD_NOTE' ? 'Note' : 'Follow-up'}</span><textarea value={note} onChange={(event) => setNote(event.target.value)} maxLength="500" required placeholder="Add concise operational context" /></label>}
          {action === 'RESOLVE' && <label className="action-field"><span>Resolution</span><select value={resolution} onChange={(event) => setResolution(event.target.value)}><option>Approved</option><option>Rejected</option><option>Closed</option></select></label>}
          <div className="action-audit-note"><Icon name="shield" size={17} /><span>This action updates the claim and creates an audit event as <strong>manager@example.test</strong>.</span></div>
          {error && <p className="action-error" role="alert">{error}</p>}
          <footer><button type="button" className="filter-reset" onClick={onClose}>Cancel</button><button type="submit" className="filter-submit" disabled={submitting}>{submitting ? 'Applying…' : 'Confirm action'}</button></footer>
        </form>
      </section>
    </div>
  )
}

