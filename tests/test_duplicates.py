"""Duplicate-detection tests: same merchant + near-identical price."""

from tests.conftest import auth_headers, register_user


def _create(client, headers, merchant, plan, price, last_used=90):
    resp = client.post("/subscriptions", json={
        "merchant": merchant,
        "plan_name": plan,
        "category": "other",
        "price_monthly_usd": price,
        "last_used_days_ago": last_used,
    }, headers=headers)
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_same_merchant_prices_within_10_percent_grouped(client):
    _user, token = register_user(client, "dupes@example.com", "secret123")
    headers = auth_headers(token)

    first = _create(client, headers, "CloudBox", "CloudBox Pro 100GB", 9.99)
    second = _create(client, headers, "CloudBox", "CloudBox Pro 100GB", 10.50)

    resp = client.get("/duplicates", headers=headers)
    assert resp.status_code == 200, resp.text
    groups = resp.json()["groups"]
    assert len(groups) == 1
    group = groups[0]
    assert group["merchant"].lower() == "cloudbox"
    assert set(group["subscription_ids"]) == {first["id"], second["id"]}
    assert "reason" in group


def test_different_merchant_does_not_add_a_group(client):
    _user, token = register_user(client, "dupes2@example.com", "secret123")
    headers = auth_headers(token)

    first = _create(client, headers, "CloudBox", "CloudBox Pro 100GB", 9.99)
    second = _create(client, headers, "CloudBox", "CloudBox Pro 100GB", 10.50)
    _create(client, headers, "OtherBox", "OtherBox Basic", 9.99)

    resp = client.get("/duplicates", headers=headers)
    assert resp.status_code == 200, resp.text
    groups = resp.json()["groups"]
    assert len(groups) == 1
    assert set(groups[0]["subscription_ids"]) == {first["id"], second["id"]}
