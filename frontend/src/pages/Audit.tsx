import { useCallback, useEffect, useState } from 'react'
import { api } from '../api/client'
import type { AuditResponse } from '../api/types'
import { formatDateTime } from '../lib/format'
import {
  Card,
  EmptyState,
  ErrorState,
  LoadingState,
  PageHeader,
} from '../components/ui'

export default function Audit() {
  const [entries, setEntries] = useState<AuditResponse['entries']>([])
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await api.get<AuditResponse>('/audit')
      setEntries(data.entries)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load audit log.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  if (loading) return <LoadingState label="Loading audit log…" />
  if (error) return <ErrorState message={error} onRetry={load} />

  return (
    <div>
      <PageHeader
        title="Audit log"
        subtitle="A record of every approval, cancellation, and change."
      />

      {entries.length === 0 ? (
        <EmptyState message="No audit entries yet." />
      ) : (
        <Card className="overflow-x-auto">
          <table className="w-full min-w-3xl text-left text-sm">
            <thead className="border-b border-slate-200 bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
              <tr>
                <th className="px-4 py-3">When</th>
                <th className="px-4 py-3">Action</th>
                <th className="px-4 py-3">Entity</th>
                <th className="px-4 py-3">Detail</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {entries.map((e) => (
                <tr key={e.id} className="hover:bg-slate-50">
                  <td className="whitespace-nowrap px-4 py-3 text-slate-600">
                    {formatDateTime(e.created_at)}
                  </td>
                  <td className="px-4 py-3">
                    <span className="rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-medium text-slate-700">
                      {e.action}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-slate-600">
                    {e.entity_type}
                    {e.entity_id ? (
                      <span className="block truncate font-mono text-xs text-slate-400">
                        {e.entity_id}
                      </span>
                    ) : null}
                  </td>
                  <td className="px-4 py-3 text-slate-600">{e.detail ?? '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  )
}
