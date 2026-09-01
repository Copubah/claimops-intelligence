import { useEffect, useState } from 'react'
import { Outlet } from 'react-router-dom'
import { Header } from './Header.jsx'
import { Sidebar } from './Sidebar.jsx'

export function DashboardLayout() {
  const [navigationOpen, setNavigationOpen] = useState(false)

  useEffect(() => {
    if (!navigationOpen) return undefined
    const previousOverflow = document.body.style.overflow
    const closeOnEscape = (event) => {
      if (event.key === 'Escape') setNavigationOpen(false)
    }
    document.body.style.overflow = 'hidden'
    window.addEventListener('keydown', closeOnEscape)
    return () => {
      document.body.style.overflow = previousOverflow
      window.removeEventListener('keydown', closeOnEscape)
    }
  }, [navigationOpen])

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
