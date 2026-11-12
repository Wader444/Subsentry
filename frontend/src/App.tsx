import { Navigate, Route, Routes } from 'react-router-dom'
import { AuthProvider, ProtectedRoute } from './context/AuthContext'
import Layout from './components/Layout'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import Inventory from './pages/Inventory'
import Proposals from './pages/Proposals'
import Report from './pages/Report'
import Ask from './pages/Ask'
import Notifications from './pages/Notifications'
import Duplicates from './pages/Duplicates'
import Audit from './pages/Audit'
import Settings from './pages/Settings'
import Admin from './pages/Admin'

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route
          element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Dashboard />} />
          <Route path="inventory" element={<Inventory />} />
          <Route path="proposals" element={<Proposals />} />
          <Route path="report" element={<Report />} />
          <Route path="ask" element={<Ask />} />
          <Route path="notifications" element={<Notifications />} />
          <Route path="duplicates" element={<Duplicates />} />
          <Route path="audit" element={<Audit />} />
          <Route path="settings" element={<Settings />} />
          <Route path="admin" element={<Admin />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AuthProvider>
  )
}
