"""Background scheduler (APScheduler).

- refresh_all_status: every 6 hours, sync every ACTIVE subscription of
  every user against PayPal.
- weekly_digest: Mondays 09:00, one in-app notification per user with
  the flagged count and potential monthly saving.

Jobs open their own DB session and never crash the app on error.
"""
import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.database import SessionLocal
from app.models import Subscription, User
from app.paypal_client import get_client
from app.services.proposals import propose
from app.services.subscriptions import sync_from_paypal

logger = logging.getLogger(__name__)


def refresh_all_status():
    """Sync every ACTIVE subscription of every user against PayPal."""
    db = SessionLocal()
    try:
        client, _mode = get_client()
        users = db.query(User).filter(User.is_active.is_(True)).all()
        for user in users:
            subs = (
                db.query(Subscription)
                .filter(
                    Subscription.user_id == user.id,
                    Subscription.status == "ACTIVE",
                )
                .all()
            )
            for sub in subs:
                try:
                    sync_from_paypal(db, user, sub.id, client)
                except Exception as exc:  # noqa: BLE001 - one sub must not stop the job
                    logger.warning("refresh failed for %s: %s", sub.id, exc)
    except Exception as exc:  # noqa: BLE001 - the job itself must not crash
        logger.warning("refresh_all_status failed: %s", exc)
    finally:
        db.close()


def weekly_digest():
    """Per-user digest notification: flagged count + potential saving."""
    db = SessionLocal()
    try:
        from app import repositories

        client, _mode = get_client()
        users = db.query(User).filter(User.is_active.is_(True)).all()
        for user in users:
            try:
                proposal = propose(db, user, client)
                flagged = len(proposal["flagged"])
                saving = proposal["monthly_saving_usd"]
                repositories.create_notification(
                    db, user.id,
                    f"Weekly digest: {flagged} subscription(s) flagged, "
                    f"${saving:.2f}/month potential savings",
                    f"You have {flagged} subscription(s) you may not be using. "
                    f"Cancelling them could save ${saving:.2f} a month.",
                )
            except Exception as exc:  # noqa: BLE001 - one user must not stop the job
                logger.warning("weekly digest failed for user %s: %s", user.id, exc)
    except Exception as exc:  # noqa: BLE001
        logger.warning("weekly_digest failed: %s", exc)
    finally:
        db.close()


def start_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        refresh_all_status, IntervalTrigger(hours=6), id="refresh_all_status"
    )
    scheduler.add_job(
        weekly_digest, CronTrigger(day_of_week="mon", hour=9, minute=0),
        id="weekly_digest",
    )
    scheduler.start()
    logger.info("scheduler started (refresh every 6h, digest Mondays 09:00)")
    return scheduler
