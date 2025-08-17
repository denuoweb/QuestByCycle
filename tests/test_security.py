import pytest
from datetime import datetime, timezone

from app import create_app, db
from app.models.user import User


@pytest.fixture
def app():
    app = create_app({
        "TESTING": True,
        "DEBUG": False,
        "WTF_CSRF_ENABLED": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SESSION_COOKIE_SECURE": True,
        "SESSION_COOKIE_SAMESITE": "Strict",
    })
    ctx = app.app_context()
    ctx.push()
    db.create_all()
    yield app
    db.session.remove()
    db.drop_all()
    ctx.pop()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def user(app):
    u = User(
        username="tester",
        email="tester@example.com",
        license_agreed=True,
        email_verified=True,
    )
    u.set_password("secret")
    u.created_at = datetime.now(timezone.utc)
    db.session.add(u)
    db.session.commit()
    return u


def test_session_cookie_flags(client, user, app):
    token_resp = client.get("/refresh-csrf")
    token = token_resp.get_json()["csrf_token"]

    login_resp = client.post(
        "/auth/login",
        data={"email": user.email, "password": "secret"},
        headers={
            "X-CSRFToken": token,
            "X-Requested-With": "XMLHttpRequest",
        },
    )
    cookie_name = app.config["SESSION_COOKIE_NAME"]
    cookies = login_resp.headers.getlist("Set-Cookie")
    session_cookie = next(c for c in cookies if c.startswith(f"{cookie_name}="))
    assert "Secure" in session_cookie
    assert "HttpOnly" in session_cookie
    assert "SameSite=Strict" in session_cookie


def test_missing_csrf_token_rejected(client):
    resp = client.post(
        "/auth/login",
        data={},
        headers={"X-Requested-With": "XMLHttpRequest"},
    )
    assert resp.status_code == 400
    body = resp.get_json()
    assert body["message"] == "CSRF token missing or incorrect"


def test_refresh_csrf_cookie_flags(client):
    resp = client.get("/refresh-csrf")
    cookies = resp.headers.getlist("Set-Cookie")
    csrf_cookie = next(c for c in cookies if c.startswith("csrf_token="))
    assert "Secure" in csrf_cookie
    assert "HttpOnly" in csrf_cookie
    assert "SameSite=Strict" in csrf_cookie
