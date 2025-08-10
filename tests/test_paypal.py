import requests

from app import create_app
from app.paypal import create_order, get_subscription_status


class DummyResp:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self) -> None:  # pragma: no cover - simple stub
        return None

    def json(self):
        return self._payload


def make_app():
    return create_app(
        {
            "TESTING": True,
            "WTF_CSRF_ENABLED": False,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "MAIL_SERVER": None,
            "PAYPAL_CLIENT_ID": "id",
            "PAYPAL_CLIENT_SECRET": "secret",
            "PAYPAL_API_BASE": "https://api.example.com",
        }
    )


def test_create_order(monkeypatch):
    token_resp = DummyResp({"access_token": "tok"})
    order_resp = DummyResp({"id": "123"})
    called = []

    def fake_post(url, *args, **kwargs):
        called.append(url)
        if url.endswith("/v1/oauth2/token"):
            return token_resp
        assert url.endswith("/v2/checkout/orders")
        assert kwargs["headers"]["Authorization"] == "Bearer tok"
        return order_resp

    monkeypatch.setattr(requests, "post", fake_post)

    app = make_app()
    with app.app_context():
        result = create_order("5.00")

    assert result == {"id": "123"}
    assert called[0].endswith("/v1/oauth2/token")
    assert called[1].endswith("/v2/checkout/orders")


def test_get_subscription_status(monkeypatch):
    token_resp = DummyResp({"access_token": "tok"})
    sub_resp = DummyResp({"status": "ACTIVE"})

    def fake_post(url, *args, **kwargs):
        return token_resp

    def fake_get(url, *args, **kwargs):
        assert url.endswith("/v1/billing/subscriptions/sub123")
        assert kwargs["headers"]["Authorization"] == "Bearer tok"
        return sub_resp

    monkeypatch.setattr(requests, "post", fake_post)
    monkeypatch.setattr(requests, "get", fake_get)

    app = make_app()
    with app.app_context():
        status = get_subscription_status("sub123")

    assert status == "ACTIVE"

