"""Auth endpoint tests: register / login / me."""

from tests.conftest import auth_headers, register_user


def test_register_returns_201_and_no_password(client):
    resp = client.post("/auth/register", json={
        "email": "alice@example.com",
        "password": "secret123",
        "full_name": "Alice",
    })
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["email"] == "alice@example.com"
    assert body["full_name"] == "Alice"
    assert "id" in body
    assert "role" in body
    # No password material of any kind may leak in the response.
    lowered = resp.text.lower()
    assert "secret123" not in lowered
    assert "password" not in lowered
    assert "hashed_password" not in lowered


def test_register_duplicate_email_returns_400(client):
    register_user(client, "dup@example.com", "secret123")
    resp = client.post("/auth/register", json={
        "email": "dup@example.com",
        "password": "otherpass",
        "full_name": "Dup",
    })
    assert resp.status_code == 400, resp.text


def test_login_returns_bearer_token(client):
    register_user(client, "bob@example.com", "secret123")
    resp = client.post("/auth/login", data={
        "username": "bob@example.com", "password": "secret123",
    })
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


def test_auth_me_with_token_returns_user(client):
    user, token = register_user(
        client, "carol@example.com", "secret123", full_name="Carol")
    resp = client.get("/auth/me", headers=auth_headers(token))
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["email"] == "carol@example.com"
    assert body["id"] == user["id"]


def test_login_wrong_password_returns_401(client):
    register_user(client, "dave@example.com", "secret123")
    resp = client.post("/auth/login", data={
        "username": "dave@example.com", "password": "wrong-password",
    })
    assert resp.status_code == 401, resp.text


def test_auth_me_without_token_returns_401(client):
    resp = client.get("/auth/me")
    assert resp.status_code == 401, resp.text
