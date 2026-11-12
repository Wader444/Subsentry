"""SQLAlchemy 2.0 database setup.

SQLite by default (``sqlite:///./subsentry.db``); Postgres when
``DATABASE_URL`` points at one. ``init_db()`` creates every table.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings

_connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    _connect_args = {"check_same_thread": False}

engine = create_engine(settings.DATABASE_URL, connect_args=_connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency: yield a session, close it after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables. Imports models so their tables are registered."""
    import app.models  # noqa: F401

    Base.metadata.create_all(bind=engine)
