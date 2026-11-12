"""SubSentry Enterprise — FastAPI application entrypoint."""
import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.routers import admin, agent, audit, auth, duplicates, health, notifications, subscriptions

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="SubSentry")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:4173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(subscriptions.router)
app.include_router(agent.router)
app.include_router(duplicates.router)
app.include_router(audit.router)
app.include_router(notifications.router)
app.include_router(admin.router)


@app.on_event("startup")
def on_startup():
    init_db()
    logger.info("database initialised")
    if os.environ.get("SUBSENTRY_SCHEDULER", "1") == "0":
        logger.info("scheduler skipped (SUBSENTRY_SCHEDULER=0)")
        return
    try:
        from app.services.scheduler import start_scheduler

        start_scheduler()
    except Exception as exc:  # noqa: BLE001 - a scheduler failure must not kill startup
        logger.warning("scheduler failed to start: %s", exc)
