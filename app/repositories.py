"""Small session-scoped repository helpers (no business logic here)."""
from sqlalchemy.orm import Session

from app import models
from app.security import hash_password


# --- Users -----------------------------------------------------------------

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def create_user(db: Session, email: str, password: str, full_name=None, role="user"):
    user = models.User(
        email=email,
        hashed_password=hash_password(password),
        full_name=full_name,
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# --- Subscriptions ---------------------------------------------------------

def get_subscription(db: Session, user_id: int, sub_id: str):
    return (
        db.query(models.Subscription)
        .filter(
            models.Subscription.id == sub_id,
            models.Subscription.user_id == user_id,
        )
        .first()
    )


def list_subscriptions(db: Session, user_id: int, status=None, category=None, q=None):
    query = db.query(models.Subscription).filter(models.Subscription.user_id == user_id)
    if status:
        query = query.filter(models.Subscription.status == status)
    if category:
        query = query.filter(models.Subscription.category == category)
    if q:
        like = f"%{q}%"
        query = query.filter(
            (models.Subscription.merchant.ilike(like))
            | (models.Subscription.plan_name.ilike(like))
        )
    return query.order_by(models.Subscription.created_at).all()


def create_subscription(db: Session, user_id: int, **fields):
    sub = models.Subscription(user_id=user_id, **fields)
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return sub


def update_subscription(db: Session, sub, **fields):
    for key, value in fields.items():
        if value is not None:
            setattr(sub, key, value)
    db.commit()
    db.refresh(sub)
    return sub


def delete_subscription(db: Session, sub):
    db.query(models.Approval).filter(
        models.Approval.subscription_id == sub.id
    ).delete()
    db.delete(sub)
    db.commit()


# --- Approvals / cancellations / audit / notifications ---------------------

def record_approval(db: Session, user_id: int, subscription_id: str):
    approval = models.Approval(
        user_id=user_id, subscription_id=subscription_id, status="APPROVED"
    )
    db.add(approval)
    db.commit()
    db.refresh(approval)
    return approval


def has_approval(db: Session, user_id: int, subscription_id: str) -> bool:
    return (
        db.query(models.Approval)
        .filter(
            models.Approval.user_id == user_id,
            models.Approval.subscription_id == subscription_id,
            models.Approval.status == "APPROVED",
        )
        .first()
        is not None
    )


def record_cancellation(db: Session, user_id: int, subscription_id: str,
                        paypal_response=None, reason=None):
    row = models.Cancellation(
        user_id=user_id,
        subscription_id=subscription_id,
        paypal_response=paypal_response,
        reason=reason,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def log_audit(db: Session, user_id, action: str, entity_type=None,
              entity_id=None, detail=None):
    row = models.AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        detail=detail,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def create_notification(db: Session, user_id: int, title: str, body: str = ""):
    row = models.Notification(user_id=user_id, title=title, body=body)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
