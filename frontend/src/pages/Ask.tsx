import { useState, type FormEvent } from 'react'
import { api } from '../api/client'
import type { AskResponse } from '../api/types'
import { Card, PageHeader } from '../components/ui'

const SUGGESTIONS = [
  'Which subscriptions am I paying for but not using?',
  'How much could I save per month?',
  'What is my most expensive subscription?',
  'Which subscriptions are still active?',
]

export default function Ask() {
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState<AskResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  const ask = async (q: string) => {
    const trimmed = q.trim()
    if (!trimmed) return
    setBusy(true)
    setError(null)
    setAnswer(null)
    try {
      const res = await api.get<AskResponse>(`/ask?q=${encodeURIComponent(trimmed)}`)
      setAnswer(res)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not get an answer.')
    } finally {
      setBusy(false)
    }
  }

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    void ask(question)
  }

  return (
    <div>
      <PageHeader
        title="Ask SubSentry"
        subtitle="Ask about your own subscriptions. Answers come only from your records — anything else is refused."
      />

      <Card className="p-5">
        <form onSubmit={handleSubmit} className="flex flex-col gap-3 sm:flex-row">
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="e.g. Which subscriptions am I paying for but not using?"
            className="min-w-0 flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          />
          <button
            type="submit"
            disabled={busy || question.trim() === ''}
            className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-50"
          >
            {busy ? 'Asking…' : 'Ask'}
          </button>
        </form>
        <div className="mt-4 flex flex-wrap gap-2">
          {SUGGESTIONS.map((s) => (
            <button
              key={s}
              type="button"
              onClick={() => {
                setQuestion(s)
                void ask(s)
              }}
              className="rounded-full bg-slate-100 px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-200"
            >
              {s}
            </button>
          ))}
        </div>
      </Card>

      {error && (
        <p className="mt-4 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </p>
      )}

      {answer && (
        <Card className="mt-4 p-5">
          <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
            You asked
          </p>
          <p className="mt-1 font-medium text-slate-900">{answer.question}</p>
          <p className="mt-4 whitespace-pre-wrap text-sm leading-relaxed text-slate-700">
            {answer.answer}
          </p>
        </Card>
      )}
    </div>
  )
}
