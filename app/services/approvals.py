"""Approvals — the user explicitly approves cancellations.

Approval is idempotent: approving an already-approved subscription
records nothing new. Approving a subscription that does not exist or
does not belong to the user is a 404.
"""
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app import repositories
from app.models import User


def approve(db: Session, user: User, subscription_ids: list[str]) -> list[str]:
    approved: list[str] = []
    for sub_id in subscription_ids:
        sub = repositories.get_subscription(db, user.id, sub_id)
        if sub is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Subscription {sub_id} not found",
            )
        if not repositories.has_approval(db, user.id, sub_id):
            repositories.record_approval(db, user.id, sub_id)
            repositories.log_audit(
                db, user.id, "APPROVE", "subscription", sub_id,
                "User approved cancellation",
            )
        approved.append(sub_id)
    return approved
