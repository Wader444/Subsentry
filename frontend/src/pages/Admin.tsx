import { useCallback, useEffect, useState } from 'react'
import { ApiError, api } from '../api/client'
import type { AdminStats, AdminUsersResponse } from '../api/types'
import { useAuth } from '../context/AuthContext'
import { money } from '../lib/format'
import {
  Card,
  EmptyState,
  ErrorState,
  LoadingState,
  PageHeader,
} from '../components/ui'

export default function Admin() {
  const { user } = useAuth()
  const [users, setUsers] = useState<AdminUsersResponse['users']>([])
  const [stats, setStats] = useState<AdminStats | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [forbidden, setForbidden] = useState(false)
  const [loading, setLoading] = useState(true)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    setForbidden(false)
    try {
      const [u, s] = await Promise.all([
        api.get<AdminUsersResponse>('/admin/users'),
        api.get<AdminStats>('/admin/stats'),
      ])
      setUsers(u.users)
      setStats(s)
    } catch (err) {
      if (err instanceof ApiError && err.status === 403) {
        setForbidden(true)
      } else {
        setError(err instanceof Error ? err.message : 'Failed to load admin data.')
      }
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  if (loading) return <LoadingState label="Loading admin data…" />

  if (forbidden) {
    return (
      <div>
        <PageHeader title="Admin" subtitle="Administration for SubSentry." />
        <Card className="border-amber-200 bg-amber-50 p-6 text-center">
          <p className="text-base font-semibold text-amber-800">Admin only</p>
          <p className="mt-2 text-sm text-amber-700">
            You are signed in as a regular user
            {user?.email ? (
              <>
                {' '}
                (<span className="font-medium">{user.email}</span>)
              </>
            ) : (
              ''
            )}
            . Only admins can view users and platform stats.
          </p>
          <p className="mt-2 text-sm text-amber-700">
            Sign in with the admin demo account (
            <code className="rounded bg-amber-100 px-1">admin@subsentry.local</code> /{' '}
            <code className="rounded bg-amber-100 px-1">admin1234</code>) to see this
            page.
          </p>
        </Card>
      </div>
    )
  }

  if (error) return <ErrorState message={error} onRetry={load} />
  if (!stats) return <EmptyState message="No admin data yet." />

  return (
    <div>
      <PageHeader
        title="Admin"
        subtitle="Platform-wide users and subscription stats."
      />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        <Card className="p-5">
          <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
            Users
          </p>
          <p className="mt-2 text-2xl font-bold text-slate-900">{stats.total_users}</p>
        </Card>
        <Card className="p-5">
          <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
            Subscriptions
          </p>
          <p className="mt-2 text-2xl font-bold text-slate-900">
            {stats.total_subscriptions}
          </p>
        </Card>
        <Card className="p-5">
          <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
            Active
          </p>
          <p className="mt-2 text-2xl font-bold text-emerald-600">
            {stats.active_subscriptions}
          </p>
        </Card>
        <Card className="p-5">
          <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
            Cancelled
          </p>
          <p className="mt-2 text-2xl font-bold text-slate-900">
            {stats.cancelled_subscriptions}
          </p>
        </Card>
        <Card className="p-5">
          <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
            Monthly volume
          </p>
          <p className="mt-2 text-2xl font-bold text-slate-900">
            {money(stats.total_monthly_usd)}
          </p>
        </Card>
      </div>

      <h2 className="mb-3 mt-8 text-base font-semibold text-slate-900">
        Users ({users.length})
      </h2>
      {users.length === 0 ? (
        <EmptyState message="No users found." />
      ) : (
        <Card className="overflow-x-auto">
          <table className="w-full min-w-xl text-left text-sm">
            <thead className="border-b border-slate-200 bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
              <tr>
                <th className="px-4 py-3">Email</th>
                <th className="px-4 py-3">Full name</th>
                <th className="px-4 py-3">Role</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {users.map((u) => (
                <tr key={u.id} className="hover:bg-slate-50">
                  <td className="px-4 py-3 font-medium text-slate-900">{u.email}</td>
                  <td className="px-4 py-3 text-slate-600">{u.full_name ?? '—'}</td>
                  <td className="px-4 py-3">
                    <span
                      className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${
                        u.role === 'admin'
                          ? 'bg-indigo-50 text-indigo-700'
                          : 'bg-slate-100 text-slate-600'
                      }`}
                    >
                      {u.role}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  )
}
