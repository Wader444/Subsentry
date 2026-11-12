# SubSentry — implementation plan (team of 2)

## 0. The hackathon, verified (read 2026-11-10)

| Fact | Value |
|---|---|
| Hackathon | PayPal AI Hackathon — "Build What's Next with PayPal and AI", global, online |
| Page | https://paypalaihackathon.devpost.com/ (rules: /rules) |
| Tracks / problem statements | **None.** No prescribed statements, no tracks. Any agent, app, automation or payment experience — the only requirement is that it **meaningfully uses both PayPal and AI** |
| Submission deadline | **Thu Nov 12, 2026, 12:00 PM PT = Fri Nov 13, 01:30 AM IST** — about **50 hours** from the evening of Nov 10 |
| Judging | Dec 1–15, 2026; winners announced ~Dec 21, 2026 |
| Prizes | **$69,750 total** ($67,500 cash + $2,250 Render credits). 1st $12,000, 2nd $8,000, 3rd $5,000. Most Creative / Most Impactful / Best Demo Delivery / Best Use of PayPal + AI / Best Use of Agentic Commerce: $5,000 each |
| Team | Individual or team; no maximum team size in the rules. One Representative submits for the team. India is **not** in the excluded list |
| Submission | Public repo (GitHub/GitLab/Bitbucket) **with a LICENSE file visible at the top of the repo**; demo video **under 3 minutes** on YouTube (public); text description; tools used identified; functional demo via setup instructions **or** a hosted URL (a mockup does not count) |
| Judging criteria | Technological Implementation; Design; Potential Impact; Innovation/Idea; Presentation |
| Project | Must be new, or an existing project **significantly updated** during the submission period. Sandbox only — no live money |

**Target for this plan: submit by 22:00 IST on Wed Nov 12** — three and a
half hours before the deadline, so the video upload and the Devpost form
cannot eat the submission.

## 1. The idea (one paragraph)

SubSentry is an AI agent that finds the subscriptions you are paying for
but not using — and cancels them, with your approval, through PayPal.
It inventories the user's PayPal subscriptions, scores each one for
waste from recency + cost, proposes cancellations ranked by money saved,
waits for the user's approval, cancels through PayPal's Subscriptions
API, and reports the saving per month and per year. Full idea, worked
example and sources: `idea.md`.

## 2. Tech stack — and why each choice (including why not Neo4j)

| Piece | Choice | Why |
|---|---|---|
| Language | **Python 3.11+** | Both members know it; fastest to a working demo |
| API | **FastAPI** | Cherish's strength; the agent and the UI share one API |
| UI | **Streamlit** | Fastest complete product experience; no frontend build step |
| Database | **SQLite** (one file, `subsentry.db`) | The data is tabular: subscriptions, transactions, cancellations, approvals. Zero server, zero setup, file lives in the repo folder. For ~30 records, anything heavier is overhead |
| PayPal | **PayPal REST API, sandbox, direct calls with `requests`** | The Subscriptions API is small and predictable: OAuth2 client credentials → Bearer token, then create plan / create subscription / show details / cancel. No SDK magic to debug at 2 AM |
| LLM | **One swappable `generate()` function** (same pattern as the RAG spec) | Any provider's key works; the prompts are the product, not the provider |
| Secrets | **`.env` at the project root, gitignored** | PayPal client ID/secret + LLM key. Never in code, never in chat |

### Why not Neo4j (asked for explicitly — the honest answer)

The data has no graph problem in it. Subscriptions relate to a user
1:N, transactions relate to a subscription 1:N, a cancellation relates
to one subscription. There is no traversal, no path-finding, no
many-to-many relationship to query. A graph database would add a
server to install, a driver to learn, and Cypher to debug — for zero
benefit on this data, inside a 50-hour window. Neo4j was the right
call for CartPilot, where matching across platforms genuinely is a
graph (`SAME_AS`, `SUBSTITUTE_FOR`). Here it is the wrong tool, so
it is not used.

### Why not Postgres

Same reasoning, smaller scale: Postgres needs a server (local install
or Docker) and connection management, for a database that will hold
about 30 rows in the demo. SQLite is a file. If the project grows
after the hackathon, the schema moves to Postgres unchanged.

### PayPal MCP server — the alternative, and why REST is primary

PayPal ships an official MCP server (`npx @paypal/mcp`, sandbox by
default, sandbox endpoint `mcp.sandbox.paypal.com`) with subscription
tools, and an agent toolkit for LangChain / OpenAI Agents SDK. It is
a legitimate route, and it is the first thing to try **if** the direct
REST calls fight back. It is not the primary route because in 50 hours
the predictable path wins: four REST endpoints, no Node dependency,
no MCP transport to debug. One more reason the approval gate is ours,
not the platform's: the MCP tools carry no confirmation step for
destructive actions, so a cancel must pass through SubSentry's own
approval check before any PayPal call is made.

## 3. Architecture (small, on purpose)

```text
Streamlit UI ──► FastAPI ──► Agent loop ──► PayPal client ──► PayPal sandbox
                    │              │                 │
                    │              ├─► SQLite (subscriptions, approvals)
                    │              └─► LLM generate() (categorise, explain, Q&A)
                    └─► /inventory /propose /approve /cancel /report /ask
```

