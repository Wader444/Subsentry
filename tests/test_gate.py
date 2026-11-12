"""Approval-gate tests: no approval, no cancellation, ever.

Flow: seeded demo user -> cancel with no approvals (blocked) ->
approve the 3 flagged -> cancel (3 cancelled, 5 still active) ->
report + audit reflect the cancellations.
"""


def _ids(items):
    """Cancelled/blocked/still_active entries may be plain ids or dicts."""
    out = []
    for item in items:
        out.append(item["id"] if isinstance(item, dict) else item)
    return out


def test_cancel_without_approval_blocks_everything(demo):
    client, _user, _token, headers, seeded = demo
    flagged_ids = {
        s["id"] for s in seeded
        if s["merchant"] in ("FitGym Pro", "CloudBox Pro", "NewsDaily Premium")
    }

    resp = client.post("/cancel", json={}, headers=headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["cancelled"] == []
    assert body["monthly_saving_usd"] == 0.0
    assert body["annual_saving_usd"] == 0.0
    assert set(_ids(body["blocked"])) == flagged_ids
    assert len(body["still_active"]) == 8

    # Nothing was actually cancelled.
    resp = client.get("/report", headers=headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["cancelled"] == []


def test_approve_unknown_id_returns_404(demo):
    client, _user, _token, headers, _seeded = demo
    resp = client.post("/approve", json={
        "subscription_ids": ["NOPE-DOES-NOT-EXIST"],
    }, headers=headers)
    assert resp.status_code == 404, resp.text


def test_full_approve_cancel_report_audit_flow(demo):
    client, _user, _token, headers, seeded = demo
    flagged_ids = {
        s["id"] for s in seeded
        if s["merchant"] in ("FitGym Pro", "CloudBox Pro", "NewsDaily Premium")
    }

    # 1. Cancel with no approvals: everything blocked, nothing cancelled.
    resp = client.post("/cancel", json={}, headers=headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["cancelled"] == []
    assert set(_ids(resp.json()["blocked"])) == flagged_ids

    # 2. Approve exactly the 3 flagged ids.
    resp = client.post("/approve", json={
        "subscription_ids": sorted(flagged_ids),
    }, headers=headers)
    assert resp.status_code == 200, resp.text
    assert set(_ids(resp.json()["approved"])) == flagged_ids

    # 3. Cancel: 3 cancelled, $30.97/month saved, 5 still active.
    resp = client.post("/cancel", json={}, headers=headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert set(_ids(body["cancelled"])) == flagged_ids
    assert body["monthly_saving_usd"] == 30.97
    assert body["annual_saving_usd"] == 371.64
    assert len(body["still_active"]) == 5

    # 4. Report agrees.
    resp = client.get("/report", headers=headers)
    assert resp.status_code == 200, resp.text
    report = resp.json()
    assert set(_ids(report["cancelled"])) == flagged_ids
    assert report["monthly_saving_usd"] == 30.97
    assert report["annual_saving_usd"] == 371.64
    assert len(report["still_active"]) == 5

    # 5. The blocked attempt left an audit trail.
    resp = client.get("/audit", headers=headers)
    assert resp.status_code == 200, resp.text
    entries = resp.json()["entries"]
    assert any("CANCEL_BLOCKED" in str(entry) for entry in entries)
