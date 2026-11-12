"""Sync 0 check for SubSentry Enterprise: prove the real PayPal sandbox
token call works — or say exactly why it does not.

Run from the project root, after copying `.env.example` to `.env` and
filling in the sandbox client ID / secret from developer.paypal.com:

    python check_sandbox.py

It never prints a credential or the token itself (only the token length).
Exit 0 = token OK. Exit 1 = sandbox reachable but rejected the
credentials (401/403 — re-check the ID/secret, and that the app is a
sandbox app). Exit 2 = credentials not set, or `PAYPAL_MODE=mock`, so
there is nothing to check — the app would be running on the mock client.
Any other failure (no network, timeout) is printed as-is.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importing the app package loads `.env` (see app/__init__.py).
from app.paypal_client import PayPalError, RealPayPalClient  # noqa: E402


def main():
    if os.environ.get("PAYPAL_MODE", "").lower() == "mock":
        print("Sandbox check: SKIPPED — PAYPAL_MODE=mock, app will use the mock client.")
        return 2
    client_id = os.environ.get("PAYPAL_CLIENT_ID")
    client_secret = os.environ.get("PAYPAL_CLIENT_SECRET")
    if not client_id or not client_secret:
        print("Sandbox check: FAIL — PAYPAL_CLIENT_ID / PAYPAL_CLIENT_SECRET not set.")
        print("Copy .env.example to .env and fill in the sandbox credentials from")
        print("developer.paypal.com -> My Apps & Credentials (sandbox app).")
        print("Until then the app runs on the mock client — that is fine for the")
        print("demo loop, but it is not the real sandbox.")
        return 2
    try:
        client = RealPayPalClient()
        token = client._token()
    except PayPalError as exc:
        print(f"Sandbox check: FAIL — {exc}")
        return 2
    except Exception as exc:  # requests errors: HTTPError, ConnectionError, Timeout
        status = getattr(getattr(exc, "response", None), "status_code", None)
        if status in (401, 403):
            print("Sandbox check: FAIL — PayPal rejected the credentials "
                  f"(HTTP {status}). Re-check the client ID/secret and that "
                  "the app is a sandbox app on developer.paypal.com.")
            return 1
        print(f"Sandbox check: FAIL — could not reach the PayPal sandbox: {exc}")
        return 1
    print(f"Sandbox check: PASS — sandbox token received ({len(token)} chars, "
          "token not printed). Sync 0 done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
