import { Navigate, Route, Routes } from 'react-router-dom'
import { useAuth } from './context/AuthContext'
import Layout from './components/Layout'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Students from './pages/Students'
import Sessions from './pages/Sessions'
import LiveAttendance from './pages/LiveAttendance'
import Reports from './pages/Reports'
import RecordsDashboard from './pages/RecordsDashboard'
import CreateUser from './pages/CreateUser'

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const { token, loading } = useAuth()
  if (loading) return <div className="loading-screen">Loading...</div>
  if (!token) return <Navigate to="/login" replace />
  return <>{children}</>
}

function AdminRoute({ children }: { children: React.ReactNode }) {
  const { isAdmin } = useAuth()
  if (!isAdmin) return <Navigate to="/" replace />
  return <>{children}</>
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/"
        element={
          <PrivateRoute>
            <Layout />
          </PrivateRoute>
        }
      >
        <Route index element={<Dashboard />} />
        <Route path="students" element={<Students />} />
        <Route path="sessions" element={<Sessions />} />
        <Route path="live" element={<LiveAttendance />} />
        <Route path="reports" element={<Reports />} />
        <Route path="records" element={<RecordsDashboard />} />
        <Route
          path="users/new"
          element={
            <AdminRoute>
              <CreateUser />
            </AdminRoute>
          }
        />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
