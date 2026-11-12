import { useCallback, useEffect, useState } from 'react'
import { api } from '../api/client'
import type { DuplicatesResponse } from '../api/types'
import { money } from '../lib/format'
import {
  Card,
  EmptyState,
  ErrorState,
  LoadingState,
  PageHeader,
  StatusBadge,
} from '../components/ui'

export default function Duplicates() {
  const [groups, setGroups] = useState<DuplicatesResponse['groups']>([])
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await api.get<DuplicatesResponse>('/duplicates')
      setGroups(data.groups)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load duplicates.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  if (loading) return <LoadingState label="Checking for duplicates…" />
  if (error) return <ErrorState message={error} onRetry={load} />

  return (
    <div>
      <PageHeader
        title="Duplicates"
        subtitle="Subscriptions that look like the same service billed twice."
      />

      {groups.length === 0 ? (
        <EmptyState message="No duplicate subscriptions found." />
      ) : (
        <div className="space-y-4">
          {groups.map((g) => (
            <Card key={g.merchant} className="p-5">
              <div className="flex flex-wrap items-baseline gap-2">
                <h2 className="text-base font-semibold text-slate-900">
                  {g.merchant}
                </h2>
                <span className="text-sm text-slate-500">
                  {g.subscriptions.length} subscriptions
                </span>
              </div>
              <p className="mt-1 text-sm text-slate-600">{g.reason}</p>
              <div className="mt-3 divide-y divide-slate-100">
                {g.subscriptions.map((s) => (
                  <div
                    key={s.id}
                    className="flex flex-wrap items-center gap-3 py-2 text-sm"
                  >
                    <span className="min-w-0 flex-1 font-medium text-slate-700">
                      {s.plan_name}
                    </span>
                    <StatusBadge status={s.status} />
                    <span className="font-medium text-slate-900">
                      {money(s.price_monthly_usd)}/mo
                    </span>
                  </div>
                ))}
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
