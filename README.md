# SubSentry

An AI agent that finds PayPal subscriptions you pay for but don't use — and
cancels them with your approval, through PayPal's Subscriptions API
(sandbox). No approval, no cancellation, ever.

## Quick start

```bash
pip install -r requirements.txt
cp .env.example .env
python seed.py
uvicorn app.main:app --reload
cd frontend && npm install && npm run dev
```

API on http://localhost:8000, UI on http://localhost:5173.

## Docker

```bash
docker compose up --build
```

- API: http://localhost:8000
- UI: http://localhost:4173 (production preview) or http://localhost:5173 (dev)
- Postgres: localhost:5432

## Tests

```bash
pytest -q
```

## Sandbox credentials (for judges)

Sandbox only — no real payments, no real money moves. Put your sandbox
client ID and secret in `.env` (from developer.paypal.com), then run:

```bash
python check_sandbox.py
```

and expect `Sandbox check: PASS`. If the sandbox fights you for more than
an hour, leave `PAYPAL_MODE=mock` — the mock client runs the full demo
offline, and the demo video should say so.

## Demo walkthrough

1. Log in as `demo@subsentry.local` / `demo1234`.
2. Inventory: 8 subscriptions, $122.92/month total.
3. Propose flags FitGym Pro ($12.99), CloudBox Pro ($9.99) and
   NewsDaily Premium ($7.99) — $30.97/month of waste.
4. Approve the three flagged subscriptions, then cancel.
5. Report: $30.97/month saved, $371.64/year, 5 subscriptions still active.

## Architecture

```
routers -> services -> repositories -> SQLAlchemy models
```

- **Routers** (`app/routers/`): thin HTTP layer — auth, subscriptions,
  inventory, propose/approve/cancel, report, ask, duplicates, audit,
  notifications, admin.
- **Services** (`app/services/`): scoring, approval gate, duplicate
  detection, Q&A over the user's own records, notifications, scheduler.
- **Repositories / models**: SQLAlchemy 2.0 models (SQLite by default,
  Postgres-ready via `DATABASE_URL`).
- **PayPal client** (`app/paypal_client.py`): one interface, two
  implementations — real sandbox client and mock client. The mock is
  used when `PAYPAL_MODE=mock` or when no sandbox credentials are set.
- **Scheduler**: APScheduler job that re-scores subscriptions and sends
  notifications (disabled in tests via `SUBSENTRY_SCHEDULER=0`).
- **Notifications**: in-app notification list with read/unread state.

Scoring (frozen): `waste = 0.7 * recency + 0.3 * price`, where
`recency` is 0.0 (<=30 days since last use) / 0.4 (31–60) / 0.7 (61–90) /
1.0 (90+ days) and `price = min(price_monthly_usd / 30, 1.0)`.
Flag at `waste >= 0.55` AND `last_used_days_ago >= 45`.

## Dates

- Freeze: **Thu 12 Nov 2026, 22:00 IST**
- Hard Devpost deadline: **Fri 13 Nov 2026, 01:30 IST**

(12 Nov 2026 is a Thursday.)
