import { useCallback, useEffect, useState } from 'react'
import { api } from '../api/client'
import type { NotificationItem, NotificationsResponse } from '../api/types'
import { formatDateTime } from '../lib/format'
import {
  Card,
  EmptyState,
  ErrorState,
  LoadingState,
  PageHeader,
} from '../components/ui'

export default function Notifications() {
  const [items, setItems] = useState<NotificationItem[]>([])
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [marking, setMarking] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await api.get<NotificationsResponse>('/notifications')
      setItems(data.notifications)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load notifications.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  const markRead = async (id: string) => {
    setMarking(id)
    try {
      await api.post(`/notifications/${id}/read`)
      setItems((prev) =>
        prev.map((n) => (n.id === id ? { ...n, is_read: true } : n)),
      )
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not mark as read.')
    } finally {
      setMarking(null)
    }
  }

  const unread = items.filter((n) => !n.is_read).length

  if (loading) return <LoadingState label="Loading notifications…" />
  if (error) return <ErrorState message={error} onRetry={load} />

  return (
    <div>
      <PageHeader
        title="Notifications"
        subtitle={
          unread > 0
            ? `${unread} unread notification${unread === 1 ? '' : 's'}`
            : 'You are all caught up.'
        }
      />

      {items.length === 0 ? (
        <EmptyState message="No notifications yet." />
      ) : (
        <div className="space-y-3">
          {items.map((n) => (
            <Card
              key={n.id}
              className={`p-4 ${n.is_read ? '' : 'border-indigo-200 bg-indigo-50/40'}`}
            >
              <div className="flex items-start justify-between gap-4">
                <div className="min-w-0">
                  <p className="flex items-center gap-2 font-semibold text-slate-900">
                    {n.title}
                    {!n.is_read && (
                      <span className="rounded-full bg-indigo-600 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-white">
                        New
                      </span>
                    )}
                  </p>
                  <p className="mt-1 text-sm text-slate-600">{n.body}</p>
                  <p className="mt-2 text-xs text-slate-400">
                    {formatDateTime(n.created_at)}
                  </p>
                </div>
                {!n.is_read && (
                  <button
                    type="button"
                    disabled={marking === n.id}
                    onClick={() => markRead(n.id)}
                    className="shrink-0 rounded-lg bg-white px-3 py-1.5 text-xs font-medium text-indigo-600 ring-1 ring-indigo-200 hover:bg-indigo-50 disabled:opacity-50"
                  >
                    {marking === n.id ? 'Marking…' : 'Mark as read'}
                  </button>
                )}
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
