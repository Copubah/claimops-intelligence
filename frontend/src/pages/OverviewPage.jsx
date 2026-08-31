import { Link } from 'react-router-dom'
import {
  Bar, BarChart, CartesianGrid, Cell, Line, LineChart, Pie, PieChart,
  ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts'
import { Icon } from '../components/Icon.jsx'
import { MetricCard } from '../components/MetricCard.jsx'
import { Panel } from '../components/Panel.jsx'
import { useOverview } from '../hooks/useOverview.js'

const slaColors = {
  HEALTHY: '#3f8b69',
  WATCH: '#d39a3c',
  AT_RISK: '#d87031',
  BREACHED: '#bd4b43',
}

const formatNumber = new Intl.NumberFormat('en-KE')

function formatMetric(value, suffix = '') {
  return `${formatNumber.format(value)}${suffix}`
}

export function OverviewPage() {
  const { data, error, loading } = useOverview()

  if (loading) return <OverviewState title="Loading operations overview" copy="Calculating the synthetic portfolio snapshot…" />
  if (error) return <OverviewState title="Overview unavailable" copy={error.message} error />

  const { metrics } = data
  const primaryMetrics = [
    ['Claims received', metrics.received_today, 'Today', 'neutral'],
    ['Claims finalized', metrics.finalized_today, 'Today', 'positive'],
    ['Pending claims', metrics.pending, 'Current backlog', 'warning'],
    ['SLA at risk', metrics.sla_at_risk, 'Requires prioritization', 'warning'],
    ['SLA breached', metrics.sla_breached, 'Immediate action', 'critical'],
    ['Risk review', metrics.risk_review, 'Additional review', 'critical'],
    ['Missing documents', metrics.missing_documents, 'Open follow-ups', 'warning'],
  ]
  const secondaryMetrics = [
    ['Approved', metrics.approved, 'Finalized portfolio', 'positive'],
    ['Rejected', metrics.rejected, 'Finalized portfolio', 'neutral'],
    ['Approval rate', metrics.approval_rate, 'Of finalized claims', 'positive', '%'],
    ['Average TAT', metrics.average_tat_hours, 'Finalized claims', 'neutral', 'h'],
    ['SLA compliance', metrics.sla_compliance, 'Across portfolio', 'positive', '%'],
    ['Unassigned', metrics.unassigned, 'Open claims', 'warning'],
    ['Escalations', metrics.active_escalations, 'Currently active', 'critical'],
  ]

  return (
    <div className="page-stack overview-page">
      <header className="page-heading overview-heading">
        <div>
          <div className="heading-meta">
            <p className="eyebrow">Operations command center</p>
            <span className="synthetic-badge">Synthetic portfolio</span>
          </div>
          <h1>Claims operations overview</h1>
          <p className="page-description">Current throughput, service-level exposure, and the work requiring attention across the fictional claims portfolio.</p>
        </div>
        <div className="page-context">
          <span className="context-label">Snapshot</span>
          <button className="context-button" type="button">31 Aug 2026 <span aria-hidden="true">⌄</span></button>
        </div>
      </header>

      <section className="metric-grid primary-metrics" aria-label="Priority operational metrics">
        {primaryMetrics.map(([label, value, detail, tone]) => (
          <MetricCard key={label} label={label} value={formatMetric(value)} detail={detail} tone={tone} prominent />
        ))}
      </section>

      <section className="metric-grid secondary-metrics" aria-label="Portfolio performance metrics">
        {secondaryMetrics.map(([label, value, detail, tone, suffix]) => (
          <MetricCard key={label} label={label} value={formatMetric(value, suffix)} detail={detail} tone={tone} />
        ))}
      </section>

      <div className="dashboard-grid dashboard-grid-top">
        <Panel title="Claims throughput" subtitle="Daily received and finalized volume · last 14 days" className="panel-wide">
          <div className="chart-container" role="img" aria-label="Line chart of claims received and finalized over 14 days">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data.volume_trend} margin={{ top: 8, right: 10, left: -25, bottom: 0 }}>
                <CartesianGrid stroke="#e7ece9" strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="date" tick={{ fill: '#77837d', fontSize: 10 }} axisLine={false} tickLine={false} interval={1} />
                <YAxis tick={{ fill: '#77837d', fontSize: 10 }} axisLine={false} tickLine={false} allowDecimals={false} />
                <Tooltip contentStyle={{ border: '1px solid #dfe5e2', borderRadius: 7, fontSize: 11 }} />
                <Line type="monotone" dataKey="received" stroke="#2d765b" strokeWidth={2.2} dot={false} activeDot={{ r: 4 }} />
                <Line type="monotone" dataKey="finalized" stroke="#8aa79a" strokeWidth={2} dot={false} activeDot={{ r: 4 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <div className="chart-legend"><span><i className="legend-received" />Received</span><span><i className="legend-finalized" />Finalized</span></div>
        </Panel>

        <Panel title="Open-claim SLA health" subtitle={`${formatNumber.format(metrics.pending)} claims currently in progress`}>
          <div className="sla-chart-layout">
            <div className="donut-chart" role="img" aria-label="Donut chart of open claims by SLA status">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={data.sla_distribution} dataKey="value" nameKey="status" innerRadius={54} outerRadius={76} paddingAngle={2} stroke="none">
                    {data.sla_distribution.map((item) => <Cell key={item.status} fill={slaColors[item.status]} />)}
                  </Pie>
                  <Tooltip contentStyle={{ border: '1px solid #dfe5e2', borderRadius: 7, fontSize: 11 }} />
                </PieChart>
              </ResponsiveContainer>
              <div className="donut-center"><strong>{formatNumber.format(metrics.pending)}</strong><span>Open</span></div>
            </div>
            <div className="sla-legend">
              {data.sla_distribution.map((item) => (
                <div key={item.status} className="sla-legend-row">
                  <span><i style={{ background: slaColors[item.status] }} />{item.status.replace('_', ' ')}</span>
                  <strong>{formatNumber.format(item.value)}</strong>
                </div>
              ))}
            </div>
          </div>
        </Panel>
      </div>

      <div className="dashboard-grid dashboard-grid-bottom">
        <Panel title="Priority attention" subtitle="Highest-severity cases in the current synthetic snapshot" className="attention-panel" action={<Link to="/actions" className="panel-link">Open Action Center <Icon name="chevron" size={14} /></Link>}>
          <div className="table-scroll">
            <table className="attention-table">
              <thead><tr><th>Priority</th><th>Claim</th><th>Issue</th><th>Stage</th><th>Owner</th><th>Recommended action</th></tr></thead>
              <tbody>
                {data.attention.map((item) => (
                  <tr key={item.claim_id}>
                    <td><span className={`priority-pill priority-${item.priority.toLowerCase()}`}>{item.priority}</span></td>
                    <td><strong>{item.claim_id}</strong><span className="cell-subtitle">{item.partner}</span></td>
                    <td>{item.issue}</td>
                    <td>{item.stage}</td>
                    <td>{item.owner}</td>
                    <td><span className="recommended-action">{item.recommended_action}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>

        <Panel title="Open pipeline" subtitle="Claims currently waiting in each operational stage">
          <div className="pipeline-chart" role="img" aria-label="Horizontal bar chart of open claims by stage">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.pipeline} layout="vertical" margin={{ top: 0, right: 16, left: 10, bottom: 0 }}>
                <CartesianGrid stroke="#edf1ef" horizontal={false} />
                <XAxis type="number" hide />
                <YAxis dataKey="stage" type="category" width={105} tick={{ fill: '#66736d', fontSize: 10 }} axisLine={false} tickLine={false} />
                <Tooltip cursor={{ fill: '#f2f6f4' }} contentStyle={{ border: '1px solid #dfe5e2', borderRadius: 7, fontSize: 11 }} />
                <Bar dataKey="value" fill="#4d8b72" radius={[0, 4, 4, 0]} barSize={16} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Panel>
      </div>

      <p className="data-footnote">Synthetic data snapshot generated {new Date(data.generated_at).toLocaleString('en-KE', { dateStyle: 'medium', timeStyle: 'short', timeZone: 'Africa/Nairobi' })}. No real customer or claim information is used.</p>
    </div>
  )
}

function OverviewState({ title, copy, error = false }) {
  return (
    <div className={`overview-state ${error ? 'is-error' : ''}`} role={error ? 'alert' : 'status'}>
      <div className="placeholder-icon"><Icon name={error ? 'bell' : 'chart'} /></div>
      <div><h1>{title}</h1><p>{copy}</p></div>
    </div>
  )
}

