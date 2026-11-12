"""Admin router — user list + aggregate stats ONLY.

Admins never see other users' subscriptions here: only counts and
the user list.
"""
from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Subscription, User
from app.schemas import AdminStats, UserOut
from app.security import require_admin

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users")
def list_users(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    return {"users": db.query(User).order_by(User.created_at).all()}


@router.get("/stats", response_model=AdminStats)
def get_stats(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    total_users = db.query(func.count(User.id)).scalar() or 0
    total_subs = db.query(func.count(Subscription.id)).scalar() or 0
    active_subs = (
        db.query(func.count(Subscription.id))
        .filter(Subscription.status == "ACTIVE")
        .scalar()
        or 0
    )
    cancelled_subs = (
        db.query(func.count(Subscription.id))
        .filter(Subscription.status == "CANCELLED")
        .scalar()
        or 0
    )
    total_monthly = (
        db.query(func.coalesce(func.sum(Subscription.price_monthly_usd), 0.0))
        .filter(Subscription.status == "ACTIVE")
        .scalar()
        or 0.0
    )
    return AdminStats(
        total_users=total_users,
        total_subscriptions=total_subs,
        active_subscriptions=active_subs,
        cancelled_subscriptions=cancelled_subs,
        total_monthly_usd=round(float(total_monthly), 2),
    )
