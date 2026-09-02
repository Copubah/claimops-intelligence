import { lazy, Suspense } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import { DashboardLayout } from '../layouts/DashboardLayout.jsx'
import { ModulePage } from '../pages/ModulePage.jsx'
import { NotFoundPage } from '../pages/NotFoundPage.jsx'
import { pageContent } from './navigation.js'

const OverviewPage = lazy(() => import('../pages/OverviewPage.jsx').then((module) => ({ default: module.OverviewPage })))
const ClaimsPage = lazy(() => import('../pages/ClaimsPage.jsx').then((module) => ({ default: module.ClaimsPage })))

export default function App() {
  return (
    <Routes>
      <Route element={<DashboardLayout />}>
        <Route index element={<Suspense fallback={<div className="route-loader" role="status">Loading operations overview…</div>}><OverviewPage /></Suspense>} />
        <Route path="/claims" element={<Suspense fallback={<div className="route-loader" role="status">Loading claims workspace…</div>}><ClaimsPage /></Suspense>} />
        {Object.entries(pageContent).filter(([path]) => !['/', '/claims'].includes(path)).map(([path, content]) => (
          <Route key={path} path={path} element={<ModulePage content={content} />} />
        ))}
        <Route path="/overview" element={<Navigate to="/" replace />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  )
}
