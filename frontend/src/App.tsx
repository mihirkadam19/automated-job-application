import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { AppLayout } from './components/layout/AppLayout'
import { SubscriptionProvider } from './context/SubscriptionContext'
import { JobDetailPage } from './routes/JobDetailPage'
import { JobListPage } from './routes/JobListPage'

function App() {
  return (
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
  )
}

export default App
