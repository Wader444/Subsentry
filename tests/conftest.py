"""Shared pytest fixtures for SubSentry Enterprise API tests.

Environment is set BEFORE the app is imported, so the app module binds
to the throwaway test database and the mock PayPal client:

- PAYPAL_MODE=mock            (never hits the real PayPal sandbox)
- DATABASE_URL=sqlite temp file (created here, deleted after the session)
- SECRET_KEY=test-secret      (test-only; never a real secret)
- SUBSENTRY_SCHEDULER=0       (no background jobs during tests)

The app's ``get_db`` dependency is overridden with a session bound to
the same test engine, so TestClient requests and the fixtures share one
database. If the backend (``app.main`` / ``app.database``) has not been
built yet, the API fixtures skip with a clear message instead of
breaking collection — the pure scoring tests in ``test_scoring.py``
do not need the backend and still run.
"""

import os
import tempfile

# ---- env BEFORE any app import -------------------------------------------
_TMP_DB = tempfile.NamedTemporaryFile(
    prefix="test_subsentry_", suffix=".db", delete=False
)
_TMP_DB.close()
os.environ["PAYPAL_MODE"] = "mock"
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP_DB.name}"
os.environ["SECRET_KEY"] = "test-secret"
os.environ["SUBSENTRY_SCHEDULER"] = "0"

import pytest  # noqa: E402

try:
    from fastapi.testclient import TestClient  # noqa: E402
except ImportError:  # httpx / fastapi not installed yet
    TestClient = None

try:
    from app.main import app  # noqa: E402
    try:
        from app.main import get_db  # noqa: E402
    except ImportError:
        from app.database import get_db  # noqa: E402
    from app.database import Base, SessionLocal, engine  # noqa: E402
    try:
        from app import models  # noqa: E402,F401  (registers models on Base.metadata)
    except ImportError:
        pass
    BACKEND_AVAILABLE = True
    BACKEND_IMPORT_ERROR = None
except ImportError as _exc:  # backend not built yet — API tests skip
    app = None
    get_db = None
    Base = SessionLocal = engine = None
    BACKEND_AVAILABLE = False
    BACKEND_IMPORT_ERROR = _exc

if BACKEND_AVAILABLE and TestClient is not None:

    def _override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _override_get_db


# ---- demo seed (frozen values — see implementation.md §4) -----------------
DEMO_EMAIL = "demo@subsentry.local"
DEMO_PASSWORD = "demo1234"
DEMO_FULL_NAME = "Demo User"

# (paypal_subscription_id, merchant, plan_name, category, price, started_on,
#  next_billing_on, last_used_days_ago)
SEED_SUBS = [
    ("SEED-01", "StreamFlix", "StreamFlix Premium", "streaming", 15.99,
     "2026-03-01", "2026-12-01", 12),
    ("SEED-02", "MusicWave", "MusicWave Plus", "music", 10.99,
     "2026-02-15", "2026-12-01", 2),
    ("SEED-03", "GameVault", "GameVault Monthly", "gaming", 14.99,
     "2026-05-10", "2026-12-01", 5),
    ("SEED-04", "DesignSuite", "DesignSuite Pro", "software", 19.99,
     "2026-01-20", "2026-12-01", 8),
    ("SEED-05", "MealKit Weekly", "MealKit Weekly Box", "food", 29.99,
     "2026-06-01", "2026-12-01", 4),
    ("SEED-06", "FitGym Pro", "FitGym Pro", "fitness", 12.99,
     "2026-08-01", "2026-12-01", 94),
    ("SEED-07", "CloudBox Pro", "CloudBox Pro 100GB", "storage", 9.99,
     "2026-07-15", "2026-12-01", 61),
    ("SEED-08", "NewsDaily Premium", "NewsDaily Premium", "news", 7.99,
     "2026-08-10", "2026-12-01", 120),
]

EXPECTED_FLAGGED_MERCHANTS = {"FitGym Pro", "CloudBox Pro", "NewsDaily Premium"}
EXPECTED_MONTHLY_SAVING = 30.97
EXPECTED_ANNUAL_SAVING = 371.64
EXPECTED_TOTAL_MONTHLY = 122.92


# ---- fixtures -------------------------------------------------------------
def _require_backend():
    if not BACKEND_AVAILABLE:
        pytest.skip(f"backend not built yet (app.main import failed: "
                    f"{BACKEND_IMPORT_ERROR})")
    if TestClient is None:
        pytest.skip("fastapi/httpx not installed yet")


@pytest.fixture(scope="session", autouse=True)
def _cleanup_test_db():
    yield
    try:
        os.unlink(_TMP_DB.name)
    except OSError:
        pass


@pytest.fixture()
def reset_db():
    """Drop + recreate all tables (fresh DB per test)."""
    _require_backend()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(reset_db):
    """TestClient bound to the test DB (dependency override set above)."""
    _require_backend()
    with TestClient(app) as test_client:
        yield test_client


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def register_user(client, email, password, full_name="Test"):
    """Register + log in; returns (user_dict, token)."""
    resp = client.post("/auth/register", json={
        "email": email, "password": password, "full_name": full_name,
    })
    assert resp.status_code == 201, resp.text
    user = resp.json()
    resp = client.post("/auth/login", data={
        "username": email, "password": password,
    })
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]
    return user, token


def seed_demo_user(client):
    """Register the demo user and seed the 8 demo subscriptions.

    Returns (user_dict, token, headers, seeded_subs) where seeded_subs
    is the list of created subscription dicts in SEED-01..08 order.
    """
    user, token = register_user(
        client, DEMO_EMAIL, DEMO_PASSWORD, full_name=DEMO_FULL_NAME)
    headers = auth_headers(token)
    seeded = []
    for seed_id, merchant, plan, category, price, started, nxt, last_used in SEED_SUBS:
        resp = client.post("/subscriptions", json={
            "merchant": merchant,
            "plan_name": plan,
            "category": category,
            "price_monthly_usd": price,
            "started_on": started,
            "next_billing_on": nxt,
            "last_used_days_ago": last_used,
            "paypal_subscription_id": seed_id,
        }, headers=headers)
        assert resp.status_code == 201, resp.text
        seeded.append(resp.json())
    return user, token, headers, seeded


@pytest.fixture()
def demo(client):
    """Seeded demo user: (client, user, token, headers, seeded_subs)."""
    user, token, headers, seeded = seed_demo_user(client)
    return client, user, token, headers, seeded
