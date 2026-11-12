"""Propose: inventory -> analyse with app.scoring -> flagged/kept + savings.

The LLM never touches scores; ``scoring.reason`` supplies the wording.
"""
import logging

from sqlalchemy.orm import Session

from app import repositories
from app.models import User
from app.services.subscriptions import enrich, live_status_for

logger = logging.getLogger(__name__)


def inventory(db: Session, user: User, client):
    """Own subscriptions enriched with live PayPal status (fallback to
    the stored status when PayPal cannot be reached)."""
    subs = repositories.list_subscriptions(db, user.id)
    return [enrich(sub, live_status=live_status_for(client, sub)) for sub in subs]


def propose(db: Session, user: User, client):
    """Flag unused paid subscriptions and total the savings.

    Returns {"flagged": [...sorted by price desc...], "kept": [...],
    "monthly_saving_usd", "annual_saving_usd", "total_monthly_usd"}.
    """
    items = inventory(db, user, client)
    flagged = sorted(
        [item for item in items if item["flagged"]],
        key=lambda item: item["price_monthly_usd"],
        reverse=True,
    )
    kept = [item for item in items if not item["flagged"]]
    monthly_saving = round(sum(item["price_monthly_usd"] for item in flagged), 2)
    annual_saving = round(monthly_saving * 12, 2)
    total_monthly = round(sum(item["price_monthly_usd"] for item in items), 2)
    repositories.log_audit(
        db, user.id, "PROPOSE", None, None,
        f"flagged={len(flagged)} monthly_saving_usd={monthly_saving:.2f}",
    )
    return {
        "flagged": flagged,
        "kept": kept,
        "monthly_saving_usd": monthly_saving,
        "annual_saving_usd": annual_saving,
        "total_monthly_usd": total_monthly,
    }
