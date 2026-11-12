"""Duplicates router."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.security import get_current_user
from app.services.duplicates import find_duplicates

router = APIRouter(tags=["duplicates"])


@router.get("/duplicates")
def get_duplicates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return {"groups": find_duplicates(db, current_user)}
