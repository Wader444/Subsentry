import { useCallback, useEffect, useState, type FormEvent } from 'react'
import { api } from '../api/client'
import type { EnrichedSubscription } from '../api/types'
import { formatDate, money } from '../lib/format'
import {
  Card,
  EmptyState,
  ErrorState,
  LoadingState,
  PageHeader,
  StatusBadge,
  WasteScoreBadge,
} from '../components/ui'

type Filter = 'all' | 'flagged' | 'active' | 'cancelled'

const FILTERS: { key: Filter; label: string }[] = [
  { key: 'all', label: 'All' },
  { key: 'flagged', label: 'Flagged' },
  { key: 'active', label: 'Active' },
  { key: 'cancelled', label: 'Cancelled' },
]

export default function Inventory() {
  const [subs, setSubs] = useState<EnrichedSubscription[]>([])
  const [filter, setFilter] = useState<Filter>('all')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)
  const [formBusy, setFormBusy] = useState(false)
  const [deleteBusy, setDeleteBusy] = useState<string | null>(null)

  const [merchant, setMerchant] = useState('')
  const [planName, setPlanName] = useState('')
  const [category, setCategory] = useState('')
  const [price, setPrice] = useState('')
  const [lastUsed, setLastUsed] = useState('')
  const [startedOn, setStartedOn] = useState('')
  const [nextBilling, setNextBilling] = useState('')

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await api.get<EnrichedSubscription[]>('/inventory')
      setSubs(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load inventory.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  const visible = subs.filter((s) => {
    if (filter === 'flagged') return s.flagged
    if (filter === 'active') return s.status === 'active'
    if (filter === 'cancelled') return s.status === 'cancelled'
    return true
  })

  const handleAdd = async (e: FormEvent) => {
    e.preventDefault()
    setFormError(null)
    setFormBusy(true)
    try {
      await api.post('/subscriptions', {
        merchant: merchant.trim(),
        plan_name: planName.trim(),
        category: category.trim() || undefined,
        price_monthly_usd: Number(price),
        last_used_days_ago: lastUsed === '' ? undefined : Number(lastUsed),
        started_on: startedOn || undefined,
        next_billing_on: nextBilling || undefined,
      })
      setMerchant('')
      setPlanName('')
      setCategory('')
      setPrice('')
      setLastUsed('')
      setStartedOn('')
      setNextBilling('')
      setShowForm(false)
      await load()
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'Could not add subscription.')
    } finally {
      setFormBusy(false)
    }
  }

  const handleDelete = async (id: string, label: string) => {
    if (!window.confirm(`Delete ${label}? This cannot be undone.`)) return
    setDeleteBusy(id)
    try {
      await api.del(`/subscriptions/${id}`)
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not delete subscription.')
    } finally {
      setDeleteBusy(null)
    }
  }

  if (loading) return <LoadingState label="Loading inventory…" />
  if (error) return <ErrorState message={error} onRetry={load} />

  return (
    <div>
      <PageHeader
        title="Inventory"
        subtitle="Every subscription SubSentry knows about, with its waste score."
      />

      <div className="mb-4 flex flex-wrap items-center gap-2">
        {FILTERS.map((f) => (
          <button
            key={f.key}
            type="button"
            onClick={() => setFilter(f.key)}
            className={`rounded-full px-3 py-1.5 text-sm font-medium ${
              filter === f.key
                ? 'bg-indigo-600 text-white'
                : 'bg-white text-slate-600 ring-1 ring-slate-300 hover:bg-slate-50'
            }`}
          >
            {f.label}
          </button>
        ))}
        <span className="ml-1 text-sm text-slate-500">
          {visible.length} of {subs.length} shown
        </span>
        <button
          type="button"
          onClick={() => setShowForm((v) => !v)}
          className="ml-auto rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700"
        >
          {showForm ? 'Close form' : '+ Add subscription'}
        </button>
      </div>

      {showForm && (
        <Card className="mb-6 p-5">
          <h2 className="text-sm font-semibold text-slate-900">Add a subscription</h2>
          <form onSubmit={handleAdd} className="mt-4 grid gap-4 sm:grid-cols-2">
            <div>
              <label htmlFor="merchant" className="block text-sm font-medium text-slate-700">
                Merchant *
              </label>
              <input
                id="merchant"
                required
                value={merchant}
                onChange={(e) => setMerchant(e.target.value)}
                placeholder="e.g. FitGym"
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              />
            </div>
            <div>
              <label htmlFor="plan_name" className="block text-sm font-medium text-slate-700">
                Plan name *
              </label>
              <input
                id="plan_name"
                required
                value={planName}
                onChange={(e) => setPlanName(e.target.value)}
                placeholder="e.g. Pro"
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              />
            </div>
            <div>
              <label htmlFor="category" className="block text-sm font-medium text-slate-700">
                Category
              </label>
              <input
                id="category"
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                placeholder="e.g. Fitness"
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              />
            </div>
            <div>
              <label htmlFor="price" className="block text-sm font-medium text-slate-700">
                Price per month (USD) *
              </label>
              <input
                id="price"
                required
                type="number"
                min="0.01"
                step="0.01"
                value={price}
                onChange={(e) => setPrice(e.target.value)}
                placeholder="9.99"
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              />
            </div>
            <div>
              <label htmlFor="last_used" className="block text-sm font-medium text-slate-700">
                Days since last use
              </label>
              <input
                id="last_used"
                type="number"
                min="0"
                step="1"
                value={lastUsed}
                onChange={(e) => setLastUsed(e.target.value)}
                placeholder="0"
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              />
            </div>
            <div>
              <label htmlFor="started_on" className="block text-sm font-medium text-slate-700">
                Started on
              </label>
              <input
                id="started_on"
                type="date"
                value={startedOn}
                onChange={(e) => setStartedOn(e.target.value)}
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              />
            </div>
            <div>
              <label htmlFor="next_billing" className="block text-sm font-medium text-slate-700">
                Next billing date
              </label>
              <input
                id="next_billing"
                type="date"
                value={nextBilling}
                onChange={(e) => setNextBilling(e.target.value)}
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              />
            </div>
            {formError && (
              <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700 sm:col-span-2">
                {formError}
              </p>
            )}
            <div className="sm:col-span-2">
              <button
                type="submit"
                disabled={formBusy}
                className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-50"
              >
                {formBusy ? 'Adding…' : 'Add subscription'}
              </button>
            </div>
          </form>
        </Card>
      )}

      {visible.length === 0 ? (
        <EmptyState message="No subscriptions match this filter." />
      ) : (
        <Card className="overflow-x-auto">
          <table className="w-full min-w-3xl text-left text-sm">
            <thead className="border-b border-slate-200 bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
              <tr>
                <th className="px-4 py-3">Subscription</th>
                <th className="px-4 py-3">Category</th>
                <th className="px-4 py-3">Price</th>
                <th className="px-4 py-3">Last used</th>
                <th className="px-4 py-3">Waste score</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Next billing</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {visible.map((s) => (
                <tr key={s.id} className="hover:bg-slate-50">
                  <td className="px-4 py-3">
                    <p className="font-medium text-slate-900">
                      {s.merchant} · {s.plan_name}
                    </p>
                    {s.flagged && s.reason && (
                      <p className="mt-0.5 text-xs text-red-600">{s.reason}</p>
                    )}
                  </td>
                  <td className="px-4 py-3 text-slate-600">{s.category ?? '—'}</td>
                  <td className="px-4 py-3 font-medium text-slate-900">
                    {money(s.price_monthly_usd)}
                    <span className="font-normal text-slate-500">/mo</span>
                  </td>
                  <td className="px-4 py-3 text-slate-600">
                    {s.last_used_days_ago === null || s.last_used_days_ago === undefined
                      ? '—'
                      : `${s.last_used_days_ago}d ago`}
                  </td>
                  <td className="px-4 py-3">
                    <WasteScoreBadge score={s.waste_score} />
                  </td>
                  <td className="px-4 py-3">
                    <StatusBadge status={s.status} />
                  </td>
                  <td className="px-4 py-3 text-slate-600">
                    {formatDate(s.next_billing_on)}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button
                      type="button"
                      disabled={deleteBusy === s.id}
                      onClick={() => handleDelete(s.id, `${s.merchant} ${s.plan_name}`)}
                      className="rounded-lg px-2 py-1 text-xs font-medium text-red-600 hover:bg-red-50 disabled:opacity-50"
                    >
                      {deleteBusy === s.id ? 'Deleting…' : 'Delete'}
                    </button>
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
