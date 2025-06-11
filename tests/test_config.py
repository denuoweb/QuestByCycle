import os
from app import create_app


def test_session_cookie_domain_defaults(monkeypatch):
    monkeypatch.delenv("SESSION_COOKIE_DOMAIN", raising=False)
    app = create_app({"TESTING": True})
    assert app.config["SESSION_COOKIE_DOMAIN"] is None


def test_session_cookie_domain_env(monkeypatch):
    monkeypatch.setenv("SESSION_COOKIE_DOMAIN", "example.com")
    app = create_app({"TESTING": True})
    assert app.config["SESSION_COOKIE_DOMAIN"] == "example.com"