The agent loop is the CartPilot shape, reused deliberately:

```
INVENTORY → ANALYSE → PROPOSE → APPROVE → ACT → CONFIRM
```

- **INVENTORY**: load subscriptions from SQLite, verify each live
  status with `show_subscription_details`.
- **ANALYSE**: waste score (deterministic, §4) + LLM category and
  one-line reason.
- **PROPOSE**: ranked list with monthly + annual saving.
- **APPROVE**: user ticks subscriptions; approvals are stored as
  rows, not flags in memory.
- **ACT**: `cancel_subscription` per approved ID, with the reason.
- **CONFIRM**: savings report + what is still active.

## 4. Frozen contracts (agree in the first hour, then do not change)

### Subscription (SQLite table `subscriptions`)

```text
id (PayPal subscription ID, text, primary key)
merchant, plan_name, category (LLM-filled, nullable)
price_monthly_usd, currency (USD in sandbox), status (ACTIVE/CANCELLED)
started_on, next_billing_on, last_used_days_ago (seed signal, int)
created_at
```

### Waste score (deterministic — the demo works without an LLM key)

```text
recency = 0.0 if last_used <= 30 days
        = 0.4 if 31–60 days
        = 0.7 if 61–90 days
        = 1.0 if 90+ days
price   = min(price_monthly_usd / 30, 1.0)
waste_score = 0.7 * recency + 0.3 * price
flag for cancellation if waste_score >= 0.60 AND last_used >= 45 days
```

