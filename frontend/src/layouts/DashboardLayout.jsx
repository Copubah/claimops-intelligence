import { useState } from 'react'
import { Outlet } from 'react-router-dom'
import { Header } from './Header.jsx'
import { Sidebar } from './Sidebar.jsx'

export function DashboardLayout() {
  const [navigationOpen, setNavigationOpen] = useState(false)

  return (
    <div className="app-shell">
      <Sidebar open={navigationOpen} onClose={() => setNavigationOpen(false)} />
      <div className="main-column">
        <Header onOpenNavigation={() => setNavigationOpen(true)} />
        <main className="page-container">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
