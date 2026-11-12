"""Tests for the frozen waste-scoring math (implementation.md §4).

    waste = 0.7 * recency + 0.3 * price
    recency = 0.0 (<=30d) / 0.4 (31-60d) / 0.7 (61-90d) / 1.0 (90+d)
    price   = min(price_monthly_usd / 30, 1.0)
    FLAG at waste >= 0.55 AND last_used_days_ago >= 45.

Pure-function tests: they do not need the FastAPI backend, the
database, or any installed third-party package beyond pytest.
"""

import pytest

from app.scoring import recency_component, should_flag, waste_score

# (merchant, price_monthly_usd, last_used_days_ago, expected waste_score)
SEED_CASES = [
    ("StreamFlix", 15.99, 12, 0.16),
    ("MusicWave", 10.99, 2, 0.11),
    ("GameVault", 14.99, 5, 0.15),
    ("DesignSuite", 19.99, 8, 0.20),
    ("MealKit Weekly", 29.99, 4, 0.30),
    ("FitGym Pro", 12.99, 94, 0.83),
    ("CloudBox Pro", 9.99, 61, 0.59),
    ("NewsDaily Premium", 7.99, 120, 0.78),
]

FLAGGED = {"FitGym Pro", "CloudBox Pro", "NewsDaily Premium"}


@pytest.mark.parametrize(
    "merchant,price,last_used,expected", SEED_CASES,
    ids=[c[0] for c in SEED_CASES],
)
def test_waste_score_all_seeds(merchant, price, last_used, expected):
    assert waste_score(price, last_used) == pytest.approx(expected, abs=0.001)


@pytest.mark.parametrize(
    "merchant,price,last_used,expected", SEED_CASES,
    ids=[c[0] for c in SEED_CASES],
)
def test_should_flag_only_the_three(merchant, price, last_used, expected):
    assert should_flag(price, last_used) is (merchant in FLAGGED)


@pytest.mark.parametrize("days,expected", [
    (0, 0.0),
    (30, 0.0),   # boundary: 30 days is still "recent"
    (31, 0.4),
    (60, 0.4),
    (61, 0.7),
    (90, 0.7),
    (91, 1.0),
    (120, 1.0),
    (365, 1.0),
])
def test_recency_component_boundaries(days, expected):
    assert recency_component(days) == expected


def test_flag_needs_both_score_and_min_days():
    # High score but used 44 days ago: below the 45-day minimum, no flag.
    assert should_flag(29.99, 44) is False
    # Same price at 45 days: recency 0.4 -> 0.7*0.4 + 0.3*1.0 = 0.58, flag.
    assert should_flag(29.99, 45) is True


def test_price_component_capped_at_one():
    # $30+/month caps the price component at 1.0: 0.7*1.0 + 0.3*1.0 = 1.0.
    assert waste_score(30.00, 120) == pytest.approx(1.0, abs=0.001)
    assert waste_score(99.99, 120) == pytest.approx(1.0, abs=0.001)
    # And a cheap long-unused sub still flags on recency alone.
    assert waste_score(3.00, 120) == pytest.approx(0.73, abs=0.001)
    assert should_flag(3.00, 120) is True
