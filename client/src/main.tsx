import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import App from './App'
import RunsPage from './pages/RunsPage'
import RunDetailPage from './pages/RunDetailPage'
import StepDetailPage from './pages/StepDetailPage'
import ComparePage from './pages/ComparePage'
import DocsPage from './pages/DocsPage'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<App />}>
          <Route index element={<RunsPage />} />
          <Route path="runs/:runId" element={<RunDetailPage />} />
          <Route path="steps/:stepId" element={<StepDetailPage />} />
          <Route path="compare" element={<ComparePage />} />
          <Route path="docs" element={<DocsPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  </React.StrictMode>,
)

