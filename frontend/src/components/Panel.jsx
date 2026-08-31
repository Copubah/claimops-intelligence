export function Panel({ title, subtitle, action, className = '', children }) {
  return (
    <section className={`dashboard-panel ${className}`}>
      <header className="panel-header">
        <div>
          <h2>{title}</h2>
          {subtitle && <p>{subtitle}</p>}
        </div>
        {action}
      </header>
      <div className="panel-content">{children}</div>
    </section>
  )
}

