"""Subscription business logic + PayPal sync.

``enrich`` is the single place a stored subscription becomes the
agent-facing dict (adds live status, waste score, flag, reason).
"""
import logging

from sqlalchemy.orm import Session

from app import repositories
from app.models import User
from app.scoring import reason as score_reason
from app.scoring import should_flag, waste_score

logger = logging.getLogger(__name__)


def enrich(sub, live_status=None):
    """Stored subscription -> enriched dict for inventory/propose/sync."""
    price = sub.price_monthly_usd or 0.0
    days = sub.last_used_days_ago or 0
    return {
        "id": sub.id,
        "merchant": sub.merchant,
        "plan_name": sub.plan_name,
        "category": sub.category,
        "price_monthly_usd": price,
        "currency": sub.currency or "USD",
        "status": sub.status,
        "started_on": sub.started_on,
        "next_billing_on": sub.next_billing_on,
        "last_used_days_ago": days,
        "live_status": live_status if live_status is not None else sub.status,
        "waste_score": waste_score(price, days),
        "flagged": should_flag(price, days),
        "reason": score_reason(
            {"merchant": sub.merchant, "last_used_days_ago": days,
             "price_monthly_usd": price}
        ),
    }


def live_status_for(client, sub):
    """Live PayPal status for one subscription; stored status on any error."""
    try:
        details = client.show_subscription_details(
            sub.paypal_subscription_id or sub.id
        )
        if isinstance(details, dict):
            return details.get("status", sub.status)
        return str(details)
    except Exception as exc:  # noqa: BLE001 - PayPal down must not break us
        logger.warning("live status check failed for %s: %s", sub.id, exc)
        return sub.status


def sync_from_paypal(db: Session, user: User, sub_id: str, client):
    """Verify one subscription's live PayPal status; update stored status
    if it changed; log SYNC. Returns the enriched dict."""
    sub = repositories.get_subscription(db, user.id, sub_id)
    if sub is None:
        return None
    live = live_status_for(client, sub)
    if live and live != sub.status:
        old = sub.status
        sub.status = live
        db.commit()
        db.refresh(sub)
        logger.info("subscription %s status %s -> %s", sub.id, old, live)
    repositories.log_audit(
        db, user.id, "SYNC", "subscription", sub.id,
        f"live_status={live}, stored_status={sub.status}",
    )
    return enrich(sub, live_status=live)
