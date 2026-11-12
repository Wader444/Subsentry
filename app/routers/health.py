"""Health router."""
from fastapi import APIRouter

from app.config import settings
from app.paypal_client import get_client

router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    _client, mode = get_client()
    db_kind = "postgres" if settings.DATABASE_URL.startswith("postgres") else "sqlite"
    return {"status": "ok", "mode": mode, "db": db_kind}
