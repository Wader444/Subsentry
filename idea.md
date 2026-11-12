# SubSentry — the idea

## One line

**SubSentry is an AI agent that finds the subscriptions you are paying for but not using — and cancels them, with your approval, through PayPal.**

## The problem (real, measured)

People do not know what their subscriptions cost them. In C+R Research's
survey of 1,000 US consumers (2022, the latest edition of the study),
people guessed they spent **$86 a month** on subscriptions; when they
itemised them, the real figure was **$219 a month** — a $133/month gap,
2.5x what they thought. **42% were still paying for a service they had
stopped using**, 74% said recurring charges are easy to forget, and 72%
had everything on autopay. A 2025 CNET/YouGov survey found about
**$205 a year** going to subscriptions the respondent had not used in
the prior 30 days.

The mechanism is not laziness. Subscriptions are designed to be
forgotten: small charges, scattered across months, no decision point
after sign-up, and cancellation buried three menus deep. The person
losing the money is the only one with no agent on their side — the
merchant has billing infrastructure, the user has a bank statement.

## Who it is for

Anyone who pays for things with PayPal — which is the point. The first
user is a student / young professional with 5–15 recurring
subscriptions (streaming, music, fitness apps, cloud storage, news,
software, food). The same agent serves freelancers and small businesses
whose SaaS stack quietly grows: same problem, larger numbers.

## How it works (the agent loop)

```
INVENTORY → ANALYSE → PROPOSE → APPROVE → ACT → CONFIRM
```

1. **Inventory.** SubSentry connects to the user's PayPal sandbox
   account and inventories their active subscriptions. PayPal's API
   has no list-all endpoint, so SubSentry stores each subscription ID
   in its own database when it is created or first seen, and verifies
   its live status through the API on every run.
2. **Analyse.** For each subscription the agent works out a waste
   score from two honest signals: how long since it was last used,
   and what it costs. An LLM categorises the merchant (streaming,
   fitness, news…) and writes a one-line, plain-English reason for
   each flag. The score itself is a deterministic formula, so the
   demo works even if the LLM key fails (see implementation.md).
3. **Propose.** The agent ranks the subscriptions by money wasted
   and proposes cancellations: which ones, how much each saves per
   month and per year, and what you keep.
4. **Approve.** Nothing is cancelled by the agent alone. The user
   ticks the ones they agree with — the approval gate is a product
   rule, not a setting. No approval, no cancellation, ever.
5. **Act.** For each approved subscription, the agent cancels it
   through PayPal's Subscriptions API and records the confirmation.
6. **Confirm.** A savings report: what was cancelled, what it cost,
   what you save per month and per year, and what is still active.
   The user can also ask in plain English — "What am I paying for
   that I don't use?" — and the agent answers from the subscription
   records.

## Worked example (illustrative — mock sandbox seed data)

Eight seeded subscriptions, $122.92/month total:

| Subscription | Cost/mo | Last used | Verdict |
|---|---|---|---|
| StreamFlix (streaming) | $15.99 | 12 days ago | Keep |
| MusicWave (music) | $10.99 | 2 days ago | Keep |
| GameVault (gaming) | $14.99 | 5 days ago | Keep |
| DesignSuite (software) | $19.99 | 8 days ago | Keep |
| MealKit Weekly (food) | $29.99 | 4 days ago | Keep |
| FitGym Pro (fitness app) | $12.99 | 94 days ago | **Cancel** |
| CloudBox Pro (storage) | $9.99 | 61 days ago | **Cancel** |
| NewsDaily Premium (news) | $7.99 | 120 days ago | **Cancel** |

The agent proposes cancelling three: **$30.97/month saved, $371.64/year**,
with a one-line reason for each. The user approves all three, the agent
cancels them through PayPal, and the report shows the new total:
$91.95/month.

## Why PayPal and AI are both central (not bolted on)

- **PayPal is the action.** The subscriptions live in PayPal, the
  cancellation happens through PayPal's Subscriptions API, and the
  money saved is PayPal money. Remove PayPal and there is no product.
- **AI is the judgement.** The agent decides what counts as waste
  (categorisation, recency + cost reasoning, plain-English
  explanations) and answers questions about the user's own spending.
  Remove AI and it is a settings page with a list.
- **The agent pattern is the novelty.** This is not a dashboard and
  not a chatbot. It is an agent with tools that acts on the user's
  behalf inside a hard guardrail (approval before any cancellation),
  which is exactly the "agentic commerce" the hackathon rewards.

## Why it wins (mapped to the judging criteria)

- **Technological Implementation** — real PayPal Subscriptions API
  calls in the sandbox (create, verify, cancel), a real agent loop
  with tools, a real approval gate. Not a mockup.
- **Design** — a complete product experience: inventory → proposal →
  approval → savings report, in one flow, not a technical demo.
- **Potential Impact** — the problem is measured ($133/month gap,
  42% paying for something unused) and the demo proves the saving
  on the user's own subscriptions, in dollars per year.
- **Innovation** — the agent acts where dashboards only inform:
  it closes the loop from "you are wasting money" to "it is
  cancelled", with the user still in control.
- **Presentation** — the 3-minute video has a natural arc: the
  total ($122.92) → the three flags → the approval → the
  cancellations landing in PayPal → the new total ($91.95).

Prize angles: **Most Impactful** ($5,000), **Best Use of PayPal + AI**
($5,000), **Best Use of Agentic Commerce** ($5,000).

## What it is not (scope, stated honestly)

- Not a bank account aggregator. It works with PayPal subscriptions
  only — that is the hackathon's requirement and the product's edge.
- Not live money. Everything runs in PayPal's free sandbox with
  virtual accounts; no real payment is ever touched.
- Not autonomous cancellation. The approval gate is the product:
  the agent proposes, the human disposes.
- "Last used" comes from the seed data in the demo (labelled mock,
  like CartPilot's catalog). In production it would come from the
  merchant or the user's activity; the hackathon proves the loop,
  not the data pipeline.

## Sources

- PayPal AI Hackathon, Devpost — rules and main page, read 2026-11-10:
  https://paypalaihackathon.devpost.com/ and /rules
- C+R Research, "Subscription Service Statistics and Costs" (2022,
  n=1,000 US consumers): $86 guessed vs $219 actual per month,
  42% paying for an unused service, 74% forget charges easily.
  2022 is the latest edition — treat as directional.
- CNET/YouGov (2025): ~$205/year on subscriptions unused in the
  prior 30 days.
- PayPal Subscriptions API + official MCP server (sandbox default),
  verified via PayPal's agent-toolkit docs, 2026-11-10.
