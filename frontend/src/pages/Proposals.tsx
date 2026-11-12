import { useCallback, useEffect, useState } from 'react'
import { api } from '../api/client'
import type { CancelResponse, ProposeResponse } from '../api/types'
import { money } from '../lib/format'
import {
  Card,
  EmptyState,
  ErrorState,
  LoadingState,
  PageHeader,
  WasteScoreBadge,
} from '../components/ui'

export default function Proposals() {
  const [propose, setPropose] = useState<ProposeResponse | null>(null)
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [actionMsg, setActionMsg] = useState<string | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)
  const [busy, setBusy] = useState<'approve' | 'cancel' | null>(null)
  const [lastCancel, setLastCancel] = useState<CancelResponse | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await api.get<ProposeResponse>('/propose')
      setPropose(data)
      setSelected(new Set())
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load proposals.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  const toggle = (id: string) => {
    setSelected((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const handleApprove = async () => {
    if (selected.size === 0) return
    setBusy('approve')
    setActionMsg(null)
    setActionError(null)
    try {
      const res = await api.post<{ approved: string[] }>('/approve', {
        subscription_ids: [...selected],
      })
      setActionMsg(
        `${res.approved.length} subscription${res.approved.length === 1 ? '' : 's'} approved for cancellation. You can now cancel them below — or leave them approved and decide later.`,
      )
    } catch (err) {
      setActionError(err instanceof Error ? err.message : 'Approval failed.')
    } finally {
      setBusy(null)
    }
  }

  const handleCancel = async () => {
    setBusy('cancel')
    setActionMsg(null)
    setActionError(null)
    setLastCancel(null)
    try {
      // No body: the backend cancels only previously approved subscriptions.
      const res = await api.postEmpty<CancelResponse>('/cancel')
      setLastCancel(res)
      if (res.cancelled.length > 0) {
        setActionMsg(
          `Cancelled ${res.cancelled.length} subscription${res.cancelled.length === 1 ? '' : 's'} — saving ${money(res.monthly_saving_usd)} a month (${money(res.annual_saving_usd)} a year).`,
        )
      } else if (res.blocked.length > 0) {
        setActionError(
          'Nothing was cancelled — every requested cancellation was blocked because it had no approval. Approve subscriptions first, then cancel.',
        )
      } else {
        setActionMsg('Nothing to cancel right now.')
      }
      await load()
    } catch (err) {
      setActionError(err instanceof Error ? err.message : 'Cancellation failed.')
    } finally {
      setBusy(null)
    }
  }

  if (loading) return <LoadingState label="Loading proposals…" />
  if (error) return <ErrorState message={error} onRetry={load} />
  if (!propose) return <EmptyState message="No proposals yet." />

  return (
    <div>
      <PageHeader
        title="Proposals"
        subtitle="Subscriptions the agent thinks you're paying for but not using."
      />

      <Card className="mb-6 border-indigo-200 bg-indigo-50 p-5">
        <p className="text-sm font-semibold text-indigo-900">
          Nothing is cancelled without your approval.
        </p>
        <p className="mt-1 text-sm text-indigo-800">
          Tick the subscriptions you want to drop, approve them, then cancel.
          Cancelling without approval is blocked by the backend — approved
          subscriptions are the only ones that can be cancelled.
        </p>
      </Card>

      {actionMsg && (
        <p className="mb-4 rounded-lg bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
          {actionMsg}
        </p>
      )}
      {actionError && (
        <p className="mb-4 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">
          {actionError}
        </p>
      )}
      {lastCancel && lastCancel.blocked.length > 0 && (
        <Card className="mb-4 border-amber-200 bg-amber-50 p-4">
          <p className="text-sm font-semibold text-amber-800">Blocked cancellations</p>
          <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-amber-700">
            {lastCancel.blocked.map((b) => (
              <li key={b.id}>
                <code className="rounded bg-amber-100 px-1">{b.id}</code> — {b.reason}
              </li>
            ))}
          </ul>
        </Card>
      )}

      <div className="mb-4 flex flex-wrap items-center gap-3">
        <p className="text-sm text-slate-600">
          Potential saving:{' '}
          <span className="font-semibold text-slate-900">
            {money(propose.monthly_saving_usd)}/mo · {money(propose.annual_saving_usd)}/yr
          </span>
        </p>
        <div className="ml-auto flex gap-2">
          <button
            type="button"
            disabled={selected.size === 0 || busy !== null}
            onClick={handleApprove}
            className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-50"
          >
            {busy === 'approve'
              ? 'Approving…'
              : `Approve selected (${selected.size})`}
          </button>
          <button
            type="button"
            disabled={busy !== null}
            onClick={handleCancel}
            className="rounded-lg bg-red-600 px-4 py-2 text-sm font-semibold text-white hover:bg-red-700 disabled:opacity-50"
          >
            {busy === 'cancel' ? 'Cancelling…' : 'Cancel approved'}
          </button>
        </div>
      </div>

      {propose.flagged.length === 0 ? (
        <EmptyState message="Nothing flagged — no cancellation proposals right now." />
      ) : (
        <div className="space-y-3">
          {propose.flagged.map((sub) => (
            <Card key={sub.id} className="p-4">
              <label className="flex cursor-pointer items-start gap-3">
                <input
                  type="checkbox"
                  checked={selected.has(sub.id)}
                  onChange={() => toggle(sub.id)}
                  className="mt-1 h-4 w-4 accent-indigo-600"
                />
                <span className="min-w-0 flex-1">
                  <span className="flex flex-wrap items-center gap-2">
                    <span className="font-semibold text-slate-900">
                      {sub.merchant} · {sub.plan_name}
                    </span>
                    <WasteScoreBadge score={sub.waste_score} />
                    <span className="text-sm font-semibold text-slate-900">
                      {money(sub.price_monthly_usd)}
                      <span className="font-normal text-slate-500">/mo</span>
                    </span>
                  </span>
                  <span className="mt-1 block text-sm text-slate-500">
                    {sub.reason ?? 'Unused subscription'}
                    {sub.last_used_days_ago !== null &&
                      sub.last_used_days_ago !== undefined &&
                      ` · last used ${sub.last_used_days_ago} days ago`}
                  </span>
                </span>
              </label>
            </Card>
          ))}
        </div>
      )}

      {propose.kept.length > 0 && (
        <div className="mt-8">
          <h2 className="mb-3 text-base font-semibold text-slate-900">
            Kept — looks worth keeping
          </h2>
          <div className="space-y-2">
            {propose.kept.map((sub) => (
              <Card key={sub.id} className="flex flex-wrap items-center gap-3 px-4 py-3">
                <span className="min-w-0 flex-1 font-medium text-slate-700">
                  {sub.merchant} · {sub.plan_name}
                </span>
                <WasteScoreBadge score={sub.waste_score} />
                <span className="text-sm text-slate-600">
                  {money(sub.price_monthly_usd)}/mo
                </span>
              </Card>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
