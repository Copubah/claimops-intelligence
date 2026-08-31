import { Link } from 'react-router-dom'

export function NotFoundPage() {
  return (
    <div className="not-found">
      <p className="eyebrow">404</p>
      <h1>Workspace not found</h1>
      <p>The requested ClaimOps route does not exist.</p>
      <Link to="/" className="primary-link">Return to overview</Link>
    </div>
  )
}

