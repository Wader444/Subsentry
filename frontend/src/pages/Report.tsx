import { useCallback, useEffect, useState } from 'react'
import { api } from '../api/client'
import type { EnrichedSubscription, ReportResponse } from '../api/types'
import { money } from '../lib/format'
import {
  Card,
  EmptyState,
  ErrorState,
  LoadingState,
  PageHeader,
} from '../components/ui'

export default function Report() {
  const [report, setReport] = useState<ReportResponse | null>(null)
  const [inventory, setInventory] = useState<EnrichedSubscription[]>([])
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [rep, inv] = await Promise.all([
        api.get<ReportResponse>('/report'),
        api.get<EnrichedSubscription[]>('/inventory'),
      ])
      setReport(rep)
      setInventory(inv)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load report.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  if (loading) return <LoadingState label="Loading report…" />
  if (error) return <ErrorState message={error} onRetry={load} />
  if (!report) return <EmptyState message="No report yet." />

  const byId = new Map(inventory.map((s) => [s.id, s]))
  const label = (id: string) => {
    const s = byId.get(id)
    return s ? `${s.merchant} · ${s.plan_name}` : id
  }
  const priceOf = (id: string) => byId.get(id)?.price_monthly_usd

  return (
    <div>
      <PageHeader
        title="Report"
        subtitle="What you've cancelled, what's still active, and what you've saved."
      />

      <div className="grid gap-4 sm:grid-cols-3">
        <Card className="p-5">
          <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
            Saving per month
          </p>
          <p className="mt-2 text-2xl font-bold text-emerald-600">
            {money(report.monthly_saving_usd)}
          </p>
        </Card>
        <Card className="p-5">
          <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
            Saving per year
          </p>
          <p className="mt-2 text-2xl font-bold text-emerald-600">
            {money(report.annual_saving_usd)}
          </p>
        </Card>
        <Card className="p-5">
          <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
            Total monthly spend
          </p>
          <p className="mt-2 text-2xl font-bold text-slate-900">
            {money(report.total_monthly_usd)}
          </p>
          <p className="mt-1 text-xs text-slate-500">
            {report.cancelled.length} cancelled · {report.still_active.length} still active
          </p>
        </Card>
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <div>
          <h2 className="mb-3 text-base font-semibold text-slate-900">
            Cancelled ({report.cancelled.length})
          </h2>
          {report.cancelled.length === 0 ? (
            <EmptyState message="Nothing cancelled yet. Review the proposals to start saving." />
          ) : (
            <div className="space-y-2">
              {report.cancelled.map((id) => (
                <Card key={id} className="flex items-center justify-between px-4 py-3">
                  <span className="font-medium text-slate-700">{label(id)}</span>
                  {priceOf(id) !== undefined && (
                    <span className="text-sm text-emerald-600">
                      was {money(priceOf(id))}/mo
                    </span>
                  )}
                </Card>
              ))}
            </div>
          )}
        </div>
        <div>
          <h2 className="mb-3 text-base font-semibold text-slate-900">
            Still active ({report.still_active.length})
          </h2>
          {report.still_active.length === 0 ? (
            <EmptyState message="No active subscriptions." />
          ) : (
            <div className="space-y-2">
              {report.still_active.map((id) => (
                <Card key={id} className="flex items-center justify-between px-4 py-3">
                  <span className="font-medium text-slate-700">{label(id)}</span>
                  {priceOf(id) !== undefined && (
                    <span className="text-sm text-slate-600">
                      {money(priceOf(id))}/mo
                    </span>
                  )}
                </Card>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
