import { Navigate, Route, Routes } from 'react-router-dom'
import { DashboardLayout } from '../layouts/DashboardLayout.jsx'
import { ModulePage } from '../pages/ModulePage.jsx'
import { NotFoundPage } from '../pages/NotFoundPage.jsx'
import { pageContent } from './navigation.js'

export default function App() {
  return (
    <Routes>
      <Route element={<DashboardLayout />}>
        {Object.entries(pageContent).map(([path, content]) => (
          <Route key={path} path={path} element={<ModulePage content={content} />} />
        ))}
        <Route path="/overview" element={<Navigate to="/" replace />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  )
}