The LLM never sets the score. It categorises the merchant and writes
the one-line reason ("You haven't opened FitGym in 94 days — $12.99 a
month since August"). If the LLM key is missing, the reason falls back
to a template with the same numbers. The demo never dies on a key.

### Agent tools (the only four the loop may call)

| Tool | Input | Output |
|---|---|---|
| `list_subscriptions` | — | subscriptions from SQLite, live status verified |
| `subscription_details` | subscription ID | price, status, next billing date |
| `cancel_subscription` | subscription ID, reason | PayPal confirmation, new status |
| `ask_subscriptions` | plain-English question | answer grounded only in the subscription records |

### PayPal calls (sandbox, `https://api-m.sandbox.paypal.com`)

| Call | Purpose |
|---|---|
| `POST /v1/oauth2/token` (client credentials) | Bearer token, cached until expiry |
| `POST /v1/billing/plans` | Seed: create the 8 mock plans |
| `POST /v1/billing/subscriptions` | Seed: create the 8 subscriptions, store the returned IDs |
| `GET /v1/billing/subscriptions/{id}` | Verify live status before proposing |
| `POST /v1/billing/subscriptions/{id}/cancel` | The one write that matters, approval-gated |

**Known gap, designed around (do not rediscover it at Hour 20):**
PayPal's API has no list-all-subscriptions endpoint. SubSentry stores
every subscription ID in SQLite at creation/seed time and verifies
status live. That is the design, not a workaround found late.

### Seed data (mock, labelled illustrative — 8 subscriptions, $122.92/mo)

StreamFlix $15.99 (12d), MusicWave $10.99 (2d), GameVault $14.99
(5d), DesignSuite $19.99 (8d), MealKit Weekly $29.99 (4d),
FitGym Pro $12.99 (94d), CloudBox Pro $9.99 (61d), NewsDaily Premium
$7.99 (120d). Expected result: 3 cancellations, **$30.97/month,
$371.64/year** saved. See `idea.md` for the full table.

## 5. The team of 2

Assumption: Cherish takes the backend (her strength: Python, FastAPI,
agents, RAG, databases); the teammate takes product + demo. If the
teammate is stronger at backend, swap the UI and API ownership — the
split below is by interface, so it survives a swap.

| Member | Owns | Does not touch |
|---|---|---|
| **Member 1 — Cherish: Backend + PayPal + Agent** | PayPal sandbox setup + seed script; SQLite schema; PayPal client; agent loop + waste score; FastAPI endpoints; LLM `generate()` + categorisation + Q&A | Streamlit layout, video, Devpost form |
| **Member 2 — Teammate: Product + Demo** | Streamlit UI (inventory → propose → approve → report); demo script + video; Devpost submission text; README + repo hygiene (LICENSE!); end-to-end happy-path testing | PayPal client internals, agent loop |

**Branches:** `main` (protected, only merges at sync points),
`feature/backend` (Cherish), `feature/ui-demo` (teammate). Merge to
`main` only at the sync points below. **Never overwrite the repo's
existing README.md or LICENSE** — add project docs under `docs/`
instead (lesson learned on the CartPilot push, Nov 10).

## 6. Hour-by-hour plan (~50h wall clock, ~24 working hours)

### Tonight — Tue Nov 10, 23:30–01:00 IST (~1.5h, both together)

- [ ] Hour 0–0.5: Create the repo, `main` + two feature branches,
  `.env.example`, `requirements.txt`, `LICENSE` (MIT), `README.md`
  skeleton. Register on Devpost + PayPal Developer (one account).
- [ ] Hour 0.5–1.5: PayPal sandbox working: developer account, app
  with client ID/secret in `.env`, one sandbox business account.
  **Sync 0 — the first thing that must work is the token call.**
  If the sandbox fights back for more than an hour, stop and use
  the mock PayPal client (same interface, canned responses) so the
  build is never blocked — swap the real client in later.

### Wed Nov 11 — build day 1 (~10h)

- [ ] Hours 1–4 (Cherish): PayPal client (token, plan, subscription,
  details, cancel) + seed script creating the 8 subscriptions and
  storing their IDs in SQLite. Verify by cancelling one seed
  subscription and re-creating it.
- [ ] Hours 1–4 (Teammate): Streamlit skeleton (inventory table,
  propose list, approve checkboxes, report page) against canned
  data. No backend needed yet.
- [ ] **Sync 1 — Hour 4:** first end-to-end thread: seed → inventory
  shows 8 → propose flags 3.
- [ ] Hours 5–8 (Cherish): agent loop + waste score + FastAPI
  endpoints + LLM `generate()` with the template fallback.
- [ ] Hours 5–8 (Teammate): wire the UI to the real API; write the
  demo script (the 3-minute arc from `idea.md`).
- [ ] **Sync 2 — Hour 8:** full happy path works: inventory →
  propose → approve → cancel (real PayPal sandbox call) → report
  shows $30.97/month saved. If the cancel call fails, the mock
  client carries the demo and the real call becomes a stretch goal
  — say so in the README, do not fake it in the video.

### Thu Nov 12 — build day 2 + submission (~10h, hard stop 22:00 IST)

- [ ] Hours 9–12 (Cherish): Q&A endpoint (`ask_subscriptions`),
  edge cases (already-cancelled, API error, no-LLM-key fallback),
  `integration_check.py` (seed → propose → approve → cancel →
  report, asserts the $30.97 figure).
- [ ] Hours 9–12 (Teammate): polish the UI, record the demo video
  (under 3 minutes), draft the Devpost text + README.
- [ ] **Sync 3 — Hour 12:** dry run of the video, start to finish,
  with a stopwatch. Anything not in the dry run is cut.
- [ ] Hours 13–16 (both): bug fixes only — no new features after
  Hour 12. Re-run the integration check. Record the final video.
- [ ] **Hour 16 — 22:00 IST, submission freeze:** repo public with
  LICENSE visible, video on YouTube (public), Devpost form filled
  and submitted. Do not touch the code after this except a
  one-line README fix.

### MVP cut-line (decide at Sync 2, Hour 8 — no debate after)

Keep: inventory + waste score + propose + approve + cancel + savings
report + video. Cut first: the Q&A endpoint, the MCP route, duplicate
detection, email summaries. A complete loop beats a wide one.

## 7. Risks and mitigations

| Risk | Mitigation |
|---|---|
| PayPal sandbox setup eats hours | Hour 0 timebox (1h). Mock PayPal client with the same interface as the fallback, so the build never blocks |
| No list-all-subscriptions endpoint | Designed around it (§4): IDs stored in SQLite at seed time |
| LLM key missing / quota / slow | Waste score is deterministic; reasons fall back to templates. The demo works with no key at all |
| Cancel call fails in the demo | Mock client carries the demo; README says so honestly. Never fake a cancel in the video |
| Video + Devpost form eat the deadline | Submission freeze at 22:00 IST Nov 12, three and a half hours early; video recorded at Hour 12 dry run |
| Overwriting the team's README/LICENSE | Docs go under `docs/`; the repo's own files are never replaced (CartPilot, Nov 10) |
| Scope creep (MCP, Q&A, duplicates) | Cut-line at §6. Anything not in the dry run at Hour 12 is cut |

## 8. Submission checklist (from the rules — verify each box)

- [ ] Public repo (GitHub/GitLab/Bitbucket) with **LICENSE visible at
  the top of the repo / in the About section**
- [ ] README with setup + run instructions **and sandbox test
  credentials** so judges can run it without asking
- [ ] Demo video **under 3 minutes**, public on YouTube, link on
  the Devpost form, shows the project actually working
- [ ] Devpost text description: problem, features, how PayPal + AI
  are used
- [ ] Tools identified (PayPal Subscriptions API, LLM provider used)
- [ ] All materials in English; original work; no third-party
  trademarks or copyrighted music in the video
- [ ] One Representative submits for the team

## 9. Definition of done

- `python integration_check.py` prints PASS: 8 seeded subscriptions,
  3 flagged, $30.97/month saved, cancel confirmed through the
  sandbox, report correct.
- The video shows the full loop in under 3 minutes, with no step
  faked.
- The repo is public, licensed, and runnable from the README alone.

## Sources

- PayPal AI Hackathon Devpost main page + official rules, read
  2026-11-10: https://paypalaihackathon.devpost.com/ and /rules
- PayPal Subscriptions API + agent toolkit / MCP server docs,
  verified 2026-11-10 (sandbox default; subscription tools:
  create / show details / cancel; no list-all endpoint).
- C+R Research (2022) and CNET/YouGov (2025) subscription figures:
  see `idea.md`.
