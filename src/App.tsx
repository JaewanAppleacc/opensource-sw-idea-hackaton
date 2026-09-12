import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { ToastProvider } from './components/ui/ToastProvider'
import { SiteLayout } from './components/layout/SiteLayout'
import { HomePage } from './pages/HomePage'
import { AiJobRecommendPage } from './pages/AiJobRecommendPage'

function App() {
  return (
    <ToastProvider>
      <BrowserRouter>
        <Routes>
          <Route element={<SiteLayout />}>
            <Route index element={<HomePage />} />
            <Route path="ai-job-recommend" element={<AiJobRecommendPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </ToastProvider>
  )
}

export default App
