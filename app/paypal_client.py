"""PayPal client — one interface, two implementations (implementation.md §4).

RealPayPalClient: direct REST calls to the sandbox
(https://api-m.sandbox.paypal.com), OAuth2 client-credentials token,
create plan / create subscription / show details / cancel.
MockPayPalClient: same interface, canned responses, no network.
Use the mock when the sandbox fights back for more than an hour, or when
running the demo / integration check offline. Never fake a cancel in the
video: if the mock is carrying the demo, say so in the README.

PayPal has no list-all-subscriptions endpoint, so SubSentry stores every
subscription ID in SQLite at seed/creation time and verifies status live
via show_subscription_details. That is the design, not a workaround.
"""
import os

try:
    import requests
except ImportError:  # offline / not installed yet; mock still works
    requests = None

SANDBOX_BASE = "https://api-m.sandbox.paypal.com"


class PayPalError(Exception):
    pass


class RealPayPalClient:
    def __init__(self, client_id=None, client_secret=None, base=SANDBOX_BASE):
        self.client_id = client_id or os.environ.get("PAYPAL_CLIENT_ID")
        self.client_secret = client_secret or os.environ.get("PAYPAL_CLIENT_SECRET")
        self.base = base
        self._access_token = None
        if not self.client_id or not self.client_secret:
            raise PayPalError("PAYPAL_CLIENT_ID / PAYPAL_CLIENT_SECRET not set (see .env.example)")

    def _token(self):
        if requests is None:
            raise PayPalError("requests is not installed — pip install -r requirements.txt")
        if self._access_token:
            return self._access_token
        r = requests.post(
            f"{self.base}/v1/oauth2/token",
            auth=(self.client_id, self.client_secret),
            data={"grant_type": "client_credentials"},
            timeout=15,
        )
        r.raise_for_status()
        self._access_token = r.json()["access_token"]
        return self._access_token

    def _headers(self):
        return {"Authorization": f"Bearer {self._token()}",
                "Content-Type": "application/json"}

    def create_plan(self, name, price_usd):
        r = requests.post(f"{self.base}/v1/billing/plans", headers=self._headers(),
                          json={"product_id": "SUBSENTRY",
                                "name": name,
                                "billing_cycles": [{"frequency": {"interval_unit": "MONTH",
                                                                 "interval_count": 1},
                                                    "tenure_type": "REGULAR",
                                                    "sequence": 1,
                                                    "total_cycles": 0,
                                                    "pricing_scheme": {"fixed_price": {
                                                        "value": f"{price_usd:.2f}",
                                                        "currency_code": "USD"}}}]},
                          timeout=15)
        r.raise_for_status()
        return r.json()

    def create_subscription(self, plan_id):
        r = requests.post(f"{self.base}/v1/billing/subscriptions",
                          headers=self._headers(),
                          json={"plan_id": plan_id}, timeout=15)
        r.raise_for_status()
        return r.json()

    def show_subscription_details(self, subscription_id):
        r = requests.get(f"{self.base}/v1/billing/subscriptions/{subscription_id}",
                         headers=self._headers(), timeout=15)
        r.raise_for_status()
        return r.json()

    def cancel_subscription(self, subscription_id, reason="Unused subscription"):
        r = requests.post(
            f"{self.base}/v1/billing/subscriptions/{subscription_id}/cancel",
            headers=self._headers(), json={"reason": reason}, timeout=15)
        r.raise_for_status()
        return {"id": subscription_id, "status": "CANCELLED", "reason": reason}


class MockPayPalClient:
    """Canned sandbox. IDs are SEED-01..08; cancel flips status in memory."""

    def __init__(self):
        self._status = {}

    def create_plan(self, name, price_usd):
        return {"id": f"P-MOCK-{name[:8].upper()}", "status": "ACTIVE"}

    def create_subscription(self, plan_id):
        sub_id = f"I-MOCK-{plan_id[-4:]}"
        self._status[sub_id] = "ACTIVE"
        return {"id": sub_id, "status": "ACTIVE"}

    def show_subscription_details(self, subscription_id):
        return {"id": subscription_id,
                "status": self._status.get(subscription_id, "ACTIVE")}

    def cancel_subscription(self, subscription_id, reason="Unused subscription"):
        self._status[subscription_id] = "CANCELLED"
        return {"id": subscription_id, "status": "CANCELLED", "reason": reason}


def get_client():
    """Real client when credentials are set, mock otherwise. Explicit opt-in
    via PAYPAL_MODE=mock forces the mock even with credentials present."""
    if os.environ.get("PAYPAL_MODE", "").lower() == "mock":
        return MockPayPalClient(), "mock"
    if os.environ.get("PAYPAL_CLIENT_ID") and os.environ.get("PAYPAL_CLIENT_SECRET"):
        return RealPayPalClient(), "sandbox"
    return MockPayPalClient(), "mock"
