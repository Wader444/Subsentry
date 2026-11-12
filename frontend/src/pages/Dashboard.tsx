import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import type { EnrichedSubscription, ProposeResponse } from '../api/types'
import { money } from '../lib/format'
import {
  Card,
  EmptyState,
  ErrorState,
  LoadingState,
  PageHeader,
  StatusBadge,
  WasteScoreBadge,
} from '../components/ui'

export default function Dashboard() {
  const [inventory, setInventory] = useState<EnrichedSubscription[] | null>(null)
  const [propose, setPropose] = useState<ProposeResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [inv, prop] = await Promise.all([
        api.get<EnrichedSubscription[]>('/inventory'),
        api.get<ProposeResponse>('/propose'),
      ])
      setInventory(inv)
      setPropose(prop)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load dashboard.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  if (loading) return <LoadingState label="Loading your subscriptions…" />
  if (error) return <ErrorState message={error} onRetry={load} />
  if (!inventory || !propose) return <EmptyState message="No data yet." />

  const flagged = propose.flagged
  const activeCount = inventory.filter((s) => s.status === 'active').length
  const savedPct =
    propose.total_monthly_usd > 0
      ? Math.round((propose.monthly_saving_usd / propose.total_monthly_usd) * 100)
      : 0

  return (
    <div>
      <PageHeader
        title="Dashboard"
        subtitle="What you're paying for, and what you could stop paying for."
      />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card className="p-5">
          <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
            Monthly total
          </p>
          <p className="mt-2 text-2xl font-bold text-slate-900">
            {money(propose.total_monthly_usd)}
            <span className="text-sm font-normal text-slate-500">/mo</span>
          </p>
          <p className="mt-1 text-xs text-slate-500">
            {inventory.length} subscriptions · {activeCount} active
          </p>
        </Card>
        <Card className="p-5">
          <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
            Potential saving
          </p>
          <p className="mt-2 text-2xl font-bold text-emerald-600">
            {money(propose.monthly_saving_usd)}
            <span className="text-sm font-normal text-slate-500">/mo</span>
          </p>
          <p className="mt-1 text-xs text-slate-500">
            {money(propose.annual_saving_usd)} per year
          </p>
        </Card>
        <Card className="p-5">
          <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
            Flagged as waste
          </p>
          <p className="mt-2 text-2xl font-bold text-red-600">{flagged.length}</p>
          <p className="mt-1 text-xs text-slate-500">
            Unused subscriptions to review
          </p>
        </Card>
        <Card className="p-5">
          <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
            Kept subscriptions
          </p>
          <p className="mt-2 text-2xl font-bold text-slate-900">
            {propose.kept.length}
          </p>
          <p className="mt-1 text-xs text-slate-500">Looks worth keeping</p>
        </Card>
      </div>

      <Card className="mt-6 p-5">
        <div className="flex items-baseline justify-between">
          <h2 className="text-sm font-semibold text-slate-900">
            Potential saving vs. total spend
          </h2>
          <span className="text-sm font-medium text-slate-600">{savedPct}% of spend</span>
        </div>
        <div className="mt-3 h-3 w-full overflow-hidden rounded-full bg-slate-200">
          <div
            className="h-full rounded-full bg-emerald-500"
            style={{ width: `${savedPct}%` }}
          />
        </div>
        <p className="mt-2 text-xs text-slate-500">
          Cancelling the {flagged.length} flagged subscription
          {flagged.length === 1 ? '' : 's'} would save{' '}
          {money(propose.monthly_saving_usd)} a month (
          {money(propose.annual_saving_usd)} a year) out of{' '}
          {money(propose.total_monthly_usd)} a month total.
        </p>
      </Card>

      <div className="mt-6">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-base font-semibold text-slate-900">
            Flagged subscriptions
          </h2>
          <Link
            to="/proposals"
            className="text-sm font-medium text-indigo-600 hover:text-indigo-700"
          >
            Review proposals →
          </Link>
        </div>
        {flagged.length === 0 ? (
          <EmptyState message="Nothing flagged — every subscription looks used." />
        ) : (
          <div className="space-y-3">
            {flagged.map((sub) => (
              <Card key={sub.id} className="flex flex-wrap items-center gap-4 p-4">
                <div className="min-w-0 flex-1">
                  <p className="font-semibold text-slate-900">
                    {sub.merchant} · {sub.plan_name}
                  </p>
                  <p className="mt-0.5 text-sm text-slate-500">
                    {sub.reason ?? 'Unused subscription'}
                  </p>
                </div>
                <WasteScoreBadge score={sub.waste_score} />
                <StatusBadge status={sub.status} />
                <span className="text-sm font-semibold text-slate-900">
                  {money(sub.price_monthly_usd)}
                  <span className="font-normal text-slate-500">/mo</span>
                </span>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
