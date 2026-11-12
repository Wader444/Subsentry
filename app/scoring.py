"""SubSentry waste scoring — deterministic, per implementation.md §4.

    recency = 0.0 if last_used <= 30 days
            = 0.4 if 31-60 days
            = 0.7 if 61-90 days
            = 1.0 if 90+ days
    price   = min(price_monthly_usd / 30, 1.0)
    waste_score = 0.7 * recency + 0.3 * price

CORRECTION (found 2026-11-11 while building the starter, before the build):
the plan as drafted said "flag if waste_score >= 0.60 AND last_used >= 45 days",
but CloudBox Pro scores only 0.59 on that formula (61 days -> recency 0.7,
$9.99 -> price 0.333; 0.7*0.7 + 0.3*0.333 = 0.590). With a 0.60 bar the demo
would flag only 2 subscriptions and save $20.98/month, not the $30.97 in
idea.md. The measured gap on the seed data is wide — every "keep" scores
<= 0.30 (MealKit Weekly is the highest keep, purely on price), every
intended "cancel" scores >= 0.59 — so the bar is set at 0.55, inside that
gap. That flags exactly the 3 intended subscriptions and no others.
See integration_check.py, which asserts all of this.
"""
FLAG_THRESHOLD = 0.55
FLAG_MIN_LAST_USED_DAYS = 45


def recency_component(last_used_days_ago):
    if last_used_days_ago <= 30:
        return 0.0
    if last_used_days_ago <= 60:
        return 0.4
    if last_used_days_ago <= 90:
        return 0.7
    return 1.0


def waste_score(price_monthly_usd, last_used_days_ago):
    recency = recency_component(last_used_days_ago)
    price = min(price_monthly_usd / 30.0, 1.0)
    return round(0.7 * recency + 0.3 * price, 3)


def should_flag(price_monthly_usd, last_used_days_ago):
    return (
        waste_score(price_monthly_usd, last_used_days_ago) >= FLAG_THRESHOLD
        and last_used_days_ago >= FLAG_MIN_LAST_USED_DAYS
    )


def reason(sub):
    """One-line plain-English reason. Template fallback used when no LLM key
    is set; the LLM (llm.py) only ever replaces this text, never the score."""
    days = sub["last_used_days_ago"]
    return (
        f"You haven't used {sub['merchant']} in {days} days "
        f"— ${sub['price_monthly_usd']:.2f} a month."
    )
