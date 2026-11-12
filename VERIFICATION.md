# SubSentry Enterprise — Verification

Restructured and re-verified by the coordinator on Thu 12 Nov 2026,
~22:40 IST, in
`~/workspace/your_files/paypal-hackathon/subsentry-enterprise/`.
Python 3.12.3, venv `~/.venvs/subsentry-venv` (pinned requirements.txt).
Node v24.22.1, npm 10.9.4. All commands run from the project root
unless stated.

**The old Python UI framework is gone.** The UI is now React +
Vite + Tailwind CSS (`frontend/`). A case-insensitive search of the
whole project for the old framework's name returns zero matches
(see §5). The previous zip (21:04 IST, old UI) is
superseded by this build.

## 1. Tests — 47 passed, 0 failed

```
PAYPAL_MODE=mock SUBSENTRY_SCHEDULER=0 ~/.venvs/subsentry-venv/bin/pytest -q
47 passed, 421 warnings in 20.79s
```

Re-run by the coordinator after the restructure — unchanged from the
previous build, as the backend was not touched except for CORS (see
§5). Warnings are deprecation-only (`datetime.utcnow()` in our code
and in python-jose); no failures. Covers: scoring bands for all 8
seed subscriptions, flag-only-3, approval gate (0 cancelled without
approval, blocked logged), approve→cancel flow, auth
register/login/me + 401s, per-user isolation, subscription CRUD,
duplicate detection, Q&A refusal with no data and on unrelated
questions, /health, /inventory, /propose, /report.

## 2. Live server — real uvicorn + real HTTP (mock PayPal) + Vite preview

Backend seeded and served with the database in /tmp only
(`DATABASE_URL="sqlite:////tmp/subsentry-react-live.db"`), so no
`.db` lands in the deliverable. Frontend served with
`npm run preview` on port 4173 from `frontend/`.

```
DATABASE_URL="sqlite:////tmp/subsentry-react-live.db" PAYPAL_MODE=mock \
  SUBSENTRY_SCHEDULER=0 SECRET_KEY=verify-secret \
  ~/.venvs/subsentry-venv/bin/python seed.py
# seeded 8 new subscription(s) for demo user (8 total, $122.92/month)
uvicorn app.main:app --host 127.0.0.1 --port 8001   # mock mode
npm run preview -- --port 4173 --host 127.0.0.1    # from frontend/
```

Results (via `curl`, script `/tmp/smoke_react.sh`):

| Check | Result |
|---|---|
| GET http://127.0.0.1:4173/ (Vite preview) | 200, title "SubSentry — Stop paying for subscriptions you don't use" |
| CORS preflight, Origin http://localhost:5173 | 200, `access-control-allow-origin: http://localhost:5173` |
| POST /auth/login (form-encoded, demo) | 200, JWT returned (144 chars) |
| GET /inventory | 200, 8 subs, flagged exactly CloudBox Pro, FitGym Pro, NewsDaily Premium; total $122.92 |
| GET /propose | 200, monthly $30.97, annual $371.64, total $122.92 |
| POST /cancel (no approval) | 200, cancelled 0, blocked 3, still_active 8 |
| POST /approve (3 flagged) | 200, approved [SEED-06, SEED-07, SEED-08] |
| POST /cancel (approved) | 200, cancelled 3, monthly $30.97, still_active 5 |
| GET /report | 200, monthly $30.97, annual $371.64 |
| GET /ask "What am I paying for that I don't use?" | 200, names FitGym/CloudBox/NewsDaily + $30.97/month |
| GET /ask "What is the weather today?" | 200, refusal: "I can only answer from your subscription records…" |
| GET /admin/stats as demo user | 403 |
| GET /inventory with no token | 401 |
| GET /notifications | 200, `{"notifications": []}` |

The /ask answers above were confirmed on a fresh seeded DB by the
previous build's live check (names the three flags + savings), and
re-confirmed here after approve→cancel. Both servers were stopped
afterwards (ports 8001 and 4173 verified closed, no stray
uvicorn/vite/esbuild processes).

## 3. React frontend — build verified by the coordinator

```
cd frontend && npm install && npm run build
vite v7.3.8 building client environment for production...
✓ 58 modules transformed.
dist/index.html                   0.44 kB │ gzip:  0.30 kB
dist/assets/index-DeoCaQhT.css   19.96 kB │ gzip:  4.71 kB
dist/assets/index-KaRoCPKq.js   308.98 kB │ gzip: 92.50 kB
✓ built in 3.71s
```

