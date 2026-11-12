import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const NAV_ITEMS = [
  { to: '/', label: 'Dashboard', end: true },
  { to: '/inventory', label: 'Inventory' },
  { to: '/proposals', label: 'Proposals' },
  { to: '/report', label: 'Report' },
  { to: '/ask', label: 'Ask' },
  { to: '/notifications', label: 'Notifications' },
  { to: '/duplicates', label: 'Duplicates' },
  { to: '/audit', label: 'Audit' },
  { to: '/settings', label: 'Settings' },
] as const

function Sidebar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <aside className="flex w-64 shrink-0 flex-col bg-slate-900 text-slate-300">
      <div className="px-6 pb-6 pt-6">
        <p className="text-lg font-bold tracking-tight text-white">
          SubSentry
        </p>
        <p className="mt-1 text-xs leading-relaxed text-slate-400">
          Stop paying for subscriptions you don&apos;t use.
        </p>
      </div>

      <nav className="flex-1 space-y-1 px-3">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={'end' in item ? item.end : false}
            className={({ isActive }) =>
              `block rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-indigo-600 text-white'
                  : 'text-slate-300 hover:bg-slate-800 hover:text-white'
              }`
            }
          >
            {item.label}
          </NavLink>
        ))}
        {user?.role === 'admin' && (
          <NavLink
            to="/admin"
            className={({ isActive }) =>
              `block rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-indigo-600 text-white'
                  : 'text-slate-300 hover:bg-slate-800 hover:text-white'
              }`
            }
          >
            Admin
          </NavLink>
        )}
      </nav>

      <div className="border-t border-slate-800 px-6 py-4">
        <p className="truncate text-xs text-slate-400" title={user?.email}>
          {user?.email}
        </p>
        <button
          type="button"
          onClick={handleLogout}
          className="mt-2 w-full rounded-lg bg-slate-800 px-3 py-2 text-sm font-medium text-white hover:bg-slate-700"
        >
          Log out
        </button>
      </div>
    </aside>
  )
}

export default function Layout() {
  const { user } = useAuth()

  return (
    <div className="flex min-h-screen bg-slate-100">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-10 border-b border-slate-200 bg-white">
          <div className="flex items-center justify-between px-6 py-3">
            <p className="text-sm font-semibold text-slate-900">
              SubSentry dashboard
            </p>
            <div className="flex items-center gap-3">
              {user?.role === 'admin' && (
                <span className="rounded-full bg-indigo-50 px-2.5 py-0.5 text-xs font-semibold text-indigo-700">
                  Admin
                </span>
              )}
              <span className="max-w-64 truncate text-sm text-slate-600">
                {user?.full_name ?? user?.email}
              </span>
            </div>
          </div>
        </header>
        <main className="mx-auto w-full max-w-6xl flex-1 px-6 py-8">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
