"""Savings report — what has actually been cancelled vs what is still active."""
from sqlalchemy.orm import Session

from app import repositories
from app.models import User


def savings_report(db: Session, user: User):
    cancelled = repositories.list_subscriptions(db, user.id, status="CANCELLED")
    still_active = repositories.list_subscriptions(db, user.id, status="ACTIVE")
    monthly = round(sum(sub.price_monthly_usd or 0.0 for sub in cancelled), 2)
    return {
        "cancelled": [sub.id for sub in cancelled],
        "still_active": [sub.id for sub in still_active],
        "monthly_saving_usd": monthly,
        "annual_saving_usd": round(monthly * 12, 2),
        "total_monthly_usd": round(
            sum(sub.price_monthly_usd or 0.0
                for sub in repositories.list_subscriptions(db, user.id)), 2
        ),
    }
