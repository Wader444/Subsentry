"""Notifications + email. Email never raises: if SMTP is not
configured it logs and returns False; any send failure is logged
and returns False."""
import logging
import smtplib
from email.message import EmailMessage

from sqlalchemy.orm import Session

from app import repositories
from app.config import settings

logger = logging.getLogger(__name__)


def create_notification(db: Session, user_id: int, title: str, body: str = ""):
    return repositories.create_notification(db, user_id, title, body)


def send_email(to: str, subject: str, body: str) -> bool:
    if not settings.SMTP_HOST:
        logger.info("email not configured, skipping send to %s", to)
        return False
    try:
        message = EmailMessage()
        message["From"] = settings.SMTP_FROM or settings.SMTP_USER or "noreply@subsentry.local"
        message["To"] = to
        message["Subject"] = subject
        message.set_content(body)
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as server:
            server.starttls()
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(message)
        logger.info("email sent to %s: %s", to, subject)
        return True
    except Exception as exc:  # noqa: BLE001 - email must never crash the app
        logger.warning("email send failed to %s: %s", to, exc)
        return False
