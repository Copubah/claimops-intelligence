import { NavLink } from 'react-router-dom'
import { Icon } from '../components/Icon.jsx'
import { navigation } from '../app/navigation.js'

export function Sidebar({ open, onClose }) {
  return (
    <>
      <div className={`sidebar-backdrop ${open ? 'is-open' : ''}`} onClick={onClose} aria-hidden="true" />
      <aside className={`sidebar ${open ? 'is-open' : ''}`} aria-label="Primary navigation">
        <div className="brand-row">
          <div className="brand-mark" aria-hidden="true"><span>CO</span></div>
          <div className="brand-copy">
            <span className="brand-name">ClaimOps</span>
            <span className="brand-subtitle">Intelligence</span>
          </div>
          <button className="icon-button sidebar-close" type="button" onClick={onClose} aria-label="Close navigation">
            <Icon name="close" />
          </button>
        </div>

        <div className="environment-row">
          <span className="environment-dot" />
          Portfolio environment
          <span className="environment-tag">DEMO</span>
        </div>

        <nav className="nav-list">
          <p className="nav-section-label">Workspace</p>
          {navigation.slice(0, 11).map((item) => <NavigationItem key={item.path} item={item} onClick={onClose} />)}
          <p className="nav-section-label nav-section-secondary">System</p>
          {navigation.slice(11).map((item) => <NavigationItem key={item.path} item={item} onClick={onClose} />)}
        </nav>

        <div className="sidebar-footer">
          <div className="user-avatar">AO</div>
          <div className="user-meta">
            <span className="user-name">Amina Otieno</span>
            <span className="user-role">Operations Manager</span>
          </div>
          <Icon name="chevron" size={16} />
        </div>
      </aside>
    </>
  )
}

function NavigationItem({ item, onClick }) {
  return (
    <NavLink to={item.path} end={item.path === '/'} onClick={onClick} className={({ isActive }) => `nav-item ${isActive ? 'is-active' : ''}`}>
      <Icon name={item.icon} size={19} />
      <span>{item.label}</span>
      {item.badge && <span className="nav-badge">{item.badge}</span>}
    </NavLink>
  )
}

