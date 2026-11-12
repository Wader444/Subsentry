"""Subscription CRUD router — always scoped to the current user."""
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import repositories
from app.database import get_db
from app.models import User
from app.paypal_client import get_client
from app.schemas import SubscriptionCreate, SubscriptionOut, SubscriptionUpdate
from app.security import get_current_user
from app.services.subscriptions import sync_from_paypal

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


def _get_owned(db: Session, user: User, sub_id: str):
    sub = repositories.get_subscription(db, user.id, sub_id)
    if sub is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found"
        )
    return sub


@router.get("", response_model=list[SubscriptionOut])
def list_subscriptions(
    status: str | None = None,
    category: str | None = None,
    q: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return repositories.list_subscriptions(db, current_user.id, status, category, q)


@router.post("", response_model=SubscriptionOut, status_code=status.HTTP_201_CREATED)
def create_subscription(
    payload: SubscriptionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sub_id = payload.paypal_subscription_id or f"LOCAL-{uuid.uuid4().hex[:8]}"
    sub = repositories.create_subscription(
        db,
        current_user.id,
        id=sub_id,
        merchant=payload.merchant,
        plan_name=payload.plan_name,
        category=payload.category,
        price_monthly_usd=payload.price_monthly_usd,
        started_on=payload.started_on,
        next_billing_on=payload.next_billing_on,
        last_used_days_ago=payload.last_used_days_ago,
        paypal_subscription_id=payload.paypal_subscription_id,
    )
    repositories.log_audit(db, current_user.id, "CREATE", "subscription", sub.id,
                           f"Created {sub.merchant} {sub.plan_name}")
    return sub


@router.get("/{sub_id}", response_model=SubscriptionOut)
def get_subscription(
    sub_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return _get_owned(db, current_user, sub_id)


@router.patch("/{sub_id}", response_model=SubscriptionOut)
def update_subscription(
    sub_id: str,
    payload: SubscriptionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sub = _get_owned(db, current_user, sub_id)
    return repositories.update_subscription(
        db, sub, **payload.model_dump(exclude_unset=True)
    )


@router.delete("/{sub_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_subscription(
    sub_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sub = _get_owned(db, current_user, sub_id)
    repositories.delete_subscription(db, sub)
    repositories.log_audit(db, current_user.id, "DELETE", "subscription", sub_id,
                           "Deleted subscription")
    return None


@router.post("/{sub_id}/sync")
def sync_subscription(
    sub_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_owned(db, current_user, sub_id)
    client, _mode = get_client()
    enriched = sync_from_paypal(db, current_user, sub_id, client)
    if enriched is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found"
        )
    return enriched