Zero TypeScript errors. Stack: Vite 7 + React 19 + TypeScript 5.8 +
Tailwind CSS v4 (`@tailwindcss/vite`) + react-router-dom 7.
`npm run build` was run twice (builder + coordinator) with identical
output hashes. `vite preview` serves HTTP 200 with the app HTML (see
§2). Pages (12): Login, Register, Dashboard, Inventory, Proposals,
Report, Ask, Notifications, Duplicates, Audit, Settings, Admin — all
wired to the live API shapes in §2, no mock data in the UI, loading
and error states on every page. A case-insensitive search of
`frontend/` for the old framework's name (excluding
node_modules/dist): zero matches.

## 4. Sandbox check (no credentials — expected exit 2)

```
PAYPAL_MODE= ~/.venvs/subsentry-venv/bin/python check_sandbox.py
# Sandbox check: FAIL — PAYPAL_CLIENT_ID / PAYPAL_CLIENT_SECRET not set.
# exit=2
```

No real sandbox credentials exist in this workspace, so a real token
call could not be proven here — the check correctly reports that
instead of pretending. With sandbox credentials in `.env` it prints
`Sandbox check: PASS` (token length only, never the token).

## 5. What changed in this restructure — and what did not

- **Removed:** the old single-file Python UI app (deleted), the
  old UI framework's pinned dependency from `requirements.txt`, the
  old `ui` service from `docker-compose.yml` (replaced by a
  `frontend` Node service), `SUBSENTRY_API_URL` from `.env.example`
  (now `VITE_API_URL`), and every mention of the old framework from
  `README.md`, this file, the Devpost draft and `implementation.md`.
- **Backend change — CORS only:** `app/main.py` gained
  `CORSMiddleware` allowing `http://localhost:5173` and
  `http://localhost:4173`. Verified live by preflight in §2.
- **Frozen contracts — unchanged:**
  ```
  diff app/scoring.py ../subsentry-starter/app/scoring.py       # identical
  diff app/paypal_client.py ../subsentry-starter/app/paypal_client.py  # identical
  diff app/__init__.py ../subsentry-starter/app/__init__.py     # identical
  ```
  Scoring formula, 0.55 flag bar, 45-day minimum, mock/sandbox
  client, and the `.env` loader are byte-identical to the verified
  starter. No endpoint shape changed.
- **Zero-matches proof:** a case-insensitive search of the whole
  project tree for the removed framework's name (excluding
  `node_modules` and `dist`) returns no output and exits 1 — no
  file, doc, or dependency mentions it anywhere.
- **Zip hygiene:** the zip contains no `node_modules`, no `dist`, no
  `.env`, no `__pycache__`, no `.db`, no `.pytest_cache`, no
  credentials (grep-checked). `docker-compose.yml` parses
  (services: `api`, `frontend`, `db`).

## 6. What was NOT verified

- **Docker image not built** — no Docker CLI/daemon in this VM.
  `frontend/Dockerfile` (node:20, `npm ci`, `npm run build`,
  preview on 4173) and the api Dockerfile are written per spec and
  the compose YAML parses, but `docker compose up --build` was not
  run.
- **Real PayPal sandbox token** — see §4; needs Cherish's sandbox
  credentials in `.env` and `python check_sandbox.py`.
- **Postgres** — the app defaults to SQLite; Postgres wiring is via
  `DATABASE_URL` + compose only, not run live here.
- **Scheduler jobs** — APScheduler code is in place (6-hour refresh,
  Monday 09:00 digest) but the jobs were disabled
  (`SUBSENTRY_SCHEDULER=0`) for testing and have not fired live.
- **SMTP email** — sender only activates when SMTP env vars are set;
  otherwise it logs and skips. Not exercised with a real server.
- **React UI in a live browser** — the preview serves HTTP 200 and
  every page is wired to API endpoints verified live in §2, but no
  live-browser session clicked through the UI.
- **Demo video / Devpost form** — need a human (teammate); the
  Devpost draft was delivered separately.

## 7. Run it

```
pip install -r requirements.txt
cp .env.example .env          # fill in sandbox creds if you have them
python seed.py                # demo@subsentry.local / demo1234, admin@subsentry.local / admin1234
uvicorn app.main:app --reload # http://localhost:8000
cd frontend && npm install && npm run dev   # http://localhost:5173
# production preview: npm run build && npm run preview   # http://localhost:4173
pytest -q
```
