"""Core API tests: health, inventory, propose, report, subscription CRUD."""

from tests.conftest import (
    EXPECTED_ANNUAL_SAVING,
    EXPECTED_FLAGGED_MERCHANTS,
    EXPECTED_MONTHLY_SAVING,
    EXPECTED_TOTAL_MONTHLY,
    auth_headers,
    register_user,
)


def test_health_returns_ok_and_mock_mode(client):
    resp = client.get("/health")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "ok"
    assert body["mode"] == "mock"
    assert body["db"] in ("sqlite", "postgres")


def test_inventory_seeded_demo_user(demo):
    client, _user, _token, headers, _seeded = demo
    resp = client.get("/subscriptions", headers=headers)
    assert resp.status_code == 200, resp.text
    assert len(resp.json()) == 8

    resp = client.get("/inventory", headers=headers)
    assert resp.status_code == 200, resp.text
    inventory = resp.json()
    assert len(inventory) == 8
    for sub in inventory:
        # Every enriched row carries the scoring fields.
        assert "live_status" in sub
        assert "waste_score" in sub
        assert "flagged" in sub
        assert "reason" in sub
    flagged = {s["merchant"] for s in inventory if s["flagged"]}
    assert flagged == EXPECTED_FLAGGED_MERCHANTS


def test_propose_flags_exactly_three(demo):
    client, _user, _token, headers, _seeded = demo
    resp = client.get("/propose", headers=headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    flagged_merchants = sorted(s["merchant"] for s in body["flagged"])
    assert flagged_merchants == [
        "CloudBox Pro", "FitGym Pro", "NewsDaily Premium",
    ]
    assert len(body["kept"]) == 5
    assert body["monthly_saving_usd"] == EXPECTED_MONTHLY_SAVING
    assert body["annual_saving_usd"] == EXPECTED_ANNUAL_SAVING
    assert body["total_monthly_usd"] == EXPECTED_TOTAL_MONTHLY


def test_report_before_cancel_is_zero(demo):
    client, _user, _token, headers, _seeded = demo
    resp = client.get("/report", headers=headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["cancelled"] == []
    assert body["monthly_saving_usd"] == 0.0
    assert body["annual_saving_usd"] == 0.0
    assert len(body["still_active"]) == 8


def test_subscription_crud(client):
    _user, token = register_user(client, "crud@example.com", "secret123")
    headers = auth_headers(token)

    # Create (no PayPal id -> server assigns a LOCAL- id).
    resp = client.post("/subscriptions", json={
        "merchant": "TestMart",
        "plan_name": "TestMart Basic",
        "category": "other",
        "price_monthly_usd": 5.99,
        "last_used_days_ago": 3,
    }, headers=headers)
    assert resp.status_code == 201, resp.text
    created = resp.json()
    assert created["id"].startswith("LOCAL-")
    assert created["merchant"] == "TestMart"
    sub_id = created["id"]

    # Get.
    resp = client.get(f"/subscriptions/{sub_id}", headers=headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["price_monthly_usd"] == 5.99

    # Patch the price.
    resp = client.patch(f"/subscriptions/{sub_id}",
                        json={"price_monthly_usd": 6.99}, headers=headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["price_monthly_usd"] == 6.99

    # Delete, then it is gone.
    resp = client.delete(f"/subscriptions/{sub_id}", headers=headers)
    assert resp.status_code == 204, resp.text
    resp = client.get(f"/subscriptions/{sub_id}", headers=headers)
    assert resp.status_code == 404, resp.text


def test_subscriptions_are_per_user(client):
    user_a, token_a = register_user(client, "a@example.com", "secret123")
    user_b, token_b = register_user(client, "b@example.com", "secret123")
    resp = client.post("/subscriptions", json={
        "merchant": "PrivateBox",
        "plan_name": "PrivateBox Basic",
        "price_monthly_usd": 4.99,
        "last_used_days_ago": 10,
    }, headers=auth_headers(token_a))
    assert resp.status_code == 201, resp.text
    sub_id = resp.json()["id"]

    # The other user must not see it — neither in list nor by id.
    resp = client.get("/subscriptions", headers=auth_headers(token_b))
    assert resp.status_code == 200, resp.text
    assert all(s["id"] != sub_id for s in resp.json())
    resp = client.get(f"/subscriptions/{sub_id}",
                      headers=auth_headers(token_b))
    assert resp.status_code == 404, resp.text
