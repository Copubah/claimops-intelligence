const tones = {
  neutral: 'metric-neutral',
  positive: 'metric-positive',
  warning: 'metric-warning',
  critical: 'metric-critical',
}

export function MetricCard({ label, value, detail, tone = 'neutral', prominent = false }) {
  return (
    <article className={`metric-card ${tones[tone]} ${prominent ? 'is-prominent' : ''}`}>
      <div className="metric-topline">
        <span className="metric-label">{label}</span>
        <span className="metric-indicator" aria-hidden="true" />
      </div>
      <strong className="metric-value">{value}</strong>
      <span className="metric-detail">{detail}</span>
    </article>
  )
}

