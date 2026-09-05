import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { AppLayout } from './components/layout/AppLayout'
import { SubscriptionProvider } from './context/SubscriptionContext'
import { ToastProvider } from './context/ToastContext'
import { JobDetailPage } from './routes/JobDetailPage'
import { JobListPage } from './routes/JobListPage'

function App() {
  return (
    <ToastProvider>
      <SubscriptionProvider>
        <BrowserRouter>
          <Routes>
            <Route element={<AppLayout />}>
              <Route index element={<JobListPage />} />
              <Route path="jobs/:jobId" element={<JobDetailPage />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </SubscriptionProvider>
    </ToastProvider>
  )
}

export default App
