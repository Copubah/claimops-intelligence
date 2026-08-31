import { Icon } from '../components/Icon.jsx'

export function Header({ onOpenNavigation }) {
  return (
    <header className="topbar">
      <button className="icon-button menu-button" type="button" onClick={onOpenNavigation} aria-label="Open navigation">
        <Icon name="menu" />
      </button>
      <div className="global-search" role="search">
        <Icon name="search" size={18} />
        <input aria-label="Search claims" placeholder="Search claims, partners, or agents" />
        <kbd>⌘ K</kbd>
      </div>
      <div className="topbar-actions">
        <div className="freshness" title="Synthetic data reference time">
          <span className="freshness-dot" />
          <span>Data current</span>
        </div>
        <button className="icon-button notification-button" type="button" aria-label="View notifications">
          <Icon name="bell" />
          <span className="notification-dot" />
        </button>
        <div className="header-avatar" aria-label="Signed in as Amina Otieno">AO</div>
      </div>
    </header>
  )
}

