"""Audit router — own entries newest first; admins see all."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AuditLog, User
from app.schemas import AuditOut
from app.security import get_current_user

router = APIRouter(tags=["audit"])


@router.get("/audit")
def get_audit(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(AuditLog)
    if current_user.role != "admin":
        query = query.filter(AuditLog.user_id == current_user.id)
    entries = query.order_by(AuditLog.created_at.desc(), AuditLog.id.desc()).all()
    return {"entries": [AuditOut.model_validate(entry) for entry in entries]}
