import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { AppLayout } from './components/layout/AppLayout'
import { JobDetailPage } from './routes/JobDetailPage'
import { JobListPage } from './routes/JobListPage'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppLayout />}>
          <Route index element={<JobListPage />} />
          <Route path="jobs/:jobId" element={<JobDetailPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
