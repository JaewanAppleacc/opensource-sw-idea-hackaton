import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { ToastProvider } from './components/ui/ToastProvider'
import { SiteLayout } from './components/layout/SiteLayout'
import { HomePage } from './pages/HomePage'
import { AiJobRecommendPage } from './pages/AiJobRecommendPage'
import { ManualAnalysisPage } from './pages/ManualAnalysisPage'

function App() {
  return (
    <ToastProvider>
      <BrowserRouter>
        <Routes>
          <Route element={<SiteLayout />}>
            <Route index element={<HomePage />} />
            <Route path="ai-job-recommend" element={<AiJobRecommendPage />} />
            <Route path="manual-analysis" element={<ManualAnalysisPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </ToastProvider>
  )
}

export default App
