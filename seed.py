"""Seed the demo data — idempotent.

Creates demo user demo@subsentry.local / demo1234 (role user) and admin
admin@subsentry.local / admin1234 (role admin) if missing, then seeds the
demo user with the 8 frozen demo subscriptions (SEED-01..08, $122.92/month
total; FitGym Pro / CloudBox Pro / NewsDaily Premium flag, $30.97/month).

Run from the project root:  python seed.py
Uses DATABASE_URL, or sqlite ./subsentry.db by default.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import repositories  # noqa: E402
from app.database import SessionLocal, init_db  # noqa: E402

SEED_SUBSCRIPTIONS = [
    # (id, merchant, plan_name, category, price, started_on, next_billing_on, last_used_days_ago)
    ("SEED-01", "StreamFlix", "StreamFlix Premium", "streaming", 15.99, "2026-03-01", "2026-12-01", 12),
    ("SEED-02", "MusicWave", "MusicWave Plus", "music", 10.99, "2026-02-15", "2026-12-01", 2),
    ("SEED-03", "GameVault", "GameVault Monthly", "gaming", 14.99, "2026-05-10", "2026-12-01", 5),
    ("SEED-04", "DesignSuite", "DesignSuite Pro", "software", 19.99, "2026-01-20", "2026-12-01", 8),
    ("SEED-05", "MealKit Weekly", "MealKit Weekly Box", "food", 29.99, "2026-06-01", "2026-12-01", 4),
    ("SEED-06", "FitGym Pro", "FitGym Pro", "fitness", 12.99, "2026-08-01", "2026-12-01", 94),
    ("SEED-07", "CloudBox Pro", "CloudBox Pro 100GB", "storage", 9.99, "2026-07-15", "2026-12-01", 61),
    ("SEED-08", "NewsDaily Premium", "NewsDaily Premium", "news", 7.99, "2026-08-10", "2026-12-01", 120),
]


def main():
    init_db()
    db = SessionLocal()
    try:
        demo = repositories.get_user_by_email(db, "demo@subsentry.local")
        if demo is None:
            demo = repositories.create_user(
                db, "demo@subsentry.local", "demo1234", full_name="Demo User", role="user"
            )
            print("created demo user demo@subsentry.local")
        admin = repositories.get_user_by_email(db, "admin@subsentry.local")
        if admin is None:
            admin = repositories.create_user(
                db, "admin@subsentry.local", "admin1234", full_name="Admin", role="admin"
            )
            print("created admin user admin@subsentry.local")

        created = 0
        for sub_id, merchant, plan_name, category, price, started, next_billing, days in SEED_SUBSCRIPTIONS:
            existing = repositories.get_subscription(db, demo.id, sub_id)
            if existing is not None:
                continue
            repositories.create_subscription(
                db,
                demo.id,
                id=sub_id,
                merchant=merchant,
                plan_name=plan_name,
                category=category,
                price_monthly_usd=price,
                started_on=started,
                next_billing_on=next_billing,
                last_used_days_ago=days,
            )
            created += 1
        total = sum(price for *_, price, _, _, _ in SEED_SUBSCRIPTIONS)
        print(f"seeded {created} new subscription(s) for demo user "
              f"({len(SEED_SUBSCRIPTIONS)} total, ${total:.2f}/month)")
        print("seed done (idempotent — re-running changes nothing)")
    finally:
        db.close()


if __name__ == "__main__":
    main()
