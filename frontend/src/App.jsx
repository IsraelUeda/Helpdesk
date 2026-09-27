import { Route, Routes } from 'react-router-dom'
import RequireAuth from './auth/RequireAuth'
import AppLayout from './layout/AppLayout'
import DashboardPage from './pages/DashboardPage'
import LoginPage from './pages/LoginPage'
import TicketDetailPage from './pages/TicketDetailPage'
import TicketsPage from './pages/TicketsPage'

function App() {
  return (
    <Routes>
      <Route path="login" element={<LoginPage />} />
      <Route
        element={
          <RequireAuth>
            <AppLayout />
          </RequireAuth>
        }
      >
        <Route index element={<DashboardPage />} />
        <Route path="tickets" element={<TicketsPage />} />
        <Route path="tickets/:id" element={<TicketDetailPage />} />
      </Route>
    </Routes>
  )
}

export default App
