import { useCallback, useEffect, useState } from 'react'
import { api, API_URL } from '../api/client'
import type { HealthResponse } from '../api/types'
import { useAuth } from '../context/AuthContext'
import {
  Card,
  ErrorState,
  LoadingState,
  PageHeader,
} from '../components/ui'

export default function Settings() {
  const { user } = useAuth()
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await api.get<HealthResponse>('/health')
      setHealth(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to reach the backend.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  return (
    <div>
      <PageHeader
        title="Settings"
        subtitle="Your account and how this app connects to the backend."
      />

      <div className="space-y-4">
        <Card className="p-5">
          <h2 className="text-sm font-semibold text-slate-900">Account</h2>
          <dl className="mt-3 space-y-2 text-sm">
            <div className="flex justify-between gap-4">
              <dt className="text-slate-500">Email</dt>
              <dd className="font-medium text-slate-900">{user?.email}</dd>
            </div>
            <div className="flex justify-between gap-4">
              <dt className="text-slate-500">Full name</dt>
              <dd className="font-medium text-slate-900">{user?.full_name ?? '—'}</dd>
            </div>
            <div className="flex justify-between gap-4">
              <dt className="text-slate-500">Role</dt>
              <dd className="font-medium text-slate-900">{user?.role}</dd>
            </div>
          </dl>
        </Card>

        <Card className="p-5">
          <h2 className="text-sm font-semibold text-slate-900">Backend connection</h2>
          {loading ? (
            <LoadingState label="Checking backend…" />
          ) : error ? (
            <ErrorState message={error} onRetry={load} />
          ) : health ? (
            <dl className="mt-3 space-y-2 text-sm">
              <div className="flex justify-between gap-4">
                <dt className="text-slate-500">API URL</dt>
                <dd className="break-all font-mono text-xs text-slate-900">{API_URL}</dd>
              </div>
              <div className="flex justify-between gap-4">
                <dt className="text-slate-500">Backend status</dt>
                <dd className="font-medium text-emerald-600">{health.status}</dd>
              </div>
              <div className="flex justify-between gap-4">
                <dt className="text-slate-500">PayPal mode</dt>
                <dd className="font-medium text-slate-900">
                  {health.mode}
                  <span className="ml-2 text-xs font-normal text-slate-500">
                    {health.mode === 'sandbox'
                      ? '— live PayPal sandbox'
                      : health.mode === 'mock'
                        ? '— simulated PayPal, no real charges'
                        : ''}
                  </span>
                </dd>
              </div>
              <div className="flex justify-between gap-4">
                <dt className="text-slate-500">Database</dt>
                <dd className="font-medium text-slate-900">{health.db}</dd>
              </div>
            </dl>
          ) : null}
          <p className="mt-4 text-xs text-slate-500">
            The API URL comes from the <code className="rounded bg-slate-100 px-1">VITE_API_URL</code>{' '}
            setting (default <code className="rounded bg-slate-100 px-1">http://localhost:8000</code>).
            Change it in <code className="rounded bg-slate-100 px-1">.env</code> and restart the dev server.
          </p>
        </Card>
      </div>
    </div>
  )
}
