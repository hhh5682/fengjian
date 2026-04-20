import { useEffect, useMemo, useState } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom'
import appIcon from '../img/图标.png'
import { Entry, Map, Itinerary, DraftBox, Login, Register, Profile, LoadingScreen } from './pages'

function ProtectedRoute({ children }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const user = localStorage.getItem('user')
    setIsAuthenticated(Boolean(user))
    setIsLoading(false)
  }, [])

  if (isLoading) {
    return (
      <div className="fj-page fj-page-padding" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        加载中...
      </div>
    )
  }

  return isAuthenticated ? children : <Navigate to="/login" replace />
}

function PhoneChrome({ children }) {
  const location = useLocation()

  const timeText = useMemo(() => {
    const now = new Date()
    return `${now.getHours()}:${String(now.getMinutes()).padStart(2, '0')}`
  }, [])

  const isAuthPage = location.pathname === '/login' || location.pathname === '/register'

  return (
    <div className="phone-shell-page">
      <div className="phone-shell">
        <div className="dynamic-island" />
        <div className="phone-status-bar">
          <div className="phone-status-time">{timeText}</div>
          <div className="phone-status-right">
            <div className="phone-signal">
              <div className="phone-signal-bar" style={{ height: 4, opacity: 0.3 }} />
              <div className="phone-signal-bar" style={{ height: 6, opacity: 0.5 }} />
              <div className="phone-signal-bar" style={{ height: 8, opacity: 0.8 }} />
              <div className="phone-signal-bar" style={{ height: 10 }} />
            </div>
            <svg width="16" height="11" viewBox="0 0 16 12" fill="#000" opacity=".8">
              <path d="M8 2C10.4 2 12.6 3 14.1 4.6L15.5 3.1C13.6 1.2 11 0 8 0S2.4 1.2.5 3.1L1.9 4.6C3.4 3 5.6 2 8 2z" opacity=".4" />
              <path d="M8 5c1.5 0 2.9.6 3.9 1.6L13.3 5.1C12 3.8 10.1 3 8 3S4 3.8 2.7 5.1L4.1 6.6C5.1 5.6 6.5 5 8 5z" opacity=".7" />
              <path d="M8 8c.8 0 1.6.3 2.1.9L11.6 7.4C10.7 6.5 9.4 6 8 6S5.3 6.5 4.4 7.4L5.9 8.9C6.4 8.3 7.2 8 8 8z" />
              <circle cx="8" cy="11" r="1.3" />
            </svg>
            <svg width="25" height="12" viewBox="0 0 25 12" fill="none">
              <rect x=".5" y=".5" width="21" height="11" rx="2.5" stroke="#000" strokeOpacity=".35" />
              <rect x="2" y="2" width="15" height="8" rx="1.5" fill="#000" />
              <path d="M23 4v4a2 2 0 000-4z" fill="#000" opacity=".4" />
            </svg>
          </div>
        </div>

        <div className="phone-screen">
          {children}
        </div>

        {!isAuthPage && (
          <div
            style={{
              position: 'absolute',
              top: 86,
              left: 28,
              zIndex: 61,
              display: 'flex',
              alignItems: 'center',
              gap: 10
            }}
          >
            <img src={appIcon} alt="风间图标" className="fj-brand-icon" />
          </div>
        )}

        <div className="phone-home-bar">
          <div className="phone-home-pill" />
        </div>
      </div>
    </div>
  )
}

function AppRoutes() {
  return (
    <PhoneChrome>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <Entry />
            </ProtectedRoute>
          }
        />
        <Route
          path="/map"
          element={
            <ProtectedRoute>
              <Map />
            </ProtectedRoute>
          }
        />
        <Route
          path="/itinerary"
          element={
            <ProtectedRoute>
              <Itinerary />
            </ProtectedRoute>
          }
        />
        <Route
          path="/loading"
          element={
            <ProtectedRoute>
              <LoadingScreen />
            </ProtectedRoute>
          }
        />
        <Route
          path="/drafts"
          element={
            <ProtectedRoute>
              <DraftBox />
            </ProtectedRoute>
          }
        />
        <Route
          path="/profile"
          element={
            <ProtectedRoute>
              <Profile />
            </ProtectedRoute>
          }
        />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </PhoneChrome>
  )
}

function App() {
  return (
    <Router>
      <AppRoutes />
    </Router>
  )
}

export default App