"""Q&A tests: answers come ONLY from the user's own subscription records."""

from tests.conftest import auth_headers, register_user

REFUSAL = "only answer from your subscription records"


def test_ask_unused_subscriptions_names_fitgym(demo):
    client, _user, _token, headers, _seeded = demo
    resp = client.get("/ask", params={
        "q": "What am I paying for that I don't use?",
    }, headers=headers)
    assert resp.status_code == 200, resp.text
    assert "FitGym" in resp.json()["answer"]


def test_ask_unrelated_question_is_refused(demo):
    client, _user, _token, headers, _seeded = demo
    resp = client.get("/ask", params={"q": "What is the weather today?"},
                      headers=headers)
    assert resp.status_code == 200, resp.text
    assert REFUSAL in resp.json()["answer"]


def test_ask_fresh_user_with_no_subscriptions(client):
    _user, token = register_user(client, "empty@example.com", "secret123")
    resp = client.get("/ask", params={
        "q": "What am I paying for that I don't use?",
    }, headers=auth_headers(token))
    assert resp.status_code == 200, resp.text
    answer = resp.json()["answer"].lower()
    assert any(phrase in answer for phrase in (
        "no subscription",
        "no active subscription",
        "don't have",
        "do not have",
        "zero subscription",
        "no subscriptions",
    )), resp.json()["answer"]
