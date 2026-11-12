"""Cancellations — the approval gate lives here.

HARD RULE: no approval, no cancellation, ever. A flagged subscription
without an approval goes on the ``blocked`` list and the attempt is
logged as CANCEL_BLOCKED. Non-flagged subscriptions are NEVER cancelled,
even if approved.
"""
import json
import logging

from sqlalchemy.orm import Session

from app import repositories
from app.models import User
from app.services.proposals import propose

logger = logging.getLogger(__name__)


def cancel_approved(db: Session, user: User, client):
    proposal = propose(db, user, client)
    cancelled: list[str] = []
    blocked: list[dict] = []
    monthly_saving = 0.0

    for item in proposal["flagged"]:
        sub_id = item["id"]
        if not repositories.has_approval(db, user.id, sub_id):
            blocked.append({"id": sub_id, "reason": "no approval"})
            repositories.log_audit(
                db, user.id, "CANCEL_BLOCKED", "subscription", sub_id,
                "Cancellation blocked: no approval recorded",
            )
            continue
        try:
            result = client.cancel_subscription(sub_id, "Unused subscription")
        except Exception as exc:  # noqa: BLE001 - PayPal failure != cancel
            logger.warning("cancel failed for %s: %s", sub_id, exc)
            blocked.append({"id": sub_id, "reason": f"cancel failed: {exc}"})
            repositories.log_audit(
                db, user.id, "CANCEL_BLOCKED", "subscription", sub_id,
                f"Cancellation failed: {exc}",
            )
            continue
        status_value = result.get("status") if isinstance(result, dict) else None
        if status_value == "CANCELLED":
            sub = repositories.get_subscription(db, user.id, sub_id)
            if sub is not None:
                sub.status = "CANCELLED"
                db.commit()
            repositories.record_cancellation(
                db, user.id, sub_id,
                paypal_response=json.dumps(result),
                reason="Unused subscription",
            )
            repositories.log_audit(
                db, user.id, "CANCEL", "subscription", sub_id,
                f"Cancelled via PayPal; saved ${item['price_monthly_usd']:.2f}/month",
            )
            cancelled.append(sub_id)
            monthly_saving += item["price_monthly_usd"]
        else:
            blocked.append(
                {"id": sub_id, "reason": f"PayPal returned status {status_value}"}
            )
            repositories.log_audit(
                db, user.id, "CANCEL_BLOCKED", "subscription", sub_id,
                f"PayPal returned status {status_value}",
            )

    monthly_saving = round(monthly_saving, 2)
    # still_active = ALL of the user's subscriptions still ACTIVE
    # (same meaning as in GET /report), not only the flagged ones.
    still_active = [
        sub.id
        for sub in repositories.list_subscriptions(db, user.id, status="ACTIVE")
    ]
    return {
        "cancelled": cancelled,
        "blocked": blocked,
        "monthly_saving_usd": monthly_saving,
        "annual_saving_usd": round(monthly_saving * 12, 2),
        "still_active": still_active,
    }
