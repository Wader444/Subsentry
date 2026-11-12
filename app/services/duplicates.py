"""Duplicate detection — same merchant billed twice.

Groups the user's ACTIVE subscriptions by normalised merchant name;
within a group, a pair counts as a duplicate when the prices are within
10% of each other OR the plan names match.
"""
import logging

from sqlalchemy.orm import Session

from app import repositories
from app.models import User
from app.services.subscriptions import enrich

logger = logging.getLogger(__name__)


def find_duplicates(db: Session, user: User):
    subs = repositories.list_subscriptions(db, user.id, status="ACTIVE")
    groups: dict[str, list] = {}
    for sub in subs:
        key = (sub.merchant or "").lower().strip()
        if key:
            groups.setdefault(key, []).append(sub)

    duplicates = []
    for merchant_key, members in groups.items():
        if len(members) < 2:
            continue
        is_duplicate = False
        reasons = set()
        for i in range(len(members)):
            for j in range(i + 1, len(members)):
                a, b = members[i], members[j]
                price_a = a.price_monthly_usd or 0.0
                price_b = b.price_monthly_usd or 0.0
                if price_a and price_b:
                    diff = abs(price_a - price_b) / max(price_a, price_b)
                    if diff <= 0.10:
                        is_duplicate = True
                        reasons.add("similar price")
                if (a.plan_name or "").strip().lower() == (b.plan_name or "").strip().lower() \
                        and (a.plan_name or "").strip():
                    is_duplicate = True
                    reasons.add("same plan name")
        if is_duplicate:
            duplicates.append({
                "merchant": members[0].merchant,
                "subscription_ids": [sub.id for sub in members],
                "subscriptions": [enrich(sub) for sub in members],
                "reason": (
                    f"Multiple active subscriptions from {members[0].merchant} "
                    f"with {', '.join(sorted(reasons))}."
                ),
            })
    repositories.log_audit(
        db, user.id, "DUPLICATE_CHECK", None, None,
        f"duplicate_groups={len(duplicates)}",
    )
    return duplicates
