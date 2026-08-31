import { Icon } from './Icon.jsx'

export function PagePlaceholder({ title }) {
  return (
    <section className="placeholder-card" aria-label={`${title} phase notice`}>
      <div className="placeholder-icon"><Icon name="pipeline" size={22} /></div>
      <div>
        <p className="placeholder-title">Workspace ready</p>
        <p className="placeholder-copy">
          The {title} module has its route and layout in place. Feature data and workflows will be added in its scheduled implementation phase.
        </p>
      </div>
      <span className="phase-chip">Shell only</span>
    </section>
  )
}

